# 06 — Storage y PostgreSQL: Persistencia de Datos

> **Anterior:** [05 - ConfigMaps y Secrets](./05-configmaps-secrets.md) | **Siguiente:** [07 - Seguridad y RBAC](./07-security-rbac.md)

---

## 🎯 Objetivos de este módulo

- Entender el modelo de almacenamiento de Kubernetes
- Usar PersistentVolume y PersistentVolumeClaim
- Desplegar PostgreSQL en Kubernetes con persistencia
- Conectar un backend a la base de datos
- Dominar SQL básico en el contexto de K8s

---

## 1. El problema del almacenamiento en K8s

Los **Pods son efímeros**. Cuando un Pod muere y se recrea, pierde todos sus datos.

```
Pod con PostgreSQL (sin PVC):
─────────────────────────────
Pod arranca  → datos en /var/lib/postgresql/data
Pod cae      → datos PERDIDOS ❌
Pod nuevo    → base de datos vacía
```

```
Pod con PostgreSQL (con PVC):
─────────────────────────────
Pod arranca  → datos montados desde PVC (/var/lib/postgresql/data)
Pod cae      → datos SEGUROS en el PVC ✅
Pod nuevo    → datos montados del mismo PVC → datos intactos
```

---

## 2. Conceptos de almacenamiento

### PersistentVolume (PV)

Un **PV** es un trozo de almacenamiento en el cluster provisionado por un administrador. Es un recurso del cluster (como un nodo).

```yaml
# PV manual (administrador lo crea)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  hostPath:
    path: /data/postgres   # En kind, usa almacenamiento del nodo Docker
```

### PersistentVolumeClaim (PVC)

Un **PVC** es una solicitud de almacenamiento por parte de un usuario. K8s busca un PV disponible que cumpla los requisitos.

```yaml
# PVC (usuario lo solicita)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### StorageClass

Define cómo se provisiona el almacenamiento. En kind, hay una StorageClass por defecto:

```bash
# Ver StorageClasses disponibles
kubectl get storageclass

# NAME                 PROVISIONER             RECLAIMPOLICY
# standard (default)   rancher.io/local-path   Delete
```

Con `StorageClass`, el PV se **provisiona automáticamente** al crear el PVC (no necesitas crear el PV manualmente).

```yaml
# PVC con StorageClass (provisioning dinámico)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard    # La StorageClass de kind
  resources:
    requests:
      storage: 1Gi
```

### Modos de acceso

| AccessMode | Descripción | Abreviatura |
|---|---|---|
| `ReadWriteOnce` | Un solo nodo puede leer/escribir | RWO |
| `ReadOnlyMany` | Muchos nodos pueden leer | ROX |
| `ReadWriteMany` | Muchos nodos pueden leer/escribir | RWX |

> Para PostgreSQL siempre usa `ReadWriteOnce`.

---

## 3. SQL completo para aprendizaje

Antes del laboratorio K8s, aquí está el SQL que usaremos:

### Crear base de datos y esquema

```sql
-- Crear base de datos (si no existe)
CREATE DATABASE tasksdb;

-- Conectar a la base de datos
\c tasksdb;

-- Crear tabla de usuarios
CREATE TABLE users (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(100) NOT NULL,
  email       VARCHAR(150) UNIQUE NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de tareas
CREATE TABLE tasks (
  id          SERIAL PRIMARY KEY,
  title       VARCHAR(200) NOT NULL,
  description TEXT,
  status      VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done')),
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor rendimiento
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_users_email ON users(email);
```

### INSERT — Insertar datos

```sql
-- Insertar usuarios
INSERT INTO users (name, email) VALUES
  ('Alice García', 'alice@example.com'),
  ('Bob Martínez', 'bob@example.com'),
  ('Carlos López', 'carlos@example.com');

-- Insertar tareas
INSERT INTO tasks (title, description, status, user_id) VALUES
  ('Configurar Kubernetes', 'Instalar kind y kubectl', 'done', 1),
  ('Crear Deployment', 'Primer deployment con nginx', 'in_progress', 1),
  ('Configurar Ingress', 'NGINX Ingress Controller', 'pending', 2),
  ('Agregar PostgreSQL', 'Base de datos con PVC', 'pending', 2),
  ('Revisar RBAC', 'Roles y permisos', 'pending', 3);
```

### SELECT — Consultar datos

```sql
-- Todos los usuarios
SELECT * FROM users;

-- Todas las tareas con nombre del usuario
SELECT
  t.id,
  t.title,
  t.status,
  u.name AS owner,
  t.created_at
FROM tasks t
JOIN users u ON t.user_id = u.id
ORDER BY t.created_at DESC;

-- Tareas por status
SELECT status, COUNT(*) as total
FROM tasks
GROUP BY status
ORDER BY total DESC;

-- Tareas de un usuario específico
SELECT t.title, t.status
FROM tasks t
JOIN users u ON t.user_id = u.id
WHERE u.email = 'alice@example.com';

-- Tareas pendientes
SELECT * FROM tasks WHERE status = 'pending';
```

### UPDATE — Actualizar datos

```sql
-- Actualizar status de una tarea
UPDATE tasks
SET status = 'done', updated_at = CURRENT_TIMESTAMP
WHERE id = 2;

-- Actualizar email de un usuario
UPDATE users
SET email = 'alice.garcia@newdomain.com'
WHERE id = 1;
```

### DELETE — Eliminar datos

```sql
-- Eliminar una tarea
DELETE FROM tasks WHERE id = 5;

-- Eliminar usuario (las tareas se eliminan por CASCADE)
DELETE FROM users WHERE id = 3;
```

---

## 4. PostgreSQL en Kubernetes

### Manifiestos completos

```yaml
# postgres.yaml
# ── NAMESPACE ─────────────────────────────────────────────
apiVersion: v1
kind: Namespace
metadata:
  name: database
---
# ── SECRET ────────────────────────────────────────────────
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: database
type: Opaque
data:
  POSTGRES_USER: cG9zdGdyZXM=         # postgres
  POSTGRES_PASSWORD: c2VjcmV0cGFzcw== # secretPass
  POSTGRES_DB: dGFza3NkYg==           # tasksdb
---
# ── PVC ───────────────────────────────────────────────────
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: database
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
---
# ── DEPLOYMENT ────────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: database
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        envFrom:
        - secretRef:
            name: postgres-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
---
# ── SERVICE ───────────────────────────────────────────────
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: database
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

---

## 🧪 Laboratorio: PostgreSQL en Kubernetes

### Paso 1: Preparar el ambiente

```bash
mkdir -p ~/k8s-lab/lab-06
cd ~/k8s-lab/lab-06
```

### Paso 2: Crear todos los manifiestos

```bash
cat > ~/k8s-lab/lab-06/postgres.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: database
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: database
type: Opaque
data:
  POSTGRES_USER: cG9zdGdyZXM=
  POSTGRES_PASSWORD: c2VjcmV0UGFzcw==
  POSTGRES_DB: dGFza3NkYg==
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: database
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: database
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        envFrom:
        - secretRef:
            name: postgres-secret
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "postgres"]
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: database
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

kubectl apply -f ~/k8s-lab/lab-06/postgres.yaml
```

### Paso 3: Verificar el despliegue

```bash
# Ver todos los recursos en el namespace database
kubectl get all -n database

# Ver el PVC (debe estar Bound)
kubectl get pvc -n database
# NAME           STATUS   VOLUME       CAPACITY
# postgres-pvc   Bound    pvc-xxxxx    1Gi

# Ver el PV creado automáticamente
kubectl get pv

# Esperar a que PostgreSQL esté listo
kubectl wait --for=condition=ready pod -l app=postgres -n database --timeout=120s

# Ver logs de PostgreSQL
kubectl logs -n database $(kubectl get pod -n database -l app=postgres -o name)
```

### Paso 4: Conectar a PostgreSQL y crear el esquema

```bash
# Conectar al pod de PostgreSQL
kubectl exec -it -n database \
  $(kubectl get pod -n database -l app=postgres -o name) \
  -- psql -U postgres -d tasksdb
```

Una vez dentro de psql, ejecutar:

```sql
-- Crear tablas
CREATE TABLE users (
  id         SERIAL PRIMARY KEY,
  name       VARCHAR(100) NOT NULL,
  email      VARCHAR(150) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
  id          SERIAL PRIMARY KEY,
  title       VARCHAR(200) NOT NULL,
  description TEXT,
  status      VARCHAR(20) DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'done')),
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- Insertar datos de prueba
INSERT INTO users (name, email) VALUES
  ('Alice García', 'alice@example.com'),
  ('Bob Martínez', 'bob@example.com');

INSERT INTO tasks (title, description, status, user_id) VALUES
  ('Aprender Kubernetes', 'Completar el curso K8s', 'in_progress', 1),
  ('Desplegar PostgreSQL', 'Con PVC para persistencia', 'done', 1),
  ('Configurar Ingress', 'NGINX Ingress Controller', 'pending', 2);

-- Verificar datos
SELECT t.id, t.title, t.status, u.name as owner
FROM tasks t
JOIN users u ON t.user_id = u.id;

-- Salir de psql
\q
```

### Paso 5: Probar la persistencia

```bash
# Eliminar el pod de postgres (simular un crash)
kubectl delete pod -n database -l app=postgres

# Ver cómo el Deployment crea un nuevo pod
kubectl get pods -n database -w

# Cuando el nuevo pod esté Running, conectar de nuevo
kubectl wait --for=condition=ready pod -l app=postgres -n database --timeout=60s

kubectl exec -it -n database \
  $(kubectl get pod -n database -l app=postgres -o name) \
  -- psql -U postgres -d tasksdb -c "SELECT * FROM tasks;"

# ¡Los datos deben seguir ahí! ✅
```

### Paso 6: Acceso desde fuera del cluster (port-forward)

```bash
# Acceder a PostgreSQL desde tu Mac
kubectl port-forward -n database service/postgres-service 5432:5432 &

# Conectar con psql local (si tienes psql instalado)
psql -h localhost -U postgres -d tasksdb

# O con un cliente gráfico como TablePlus, DBeaver, etc.
# Host: localhost
# Port: 5432
# User: postgres
# Password: secretPass
# Database: tasksdb
```

### Paso 7: Backup de la base de datos

```bash
# Hacer un dump de la base de datos
kubectl exec -n database \
  $(kubectl get pod -n database -l app=postgres -o name) \
  -- pg_dump -U postgres tasksdb > ~/k8s-lab/lab-06/tasksdb-backup.sql

# Restaurar desde backup
kubectl exec -i -n database \
  $(kubectl get pod -n database -l app=postgres -o name) \
  -- psql -U postgres tasksdb < ~/k8s-lab/lab-06/tasksdb-backup.sql
```

### Limpiar

```bash
kill %1  # Matar port-forward
kubectl delete namespace database
# Esto elimina: pods, services, pvc, secrets del namespace
```

---

## 5. Conectar un backend a PostgreSQL

```javascript
// backend/db.js — Conexión desde Node.js
const { Pool } = require('pg');

const pool = new Pool({
  host:     process.env.DB_HOST,      // postgres-service.database.svc.cluster.local
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,      // tasksdb
  user:     process.env.DB_USER,      // postgres
  password: process.env.DB_PASSWORD,  // desde Secret
});

// Probar conexión
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('Error conectando a PostgreSQL:', err);
  } else {
    console.log('PostgreSQL conectado:', res.rows[0].now);
  }
});

module.exports = pool;
```

```yaml
# En el Deployment del backend
env:
- name: DB_HOST
  value: "postgres-service.database.svc.cluster.local"
- name: DB_PORT
  value: "5432"
- name: DB_NAME
  value: "tasksdb"
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: POSTGRES_USER
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: POSTGRES_PASSWORD
```

---

## ✅ Validaciones

```bash
# PVC debe estar Bound
kubectl get pvc -n database
# STATUS: Bound

# Pod de postgres Running
kubectl get pods -n database
# STATUS: Running, READY: 1/1

# Los datos persisten al reiniciar el pod
kubectl delete pod -n database -l app=postgres
kubectl wait --for=condition=ready pod -l app=postgres -n database --timeout=60s
kubectl exec -n database $(kubectl get pod -n database -l app=postgres -o name) \
  -- psql -U postgres -d tasksdb -c "\dt"
# Debe mostrar las tablas users y tasks
```

---

## 🚨 Errores comunes

### PVC en estado `Pending`

```
NAME           STATUS    VOLUME   CAPACITY
postgres-pvc   Pending
```

**Causa:** No hay StorageClass disponible o el provisioner no está corriendo.  
**Solución:**
```bash
kubectl get storageclass
# Si no hay ninguna con (default), reinstalar kind o usar:
kubectl patch storageclass standard -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### `password authentication failed`

**Causa:** La contraseña en el Secret no coincide.  
**Solución:**
```bash
# Verificar la contraseña decodificada
kubectl get secret -n database postgres-secret -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 --decode
```

### `FATAL: database "tasksdb" does not exist`

**Causa:** La variable `POSTGRES_DB` en el Secret no está bien configurada.  
**Solución:**
```bash
# Verificar el valor
kubectl get secret -n database postgres-secret -o jsonpath='{.data.POSTGRES_DB}' | base64 --decode
# Debe retornar: tasksdb
```

### Datos perdidos al reiniciar el pod

**Causa:** El pod no está usando el PVC (olvidaste agregar el volumeMount).  
**Solución:**
```bash
# Verificar que el pod tiene el volumen montado
kubectl describe pod -n database -l app=postgres | grep -A10 "Volumes:"
# Debe mostrar el PVC
```

---

## 📝 Resumen

- Los datos de los Pods son **efímeros** — usa PVC para persistencia
- **PVC** solicita almacenamiento al cluster
- **StorageClass** provisiona el PV automáticamente
- PostgreSQL en K8s: Secret + PVC + Deployment + Service
- Usa `pg_isready` como readiness probe
- El DNS interno para PostgreSQL: `postgres-service.database.svc.cluster.local`

---

## ➡️ Siguiente módulo

👉 [07 - Seguridad y RBAC: Control de acceso](./07-security-rbac.md)
