# 01 — Kubernetes Basics: Arquitectura y Objetos Fundamentales

> **Anterior:** [00 - Introducción](./00-introduccion.md) | **Siguiente:** [02 - Kind Local Cluster](./02-kind-local-cluster.md)

---

## 🎯 Objetivos de este módulo

- Entender la arquitectura interna de Kubernetes
- Conocer los objetos principales: Pod, ReplicaSet, Deployment, Service
- Dominar los comandos esenciales de kubectl
- Escribir y aplicar YAML básico

---

## 1. Arquitectura de Kubernetes

Un cluster de Kubernetes tiene dos tipos de componentes:

### Control Plane (El Cerebro)

```
┌────────────────────────────────────────────────────┐
│                   CONTROL PLANE                    │
│                                                    │
│  ┌─────────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ API Server  │  │   etcd   │  │  Scheduler    │ │
│  │ (kube-      │  │ (base de │  │  (decide en   │ │
│  │  apiserver) │  │  datos)  │  │  qué nodo va) │ │
│  └─────────────┘  └──────────┘  └───────────────┘ │
│                                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │         Controller Manager                  │   │
│  │  (monitorea y corrige el estado del cluster)│   │
│  └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

| Componente | Función |
|---|---|
| **API Server** | Punto de entrada de todas las operaciones. kubectl habla con él |
| **etcd** | Base de datos distribuida que guarda todo el estado del cluster |
| **Scheduler** | Decide en qué Node se crea cada Pod |
| **Controller Manager** | Asegura que el estado actual = estado deseado |

### Worker Nodes (Los Trabajadores)

```
┌──────────────────────────────────────────┐
│               WORKER NODE                │
│                                          │
│  ┌──────────┐  ┌──────────┐              │
│  │  kubelet │  │kube-proxy│              │
│  │(agente)  │  │(networking)             │
│  └──────────┘  └──────────┘              │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  Container Runtime (Docker/containerd) │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌───────┐  ┌───────┐  ┌───────┐         │
│  │ Pod 1 │  │ Pod 2 │  │ Pod 3 │         │
│  └───────┘  └───────┘  └───────┘         │
└──────────────────────────────────────────┘
```

| Componente | Función |
|---|---|
| **kubelet** | Agente que corre en cada nodo. Comunica con el API Server |
| **kube-proxy** | Gestiona las reglas de red del nodo |
| **Container Runtime** | Ejecuta los contenedores (Docker, containerd) |

---

## 2. Los objetos fundamentales

### 🟢 Pod

El Pod es la **unidad mínima deployable** en Kubernetes. Contiene uno o más contenedores que comparten:
- Red (misma IP)
- Almacenamiento
- Ciclo de vida

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: mi-primer-pod
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

> **Regla de oro:** Los Pods son **efímeros** — pueden morir en cualquier momento. Por eso usamos Deployments.

### 🔵 ReplicaSet

Garantiza que un número específico de réplicas de un Pod están corriendo en todo momento.

```yaml
# replicaset.yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-replicaset
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
```

> **En práctica**, raramente creas ReplicaSets directamente. Los Deployments los gestionan automáticamente.

### 🟡 Deployment

El **Deployment** es lo que usarás el 90% del tiempo. Gestiona:
- Cuántas réplicas correr
- Rolling updates (actualizar sin downtime)
- Rollbacks

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### 🟠 Service

Los Pods tienen IPs que cambian. Un **Service** da una IP/DNS estable para acceder a un grupo de Pods.

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx      # Conecta con Pods que tengan label app=nginx
  ports:
  - protocol: TCP
    port: 80        # Puerto del Service
    targetPort: 80  # Puerto del contenedor
  type: ClusterIP   # Solo accesible dentro del cluster
```

**Tipos de Service:**

| Tipo | Acceso | Uso |
|---|---|---|
| **ClusterIP** | Solo dentro del cluster | Comunicación interna entre servicios |
| **NodePort** | IP del nodo + puerto fijo | Pruebas locales |
| **LoadBalancer** | IP externa (cloud) | Producción en cloud |

---

## 3. kubectl — La CLI esencial

### Configurar kubectl

```bash
# Ver la configuración actual
kubectl config view

# Ver el cluster actual
kubectl config current-context

# Listar clusters disponibles
kubectl config get-contexts
```

### Comandos GET — Ver recursos

```bash
# Ver todos los pods del namespace actual
kubectl get pods

# Ver pods de todos los namespaces
kubectl get pods -A

# Ver pods con más información
kubectl get pods -o wide

# Ver pods en formato YAML
kubectl get pod mi-pod -o yaml

# Ver varios recursos a la vez
kubectl get pods,services,deployments

# Ver nodos del cluster
kubectl get nodes
```

### Comandos DESCRIBE — Inspeccionar

```bash
# Describir un pod (muy útil para debugging)
kubectl describe pod <nombre-del-pod>

# Describir un deployment
kubectl describe deployment nginx-deployment

# Describir un nodo
kubectl describe node <nombre-del-nodo>
```

### Comandos APPLY — Crear/Actualizar

```bash
# Aplicar un archivo YAML (crear o actualizar)
kubectl apply -f deployment.yaml

# Aplicar todos los YAML de un directorio
kubectl apply -f ./mi-app/

# Crear recurso de forma imperativa (para pruebas rápidas)
kubectl run nginx --image=nginx:1.25
```

### Comandos LOGS — Ver logs

```bash
# Ver logs de un pod
kubectl logs <nombre-del-pod>

# Ver logs en tiempo real (follow)
kubectl logs -f <nombre-del-pod>

# Ver logs de un contenedor específico (si el pod tiene varios)
kubectl logs <nombre-del-pod> -c <nombre-contenedor>

# Ver últimas 50 líneas
kubectl logs --tail=50 <nombre-del-pod>
```

### Comandos DELETE — Eliminar

```bash
# Eliminar un pod
kubectl delete pod <nombre-del-pod>

# Eliminar usando archivo YAML
kubectl delete -f deployment.yaml

# Eliminar un deployment (también elimina sus pods)
kubectl delete deployment nginx-deployment
```

### Comandos EXEC — Ejecutar comandos dentro de un Pod

```bash
# Abrir una terminal interactiva en un pod
kubectl exec -it <nombre-del-pod> -- /bin/bash

# Ejecutar un comando único
kubectl exec <nombre-del-pod> -- ls /app

# En pod con múltiples contenedores
kubectl exec -it <nombre-del-pod> -c <contenedor> -- /bin/sh
```

### Port-forwarding — Acceso local a un servicio

```bash
# Acceder al puerto 80 del pod desde localhost:8080
kubectl port-forward pod/<nombre-del-pod> 8080:80

# Acceder a un service
kubectl port-forward service/nginx-service 8080:80
```

---

## 4. YAML básico de Kubernetes

Todo YAML de Kubernetes tiene esta estructura:

```yaml
apiVersion: <version-de-la-API>   # Ejemplo: apps/v1, v1
kind: <tipo-de-recurso>            # Pod, Deployment, Service, etc.
metadata:
  name: <nombre-del-recurso>       # Nombre único en el namespace
  namespace: default               # Namespace (default si no se especifica)
  labels:                          # Etiquetas para seleccionar recursos
    app: mi-app
    version: "1.0"
spec:                              # La especificación del recurso
  # ... depende del kind
```

**Referencia rápida de apiVersion:**

| Tipo | apiVersion |
|---|---|
| Pod, Service, ConfigMap, Secret | `v1` |
| Deployment, ReplicaSet, DaemonSet | `apps/v1` |
| Ingress | `networking.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling/v2` |
| Role, RoleBinding | `rbac.authorization.k8s.io/v1` |

---

## 🧪 Laboratorio: Tu primer Deployment

### Paso 1: Asegúrate de tener un cluster corriendo

> Si aún no tienes kind instalado, ve al [Módulo 02](./02-kind-local-cluster.md) primero.

```bash
# Verificar que kubectl tiene acceso a un cluster
kubectl cluster-info
kubectl get nodes
```

### Paso 2: Crear el Deployment

```bash
# Crear el archivo deployment.yaml
cat > nginx-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
EOF
```

### Paso 3: Aplicar el Deployment

```bash
kubectl apply -f nginx-deployment.yaml
```

Salida esperada:
```
deployment.apps/nginx-deployment created
```

### Paso 4: Ver los Pods creados

```bash
kubectl get pods
```

Salida esperada:
```
NAME                                READY   STATUS    RESTARTS   AGE
nginx-deployment-7b9f4c8888-abc12   1/1     Running   0          30s
nginx-deployment-7b9f4c8888-def34   1/1     Running   0          30s
nginx-deployment-7b9f4c8888-ghi56   1/1     Running   0          30s
```

### Paso 5: Ver logs de un Pod

```bash
# Toma el nombre de uno de tus pods
kubectl logs nginx-deployment-7b9f4c8888-abc12
```

### Paso 6: Describir el Deployment

```bash
kubectl describe deployment nginx-deployment
```

### Paso 7: Escalar el Deployment

```bash
# Escalar a 5 réplicas
kubectl scale deployment nginx-deployment --replicas=5

# Verificar
kubectl get pods
```

### Paso 8: Hacer un Rolling Update

```bash
# Actualizar la imagen de nginx
kubectl set image deployment/nginx-deployment nginx=nginx:1.26

# Ver el progreso del rollout
kubectl rollout status deployment/nginx-deployment
```

### Paso 9: Rollback

```bash
# Ver historial de deploys
kubectl rollout history deployment/nginx-deployment

# Hacer rollback a la versión anterior
kubectl rollout undo deployment/nginx-deployment
```

### Paso 10: Limpiar

```bash
kubectl delete -f nginx-deployment.yaml
# O directamente:
kubectl delete deployment nginx-deployment
```

---

## ✅ Validaciones

```bash
# El deployment debe mostrar READY 3/3
kubectl get deployment nginx-deployment

# Los pods deben estar en estado Running
kubectl get pods -l app=nginx

# Debe mostrar 3 pods en los eventos
kubectl describe deployment nginx-deployment | grep -A5 "Replicas:"
```

---

## 🚨 Errores comunes

### Error: `ImagePullBackOff`
```
STATUS: ImagePullBackOff
```
**Causa:** K8s no puede descargar la imagen Docker.  
**Solución:**
```bash
kubectl describe pod <nombre-pod>  # Ver el error exacto
# Verificar nombre de la imagen y tag
# Verificar conexión a internet
```

### Error: `CrashLoopBackOff`
```
STATUS: CrashLoopBackOff
```
**Causa:** El contenedor arranca y se cae repetidamente.  
**Solución:**
```bash
kubectl logs <nombre-pod>           # Ver los logs del crash
kubectl logs <nombre-pod> --previous  # Ver logs del crash anterior
```

### Error: `Pending`
```
STATUS: Pending
```
**Causa:** El Pod no puede ser asignado a ningún nodo (recursos insuficientes).  
**Solución:**
```bash
kubectl describe pod <nombre-pod>   # Ver la razón en Events
kubectl get nodes                   # Ver el estado de los nodos
```

### Error: `kubectl: command not found`
**Causa:** kubectl no está instalado o no está en el PATH.  
**Solución:**
```bash
brew install kubectl
```

---

## 📝 Resumen

- **Control Plane** = El cerebro (API Server, etcd, Scheduler, Controller Manager)
- **Worker Nodes** = Donde corren los Pods
- **Pod** = Unidad mínima, ephemeral
- **ReplicaSet** = Garantiza N réplicas
- **Deployment** = Gestiona ReplicaSets + rolling updates
- **Service** = IP estable para acceder a Pods
- **kubectl** = La CLI que usarás todo el tiempo

---

## ➡️ Siguiente módulo

👉 [02 - Kind Local Cluster: Tu cluster Kubernetes en Docker](./02-kind-local-cluster.md)
