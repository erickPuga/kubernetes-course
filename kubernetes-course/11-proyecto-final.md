# 11 — Proyecto Final: Sistema Full-Stack por Etapas

> **Anterior:** [10 - CI/CD con GitHub Actions](./10-cicd-github-actions.md)

---

## Objetivo general

Construir un **Gestor de Tareas (Task Manager)** completo siguiendo un flujo progresivo:

1. Base de datos local
2. Backend local (sin Docker)
3. Frontend local
4. Dockerizacion con docker-compose
5. Despliegue en Kubernetes (kind)
6. Validacion y troubleshooting
7. Limpieza y proximos pasos

Todo funciona **100% en local**, sin Cloud Provider.

### Arquitectura final

```
Browser
   |
Ingress (tasks.local)
   |
   +-- /        --> frontend-service --> frontend pods (React/Nginx)
   +-- /api/*   --> backend-service  --> backend pods (Node.js)
                                               |
                                        postgres-service
                                               |
                                         postgres pod + PVC
```

### Estructura de carpetas del proyecto

```
task-manager/
├── backend/
│   ├── src/
│   │   ├── index.js
│   │   ├── db.js
│   │   └── routes/
│   │       └── tasks.js
│   ├── .env
│   ├── .env.example
│   ├── package.json
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── api.js
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-secret.yaml
    ├── 02-configmap.yaml
    ├── 03-postgres-pvc.yaml
    ├── 04-postgres-deployment.yaml
    ├── 05-postgres-service.yaml
    ├── 06-backend-deployment.yaml
    ├── 07-backend-service.yaml
    ├── 08-frontend-deployment.yaml
    ├── 09-frontend-service.yaml
    └── 10-ingress.yaml
```

---

# ETAPA 1 — Base de Datos (LOCAL)

## Objetivo

Entender el modelo de datos y dejarlo funcionando en local antes de cualquier contenedor.

## Diagrama logico

```
tasks
-----
id          SERIAL PK
title       VARCHAR(200) NOT NULL
description TEXT
status      VARCHAR(20)  DEFAULT 'pending'
             CHECK IN ('pending','in_progress','done')
created_at  TIMESTAMP    DEFAULT NOW()
updated_at  TIMESTAMP    DEFAULT NOW()
```

## Paso 1.1 — Levantar PostgreSQL local con Docker

```bash
docker run -d \
  --name tasks-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=tasksdb \
  -p 5432:5432 \
  postgres:15-alpine

# Verificar que esta corriendo
docker ps | grep tasks-db
```

## Paso 1.2 — Conectarse y crear el esquema

```bash
# Conectarse a la DB
docker exec -it tasks-db psql -U postgres -d tasksdb
```

Dentro de psql, ejecutar:

```sql
-- Crear tabla principal
CREATE TABLE tasks (
  id          SERIAL PRIMARY KEY,
  title       VARCHAR(200) NOT NULL,
  description TEXT,
  status      VARCHAR(20) DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'done')),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para mejorar rendimiento
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);

-- Verificar la tabla
\d tasks
```

## Paso 1.3 — Insertar datos de ejemplo

```sql
INSERT INTO tasks (title, description, status) VALUES
  ('Aprender Kubernetes', 'Completar todos los modulos del curso', 'in_progress'),
  ('Dockerizar la app',   'Crear Dockerfiles y docker-compose',    'pending'),
  ('Desplegar en kind',   'Crear los manifiestos YAML',            'pending'),
  ('Configurar Ingress',  'NGINX Ingress Controller',               'done');
```

## Paso 1.4 — Queries usadas por el backend

```sql
-- GET /api/tasks
SELECT id, title, description, status, created_at
FROM tasks
ORDER BY created_at DESC;

-- GET /api/tasks/:id
SELECT id, title, description, status, created_at
FROM tasks
WHERE id = $1;

-- POST /api/tasks
INSERT INTO tasks (title, description, status)
VALUES ($1, $2, $3)
RETURNING *;

-- PUT /api/tasks/:id
UPDATE tasks
SET title = $1, description = $2, status = $3, updated_at = NOW()
WHERE id = $4
RETURNING *;

-- DELETE /api/tasks/:id
DELETE FROM tasks WHERE id = $1
RETURNING id;
```

## Paso 1.5 — Validaciones

```bash
# Dentro de psql
SELECT * FROM tasks;
SELECT status, COUNT(*) FROM tasks GROUP BY status;
\q
```

---

# ETAPA 2 — Backend (LOCAL, SIN DOCKER)

## Objetivo

Construir la API REST conectada a la DB local, sin contenedores.

## Paso 2.1 — Crear el proyecto

```bash
mkdir -p ~/task-manager/backend/src/routes
cd ~/task-manager/backend

npm init -y
npm install express pg cors dotenv
npm install --save-dev nodemon
```

## Paso 2.2 — Archivos del backend

### `.env.example`

```bash
# Copiar como .env y ajustar valores
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tasksdb
DB_USER=postgres
DB_PASSWORD=postgres
PORT=3000
NODE_ENV=development
```

```bash
cp .env.example .env
```

### `src/db.js` — Conexion a PostgreSQL

```javascript
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'tasksdb',
  user:     process.env.DB_USER     || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

// Probar conexion al iniciar
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('[DB] Error de conexion:', err.message);
  } else {
    console.log('[DB] Conectado a PostgreSQL:', res.rows[0].now);
  }
});

module.exports = pool;
```

### `src/routes/tasks.js` — Rutas CRUD

```javascript
const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/tasks
router.get('/', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC'
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[GET /tasks]', err.message);
    res.status(500).json({ error: 'Error al obtener tareas' });
  }
});

// GET /api/tasks/:id
router.get('/:id', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT * FROM tasks WHERE id = $1',
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tasks
router.post('/', async (req, res) => {
  const { title, description = '', status = 'pending' } = req.body;
  if (!title || title.trim() === '') {
    return res.status(400).json({ error: 'El campo title es obligatorio' });
  }
  try {
    const result = await db.query(
      'INSERT INTO tasks (title, description, status) VALUES ($1, $2, $3) RETURNING *',
      [title.trim(), description, status]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/tasks/:id
router.put('/:id', async (req, res) => {
  const { title, description, status } = req.body;
  try {
    const result = await db.query(
      `UPDATE tasks
       SET title = COALESCE($1, title),
           description = COALESCE($2, description),
           status = COALESCE($3, status),
           updated_at = NOW()
       WHERE id = $4
       RETURNING *`,
      [title, description, status, req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/tasks/:id
router.delete('/:id', async (req, res) => {
  try {
    const result = await db.query(
      'DELETE FROM tasks WHERE id = $1 RETURNING id',
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
```

### `src/index.js` — Servidor principal

```javascript
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const tasksRouter = require('./routes/tasks');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Health checks
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

app.get('/health/ready', async (req, res) => {
  const db = require('./db');
  try {
    await db.query('SELECT 1');
    res.json({ status: 'ready', db: 'connected' });
  } catch (e) {
    res.status(503).json({ status: 'not ready', error: e.message });
  }
});

// Rutas de la API
app.use('/api/tasks', tasksRouter);

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: `Ruta ${req.path} no encontrada` });
});

app.listen(PORT, () => {
  console.log(`[Server] Backend corriendo en http://localhost:${PORT}`);
});
```

### `package.json` — scripts

```json
{
  "name": "tasks-backend",
  "version": "1.0.0",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.0.0",
    "express": "^4.18.0",
    "pg": "^8.11.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}
```

## Paso 2.3 — Ejecutar y probar

```bash
# Asegurate de que el contenedor tasks-db este corriendo
cd ~/task-manager/backend
npm run dev
```

Probar con curl:

```bash
# Health check
curl http://localhost:3000/health

# Listar tareas
curl http://localhost:3000/api/tasks

# Crear tarea
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Nueva tarea","description":"Descripcion","status":"pending"}'

# Actualizar tarea (cambia 1 por el id real)
curl -X PUT http://localhost:3000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'

# Eliminar tarea
curl -X DELETE http://localhost:3000/api/tasks/1
```

## Validaciones de la Etapa 2

```bash
# El servidor imprime: [DB] Conectado a PostgreSQL
# GET /api/tasks devuelve JSON con las tareas
# POST crea la tarea y la persiste en la DB
# Ver en psql: SELECT * FROM tasks;
```

---

# ETAPA 3 — Frontend (LOCAL)

## Objetivo

Construir la interfaz React que consume el backend local.

## Paso 3.1 — Crear el proyecto React

```bash
cd ~/task-manager
npm create vite@latest frontend -- --template react
cd frontend
npm install axios
```

## Paso 3.2 — Archivos del frontend

### `.env`

```bash
VITE_API_URL=http://localhost:3000/api
```

### `src/api.js` — Cliente de la API

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const getTasks   = ()         => api.get('/tasks');
export const createTask = (data)     => api.post('/tasks', data);
export const updateTask = (id, data) => api.put(`/tasks/${id}`, data);
export const deleteTask = (id)       => api.delete(`/tasks/${id}`);
```

### `src/App.jsx` — Componente principal

```jsx
import { useState, useEffect } from 'react';
import { getTasks, createTask, updateTask, deleteTask } from './api';

const STATUS_LABELS = {
  pending:     { label: 'Pendiente',   color: '#f59e0b' },
  in_progress: { label: 'En progreso', color: '#3b82f6' },
  done:        { label: 'Completada',  color: '#10b981' },
};

export default function App() {
  const [tasks,   setTasks]   = useState([]);
  const [title,   setTitle]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const loadTasks = async () => {
    try {
      const { data } = await getTasks();
      setTasks(data);
    } catch (e) {
      setError('Error al cargar tareas: ' + e.message);
    }
  };

  useEffect(() => { loadTasks(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      await createTask({ title: title.trim() });
      setTitle('');
      await loadTasks();
    } catch (e) {
      setError('Error al crear: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStatus = async (id, status) => {
    try {
      await updateTask(id, { status });
      await loadTasks();
    } catch (e) {
      setError('Error al actualizar: ' + e.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Eliminar esta tarea?')) return;
    try {
      await deleteTask(id);
      await loadTasks();
    } catch (e) {
      setError('Error al eliminar: ' + e.message);
    }
  };

  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 700, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ color: '#1e293b' }}>Task Manager</h1>
      <p style={{ color: '#64748b', marginBottom: 24 }}>
        API: {import.meta.env.VITE_API_URL}
      </p>

      {error && (
        <div style={{ background: '#fee2e2', color: '#991b1b', padding: '10px 14px',
                      borderRadius: 6, marginBottom: 16 }}>
          {error}
          <button onClick={() => setError('')} style={{ float: 'right', background: 'none',
                  border: 'none', cursor: 'pointer', fontSize: 16 }}>×</button>
        </div>
      )}

      <form onSubmit={handleCreate} style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Nueva tarea..."
          style={{ flex: 1, padding: '10px 14px', border: '1px solid #e2e8f0',
                   borderRadius: 6, fontSize: 15 }}
        />
        <button disabled={loading}
          style={{ padding: '10px 20px', background: '#3b82f6', color: 'white',
                   border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14 }}>
          {loading ? '...' : 'Agregar'}
        </button>
      </form>

      {tasks.length === 0 ? (
        <p style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>
          No hay tareas. Crea una arriba.
        </p>
      ) : (
        tasks.map(task => {
          const s = STATUS_LABELS[task.status] || STATUS_LABELS.pending;
          return (
            <div key={task.id} style={{ background: 'white', border: '1px solid #e2e8f0',
                borderRadius: 8, padding: '14px 16px', marginBottom: 10,
                display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ flex: 1, textDecoration: task.status === 'done' ? 'line-through' : 'none',
                             color: task.status === 'done' ? '#94a3b8' : '#1e293b' }}>
                {task.title}
              </span>
              <span style={{ background: s.color + '22', color: s.color,
                             padding: '2px 10px', borderRadius: 20, fontSize: 12 }}>
                {s.label}
              </span>
              <select value={task.status}
                onChange={e => handleStatus(task.id, e.target.value)}
                style={{ padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: 4 }}>
                <option value="pending">Pendiente</option>
                <option value="in_progress">En progreso</option>
                <option value="done">Completada</option>
              </select>
              <button onClick={() => handleDelete(task.id)}
                style={{ padding: '4px 12px', background: '#ef4444', color: 'white',
                         border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                Eliminar
              </button>
            </div>
          );
        })
      )}
    </div>
  );
}
```

### `vite.config.js`

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:3000'  // Proxy en dev para evitar CORS
    }
  }
});
```

## Paso 3.3 — Ejecutar el frontend

```bash
# Terminal 1: Backend (asegurate de que siga corriendo)
cd ~/task-manager/backend && npm run dev

# Terminal 2: Frontend
cd ~/task-manager/frontend && npm run dev

# Abrir en el navegador
open http://localhost:5173
```

## Validaciones de la Etapa 3

```
- La lista de tareas se muestra al cargar la pagina
- Crear una tarea y verla aparecer inmediatamente
- Cambiar el status con el selector
- Eliminar una tarea
- Confirmar los cambios en la DB: SELECT * FROM tasks;
```

---

# ETAPA 4 — Dockerizacion

## Objetivo

Convertir el sistema local en contenedores Docker y orquestarlos con docker-compose.

## Paso 4.1 — Dockerfile del Backend

```dockerfile
# backend/Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json .
RUN npm ci --production
COPY src/ ./src/
EXPOSE 3000
CMD ["node", "src/index.js"]
```

## Paso 4.2 — Dockerfile del Frontend

```dockerfile
# frontend/Dockerfile

# Etapa 1: Build de React
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
# En build, VITE_API_URL queda vacio para usar /api (proxy via Ingress)
RUN VITE_API_URL=/api npm run build

# Etapa 2: Servir con Nginx
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Configuracion para que React Router funcione
RUN echo 'server { \
  listen 80; \
  location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Paso 4.3 — docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: tasks-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: tasksdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: tasks-backend
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: tasksdb
      DB_USER: postgres
      DB_PASSWORD: postgres
      PORT: 3000
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    container_name: tasks-frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Paso 4.4 — Ejecutar con docker-compose

```bash
cd ~/task-manager

# Construir y levantar todos los servicios
docker compose up --build -d

# Ver el estado
docker compose ps

# Ver logs de todos los servicios
docker compose logs -f

# Ver logs solo del backend
docker compose logs -f backend

# Probar
curl http://localhost:3000/health
open http://localhost:8080
```

## Paso 4.5 — Validar persistencia

```bash
# Crear una tarea
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Tarea persistente"}'

# Reiniciar el contenedor de postgres
docker compose restart postgres

# Esperar a que este listo
sleep 5

# Los datos deben seguir ahi
curl http://localhost:3000/api/tasks
```

## Paso 4.6 — Limpiar docker-compose

```bash
# Parar y eliminar contenedores (mantiene el volumen)
docker compose down

# Eliminar todo incluyendo el volumen de datos
docker compose down -v
```

---

# ETAPA 5 — Kubernetes (kind)

## Objetivo

Desplegar el sistema dockerizado en Kubernetes local con kind.

## Paso 5.1 — Preparar el cluster

```bash
# Verificar que el cluster esta corriendo (del Modulo 02)
kubectl cluster-info --context kind-curso-k8s

# Si no tienes cluster, crearlo con el kind-config.yaml del Modulo 02:
# kind create cluster --name curso-k8s --config ~/k8s-lab/kind-config.yaml
```

## Paso 5.2 — Construir y cargar imagenes en kind

```bash
cd ~/task-manager

# Build de las imagenes
docker build -t tasks-backend:v1  ./backend/
docker build -t tasks-frontend:v1 ./frontend/

# Cargar en kind (no hace pull de internet)
kind load docker-image tasks-backend:v1  --name curso-k8s
kind load docker-image tasks-frontend:v1 --name curso-k8s

# Verificar
docker exec curso-k8s-control-plane crictl images | grep tasks
```

## Paso 5.3 — Crear todos los manifiestos YAML

```bash
mkdir -p ~/task-manager/k8s
cd ~/task-manager/k8s
```

### 00-namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tasks-app
  labels:
    app.kubernetes.io/managed-by: kubectl
```

### 01-secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: tasks-app
type: Opaque
data:
  # echo -n "postgres" | base64
  POSTGRES_USER:     cG9zdGdyZXM=
  # echo -n "postgres" | base64
  POSTGRES_PASSWORD: cG9zdGdyZXM=
  # echo -n "tasksdb" | base64
  POSTGRES_DB:       dGFza3NkYg==
```

### 02-configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: tasks-app
data:
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "tasksdb"
  PORT:    "3000"
  NODE_ENV: "production"
```

### 03-postgres-pvc.yaml

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: tasks-app
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
```

### 04-postgres-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: tasks-app
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
            cpu: "500m"
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "postgres"]
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 5
        livenessProbe:
          exec:
            command: ["pg_isready", "-U", "postgres"]
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### 05-postgres-service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: tasks-app
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### 06-backend-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: tasks-app
  labels:
    app: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: tasks-backend:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: backend-config
        env:
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
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "300m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 15
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 5
```

### 07-backend-service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: tasks-app
spec:
  selector:
    app: backend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

### 08-frontend-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: tasks-app
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
        image: tasks-frontend:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "32Mi"
            cpu: "25m"
          limits:
            memory: "64Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 09-frontend-service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: tasks-app
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### 10-ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tasks-ingress
  namespace: tasks-app
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  ingressClassName: nginx
  rules:
  - host: tasks.local
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: backend-service
            port:
              number: 3000
      - path: /()(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## Paso 5.4 — Instalar NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

## Paso 5.5 — Aplicar los manifiestos en orden

```bash
cd ~/task-manager/k8s

kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secret.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-postgres-pvc.yaml
kubectl apply -f 04-postgres-deployment.yaml
kubectl apply -f 05-postgres-service.yaml

# Esperar a que postgres este Ready
kubectl wait --for=condition=ready pod -l app=postgres \
  -n tasks-app --timeout=120s

kubectl apply -f 06-backend-deployment.yaml
kubectl apply -f 07-backend-service.yaml
kubectl apply -f 08-frontend-deployment.yaml
kubectl apply -f 09-frontend-service.yaml
kubectl apply -f 10-ingress.yaml
```

## Paso 5.6 — Configurar /etc/hosts y verificar

```bash
echo "127.0.0.1 tasks.local" | sudo tee -a /etc/hosts

# Esperar a que todos los pods esten Ready
kubectl wait --for=condition=ready pod -l app=backend  -n tasks-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=frontend -n tasks-app --timeout=60s

# Probar
curl http://tasks.local/api/tasks

curl -X POST http://tasks.local/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Mi primera tarea en K8s"}'

# Abrir en el navegador
open http://tasks.local
```

---

# ETAPA 6 — Validacion y Troubleshooting

## Ver estado general

```bash
# Todos los recursos del namespace
kubectl get all -n tasks-app

# Estado de los pods
kubectl get pods -n tasks-app -o wide

# Ver el PVC
kubectl get pvc -n tasks-app

# Ver el Ingress
kubectl get ingress -n tasks-app
```

## Ver logs

```bash
# Logs del backend
kubectl logs -n tasks-app deployment/backend

# Logs en tiempo real
kubectl logs -n tasks-app deployment/backend -f

# Logs del pod anterior (si crasheo)
kubectl logs -n tasks-app <nombre-pod> --previous

# Logs de postgres
kubectl logs -n tasks-app deployment/postgres
```

## Ejecutar comandos dentro de pods

```bash
# Shell en el backend
kubectl exec -it -n tasks-app deployment/backend -- sh

# Ejecutar una query en postgres
kubectl exec -it -n tasks-app deployment/postgres -- \
  psql -U postgres -d tasksdb -c "SELECT * FROM tasks;"

# Probar conectividad entre pods
kubectl run nettest --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://backend-service.tasks-app.svc.cluster.local:3000/health
```

## Diagnosticar CrashLoopBackOff

```bash
# Ver el motivo del crash
kubectl describe pod -n tasks-app <nombre-pod>
kubectl logs -n tasks-app <nombre-pod> --previous

# Causas comunes:
# - Imagen no encontrada → kind load docker-image ...
# - Variables de entorno mal configuradas → kubectl describe pod
# - La DB no esta lista → ver readinessProbe
```

## Diagnosticar ImagePullBackOff

```bash
kubectl describe pod -n tasks-app <nombre-pod> | grep -A5 "Events:"
# Si dice ErrImageNeverPull o ImagePullBackOff:

# Verificar que la imagen existe en kind
docker exec curso-k8s-control-plane crictl images | grep tasks

# Recargar la imagen
kind load docker-image tasks-backend:v1 --name curso-k8s
```

## Diagnosticar problemas de conexion a DB

```bash
# Verificar que el servicio de postgres existe
kubectl get service postgres-service -n tasks-app

# Verificar que postgres tiene endpoints (pods activos)
kubectl get endpoints postgres-service -n tasks-app

# Verificar desde el backend
kubectl exec -it -n tasks-app deployment/backend -- \
  sh -c "nc -zv postgres-service 5432 && echo 'OK' || echo 'FALLO'"
```

## Diagnosticar fallas de Ingress

```bash
# Verificar que el Ingress tiene ADDRESS
kubectl get ingress -n tasks-app
# Si ADDRESS esta vacio, el Ingress Controller no esta listo

# Ver logs del Ingress Controller
kubectl logs -n ingress-nginx \
  $(kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o name) \
  --tail=30

# Verificar IngressClass
kubectl get ingressclass

# Verificar /etc/hosts
grep tasks.local /etc/hosts
```

---

# ETAPA 7 — Limpieza y Proximos Pasos

## Limpiar los recursos de Kubernetes

```bash
# Eliminar solo los recursos de la app (mantiene el cluster)
kubectl delete namespace tasks-app

# Verificar que se elimino todo
kubectl get all -n tasks-app
```

## Limpiar /etc/hosts

```bash
# Abrir y eliminar la linea tasks.local
sudo nano /etc/hosts
# Eliminar: 127.0.0.1 tasks.local
```

## Limpiar docker-compose (si aplica)

```bash
cd ~/task-manager
docker compose down -v
docker rmi tasks-backend:v1 tasks-frontend:v1
```

## Eliminar el cluster kind (opcional)

```bash
kind delete cluster --name curso-k8s
```

---

## Ideas de mejoras futuras

Una vez completado el proyecto base, puedes extenderlo con:

1. **Autenticacion con JWT**
   - Agregar endpoint `POST /api/auth/login`
   - Middleware de autenticacion en el backend
   - Guardar el token en el frontend

2. **Horizontal Pod Autoscaler (HPA)**
   - Escalar el backend automaticamente segun CPU
   - Requiere `metrics-server` instalado

3. **Observabilidad con Prometheus y Grafana**
   - Exponer `/metrics` desde el backend con `prom-client`
   - Instalar `kube-prometheus-stack` con Helm

4. **CI/CD con GitHub Actions**
   - Pipeline que construye y pushea las imagenes
   - Deploy automatico al cluster

5. **GitOps con ArgoCD**
   - El cluster se sincroniza automaticamente desde el repositorio Git

6. **TLS/HTTPS con cert-manager**
   - Certificados automaticos con Let's Encrypt en produccion

---

## Checklist final

Verifica que completaste todas las etapas:

- [ ] Etapa 1: DB local con PostgreSQL, tablas creadas, datos insertados
- [ ] Etapa 2: Backend corriendo en localhost:3000, CRUD probado con curl
- [ ] Etapa 3: Frontend React corriendo en localhost:5173, flujo completo funcional
- [ ] Etapa 4: docker compose up levanta los 3 servicios, datos persisten
- [ ] Etapa 5: Imagenes cargadas en kind, todos los YAMLs aplicados
- [ ] Etapa 5: `http://tasks.local` abre la app desde el navegador
- [ ] Etapa 5: CRUD de tareas funciona desde el navegador contra K8s
- [ ] Etapa 5: Los datos persisten al reiniciar el pod de postgres
- [ ] Etapa 6: Sabes ver logs, describir pods y diagnosticar errores comunes
- [ ] Etapa 7: Sabes limpiar los recursos correctamente
