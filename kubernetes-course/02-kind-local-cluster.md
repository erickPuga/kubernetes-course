# 02 — Kind: Tu Cluster Kubernetes Local

> **Anterior:** [01 - Kubernetes Basics](./01-kubernetes-basics.md) | **Siguiente:** [03 - Pods, Deployments, Services](./03-pods-deployments-services.md)

---

## 🎯 Objetivos de este módulo

- Instalar kind en Mac
- Crear tu primer cluster de Kubernetes local
- Cargar imágenes Docker locales en kind
- Gestionar múltiples clusters
- Eliminar y recrear clusters

---

## 1. ¿Qué es kind?

**kind** = **K**ubernetes **IN** **D**ocker

kind corre nodos de Kubernetes como **contenedores Docker** en tu Mac. Esto lo hace perfecto para:
- Aprender Kubernetes sin necesidad de VMs ni Cloud
- Desarrollo y pruebas locales
- CI/CD testing

```
Tu Mac
└── Docker Desktop
    ├── contenedor: kind-control-plane  ← Nodo Control Plane de K8s
    ├── contenedor: kind-worker         ← Nodo Worker 1
    └── contenedor: kind-worker2        ← Nodo Worker 2
```

### kind vs otras alternativas

| Herramienta | Descripción | Uso recomendado |
|---|---|---|
| **kind** | K8s en Docker containers | CI/CD, aprendizaje, tests |
| minikube | VM con K8s | Aprendizaje básico |
| k3s/k3d | K8s ligero | Edge, recursos limitados |
| Docker Desktop K8s | K8s integrado en Docker Desktop | Muy básico |

---

## 2. Instalación en Mac

### Requisitos previos

```bash
# Verificar que Docker Desktop está corriendo
docker info

# Si Docker no está instalado, descargar de:
# https://www.docker.com/products/docker-desktop/
```

### Instalar kind y kubectl

```bash
# Instalar kind
brew install kind

# Instalar kubectl (si no lo tienes)
brew install kubectl

# Verificar instalaciones
kind --version
# kind v0.22.0 (o similar)

kubectl version --client
# Client Version: v1.29.x (o similar)
```

### Instalación manual (sin Homebrew)

```bash
# Para Mac Intel (amd64)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-darwin-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Para Mac Apple Silicon (arm64)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-darwin-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

---

## 3. Crear tu primer cluster kind

### Cluster básico (1 nodo)

```bash
# Crear cluster con nombre por defecto "kind"
kind create cluster

# Salida esperada:
# Creating cluster "kind" ...
#  ✓ Ensuring node image (kindest/node:v1.29.2) 🖼
#  ✓ Preparing nodes 📦
#  ✓ Writing configuration 📜
#  ✓ Starting control-plane 🕹️
#  ✓ Installing CNI 🔌
#  ✓ Installing StorageClass 💾
# Set kubectl context to "kind-kind"
# You can now use your cluster with:
# kubectl cluster-info --context kind-kind
```

```bash
# Verificar que el cluster está corriendo
kubectl cluster-info
kubectl get nodes
```

Salida esperada:
```
NAME                 STATUS   ROLES           AGE   VERSION
kind-control-plane   Ready    control-plane   1m    v1.29.2
```

---

## 4. Configuración recomendada — Cluster multi-nodo

Para el curso, usaremos un cluster con **1 control-plane + 2 workers**:

```bash
# Crear archivo de configuración
cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: curso-k8s
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
```

```bash
# Crear el cluster con la configuración
kind create cluster --config kind-config.yaml

# Verificar nodos
kubectl get nodes
```

Salida esperada:
```
NAME                      STATUS   ROLES           AGE   VERSION
curso-k8s-control-plane   Ready    control-plane   2m    v1.29.2
curso-k8s-worker          Ready    <none>          1m    v1.29.2
curso-k8s-worker2         Ready    <none>          1m    v1.29.2
```

> Los puertos 80 y 443 en el control-plane son necesarios para el **NGINX Ingress Controller** que usaremos en el [Módulo 04](./04-networking-ingress.md).

---

## 5. Gestionar múltiples clusters

```bash
# Listar todos los clusters kind
kind get clusters

# Cambiar entre clusters (contextos kubectl)
kubectl config get-contexts

# Usar un cluster específico
kubectl config use-context kind-curso-k8s

# Ver el cluster actual
kubectl config current-context
```

---

## 6. Cargar imágenes Docker locales en kind

Este es uno de los pasos más importantes: kind corre en Docker, pero **no tiene acceso al Docker daemon de tu Mac directamente**. Debes cargar las imágenes manualmente.

### Sin cargar la imagen (ERROR)

```bash
# Si intentas usar una imagen local sin cargarla:
kubectl run mi-app --image=mi-imagen-local:v1
# Error: ErrImagePull / ImagePullBackOff ← K8s no encuentra la imagen
```

### Cómo cargar imágenes correctamente

```bash
# Paso 1: Construir la imagen con Docker normalmente
docker build -t mi-app:v1 ./mi-app/

# Paso 2: Cargar la imagen en el cluster kind
kind load docker-image mi-app:v1 --name curso-k8s

# Paso 3: En el YAML, usar imagePullPolicy: Never o IfNotPresent
# para que K8s use la imagen local y no intente descargarla
```

Ejemplo de Deployment con imagen local:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mi-app
  template:
    metadata:
      labels:
        app: mi-app
    spec:
      containers:
      - name: mi-app
        image: mi-app:v1
        imagePullPolicy: Never   # ← IMPORTANTE: usar imagen local
        ports:
        - containerPort: 3000
```

### Verificar imágenes cargadas en kind

```bash
# Ver imágenes disponibles en el cluster
docker exec -it curso-k8s-control-plane crictl images
```

---

## 🧪 Laboratorio: Crear cluster y desplegar imagen custom

### Paso 1: Crear el archivo de configuración

```bash
mkdir -p ~/k8s-lab
cd ~/k8s-lab

cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: curso-k8s
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
```

### Paso 2: Crear el cluster

```bash
kind create cluster --config kind-config.yaml

# Verificar
kubectl get nodes
kubectl cluster-info
```

### Paso 3: Crear una imagen Docker custom

```bash
# Crear una app web simple
mkdir -p ~/k8s-lab/mi-web
cd ~/k8s-lab/mi-web

# Crear index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Mi App en K8s</title></head>
<body>
  <h1>🚀 Hola desde Kubernetes!</h1>
  <p>Esta app corre en un Pod dentro de kind.</p>
</body>
</html>
EOF

# Crear Dockerfile
cat > Dockerfile << 'EOF'
FROM nginx:1.25-alpine
COPY index.html /usr/share/nginx/html/index.html
EOF
```

### Paso 4: Construir y cargar la imagen

```bash
# Construir la imagen
docker build -t mi-web:v1 ~/k8s-lab/mi-web/

# Verificar que existe en Docker
docker images | grep mi-web

# Cargar la imagen en kind
kind load docker-image mi-web:v1 --name curso-k8s

# Verificar que se cargó
docker exec -it curso-k8s-control-plane crictl images | grep mi-web
```

### Paso 5: Desplegar la imagen en Kubernetes

```bash
cat > ~/k8s-lab/mi-web-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-web
  labels:
    app: mi-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mi-web
  template:
    metadata:
      labels:
        app: mi-web
    spec:
      containers:
      - name: mi-web
        image: mi-web:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: mi-web-service
spec:
  selector:
    app: mi-web
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f ~/k8s-lab/mi-web-deployment.yaml
```

### Paso 6: Ver los pods y acceder a la app

```bash
# Ver pods
kubectl get pods -l app=mi-web

# Acceder a la app via port-forward
kubectl port-forward service/mi-web-service 8080:80 &

# Abrir en el navegador
open http://localhost:8080
# O con curl:
curl http://localhost:8080
```

### Paso 7: Ver los nodos y sus pods

```bash
# Ver en qué nodo está cada pod
kubectl get pods -o wide

# Ver detalles del nodo
kubectl describe node curso-k8s-worker
```

### Paso 8: Limpiar

```bash
# Matar el port-forward
kill %1

# Eliminar los recursos
kubectl delete -f ~/k8s-lab/mi-web-deployment.yaml
```

---

## 7. Comandos útiles de kind

```bash
# Crear cluster con nombre específico
kind create cluster --name mi-cluster

# Crear cluster con versión específica de K8s
kind create cluster --image kindest/node:v1.28.0

# Listar clusters
kind get clusters

# Ver nodos de un cluster
kind get nodes --name curso-k8s

# Obtener kubeconfig
kind get kubeconfig --name curso-k8s

# Exportar kubeconfig a archivo
kind get kubeconfig --name curso-k8s > ~/.kube/kind-config

# Eliminar un cluster específico
kind delete cluster --name curso-k8s

# Eliminar todos los clusters
kind delete clusters --all
```

---

## 8. Eliminar el cluster

```bash
# Eliminar el cluster del curso
kind delete cluster --name curso-k8s

# Verificar que se eliminó
kind get clusters
docker ps  # No deben aparecer contenedores de kind
```

---

## ✅ Validaciones

```bash
# 1. Cluster debe estar corriendo
kind get clusters
# curso-k8s

# 2. Todos los nodos deben estar Ready
kubectl get nodes
# NAME                      STATUS   ROLES           
# curso-k8s-control-plane   Ready    control-plane   
# curso-k8s-worker          Ready    <none>          
# curso-k8s-worker2         Ready    <none>          

# 3. Pods del sistema deben estar Running
kubectl get pods -n kube-system

# 4. Context activo correcto
kubectl config current-context
# kind-curso-k8s
```

---

## 🚨 Errores comunes

### Error: `Docker not running`
```
ERROR: failed to create cluster: failed to list nodes: ...
```
**Causa:** Docker Desktop no está abierto.  
**Solución:** Abrir Docker Desktop y esperar a que inicie completamente.

### Error: `port is already allocated`
```
ERROR: failed to create cluster: ... address already in use
```
**Causa:** El puerto 80 o 443 ya está en uso por otro proceso.  
**Solución:**
```bash
# Ver qué usa el puerto 80
lsof -i :80
# Matar el proceso o cambiar el puerto en kind-config.yaml
```

### Error: `ImagePullBackOff` con imagen local
```
STATUS: ImagePullBackOff
```
**Causa:** Olvidaste cargar la imagen en kind.  
**Solución:**
```bash
kind load docker-image mi-imagen:tag --name curso-k8s
# Y asegúrate de usar imagePullPolicy: Never en el YAML
```

### Error: `Cannot connect to Docker daemon`
```
ERROR: Cannot connect to the Docker daemon
```
**Causa:** Docker no está instalado o el servicio no está corriendo.  
**Solución:**
```bash
# Verificar Docker
docker info
# Reiniciar Docker Desktop si es necesario
```

### El cluster está lento al crear

Esto es normal la primera vez porque descarga la imagen `kindest/node` (~700MB). Las siguientes veces es mucho más rápido porque la imagen ya está en caché.

---

## 📝 Resumen

- **kind** corre K8s dentro de contenedores Docker — perfecto para Mac
- Crear cluster: `kind create cluster --config kind-config.yaml`
- Para imágenes locales: `kind load docker-image imagen:tag --name cluster`
- Siempre usar `imagePullPolicy: Never` para imágenes locales
- Eliminar cluster: `kind delete cluster --name cluster`

---

## ➡️ Siguiente módulo

👉 [03 - Pods, Deployments y Services en profundidad](./03-pods-deployments-services.md)
