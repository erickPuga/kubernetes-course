# 04 — Networking e Ingress: Exponer Apps al Mundo

> **Anterior:** [03 - Pods, Deployments, Services](./03-pods-deployments-services.md) | **Siguiente:** [05 - ConfigMaps y Secrets](./05-configmaps-secrets.md)

---

## 🎯 Objetivos de este módulo

- Entender el modelo de networking de Kubernetes
- Instalar NGINX Ingress Controller en kind
- Configurar Ingress con hosts y paths
- Acceder a una app desde el navegador usando un dominio local
- Debuggear problemas de Ingress

---

## 1. Networking en Kubernetes

### Modelo fundamental

Kubernetes tiene 4 problemas de networking que resuelve:

```
1. Comunicación contenedor-a-contenedor    → Misma red del Pod (localhost)
2. Comunicación Pod-a-Pod                  → Red flat del cluster (sin NAT)
3. Comunicación Pod-a-Service              → kube-proxy + iptables
4. Comunicación externa-a-Service          → Ingress / LoadBalancer
```

### Red del cluster

```
┌──────────────────────────────────────────────────────┐
│                   CLUSTER NETWORK                    │
│                                                      │
│  Pod A (10.244.0.1)  ──────→  Pod B (10.244.1.5)    │
│         ↕                                            │
│  Service (10.96.0.100)                               │
│         ↕                                            │
│  Ingress Controller                                  │
│         ↕                                            │
│  Tu navegador (localhost)                            │
└──────────────────────────────────────────────────────┘
```

### DNS interno de K8s

Kubernetes provee DNS automático:

```bash
# Formato: <service>.<namespace>.svc.cluster.local
backend-service.default.svc.cluster.local
postgres.database.svc.cluster.local

# Dentro del mismo namespace, puedes usar solo el nombre:
http://backend-service:8080

# Desde otro namespace:
http://backend-service.default.svc.cluster.local:8080
```

---

## 2. Ingress vs Service

| | Service (NodePort/LoadBalancer) | Ingress |
|---|---|---|
| **Routing** | Solo por puerto | Por host y path |
| **SSL/TLS** | Manual | Centralizado |
| **Cost** | 1 IP/LB por servicio | 1 LB para todo |
| **Funcionalidades** | Básicas | Rewrite, auth, rate limiting |

**Cuándo usar Ingress:**
- Múltiples servicios bajo un mismo dominio
- Routing por path (`/api/`, `/frontend/`, `/admin/`)
- SSL termination centralizado

---

## 3. NGINX Ingress Controller en kind

### ¿Qué es un Ingress Controller?

Un **Ingress** por sí solo es solo una configuración (reglas). Necesitas un **Ingress Controller** que ejecute esas reglas. Usaremos NGINX.

```
Tráfico → Ingress Controller (NGINX Pod) → Service → Pods
                    ↑
          Lee las reglas del Ingress
```

### Instalar NGINX Ingress en kind

> **Prerrequisito:** El cluster kind debe tener el puerto 80 mapeado (como en el `kind-config.yaml` del [Módulo 02](./02-kind-local-cluster.md))

```bash
# Instalar NGINX Ingress Controller para kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Esperar a que esté listo (puede tomar 1-2 minutos)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Verificar la instalación

```bash
# Ver el namespace ingress-nginx
kubectl get all -n ingress-nginx

# El pod del controller debe estar Running
kubectl get pods -n ingress-nginx
# NAME                                        READY   STATUS
# ingress-nginx-controller-xxxxxxxxx-xxxxx    1/1     Running
```

---

## 4. Configurar Ingress

### Ingress básico por path

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mi-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 3000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Ingress por host (virtual hosting)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 3000
```

### Usar dominios locales en Mac

Para que `app.local` y `api.local` resuelvan a localhost, edita `/etc/hosts`:

```bash
# Agregar al final de /etc/hosts
sudo sh -c 'echo "127.0.0.1 app.local api.local" >> /etc/hosts'

# Verificar
cat /etc/hosts | grep local
ping -c 1 app.local  # Debe responder 127.0.0.1
```

### PathType explicado

| PathType | Ejemplo path | Coincide con |
|---|---|---|
| `Exact` | `/api/v1` | Solo `/api/v1` |
| `Prefix` | `/api` | `/api`, `/api/users`, `/api/v1/...` |
| `ImplementationSpecific` | Depende del controller | Varía |

---

## 5. Annotations de NGINX Ingress

```yaml
metadata:
  annotations:
    # Reescribir el path antes de enviarlo al backend
    nginx.ingress.kubernetes.io/rewrite-target: /$2

    # Habilitar CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"

    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "10"

    # Tamaño máximo del body
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"

    # Timeout
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"

    # SSL redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
```

---

## 6. Debugging de Ingress

```bash
# Ver todos los ingress
kubectl get ingress

# Describir un ingress (ver eventos y estado)
kubectl describe ingress mi-ingress

# Ver logs del ingress controller
kubectl logs -n ingress-nginx \
  $(kubectl get pods -n ingress-nginx -o jsonpath='{.items[0].metadata.name}')

# Ver logs en tiempo real
kubectl logs -n ingress-nginx \
  $(kubectl get pods -n ingress-nginx -o jsonpath='{.items[0].metadata.name}') -f

# Verificar que el Service existe y tiene endpoints
kubectl get endpoints mi-service

# Test directo desde dentro del cluster
kubectl run test-pod --image=curlimages/curl -it --rm --restart=Never -- \
  curl http://backend-service:3000/health
```

---

## 🧪 Laboratorio: Publicar dos apps vía Ingress

### Preparar el ambiente

```bash
mkdir -p ~/k8s-lab/lab-04
cd ~/k8s-lab/lab-04
```

### Paso 1: Crear dos apps

**App Frontend (simple HTML):**

```bash
mkdir -p ~/k8s-lab/lab-04/frontend
cat > ~/k8s-lab/lab-04/frontend/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <title>Frontend - Kubernetes Demo</title>
  <style>
    body { font-family: Arial; text-align: center; margin-top: 50px; background: #f0f8ff; }
    .card { background: white; padding: 30px; border-radius: 10px;
            display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
  </style>
</head>
<body>
  <div class="card">
    <h1>🚀 Frontend</h1>
    <p>Sirviendo desde Kubernetes con NGINX Ingress</p>
    <p>Visita <a href="http://api.local/health">/api para el backend</a></p>
  </div>
</body>
</html>
EOF

cat > ~/k8s-lab/lab-04/frontend/Dockerfile << 'EOF'
FROM nginx:1.25-alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
EOF
```

**App Backend (Node.js):**

```bash
mkdir -p ~/k8s-lab/lab-04/backend
cat > ~/k8s-lab/lab-04/backend/package.json << 'EOF'
{
  "name": "backend-demo",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

cat > ~/k8s-lab/lab-04/backend/index.js << 'EOF'
const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

// CORS para el frontend
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  next();
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'backend' });
});

app.get('/api/info', (req, res) => {
  res.json({
    service: 'backend-api',
    version: '1.0.0',
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
EOF

cat > ~/k8s-lab/lab-04/backend/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY index.js .
EXPOSE 3000
CMD ["node", "index.js"]
EOF
```

### Paso 2: Build y cargar imágenes

```bash
docker build -t frontend-demo:v1 ~/k8s-lab/lab-04/frontend/
docker build -t backend-demo:v1 ~/k8s-lab/lab-04/backend/

kind load docker-image frontend-demo:v1 --name curso-k8s
kind load docker-image backend-demo:v1 --name curso-k8s
```

### Paso 3: Crear manifiestos de K8s

```bash
cat > ~/k8s-lab/lab-04/k8s-manifests.yaml << 'EOF'
# ── FRONTEND ──────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: frontend-demo:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
---
# ── BACKEND ───────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: backend-demo:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
---
# ── INGRESS ───────────────────────────────────────────
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: demo-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
  - host: app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 3000
EOF

kubectl apply -f ~/k8s-lab/lab-04/k8s-manifests.yaml
```

### Paso 4: Configurar /etc/hosts

```bash
# Agregar dominios locales
echo "127.0.0.1 app.local api.local" | sudo tee -a /etc/hosts

# Verificar
grep "app.local" /etc/hosts
```

### Paso 5: Verificar y probar

```bash
# Ver todos los recursos
kubectl get pods,services,ingress

# Esperar a que los pods estén Running
kubectl wait --for=condition=ready pod -l app=frontend --timeout=60s
kubectl wait --for=condition=ready pod -l app=backend --timeout=60s

# Probar desde terminal
curl http://app.local
curl http://api.local/health
curl http://api.local/api/info

# Abrir en el navegador
open http://app.local
open http://api.local/api/info
```

### Paso 6: Debugging

```bash
# Ver el ingress
kubectl describe ingress demo-ingress

# Ver logs del nginx ingress controller
kubectl logs -n ingress-nginx \
  $(kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o name) \
  --tail=20

# Ver endpoints de los servicios
kubectl get endpoints frontend-service backend-service
```

### Limpiar

```bash
kubectl delete -f ~/k8s-lab/lab-04/k8s-manifests.yaml

# Limpiar /etc/hosts (opcional)
# sudo nano /etc/hosts   ← elimina las líneas app.local api.local
```

---

## ✅ Validaciones

```bash
# 1. Ingress controller corriendo
kubectl get pods -n ingress-nginx
# STATUS: Running

# 2. Ingress creado correctamente
kubectl get ingress demo-ingress
# Debe mostrar ADDRESS: localhost

# 3. Frontend accesible
curl -s http://app.local | grep "Frontend"

# 4. Backend accesible
curl -s http://api.local/health | jq .status
# "healthy"

# 5. Routing correcto
# app.local → frontend (nginx en puerto 80)
# api.local → backend (node en puerto 3000)
```

---

## 🚨 Errores comunes

### `curl: (7) Failed to connect to app.local port 80`

**Causa:** No se agregó el dominio a `/etc/hosts` o el ingress controller no está listo.  
**Solución:**
```bash
# Verificar /etc/hosts
grep app.local /etc/hosts

# Verificar ingress controller
kubectl get pods -n ingress-nginx

# Si el kind cluster no tiene el puerto 80 mapeado:
# Recrear el cluster con el kind-config.yaml del módulo 02
```

### `404 Not Found` desde nginx

**Causa:** El Ingress no encuentra el Service o tiene un selector incorrecto.  
**Solución:**
```bash
kubectl describe ingress demo-ingress
kubectl get endpoints frontend-service
# Si Endpoints es <none>, el Service no tiene pods que coincidan
```

### `502 Bad Gateway`

**Causa:** El servicio backend no está respondiendo.  
**Solución:**
```bash
kubectl get pods -l app=backend
kubectl logs <nombre-del-pod-backend>
kubectl port-forward service/backend-service 3001:3000
curl http://localhost:3001/health  # Probar directamente
```

### Ingress no tiene ADDRESS

```bash
kubectl get ingress
# ADDRESS está vacío
```

**Causa:** El ingress controller no está instalado o no tiene la clase `nginx`.  
**Solución:**
```bash
# Verificar que existe el IngressClass
kubectl get ingressclass

# Si no existe, reinstalar el ingress controller:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

---

## 📝 Resumen

- **Ingress** gestiona el acceso externo HTTP/HTTPS con routing por host y path
- **NGINX Ingress Controller** ejecuta las reglas del Ingress
- En kind: los puertos 80/443 deben estar mapeados en `kind-config.yaml`
- Usa `/etc/hosts` para dominios locales en desarrollo
- Debug: `kubectl describe ingress`, logs del controller, `kubectl get endpoints`

---

## ➡️ Siguiente módulo

👉 [05 - ConfigMaps y Secrets: Gestión de configuración](./05-configmaps-secrets.md)
