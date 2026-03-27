# 🚀 Curso Completo de Kubernetes — Local con kind

> Aprende Kubernetes desde cero, ejecutando **todo en tu Mac con Docker**, sin necesidad de ningún Cloud Provider.

---

## 📋 Descripción

Este curso te lleva desde los conceptos básicos hasta un proyecto final funcional con **Frontend React + Backend Node.js + PostgreSQL**, todo desplegado en Kubernetes local usando **kind (Kubernetes IN Docker)**.

El enfoque es **100% práctico**, con laboratorios reales, comandos reales y YAML real.

---

## ✅ Requisitos

- Mac con macOS 12+ (Intel o Apple Silicon)
- **Docker Desktop** instalado y corriendo
- Terminal (zsh o bash)
- Conocimientos básicos de terminal
- Conocimientos básicos de desarrollo web (HTML, JS)
- **CERO conocimiento previo de Kubernetes** ← ¡Este curso es para ti!

---

## 🛠️ Herramientas que usaremos

| Herramienta | Propósito | Instalación |
|---|---|---|
| **Docker** | Contenedores | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **kind** | Kubernetes local | `brew install kind` |
| **kubectl** | CLI de Kubernetes | `brew install kubectl` |
| **Helm** | Package manager K8s | `brew install helm` |
| **Node.js** | Backend | `brew install node` |

### Instalación rápida de todo:
```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar herramientas
brew install kind kubectl helm node

# Verificar versiones
docker --version
kind --version
kubectl version --client
helm version
node --version
```

---

## 🗺️ Mapa de Aprendizaje

```
00-introduccion    ─→  ¿Qué es K8s? Conceptos fundamentales
01-kubernetes-basics  ─→  Arquitectura, objetos, kubectl
02-kind-local-cluster ─→  Tu primer cluster local
03-pods-deployments   ─→  Deployments, Services, scaling
04-networking-ingress ─→  Ingress, NGINX, acceso desde browser
05-configmaps-secrets ─→  Configuración y secretos
06-storage-postgresql ─→  Volúmenes, PVC, PostgreSQL
07-security-rbac      ─→  RBAC, ServiceAccounts
08-observability      ─→  Logs, probes, métricas
09-helm-kustomize     ─→  Packaging y templating
10-cicd-github-actions─→  CI/CD con GitHub Actions
11-proyecto-final ⭐   ─→  App completa en Kubernetes
```

---

## 📁 Estructura del Curso

```
kubernetes-course/
├── README.md                    ← Estás aquí
├── 00-introduccion.md
├── 01-kubernetes-basics.md
├── 02-kind-local-cluster.md
├── 03-pods-deployments-services.md
├── 04-networking-ingress.md
├── 05-configmaps-secrets.md
├── 06-storage-postgresql.md
├── 07-security-rbac.md
├── 08-observability-operations.md
├── 09-packaging-helm-kustomize.md
├── 10-cicd-github-actions.md
└── 11-proyecto-final.md
```

---

## 🚀 ¿Cómo navegar el curso?

1. **Lee los módulos en orden** — cada uno construye sobre el anterior
2. **Ejecuta cada laboratorio** — no solo leas, hazlo
3. **Si algo falla**, revisa la sección de **Errores comunes** de cada módulo
4. **El proyecto final** integra todo lo aprendido

---

## 📚 Módulos

| # | Módulo | Descripción |
|---|---|---|
| [00](./00-introduccion.md) | Introducción | ¿Qué es K8s y por qué existe? |
| [01](./01-kubernetes-basics.md) | Kubernetes Basics | Arquitectura y objetos fundamentales |
| [02](./02-kind-local-cluster.md) | Kind Local Cluster | Tu cluster local en minutos |
| [03](./03-pods-deployments-services.md) | Pods, Deployments, Services | Los bloques principales |
| [04](./04-networking-ingress.md) | Networking e Ingress | Exponer apps al mundo |
| [05](./05-configmaps-secrets.md) | ConfigMaps y Secrets | Configuración segura |
| [06](./06-storage-postgresql.md) | Storage y PostgreSQL | Persistencia de datos |
| [07](./07-security-rbac.md) | Seguridad y RBAC | Control de acceso |
| [08](./08-observability-operations.md) | Observabilidad | Logs, métricas, probes |
| [09](./09-packaging-helm-kustomize.md) | Helm y Kustomize | Packaging avanzado |
| [10](./10-cicd-github-actions.md) | CI/CD | Pipeline automatizado |
| [11](./11-proyecto-final.md) ⭐ | Proyecto Final | App completa en K8s |

---

## ▶️ ¡Comienza aquí!

👉 [00 - Introducción a Kubernetes](./00-introduccion.md)

---

*Curso creado para ejecutarse 100% en local. No se requiere ningún Cloud Provider.*
