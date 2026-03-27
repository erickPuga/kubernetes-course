# 08 — Observabilidad y Operaciones

> **Anterior:** [07 - Seguridad y RBAC](./07-security-rbac.md) | **Siguiente:** [09 - Helm y Kustomize](./09-packaging-helm-kustomize.md)

---

## Objetivos de este modulo

- Configurar Liveness y Readiness Probes
- Definir Resource Requests y Limits
- Entender HPA (Horizontal Pod Autoscaler)
- Dominar el debugging con logs
- Introduccion a Prometheus y Grafana

---

## 1. Health Probes

Kubernetes usa probes para saber si un Pod esta sano y listo para recibir trafico.

### Tipos de Probes

| Probe | Pregunta | Accion si falla |
|---|---|---|
| **livenessProbe** | Esta vivo el contenedor? | Reinicia el contenedor |
| **readinessProbe** | Esta listo para recibir trafico? | Lo saca del Service (sin reiniciar) |
| **startupProbe** | Ha terminado de iniciar? | Bloquea liveness/readiness hasta que pase |

### Metodos de probe

```yaml
# 1. HTTP GET (mas comun para APIs)
livenessProbe:
  httpGet:
    path: /health
    port: 3000
    httpHeaders:
    - name: X-Health-Check
      value: "true"
  initialDelaySeconds: 15    # Esperar antes del primer check
  periodSeconds: 10          # Cada cuanto verificar
  timeoutSeconds: 5          # Timeout de la peticion
  failureThreshold: 3        # Fallos antes de reiniciar
  successThreshold: 1        # Exitos para considerar sano

# 2. TCP Socket (para bases de datos, etc.)
readinessProbe:
  tcpSocket:
    port: 5432
  initialDelaySeconds: 10
  periodSeconds: 5

# 3. Exec (ejecutar un comando)
livenessProbe:
  exec:
    command:
    - pg_isready
    - -U
    - postgres
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Configuracion recomendada por tipo de app

```yaml
# API REST (Node.js, Python Flask, etc.)
livenessProbe:
  httpGet:
    path: /health/live
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 15
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2

# App con inicio lento (JVM, etc.)
startupProbe:
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30     # 30 * 10s = 5 minutos para iniciar
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
```

### Endpoints de health recomendados

```javascript
// Node.js Express - health endpoints
app.get('/health/live', (req, res) => {
  // Solo verificar si el proceso esta vivo
  res.json({ status: 'alive' });
});

app.get('/health/ready', async (req, res) => {
  try {
    // Verificar que las dependencias estan listas
    await db.query('SELECT 1');  // Test DB
    res.json({ status: 'ready', db: 'connected' });
  } catch (err) {
    res.status(503).json({ status: 'not ready', error: err.message });
  }
});
```

---

## 2. Resource Requests y Limits

### Conceptos

```
requests = lo que el scheduler garantiza (minimo reservado)
limits   = el maximo que puede usar (techo)
```

```yaml
resources:
  requests:
    memory: "128Mi"   # El nodo debe tener al menos 128MB disponibles
    cpu: "100m"       # 100 millicores = 0.1 CPU cores
  limits:
    memory: "256Mi"   # Si supera 256MB → OOMKilled
    cpu: "500m"       # Si supera 0.5 CPU → throttled (no muere, se limita)
```

### Unidades

**CPU:**
- `1` = 1 core completo
- `500m` = 0.5 cores (500 millicores)
- `100m` = 0.1 cores

**Memoria:**
- `Mi` = Mebibytes (1 Mi = 1024 * 1024 bytes)
- `Gi` = Gibibytes
- `M` = Megabytes (1 M = 1000 * 1000 bytes)

### Recomendaciones de sizing

```yaml
# App Node.js ligera
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "200m"

# API con base de datos
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"

# PostgreSQL
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "1000m"

# JVM (Spring Boot)
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Ver uso actual de recursos

```bash
# Ver uso de CPU y memoria por nodo
kubectl top nodes

# Ver uso de CPU y memoria por pod
kubectl top pods

# Ver uso en todos los namespaces
kubectl top pods -A
```

> Necesitas metrics-server instalado. En kind:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# Para kind, agregar --kubelet-insecure-tls al deployment de metrics-server
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

---

## 3. HPA — Horizontal Pod Autoscaler

El HPA escala automaticamente el numero de replicas basandose en metricas.

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2       # Minimo de pods
  maxReplicas: 10      # Maximo de pods
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # Escala si CPU > 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80   # Escala si memoria > 80%
```

```bash
# Ver el HPA y su estado
kubectl get hpa

# Describir el HPA (ver cuando escalo y por que)
kubectl describe hpa backend-hpa

# Simular carga para probar el HPA
kubectl run load-test --image=busybox --rm -it --restart=Never -- \
  sh -c "while true; do wget -q -O- http://backend-service/; done"
```

---

## 4. Logs en Kubernetes

### Comandos esenciales

```bash
# Ver logs de un pod
kubectl logs <nombre-pod>

# Logs en tiempo real (follow)
kubectl logs -f <nombre-pod>

# Ultimas 100 lineas
kubectl logs --tail=100 <nombre-pod>

# Logs desde hace 1 hora
kubectl logs --since=1h <nombre-pod>

# Logs de un contenedor especifico (multi-container pod)
kubectl logs <nombre-pod> -c <nombre-contenedor>

# Logs del pod anterior (si crasheo)
kubectl logs <nombre-pod> --previous

# Logs de todos los pods de un deployment
kubectl logs -l app=backend --all-containers=true

# Logs de un deployment directamente
kubectl logs deployment/backend
```

### Filtrar logs

```bash
# Buscar errores en los logs
kubectl logs <nombre-pod> | grep -i error

# Buscar por texto
kubectl logs <nombre-pod> | grep "POST /api"

# Ver solo los ultimos errores en tiempo real
kubectl logs -f <nombre-pod> | grep -i "error\|fatal\|exception"
```

### Agregar logs estructurados en Node.js

```javascript
// Usar JSON logging para mejor integracion con herramientas
const log = (level, message, meta = {}) => {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...meta,
    pod: process.env.HOSTNAME,
    service: process.env.APP_NAME || 'unknown'
  }));
};

// Uso:
log('info', 'Request received', { method: 'GET', path: '/api/tasks' });
log('error', 'DB connection failed', { error: err.message });
```

---

## 5. Debugging avanzado

### Comandos de diagnostico completo

```bash
# Ver el estado de todos los recursos en un namespace
kubectl get all -n mi-namespace

# Ver eventos recientes del cluster
kubectl get events --sort-by='.lastTimestamp'

# Ver eventos de un namespace especifico
kubectl get events -n mi-namespace --sort-by='.lastTimestamp'

# Describir pod (ver eventos, condiciones, contenedores)
kubectl describe pod <nombre-pod>

# Ver por que un pod no inicia
kubectl describe pod <nombre-pod> | grep -A20 "Events:"

# Ejecutar un pod de debug temporal
kubectl run debug-pod \
  --image=nicolaka/netshoot \
  --rm -it \
  --restart=Never \
  -- bash
```

### Debugging de red

```bash
# Desde el pod de debug, probar conectividad
kubectl run nettest --image=curlimages/curl \
  --rm -it --restart=Never \
  -- curl http://backend-service:3000/health

# Ver las reglas de iptables en un nodo
kubectl debug node/curso-k8s-worker1 \
  -it --image=ubuntu -- bash

# Verificar DNS
kubectl run dns-test --image=busybox \
  --rm -it --restart=Never \
  -- nslookup backend-service.default.svc.cluster.local
```

### Debugging de un contenedor que no inicia

```bash
# El contenedor crashea antes de poder hacer exec
# Usar una imagen alternativa para debug:
kubectl debug <nombre-pod> \
  -it \
  --image=ubuntu \
  --copy-to=debug-pod \
  --container=debug

# O modificar el comando del contenedor para que no crashee
# (temporal para investigar)
kubectl patch deployment mi-app \
  --type='json' \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["sleep","3600"]}]'
```

---

## 6. Introduccion a Prometheus y Grafana

### Arquitectura de observabilidad

```
Tu App → expone metricas en /metrics
Prometheus → las recolecta y almacena
Grafana → las visualiza con dashboards
AlertManager → envia alertas
```

### Instalar con kube-prometheus-stack (Helm)

```bash
# Agregar repo de Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Instalar el stack completo
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123

# Ver los pods instalados
kubectl get pods -n monitoring

# Acceder a Grafana
kubectl port-forward -n monitoring service/monitoring-grafana 3000:80 &
open http://localhost:3000
# Usuario: admin
# Password: admin123
```

### Exponer metricas desde Node.js

```bash
npm install prom-client
```

```javascript
const express = require('express');
const client = require('prom-client');
const app = express();

// Habilitar metricas por defecto (CPU, memoria, etc.)
const collectDefaultMetrics = client.collectDefaultMetrics;
collectDefaultMetrics();

// Metrica personalizada: contador de requests
const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status']
});

// Middleware para contar requests
app.use((req, res, next) => {
  res.on('finish', () => {
    httpRequestsTotal.inc({
      method: req.method,
      path: req.path,
      status: res.statusCode
    });
  });
  next();
});

// Endpoint de metricas para Prometheus
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

### ServiceMonitor para que Prometheus scrape tu app

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
```

---

## Lab: Configurar Probes y ver Metricas

### Paso 1: Crear app con health endpoints

```bash
mkdir -p ~/k8s-lab/lab-08/app
cat > ~/k8s-lab/lab-08/app/index.js << 'EOF'
const express = require('express');
const app = express();
const PORT = 3000;

let isReady = false;
// Simular startup de 10 segundos
setTimeout(() => { isReady = true; }, 10000);

app.get('/health/live', (req, res) => {
  res.json({ status: 'alive', uptime: process.uptime() });
});

app.get('/health/ready', (req, res) => {
  if (isReady) {
    res.json({ status: 'ready' });
  } else {
    res.status(503).json({ status: 'starting...' });
  }
});

app.get('/api/data', (req, res) => {
  res.json({ data: [1, 2, 3], timestamp: Date.now() });
});

app.listen(PORT, () => console.log(`App on port ${PORT}`));
EOF

cat > ~/k8s-lab/lab-08/app/package.json << 'EOF'
{"name":"probe-demo","version":"1.0.0","dependencies":{"express":"^4.18.0"}}
EOF

cat > ~/k8s-lab/lab-08/app/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY index.js .
EXPOSE 3000
CMD ["node", "index.js"]
EOF

docker build -t probe-demo:v1 ~/k8s-lab/lab-08/app/
kind load docker-image probe-demo:v1 --name curso-k8s
```

### Paso 2: Deployment con probes y limits

```bash
cat > ~/k8s-lab/lab-08/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: probe-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: probe-demo
  template:
    metadata:
      labels:
        app: probe-demo
    spec:
      containers:
      - name: app
        image: probe-demo:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        startupProbe:
          httpGet:
            path: /health/ready
            port: 3000
          failureThreshold: 12
          periodSeconds: 2
        livenessProbe:
          httpGet:
            path: /health/live
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: probe-demo-service
spec:
  selector:
    app: probe-demo
  ports:
  - port: 80
    targetPort: 3000
EOF

kubectl apply -f ~/k8s-lab/lab-08/deployment.yaml
```

### Paso 3: Observar el ciclo de vida

```bash
# Ver como los pods pasan por los estados
kubectl get pods -l app=probe-demo -w

# En otra terminal, ver los eventos
kubectl get events --sort-by='.lastTimestamp' -w

# Ver cuando el readiness probe falla (los primeros 10s)
kubectl describe pod $(kubectl get pod -l app=probe-demo -o name | head -1)
# Buscar: "Readiness probe failed"
```

### Paso 4: Ver logs

```bash
# Ver logs en tiempo real
kubectl logs -f deployment/probe-demo

# Ver logs de todos los pods del deployment
kubectl logs -l app=probe-demo --all-containers=true

# Ver recursos usados
kubectl top pods -l app=probe-demo
```

### Limpiar

```bash
kubectl delete -f ~/k8s-lab/lab-08/deployment.yaml
```

---

## Validaciones

```bash
# Pods con probes configurados
kubectl describe deployment probe-demo | grep -A5 "Liveness\|Readiness"

# Pods en Running con READY 1/1
kubectl get pods -l app=probe-demo
# READY: 1/1 (no Ready hasta que pasa readiness probe)

# Recursos dentro de los limits
kubectl top pods -l app=probe-demo
```

---

## Errores comunes

### `Liveness probe failed: HTTP probe failed with statuscode: 500`

**Causa:** El endpoint `/health/live` retorna error.
**Solucion:** Revisar los logs del pod y el endpoint de health.

### `OOMKilled` — Pod muerto por falta de memoria

```
Last State: Terminated
  Reason: OOMKilled
```

**Causa:** El contenedor supero el limite de memoria.
**Solucion:**
```bash
# Ver el uso real de memoria
kubectl top pods

# Aumentar el limite en el Deployment
# limits.memory: "512Mi"  # o mas
```

### `Back-off restarting failed container`

**Causa:** CrashLoopBackOff - el contenedor crashea al arrancar.
**Solucion:**
```bash
kubectl logs <pod-name> --previous  # Ver logs del crash anterior
kubectl describe pod <pod-name>      # Ver los eventos
```

---

## Resumen

- **livenessProbe**: reinicia el contenedor si falla
- **readinessProbe**: saca el pod del trafico si falla
- **startupProbe**: bloquea las otras probes durante el arranque
- **requests**: recursos garantizados para el scheduler
- **limits**: techo de recursos (OOMKilled si supera memoria)
- **HPA**: escalado automatico basado en metricas
- `kubectl logs`, `kubectl describe`, `kubectl top` son tus mejores amigos

---

## Siguiente modulo

[09 - Helm y Kustomize: Packaging avanzado](./09-packaging-helm-kustomize.md)
