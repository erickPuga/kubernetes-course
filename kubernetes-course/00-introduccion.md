# 00 — Introducción a Kubernetes

> **Anterior:** [README](./README.md) | **Siguiente:** [01 - Kubernetes Basics](./01-kubernetes-basics.md)

---

## 🎯 Objetivos de este módulo

Al terminar este módulo sabrás:
- Qué problema resuelve Kubernetes
- La diferencia entre contenedores y Kubernetes
- Los casos de uso más comunes
- Los términos básicos que usaremos en todo el curso

---

## 1. ¿Qué es Kubernetes?

**Kubernetes** (también llamado **K8s**) es una plataforma de **orquestación de contenedores** de código abierto, creada originalmente por Google y donada a la Cloud Native Computing Foundation (CNCF) en 2014.

En términos simples:

> Kubernetes es el **sistema operativo de la nube** — gestiona dónde y cómo se ejecutan tus aplicaciones en contenedores.

Si Docker te permite **empaquetar** una aplicación en un contenedor, Kubernetes te dice **cuántas copias** correr, **dónde** correrlas, **cómo escalarlas**, y **qué hacer** si una cae.

---

## 2. Problemas que resuelve Kubernetes

### 😩 El problema antes de Kubernetes

Imagina que tienes una aplicación en producción:
- 1 servidor web Node.js
- 1 base de datos PostgreSQL
- 1 servidor de caché Redis

Preguntas comunes:
- ¿Qué pasa si el servidor Node.js se cae?
- ¿Cómo escalo a 10 instancias cuando hay mucho tráfico?
- ¿Cómo actualizo la app sin tiempo de inactividad (downtime)?
- ¿Cómo distribuyo la carga entre múltiples servidores?
- ¿Cómo gestiono los secretos (passwords, tokens)?

**Sin Kubernetes:** Tienes que resolver todo esto manualmente, con scripts frágiles.  
**Con Kubernetes:** Todo esto está automatizado y es declarativo.

---

### ✅ Lo que Kubernetes automatiza

| Problema | Solución en K8s |
|---|---|
| App se cae | Auto-restart automático |
| Más tráfico | Auto-scaling (HPA) |
| Deploy sin downtime | Rolling updates |
| Distribuir carga | Load balancing integrado |
| Gestión de configs | ConfigMaps y Secrets |
| Almacenamiento | Persistent Volumes |
| Acceso externo | Ingress Controllers |

---

## 3. Contenedores vs Kubernetes

Es una confusión muy común. Aquí la diferencia clara:

```
Docker (contenedores)      Kubernetes (orquestador)
─────────────────────      ─────────────────────────
"Empaqueta mi app"         "Corre mi app a escala"
1 contenedor               Miles de contenedores
Tu laptop                  Un cluster de servidores
Manual                     Declarativo / automático
```

**Analogía real:**
- Un **contenedor Docker** es como un vagón de tren.
- **Kubernetes** es el sistema ferroviario completo: las vías, los horarios, el control de tráfico.

---

## 4. Arquitectura simplificada

```
┌─────────────────────────────────────────┐
│           KUBERNETES CLUSTER            │
│                                         │
│  ┌─────────────────┐  ┌──────────────┐  │
│  │  Control Plane  │  │    Node 1    │  │
│  │  (el cerebro)   │  │  ┌────────┐  │  │
│  │                 │  │  │ Pod A  │  │  │
│  │  API Server     │  │  └────────┘  │  │
│  │  Scheduler      │  │  ┌────────┐  │  │
│  │  etcd           │  │  │ Pod B  │  │  │
│  │  Controller Mgr │  │  └────────┘  │  │
│  └─────────────────┘  └──────────────┘  │
│                        ┌──────────────┐  │
│                        │    Node 2    │  │
│                        │  ┌────────┐  │  │
│                        │  │ Pod C  │  │  │
│                        │  └────────┘  │  │
│                        └──────────────┘  │
└─────────────────────────────────────────┘
```

> No te preocupes por entender todo esto ahora. Lo veremos en detalle en el [Módulo 01](./01-kubernetes-basics.md).

---

## 5. Casos de uso reales

### 🏦 Fintech / Banking
- Deploys sin downtime para servicios críticos
- Scaling automático en horarios pico

### 🛒 E-Commerce
- Escalar el carrito de compras en Black Friday (x100)
- Microservicios: pagos, inventario, catálogo — todos separados

### 🎮 Gaming
- Servidores de juego que escalan con la demanda
- Zero-downtime updates

### 📱 Startups SaaS
- Desplegar nuevas versiones de forma segura
- Rollback instantáneo si algo falla

---

## 6. Glosario básico

Estos términos los usarás en **todo el curso**. Memorízalos:

| Término | Significado |
|---|---|
| **Cluster** | Conjunto de máquinas (nodes) que corren Kubernetes |
| **Node** | Una máquina (física o virtual) dentro del cluster |
| **Pod** | La unidad más pequeña de K8s. Contiene uno o más contenedores |
| **Deployment** | Gestiona cuántas copias (réplicas) de un Pod deben correr |
| **Service** | Expone un Pod o grupo de Pods a la red |
| **Namespace** | Espacio de nombres para organizar recursos |
| **ConfigMap** | Configuración en texto plano para tu app |
| **Secret** | Configuración sensible (passwords, tokens) |
| **Ingress** | Reglas para acceso externo HTTP/HTTPS |
| **PVC** | Persistent Volume Claim — solicitud de almacenamiento |
| **kubectl** | La CLI para interactuar con Kubernetes |
| **YAML** | El formato de configuración que usa K8s |
| **kind** | Kubernetes IN Docker — nuestro cluster local |

---

## 7. Filosofía de Kubernetes: Declarativo vs Imperativo

Este concepto es **clave** para entender K8s:

### Imperativo (cómo hacerlo):
```bash
# Le dices QUÉ HACER paso a paso
docker run -d nginx
docker run -d nginx
docker run -d nginx
```

### Declarativo (qué quieres):
```yaml
# Le dices EL ESTADO DESEADO
# Kubernetes se encarga del resto
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3      # Quiero 3 copias corriendo
  # Si una cae, K8s crea una nueva automáticamente
```

> **K8s siempre intenta reconciliar el estado actual con el estado deseado.**

Si dices "quiero 3 réplicas" y una se cae, K8s crea una nueva automáticamente. No tienes que hacer nada.

---

## ✅ Validación del módulo

Asegúrate de poder responder:

- [ ] ¿Qué problema principal resuelve Kubernetes?
- [ ] ¿Cuál es la diferencia entre Docker y Kubernetes?
- [ ] ¿Qué es un Pod?
- [ ] ¿Qué significa "declarativo" en el contexto de K8s?
- [ ] ¿Qué es kind y por qué lo usamos?

---

## 🚨 Errores conceptuales comunes

**Error:** "Kubernetes reemplaza a Docker"  
**Correcto:** K8s *usa* Docker (u otros runtimes). Son complementarios.

**Error:** "K8s es solo para empresas grandes"  
**Correcto:** Desde startups hasta Google, K8s se adapta a cualquier escala.

**Error:** "Necesito un Cloud Provider para usar K8s"  
**Correcto:** Puedes correr K8s localmente con kind, minikube, k3s, etc.

---

## 📝 Resumen

- Kubernetes **orquesta contenedores** a escala
- Automatiza: restarts, scaling, deploys, configuración
- Funciona con un modelo **declarativo** — describes el estado deseado
- Usaremos **kind** para tener un cluster 100% local en Docker
- Los conceptos básicos: Cluster, Node, Pod, Deployment, Service

---

## ➡️ Siguiente módulo

👉 [01 - Kubernetes Basics: Arquitectura y objetos fundamentales](./01-kubernetes-basics.md)
