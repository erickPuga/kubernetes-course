# 07 — Seguridad y RBAC: Control de Acceso

> **Anterior:** [06 - Storage y PostgreSQL](./06-storage-postgresql.md) | **Siguiente:** [08 - Observabilidad](./08-observability-operations.md)

---

## Objetivos de este modulo

- Entender el modelo de seguridad de Kubernetes
- Crear Roles y ClusterRoles
- Asignar permisos con RoleBindings
- Usar ServiceAccounts correctamente
- Aplicar el principio de minimo privilegio

---

## 1. Modelo de seguridad de Kubernetes

```
Tu peticion a la API:
kubectl get pods

Paso 1: Autenticacion  →  ¿Quien eres?     (certificado, token)
Paso 2: Autorizacion   →  ¿Puedes hacerlo? (RBAC)
Paso 3: Admission      →  ¿Esta permitido? (politicas)
```

### Dos tipos de usuarios en K8s

| Tipo | Descripcion | Gestionado por |
|---|---|---|
| **User** | Personas/sistemas externos | Fuera de K8s (certificados, OIDC) |
| **ServiceAccount** | Pods/aplicaciones dentro del cluster | Kubernetes |

> En este curso usaremos **ServiceAccounts** (los User accounts son para produccion con proveedores de identidad).

---

## 2. RBAC — Role-Based Access Control

RBAC controla **quien puede hacer que** en el cluster.

### Conceptos principales

```
ServiceAccount  → "Identidad" del Pod
Role            → "Que acciones puede hacer" (en un namespace)
ClusterRole     → "Que acciones puede hacer" (en todo el cluster)
RoleBinding     → "Asignar Role a una identidad" (en un namespace)
ClusterRoleBinding → "Asignar ClusterRole a una identidad" (todo el cluster)
```

### Estructura de permisos

```yaml
# Un permiso en RBAC tiene 3 partes:
# apiGroups + resources + verbs

apiGroups: [""]        # API group (vacio = core: pods, services, etc.)
resources: ["pods"]    # Que recurso
verbs: ["get", "list"] # Que acciones
```

**Verbs disponibles:**

| Verb | Descripcion | Equivale a |
|---|---|---|
| `get` | Obtener un recurso | READ por ID |
| `list` | Listar recursos | READ ALL |
| `watch` | Observar cambios | STREAM |
| `create` | Crear recurso | CREATE |
| `update` | Actualizar completo | PUT |
| `patch` | Actualizar parcial | PATCH |
| `delete` | Eliminar recurso | DELETE |
| `*` | Todos los verbos | ALL |

---

## 3. Role (namespace-scoped)

Un **Role** solo aplica dentro de un namespace especifico.

```yaml
# role-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
```

```yaml
# role-app-manager.yaml — Rol mas completo
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-manager
  namespace: production
rules:
# Gestionar Deployments
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]

# Ver Pods y logs
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["get", "list", "watch", "create"]

# Ver Services
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list", "watch"]

# Ver ConfigMaps (no Secrets)
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
```

---

## 4. ClusterRole (cluster-scoped)

Un **ClusterRole** aplica en todo el cluster o para recursos no-namespaciados (como Nodes).

```yaml
# clusterrole-node-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]

- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
```

### ClusterRoles predefinidos

K8s incluye ClusterRoles de sistema:

```bash
# Ver todos los ClusterRoles del sistema
kubectl get clusterroles | grep -v system:

# Roles mas importantes:
# cluster-admin  → acceso total (usar con cuidado!)
# admin          → acceso admin en un namespace
# edit           → leer y escribir la mayoria de recursos
# view           → solo lectura
```

---

## 5. RoleBinding

**RoleBinding** asigna un Role a un usuario/grupo/ServiceAccount **dentro de un namespace**.

```yaml
# rolebinding-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: default
subjects:
# Quien recibe el permiso:
- kind: ServiceAccount
  name: mi-app-sa
  namespace: default
# Tambien puede ser User o Group:
# - kind: User
#   name: alice@empresa.com
roleRef:
  # El Role o ClusterRole que se asigna
  kind: Role              # o ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Asignar ClusterRole en un namespace

```yaml
# Puedes usar un ClusterRole dentro de un namespace via RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: edit-binding
  namespace: staging
subjects:
- kind: ServiceAccount
  name: deploy-bot
  namespace: staging
roleRef:
  kind: ClusterRole    # ClusterRole usado en namespace especifico
  name: edit
  apiGroup: rbac.authorization.k8s.io
```

---

## 6. ClusterRoleBinding

Asigna un ClusterRole a nivel de todo el cluster.

```yaml
# Usar con mucho cuidado — da acceso global
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: monitoring-binding
subjects:
- kind: ServiceAccount
  name: prometheus-sa
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## 7. ServiceAccounts

Cada Pod tiene automaticamente un ServiceAccount (`default`). Para mayor control, crea ServiceAccounts especificos.

```yaml
# serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: production
  labels:
    app: backend
```

### Usar ServiceAccount en un Pod

```yaml
spec:
  serviceAccountName: backend-sa   # ← Asignar al Pod
  containers:
  - name: backend
    image: mi-backend:v1
```

### Token del ServiceAccount

El token se monta automaticamente en el Pod:

```bash
# Ver el token desde dentro del pod
kubectl exec -it mi-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/token

# Ver el namespace
kubectl exec -it mi-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
```

---

## 8. Principio de minimo privilegio

> "Una aplicacion debe tener SOLO los permisos que necesita para funcionar."

### Ejemplo practico

**Backend que solo necesita leer ConfigMaps:**

```yaml
# Solo dar acceso de lectura a ConfigMaps en su namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
  resourceNames: ["app-config"]  # Restringir a UN ConfigMap especifico
```

**NO hacer esto (demasiados permisos):**

```yaml
# MAL - Demasiados permisos
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

---

## Lab: RBAC en practica

### Paso 1: Crear namespace y ServiceAccount

```bash
mkdir -p ~/k8s-lab/lab-07
cd ~/k8s-lab/lab-07

cat > ~/k8s-lab/lab-07/rbac.yaml << 'EOF'
# Namespace para la app
apiVersion: v1
kind: Namespace
metadata:
  name: app-prod
---
# ServiceAccount para el backend
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: app-prod
---
# Role: el backend puede leer pods y configmaps
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: app-prod
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
# RoleBinding: asignar el role al ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-rolebinding
  namespace: app-prod
subjects:
- kind: ServiceAccount
  name: backend-sa
  namespace: app-prod
roleRef:
  kind: Role
  name: backend-role
  apiGroup: rbac.authorization.k8s.io
---
# Pod de prueba usando el ServiceAccount
apiVersion: v1
kind: Pod
metadata:
  name: backend-pod
  namespace: app-prod
spec:
  serviceAccountName: backend-sa
  containers:
  - name: backend
    image: curlimages/curl:latest
    command: ["sleep", "3600"]
EOF

kubectl apply -f ~/k8s-lab/lab-07/rbac.yaml
```

### Paso 2: Verificar los permisos

```bash
# Ver los recursos creados
kubectl get serviceaccount,role,rolebinding -n app-prod

# Verificar permisos con kubectl auth can-i
kubectl auth can-i get pods \
  --as=system:serviceaccount:app-prod:backend-sa \
  --namespace=app-prod
# yes

kubectl auth can-i delete pods \
  --as=system:serviceaccount:app-prod:backend-sa \
  --namespace=app-prod
# no

kubectl auth can-i get secrets \
  --as=system:serviceaccount:app-prod:backend-sa \
  --namespace=app-prod
# no
```

### Paso 3: Probar desde dentro del Pod

```bash
# Entrar al pod
kubectl exec -it -n app-prod backend-pod -- sh

# Dentro del pod, usar el token para hacer peticiones a la API
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

# Listar pods (permitido)
curl -sk -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/pods \
  | head -20

# Intentar listar secrets (denegado)
curl -sk -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/secrets

# Salir
exit
```

### Paso 4: Rol de solo lectura global

```bash
cat > ~/k8s-lab/lab-07/readonly-binding.yaml << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: monitoring-sa
  namespace: app-prod
---
# Usar ClusterRole "view" predefinido (solo lectura en el namespace)
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: monitoring-view-binding
  namespace: app-prod
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: app-prod
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl apply -f ~/k8s-lab/lab-07/readonly-binding.yaml

# Verificar
kubectl auth can-i list deployments \
  --as=system:serviceaccount:app-prod:monitoring-sa \
  --namespace=app-prod
# yes

kubectl auth can-i create deployments \
  --as=system:serviceaccount:app-prod:monitoring-sa \
  --namespace=app-prod
# no
```

### Limpiar

```bash
kubectl delete namespace app-prod
```

---

## Comandos utiles de RBAC

```bash
# Ver que puede hacer un usuario/SA
kubectl auth can-i --list \
  --as=system:serviceaccount:default:mi-sa

# Ver permisos en un namespace
kubectl auth can-i --list \
  --as=system:serviceaccount:default:mi-sa \
  --namespace=production

# Ver todos los roles en un namespace
kubectl get roles,rolebindings -n default

# Describir un role (ver sus permisos)
kubectl describe role pod-reader -n default

# Ver quien puede hacer que (audit)
kubectl get rolebindings -A \
  -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,ROLE:.roleRef.name,SUBJECTS:.subjects[*].name'
```

---

## Validaciones

```bash
# ServiceAccounts creados
kubectl get serviceaccounts -n app-prod

# Roles y bindings
kubectl get roles,rolebindings -n app-prod

# Permisos correctos
kubectl auth can-i get pods \
  --as=system:serviceaccount:app-prod:backend-sa -n app-prod
# yes

kubectl auth can-i delete pods \
  --as=system:serviceaccount:app-prod:backend-sa -n app-prod
# no
```

---

## Errores comunes

### `Forbidden: pods is forbidden`

```
Error from server (Forbidden): pods is forbidden: 
User "system:serviceaccount:default:default" 
cannot list resource "pods" in API group "" in the namespace "default"
```

**Causa:** El ServiceAccount `default` no tiene permisos.  
**Solucion:** Crear un Role y RoleBinding para el SA.

### El ServiceAccount no tiene el Role correcto

```bash
# Verificar el binding
kubectl describe rolebinding mi-binding -n mi-namespace

# Verificar que el SA es el correcto
kubectl get pod mi-pod -o jsonpath='{.spec.serviceAccountName}'
```

### `clusterrolebindings.rbac.authorization.k8s.io is forbidden`

**Causa:** Solo un cluster-admin puede crear ClusterRoleBindings.  
**Solucion:** Usar `kubectl` con privilegios de admin del cluster kind.

---

## Resumen

- **RBAC** controla quien puede hacer que en el cluster
- **Role** = permisos en un namespace
- **ClusterRole** = permisos en todo el cluster
- **RoleBinding** = asigna Role a una identidad en un namespace
- **ServiceAccount** = identidad para los Pods
- Principio clave: **minimo privilegio** — solo lo necesario
- Verificar permisos: `kubectl auth can-i`

---

## Siguiente modulo

[08 - Observabilidad: Logs, Probes y Metricas](./08-observability-operations.md)
