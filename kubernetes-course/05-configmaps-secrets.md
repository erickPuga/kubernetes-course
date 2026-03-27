# 05 — ConfigMaps y Secrets: Gestión de Configuración

> **Anterior:** [04 - Networking e Ingress](./04-networking-ingress.md) | **Siguiente:** [06 - Storage y PostgreSQL](./06-storage-postgresql.md)

---

## 🎯 Objetivos de este módulo

- Entender la diferencia entre ConfigMap y Secret
- Inyectar configuración como variables de entorno
- Montar configuración como archivos (volúmenes)
- Conocer las buenas prácticas de seguridad
- Gestionar configuraciones por ambiente (dev/staging/prod)

---

## 1. ¿Por qué separar la configuración del código?

El **Principio de los 12 factores** (12-Factor App) establece:

> "La configuración que varía entre ambientes (dev, staging, prod) debe almacenarse en **variables de entorno**, no en el código."

**Configuración que debe estar separada:**
- URLs de bases de datos
- Puertos
- Feature flags
- Parámetros de la app

**Configuración sensible (en Secrets):**
- Passwords
- API Keys
- Tokens JWT
- Certificados TLS

---

## 2. ConfigMap

Un **ConfigMap** almacena datos de configuración en texto plano (no sensibles).

### Crear un ConfigMap desde YAML

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  # Valores clave-valor simples
  APP_ENV: "production"
  APP_PORT: "3000"
  LOG_LEVEL: "info"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "myapp"

  # Valor multi-línea (como un archivo)
  app.properties: |
    server.port=3000
    server.timeout=30
    cache.ttl=3600

  # Configuración JSON
  feature-flags.json: |
    {
      "newUI": true,
      "betaFeatures": false,
      "maxUploadSize": 10485760
    }
```

### Crear ConfigMap desde la CLI

```bash
# Desde literales
kubectl create configmap app-config \
  --from-literal=APP_ENV=production \
  --from-literal=APP_PORT=3000 \
  --from-literal=DB_HOST=postgres-service

# Desde un archivo
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# Desde un directorio (todos los archivos)
kubectl create configmap app-configs \
  --from-file=./configs/

# Ver el ConfigMap creado
kubectl get configmap app-config -o yaml
```

### Usar ConfigMap como variables de entorno

```yaml
spec:
  containers:
  - name: mi-app
    image: mi-app:v1
    # Método 1: Variables individuales
    env:
    - name: APP_ENV
      valueFrom:
        configMapKeyRef:
          name: app-config    # nombre del ConfigMap
          key: APP_ENV        # clave dentro del ConfigMap

    # Método 2: Todas las claves del ConfigMap como env vars
    envFrom:
    - configMapRef:
        name: app-config      # importa TODAS las claves
```

### Usar ConfigMap como archivo (volumen)

```yaml
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    volumeMounts:
    - name: config-volume
      mountPath: /etc/nginx/conf.d    # Directorio donde montar
      readOnly: true

  volumes:
  - name: config-volume
    configMap:
      name: nginx-config              # ConfigMap a montar
```

---

## 3. Secret

Un **Secret** almacena datos sensibles en **base64**. No es encriptación fuerte, pero previene exposición accidental.

> ⚠️ **Importante:** Base64 NO es encriptación. Para producción real, usa HashiCorp Vault, AWS Secrets Manager, o Sealed Secrets.

### Crear un Secret desde YAML

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
  namespace: default
type: Opaque
data:
  # Los valores DEBEN estar en base64
  # echo -n "mi-password" | base64
  DB_PASSWORD: bWktcGFzc3dvcmQ=
  DB_USER: cG9zdGdyZXM=
  JWT_SECRET: bXlzdXBlcnNlY3JldGp3dHRva2Vu
```

**Generar valores en base64:**

```bash
# Codificar
echo -n "mi-password-seguro" | base64
# bWktcGFzc3dvcmQtc2VndXJv

# Decodificar (para verificar)
echo "bWktcGFzc3dvcmQtc2VndXJv" | base64 --decode
# mi-password-seguro
```

### Crear Secret desde la CLI (recomendado — evita poner base64 manual)

```bash
# Desde literales (kubectl codifica automáticamente en base64)
kubectl create secret generic db-secret \
  --from-literal=DB_PASSWORD=mi-password-seguro \
  --from-literal=DB_USER=postgres \
  --from-literal=JWT_SECRET=mysupersecretjwttoken

# Desde un archivo
kubectl create secret generic tls-certs \
  --from-file=tls.crt=./cert.crt \
  --from-file=tls.key=./cert.key

# Ver el secret (los valores aparecen en base64)
kubectl get secret db-secret -o yaml

# Decodificar un valor específico
kubectl get secret db-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 --decode
```

### Usar Secret como variables de entorno

```yaml
spec:
  containers:
  - name: mi-app
    image: mi-app:v1
    # Variable individual desde Secret
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret       # nombre del Secret
          key: DB_PASSWORD      # clave dentro del Secret

    # Todas las claves del Secret como env vars
    envFrom:
    - secretRef:
        name: db-secret
```

### Usar Secret como archivo (volumen)

```yaml
spec:
  containers:
  - name: mi-app
    image: mi-app:v1
    volumeMounts:
    - name: secrets-volume
      mountPath: /app/secrets
      readOnly: true

  volumes:
  - name: secrets-volume
    secret:
      secretName: db-secret
      # Resultado: /app/secrets/DB_PASSWORD (archivo con el valor)
```

---

## 4. Tipos de Secrets

| Tipo | Uso |
|---|---|
| `Opaque` | Datos genéricos (el más común) |
| `kubernetes.io/dockerconfigjson` | Credenciales de registry Docker |
| `kubernetes.io/tls` | Certificados TLS |
| `kubernetes.io/service-account-token` | Tokens de ServiceAccount |

### Secret para registry privado de Docker

```bash
kubectl create secret docker-registry my-registry-secret \
  --docker-server=registry.mi-empresa.com \
  --docker-username=mi-usuario \
  --docker-password=mi-token \
  --docker-email=mi@email.com
```

```yaml
spec:
  imagePullSecrets:
  - name: my-registry-secret  # ← Usar para pull de imágenes privadas
  containers:
  - name: mi-app
    image: registry.mi-empresa.com/mi-app:v1
```

---

## 5. Buenas prácticas

### ✅ DO (Hacer)

```yaml
# Separar configs por namespace/ambiente
# dev-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: dev

# prod-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: prod
```

```bash
# Nunca commitear Secrets en git
# Usar .gitignore
echo "secrets*.yaml" >> .gitignore
echo "*-secret.yaml" >> .gitignore
```

### ❌ DON'T (No hacer)

```yaml
# ❌ NO pongas passwords directamente en el Deployment
env:
- name: DB_PASSWORD
  value: "mi-password-en-texto"  # ← MAL

# ✅ Usa Secrets
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: DB_PASSWORD
```

### Actualizar ConfigMaps y Secrets

```bash
# Actualizar un valor en un ConfigMap
kubectl edit configmap app-config

# Aplicar cambios desde YAML
kubectl apply -f configmap.yaml

# Los pods deben reiniciarse para ver los cambios en env vars
# (las variables de entorno no se actualizan en caliente)
kubectl rollout restart deployment/mi-app
```

---

## 🧪 Laboratorio completo

### Preparar el ambiente

```bash
mkdir -p ~/k8s-lab/lab-05
cd ~/k8s-lab/lab-05
```

### Paso 1: Crear ConfigMap y Secret

```bash
cat > ~/k8s-lab/lab-05/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "development"
  APP_PORT: "3000"
  LOG_LEVEL: "debug"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "tasksdb"
  app.json: |
    {
      "pagination": { "defaultLimit": 20, "maxLimit": 100 },
      "features": { "registration": true }
    }
EOF

cat > ~/k8s-lab/lab-05/secret.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DB_USER: cG9zdGdyZXM=
  DB_PASSWORD: c2VjcmV0cGFzc3dvcmQ=
  JWT_SECRET: bXlzdXBlcnNlY3JldGtleWZvcmp3dA==
EOF

kubectl apply -f ~/k8s-lab/lab-05/configmap.yaml
kubectl apply -f ~/k8s-lab/lab-05/secret.yaml
```

### Paso 2: Crear una app que lee la configuración

```bash
mkdir -p ~/k8s-lab/lab-05/config-app
cat > ~/k8s-lab/lab-05/config-app/package.json << 'EOF'
{
  "name": "config-demo",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

cat > ~/k8s-lab/lab-05/config-app/index.js << 'EOF'
const express = require('express');
const fs = require('fs');
const app = express();
const PORT = process.env.APP_PORT || 3000;

app.get('/config', (req, res) => {
  // Leer variables de entorno
  const config = {
    fromEnv: {
      APP_ENV: process.env.APP_ENV,
      APP_PORT: process.env.APP_PORT,
      LOG_LEVEL: process.env.LOG_LEVEL,
      DB_HOST: process.env.DB_HOST,
      DB_PORT: process.env.DB_PORT,
      DB_NAME: process.env.DB_NAME,
      // Secrets (ocultar valor real por seguridad)
      DB_USER: process.env.DB_USER ? '***' : 'NOT SET',
      DB_PASSWORD: process.env.DB_PASSWORD ? '***' : 'NOT SET',
      JWT_SECRET: process.env.JWT_SECRET ? '***' : 'NOT SET',
    },
    fromFile: {}
  };

  // Leer configuración desde archivo montado
  try {
    const appJson = fs.readFileSync('/app/config/app.json', 'utf8');
    config.fromFile = JSON.parse(appJson);
  } catch (e) {
    config.fromFile = { error: 'File not found: ' + e.message };
  }

  res.json(config);
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => console.log(`Config demo app on port ${PORT}`));
EOF

cat > ~/k8s-lab/lab-05/config-app/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY index.js .
EXPOSE 3000
CMD ["node", "index.js"]
EOF
```

### Paso 3: Build, load y deploy

```bash
docker build -t config-demo:v1 ~/k8s-lab/lab-05/config-app/
kind load docker-image config-demo:v1 --name curso-k8s

cat > ~/k8s-lab/lab-05/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-demo
  labels:
    app: config-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: config-demo
  template:
    metadata:
      labels:
        app: config-demo
    spec:
      containers:
      - name: config-demo
        image: config-demo:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000

        # Variables de entorno desde ConfigMap
        envFrom:
        - configMapRef:
            name: app-config

        # Variables de entorno desde Secret
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secret

        # Montar el archivo app.json desde el ConfigMap
        volumeMounts:
        - name: app-config-volume
          mountPath: /app/config
          readOnly: true

      volumes:
      - name: app-config-volume
        configMap:
          name: app-config
          items:
          - key: app.json
            path: app.json
---
apiVersion: v1
kind: Service
metadata:
  name: config-demo-service
spec:
  selector:
    app: config-demo
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
EOF

kubectl apply -f ~/k8s-lab/lab-05/deployment.yaml
```

### Paso 4: Verificar la configuración

```bash
# Ver ConfigMap
kubectl get configmap app-config -o yaml

# Ver Secret (valores en base64)
kubectl get secret app-secret -o yaml

# Decodificar el password
kubectl get secret app-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 --decode
echo ""

# Port-forward y probar
kubectl port-forward service/config-demo-service 8080:80 &
sleep 2
curl -s http://localhost:8080/config | jq .
```

### Paso 5: Actualizar la configuración

```bash
# Actualizar el ConfigMap
kubectl patch configmap app-config --type merge -p '{"data":{"LOG_LEVEL":"warn"}}'

# Reiniciar el deployment para que tome los nuevos valores
kubectl rollout restart deployment/config-demo

# Verificar el cambio
kubectl wait --for=condition=ready pod -l app=config-demo --timeout=30s
curl -s http://localhost:8080/config | jq .fromEnv.LOG_LEVEL
# "warn"
```

### Paso 6: Ver la configuración dentro del pod

```bash
# Entrar al pod y ver las variables de entorno
kubectl exec -it $(kubectl get pod -l app=config-demo -o name | head -1) -- env | grep -E "APP|DB|LOG|JWT"

# Ver el archivo montado
kubectl exec -it $(kubectl get pod -l app=config-demo -o name | head -1) -- cat /app/config/app.json
```

### Limpiar

```bash
kill %1  # Matar port-forward
kubectl delete -f ~/k8s-lab/lab-05/deployment.yaml
kubectl delete configmap app-config
kubectl delete secret app-secret
```

---

## ✅ Validaciones

```bash
# ConfigMap existe
kubectl get configmap app-config
# Las variables de entorno llegan al pod
kubectl exec deploy/config-demo -- env | grep APP_ENV
# APP_ENV=development

# El Secret existe
kubectl get secret app-secret
# Los valores están en base64
kubectl get secret app-secret -o jsonpath='{.data.DB_PASSWORD}'
# NO debe mostrar texto plano

# El archivo app.json está montado
kubectl exec deploy/config-demo -- cat /app/config/app.json
```

---

## 🚨 Errores comunes

### `CreateContainerConfigError`

```
STATUS: CreateContainerConfigError
```

**Causa:** El ConfigMap o Secret referenciado no existe.  
**Solución:**
```bash
kubectl describe pod <nombre-pod>  # Ver el error exacto
kubectl get configmap               # Verificar que existe
kubectl get secret                  # Verificar que existe
```

### Variables de entorno no se actualizan

**Causa:** Los cambios en ConfigMap/Secret no se aplican automáticamente a pods existentes.  
**Solución:**
```bash
# Reiniciar el deployment
kubectl rollout restart deployment/mi-app
```

### `base64: invalid input`

**Causa:** El valor en el Secret YAML tiene un padding base64 incorrecto.  
**Solución:**
```bash
# Siempre usar -n para evitar newline al codificar
echo -n "mi-valor" | base64
# NO usar: echo "mi-valor" | base64  (incluye \n al final)
```

### `Error: secret "xxx" not found`

**Causa:** El namespace del Secret es diferente al del Pod.  
**Solución:**
```bash
# Los Secrets y Pods deben estar en el mismo namespace
kubectl get secret app-secret -n mi-namespace
kubectl apply -f deployment.yaml -n mi-namespace
```

---

## 📝 Resumen

- **ConfigMap** = configuración no sensible (env vars, archivos de config)
- **Secret** = configuración sensible (passwords, tokens) codificada en base64
- Inyección como **env vars**: `envFrom` o `env.valueFrom`
- Inyección como **archivos**: `volumeMounts` + `volumes`
- Cambios en ConfigMap/Secret requieren **restart del deployment**
- Nunca commitear Secrets en Git

---

## ➡️ Siguiente módulo

👉 [06 - Storage y PostgreSQL: Persistencia de datos](./06-storage-postgresql.md)
