# 03 — Pods, Deployments y Services en Profundidad

> **Anterior:** [02 - Kind Local Cluster](./02-kind-local-cluster.md) | **Siguiente:** [04 - Networking e Ingress](./04-networking-ingress.md)

---

## 🎯 Objetivos de este módulo

- Dominar Deployments con todas sus opciones
- Entender Services (ClusterIP, NodePort)
- Usar Labels y Selectors correctamente
- Escalar aplicaciones
- Hacer Rolling Updates y Rollbacks

---

## 1. Deployments en profundidad

### Anatomía completa de un Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-app
  namespace: default
  labels:
    app: mi-app
    version: "1.0"
  annotations:
    description: "Mi aplicación de ejemplo"
spec:
  replicas: 3

  # Selector: cómo el Deployment encuentra sus Pods
  selector:
    matchLabels:
      app: mi-app

  # Estrategia de actualización
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # Máximo pods extra durante update
      maxUnavailable: 0    # Mínimo: ningún pod fuera de servicio

  # Template del Pod
  template:
    metadata:
      labels:
        app: mi-app         # Debe coincidir con selector
        version: "1.0"
    spec:
      containers:
      - name: mi-app
        image: nginx:1.25

        # Puertos
        ports:
        - containerPort: 80
          name: http

        # Variables de entorno
        env:
        - name: APP_ENV
          value: "production"
        - name: APP_PORT
          value: "80"

        # Recursos
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"

        # Health checks
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Estrategias de actualización

#### Rolling Update (por defecto)
Actualiza los pods gradualmente, manteniendo el servicio disponible:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Crear 1 pod nuevo antes de eliminar viejo
    maxUnavailable: 0  # Nunca quitar un pod sin tener otro listo
```

#### Recreate
Elimina todos los pods viejos y luego crea los nuevos (hay downtime):

```yaml
strategy:
  type: Recreate
# Útil cuando no puedes tener dos versiones al mismo tiempo
```

---

## 2. Labels y Selectors

Los **labels** son pares clave-valor que se asignan a recursos. Los **selectors** filtran recursos por sus labels.

### Asignar labels

```yaml
metadata:
  labels:
    app: mi-app          # Nombre de la app
    version: "2.0"       # Versión
    env: production      # Ambiente
    tier: frontend       # Capa
    team: platform       # Equipo responsable
```

### Filtrar por labels con kubectl

```bash
# Ver pods con label app=mi-app
kubectl get pods -l app=mi-app

# Ver pods con múltiples labels
kubectl get pods -l app=mi-app,env=production

# Ver pods que NO tienen un label
kubectl get pods -l '!env'

# Ver pods con label env que sea production o staging
kubectl get pods -l 'env in (production, staging)'

# Añadir un label a un pod existente
kubectl label pod mi-pod-abc version=1.1

# Eliminar un label
kubectl label pod mi-pod-abc version-
```

### Selector con matchExpressions (más poderoso)

```yaml
selector:
  matchExpressions:
  - key: app
    operator: In
    values:
    - mi-app
    - mi-app-v2
  - key: env
    operator: NotIn
    values:
    - dev
  - key: tier
    operator: Exists
```

---

## 3. Services en detalle

### ClusterIP (por defecto)

Solo accesible **dentro del cluster**. Ideal para comunicación interna entre microservicios.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - name: http
    protocol: TCP
    port: 8080        # Puerto del Service (dentro del cluster)
    targetPort: 3000  # Puerto donde escucha el contenedor
  type: ClusterIP
```

Acceso interno: `http://backend-service:8080` o `http://backend-service.default.svc.cluster.local:8080`

### NodePort

Expone el servicio en un puerto de **cada nodo** del cluster. Útil para pruebas locales.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - name: http
    protocol: TCP
    port: 80          # Puerto del Service
    targetPort: 80    # Puerto del contenedor
    nodePort: 30080   # Puerto en el nodo (30000-32767)
  type: NodePort
```

Con kind, accedes en: `http://localhost:30080`

### Headless Service (sin ClusterIP)

Útil para StatefulSets y bases de datos:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None    # ← Headless
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

---

## 4. Scaling — Escalar aplicaciones

### Escalar manualmente

```bash
# Escalar a 5 réplicas
kubectl scale deployment mi-app --replicas=5

# Verificar
kubectl get deployment mi-app
kubectl get pods -l app=mi-app
```

### Escalar en el YAML

```yaml
spec:
  replicas: 5    # Cambiar y hacer kubectl apply
```

### Ver el estado del scaling

```bash
# Ver detalles del deployment
kubectl describe deployment mi-app

# Ver el rollout en tiempo real
watch kubectl get pods -l app=mi-app
```

---

## 5. Rolling Updates paso a paso

```bash
# Ver versión actual
kubectl describe deployment mi-app | grep Image

# Actualizar la imagen
kubectl set image deployment/mi-app mi-app=nginx:1.26

# Ver el progreso en tiempo real
kubectl rollout status deployment/mi-app

# Ver el historial
kubectl rollout history deployment/mi-app

# Ver detalles de una revisión
kubectl rollout history deployment/mi-app --revision=2
```

### Cómo funciona el Rolling Update:

```
Antes del update (3 pods con v1):
[Pod-v1] [Pod-v1] [Pod-v1]

Durante el update (maxSurge=1, maxUnavailable=0):
Paso 1: [Pod-v1] [Pod-v1] [Pod-v1] [Pod-v2]  ← crea v2 extra
Paso 2: [Pod-v1] [Pod-v1] [Pod-v2]            ← elimina un v1
Paso 3: [Pod-v1] [Pod-v1] [Pod-v2] [Pod-v2]  ← crea otro v2
Paso 4: [Pod-v1] [Pod-v2] [Pod-v2]            ← elimina otro v1
Paso 5: [Pod-v1] [Pod-v2] [Pod-v2] [Pod-v2]  ← crea el último v2
Paso 6: [Pod-v2] [Pod-v2] [Pod-v2]            ← elimina el último v1

Resultado: 3 pods con v2, sin downtime!
```

---

## 6. Rollback

```bash
# Rollback a la versión anterior
kubectl rollout undo deployment/mi-app

# Rollback a una revisión específica
kubectl rollout undo deployment/mi-app --to-revision=1

# Pausar un rollout
kubectl rollout pause deployment/mi-app

# Reanudar un rollout
kubectl rollout resume deployment/mi-app
```

---

## 🧪 Laboratorio completo

### Preparar el ambiente

```bash
# Asegúrate de tener el cluster corriendo
kubectl config current-context
# Debe ser: kind-curso-k8s

# Si no tienes el cluster, créalo
# Ver módulo 02
```

### Lab 1: Deployment con Node.js

```bash
mkdir -p ~/k8s-lab/lab-03
cd ~/k8s-lab/lab-03
```

Crear una app Node.js simple:

```bash
mkdir -p ~/k8s-lab/lab-03/node-app
cd ~/k8s-lab/lab-03/node-app

# Crear package.json
cat > package.json << 'EOF'
{
  "name": "k8s-demo",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

# Crear la app
cat > index.js << 'EOF'
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const VERSION = process.env.VERSION || 'v1';

app.get('/', (req, res) => {
  res.json({
    message: 'Hola desde Kubernetes!',
    version: VERSION,
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
  console.log(`App ${VERSION} corriendo en puerto ${PORT}`);
});
EOF

# Crear Dockerfile
cat > Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY index.js .
EXPOSE 3000
CMD ["node", "index.js"]
EOF
```

### Lab 2: Build, load y deploy

```bash
# Build imagen v1
docker build -t node-demo:v1 --build-arg VERSION=v1 ~/k8s-lab/lab-03/node-app/

# Cargar en kind
kind load docker-image node-demo:v1 --name curso-k8s

# Crear manifiestos
cd ~/k8s-lab/lab-03

cat > deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-demo
  labels:
    app: node-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: node-demo
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: node-demo
        version: v1
    spec:
      containers:
      - name: node-demo
        image: node-demo:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
        env:
        - name: VERSION
          value: "v1"
        - name: PORT
          value: "3000"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

cat > service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: node-demo-service
spec:
  selector:
    app: node-demo
  ports:
  - name: http
    port: 80
    targetPort: 3000
  type: ClusterIP
EOF

# Aplicar
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Lab 3: Verificar el deployment

```bash
# Ver pods
kubectl get pods -l app=node-demo

# Ver deployment
kubectl get deployment node-demo

# Acceder a la app
kubectl port-forward service/node-demo-service 8080:80 &

curl http://localhost:8080
# Respuesta: {"message":"Hola desde Kubernetes!","version":"v1",...}

# Ver balanceo de carga (diferente hostname cada vez)
for i in {1..5}; do curl -s http://localhost:8080 | jq .hostname; done
```

### Lab 4: Rolling Update

```bash
# Modificar el Dockerfile para v2 (cambio mínimo)
# En una app real, harías cambios de código

# Build v2
cd ~/k8s-lab/lab-03/node-app
cat > index.js << 'EOF'
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const VERSION = process.env.VERSION || 'v2';

app.get('/', (req, res) => {
  res.json({
    message: '¡Actualizado a v2!',
    version: VERSION,
    hostname: require('os').hostname(),
    features: ['nueva-funcionalidad', 'bug-fix'],
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', version: VERSION });
});

app.listen(PORT, () => {
  console.log(`App ${VERSION} corriendo en puerto ${PORT}`);
});
EOF

docker build -t node-demo:v2 ~/k8s-lab/lab-03/node-app/
kind load docker-image node-demo:v2 --name curso-k8s

# En otra terminal, observar los pods en tiempo real:
# kubectl get pods -l app=node-demo -w

# Hacer el rolling update
kubectl set image deployment/node-demo node-demo=node-demo:v2

# Ver el progreso
kubectl rollout status deployment/node-demo

# Verificar la nueva versión
curl http://localhost:8080
# Respuesta: {"message":"¡Actualizado a v2!",...}
```

### Lab 5: Rollback

```bash
# Ver historial
kubectl rollout history deployment/node-demo

# Rollback a v1
kubectl rollout undo deployment/node-demo

# Verificar
kubectl rollout status deployment/node-demo
curl http://localhost:8080
# Debe mostrar v1 de nuevo
```

### Lab 6: Scaling

```bash
# Escalar a 6 réplicas
kubectl scale deployment node-demo --replicas=6

# Ver los pods creados
kubectl get pods -l app=node-demo

# Escalar a 1 réplica
kubectl scale deployment node-demo --replicas=1

# Ver reducción
kubectl get pods -l app=node-demo
```

### Limpiar

```bash
# Matar port-forward
kill %1

kubectl delete -f ~/k8s-lab/lab-03/deployment.yaml
kubectl delete -f ~/k8s-lab/lab-03/service.yaml
```

---

## ✅ Validaciones

```bash
# Deployment con 3 réplicas activas
kubectl get deployment node-demo
# READY: 3/3

# Todos los pods Running
kubectl get pods -l app=node-demo
# STATUS: Running para todos

# Service apuntando a los pods correctos
kubectl describe service node-demo-service
# Endpoints debe mostrar IPs de los pods

# Historial del rollout
kubectl rollout history deployment/node-demo
# Debe mostrar al menos 2 revisiones
```

---

## 🚨 Errores comunes

### Rolling Update se queda pegado

```
Waiting for deployment "mi-app" rollout to finish: 1 out of 3 new replicas have been updated...
```

**Causa:** Los nuevos pods no pasan el readiness probe.  
**Solución:**
```bash
kubectl get pods -l app=mi-app        # Ver qué pasa
kubectl describe pod <nombre-pod-nuevo>  # Ver el error
kubectl logs <nombre-pod-nuevo>          # Ver logs
# Corregir la imagen o el readiness probe
```

### Service no llega a los pods

```bash
# Verificar que el selector del Service coincide con los labels del Pod
kubectl describe service mi-service  # Ver Selector y Endpoints
kubectl get pods --show-labels       # Ver labels de los pods
```

### `exec format error` al hacer build

```
exec /app/index.js: exec format error
```

**Causa:** La imagen fue construida para una arquitectura diferente (ej: Linux/arm64 vs amd64).  
**Solución:**
```bash
# En Mac Apple Silicon, forzar la plataforma
docker build --platform linux/amd64 -t mi-app:v1 .
```

---

## 📝 Resumen

- **Deployment** gestiona rolling updates, rollbacks y scaling
- **Labels** permiten seleccionar y filtrar recursos
- **Service ClusterIP** = comunicación interna
- **Service NodePort** = exposición externa (para pruebas)
- Rolling update: `kubectl set image deployment/...`
- Rollback: `kubectl rollout undo deployment/...`
- Scale: `kubectl scale deployment/... --replicas=N`

---

## ➡️ Siguiente módulo

👉 [04 - Networking e Ingress: Exponer apps al mundo](./04-networking-ingress.md)
