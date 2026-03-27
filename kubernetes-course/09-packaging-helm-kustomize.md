# 09 — Helm y Kustomize: Packaging Avanzado

> **Anterior:** [08 - Observabilidad](./08-observability-operations.md) | **Siguiente:** [10 - CI/CD con GitHub Actions](./10-cicd-github-actions.md)

---

## Objetivos de este modulo

- Entender el problema que resuelven Helm y Kustomize
- Crear y usar Charts de Helm
- Usar Kustomize para configuracion por ambiente
- Saber cuando usar cada herramienta

---

## 1. El problema

Cuando tienes multiples ambientes (dev, staging, prod), copiar y pegar YAML es un problema:

```
Sin Helm/Kustomize:
dev-deployment.yaml   → image: mi-app:dev,   replicas: 1
stg-deployment.yaml   → image: mi-app:stg,   replicas: 2
prd-deployment.yaml   → image: mi-app:prod,  replicas: 5

Problema: cambiar el puerto requiere editar 3 archivos
```

```
Con Helm o Kustomize:
Un solo template + valores por ambiente
```

---

## 2. Helm vs Kustomize

| Caracteristica | Helm | Kustomize |
|---|---|---|
| **Concepto** | Templates con variables | Patches sobre YAML base |
| **Lenguaje** | Go templates | YAML puro |
| **Curva** | Mayor | Menor |
| **Gestiona releases** | Si (instalar/actualizar/rollback) | No |
| **Ecosistema** | Enorme (charts publicos) | Limitado |
| **Cuando usar** | Apps complejas, charts de terceros | Overlays por ambiente |

**Regla practica:**
- **Helm** → para instalar software de terceros (Prometheus, nginx, postgres)
- **Kustomize** → para gestionar tus propias apps por ambiente

---

## 3. Helm

### Instalacion

```bash
brew install helm

# Verificar
helm version
```

### Conceptos de Helm

```
Chart     = Paquete de K8s (como un .zip con templates + valores)
Release   = Instancia de un Chart instalado en el cluster
Values    = Variables que personalizan el Chart
Repository = Coleccion de Charts
```

### Usar Charts publicos (lo mas comun)

```bash
# Buscar un chart
helm search hub postgresql

# Agregar un repositorio
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Ver valores disponibles del chart
helm show values bitnami/postgresql

# Instalar PostgreSQL con Helm
helm install my-postgres bitnami/postgresql \
  --namespace database \
  --create-namespace \
  --set auth.postgresPassword=secretpassword \
  --set auth.database=tasksdb

# Ver las releases instaladas
helm list -A

# Actualizar una release
helm upgrade my-postgres bitnami/postgresql \
  --set auth.postgresPassword=newpassword

# Rollback de una release
helm rollback my-postgres 1

# Desinstalar
helm uninstall my-postgres -n database
```

### Crear tu propio Chart

```bash
# Crear estructura de un Chart
helm create mi-app
# Crea:
# mi-app/
#   Chart.yaml         ← Metadata del chart
#   values.yaml        ← Valores por defecto
#   templates/         ← Templates YAML con Go templates
#     deployment.yaml
#     service.yaml
#     ingress.yaml
#     _helpers.tpl     ← Helpers/parciales
```

### Chart.yaml

```yaml
# mi-app/Chart.yaml
apiVersion: v2
name: mi-app
description: Mi aplicacion de tareas
type: application
version: 0.1.0
appVersion: "1.0.0"
```

### values.yaml

```yaml
# mi-app/values.yaml (valores por defecto)
replicaCount: 1

image:
  repository: mi-app
  tag: "v1"
  pullPolicy: Never

service:
  type: ClusterIP
  port: 80
  targetPort: 3000

ingress:
  enabled: false
  host: app.local

resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "200m"

env:
  APP_ENV: production
  LOG_LEVEL: info
```

### templates/deployment.yaml

```yaml
# mi-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-{{ .Chart.Name }}
  labels:
    app: {{ .Chart.Name }}
    release: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
  template:
    metadata:
      labels:
        app: {{ .Chart.Name }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
        env:
        {{- range $key, $val := .Values.env }}
        - name: {{ $key }}
          value: {{ $val | quote }}
        {{- end }}
```

### Instalar tu Chart

```bash
# Instalar en dev (valores por defecto)
helm install mi-app-dev ./mi-app

# Instalar en produccion (sobrescribir valores)
helm install mi-app-prod ./mi-app \
  --set replicaCount=3 \
  --set image.tag=v2 \
  --set ingress.enabled=true

# Con archivo de valores por ambiente
helm install mi-app-prod ./mi-app -f values-prod.yaml

# Ver el YAML que generaria sin instalar
helm template mi-app-dev ./mi-app

# Verificar el chart antes de instalar
helm lint ./mi-app
```

### values-prod.yaml

```yaml
replicaCount: 3
image:
  tag: "v2"
  pullPolicy: Always
ingress:
  enabled: true
  host: mi-app.com
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
env:
  APP_ENV: production
  LOG_LEVEL: warn
```

---

## 4. Kustomize

Kustomize viene integrado en `kubectl` (no necesita instalacion).

### Estructura de Kustomize

```
k8s/
├── base/                    ← YAML comun para todos los ambientes
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/                 ← Cambios especificos para dev
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml
    └── prod/                ← Cambios especificos para prod
        ├── kustomization.yaml
        └── patch-replicas.yaml
```

### base/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

commonLabels:
  app: mi-app
  managed-by: kustomize
```

### base/deployment.yaml

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
```

### overlays/dev/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

namespace: dev

patches:
- path: patch-dev.yaml

images:
- name: mi-app
  newTag: "dev-latest"
```

### overlays/dev/patch-dev.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-app
spec:
  replicas: 1    # dev: 1 replica
  template:
    spec:
      containers:
      - name: mi-app
        env:
        - name: APP_ENV
          value: "development"
        - name: LOG_LEVEL
          value: "debug"
```

### overlays/prod/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

namespace: production

patches:
- path: patch-prod.yaml

images:
- name: mi-app
  newName: registry.empresa.com/mi-app
  newTag: "1.2.0"
```

### overlays/prod/patch-prod.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-app
spec:
  replicas: 3    # prod: 3 replicas
  template:
    spec:
      containers:
      - name: mi-app
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: APP_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "warn"
```

### Usar Kustomize

```bash
# Ver el YAML generado sin aplicar
kubectl kustomize overlays/dev/

# Aplicar el overlay de dev
kubectl apply -k overlays/dev/

# Aplicar el overlay de prod
kubectl apply -k overlays/prod/

# Ver los recursos aplicados
kubectl get all -n dev
kubectl get all -n production
```

---

## Lab: Kustomize con 3 ambientes

```bash
mkdir -p ~/k8s-lab/lab-09/{base,overlays/{dev,staging,prod}}
cd ~/k8s-lab/lab-09

# Base
cat > base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tasks-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tasks-api
  template:
    metadata:
      labels:
        app: tasks-api
    spec:
      containers:
      - name: tasks-api
        image: tasks-api:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
EOF

cat > base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: tasks-api
spec:
  selector:
    app: tasks-api
  ports:
  - port: 80
    targetPort: 3000
EOF

cat > base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
- service.yaml
EOF

# Dev overlay
cat > overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
namespace: dev
patches:
- path: patch.yaml
EOF

cat > overlays/dev/patch.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tasks-api
spec:
  replicas: 1
EOF

# Prod overlay
cat > overlays/prod/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
namespace: production
patches:
- path: patch.yaml
EOF

cat > overlays/prod/patch.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tasks-api
spec:
  replicas: 3
EOF

# Ver el YAML generado para cada ambiente
echo "=== DEV ==="
kubectl kustomize overlays/dev/

echo "=== PROD ==="
kubectl kustomize overlays/prod/

# Aplicar dev
kubectl create namespace dev 2>/dev/null || true
kubectl apply -k overlays/dev/

# Verificar
kubectl get all -n dev
```

---

## Resumen

- **Helm**: para instalar software de terceros y apps con muchas opciones
- **Kustomize**: para gestionar tus apps en multiples ambientes con YAML puro
- Ambos resuelven el problema de configuracion repetida por ambiente
- `helm template` y `kubectl kustomize` muestran el YAML final sin aplicar

---

## Siguiente modulo

[10 - CI/CD con GitHub Actions](./10-cicd-github-actions.md)
