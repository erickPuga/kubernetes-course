# 10 — CI/CD con GitHub Actions

> **Anterior:** [09 - Helm y Kustomize](./09-packaging-helm-kustomize.md) | **Siguiente:** [11 - Proyecto Final](./11-proyecto-final.md)

---

## Objetivos de este modulo

- Entender el flujo CI/CD para apps en Kubernetes
- Crear pipelines con GitHub Actions
- Build, tag y push de imagenes Docker
- Deploy automatico a un cluster (kind local o EKS/GKE)

---

## 1. Flujo CI/CD para Kubernetes

```
Developer → git push → GitHub
                          ↓
                   GitHub Actions
                          ↓
              ┌───────────┴──────────┐
              ↓                      ↓
           CI (build)             CD (deploy)
         ─────────────           ─────────────
         1. Tests               1. kubectl apply
         2. Docker build        2. helm upgrade
         3. Push to registry    3. kustomize apply
```

---

## 2. Estructura del repositorio

```
my-app/
├── .github/
│   └── workflows/
│       ├── ci.yml          ← Build y test
│       └── cd.yml          ← Deploy a K8s
├── src/
│   └── index.js
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── overlays/
│       ├── staging/
│       └── production/
├── Dockerfile
└── package.json
```

---

## 3. Workflow de CI — Build y Push

```yaml
# .github/workflows/ci.yml
name: CI - Build and Push

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: npm test

    - name: Run linter
      run: npm run lint

  build-and-push:
    name: Build and Push Docker Image
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
    - uses: actions/checkout@v4

    # Login al GitHub Container Registry
    - name: Login to GHCR
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    # Generar tags automaticos (version semver, branch, sha)
    - name: Extract metadata for Docker
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=sha,prefix=sha-

    # Build y push multi-plataforma
    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

---

## 4. Workflow de CD — Deploy a Kubernetes

```yaml
# .github/workflows/cd.yml
name: CD - Deploy to Kubernetes

on:
  workflow_run:
    workflows: ["CI - Build and Push"]
    types: [completed]
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Ambiente de deploy'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production
      image-tag:
        description: 'Tag de imagen a desplegar'
        required: false

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    # Configurar kubectl con las credenciales del cluster
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

    # Actualizar la imagen con kustomize
    - name: Update image tag
      run: |
        IMAGE_TAG=sha-${GITHUB_SHA::7}
        cd k8s/overlays/staging
        kustomize edit set image \
          app-image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${IMAGE_TAG}

    # Aplicar los manifiestos
    - name: Deploy to staging
      run: |
        kubectl apply -k k8s/overlays/staging/
        kubectl rollout status deployment/mi-app -n staging --timeout=120s

    # Smoke test basico
    - name: Smoke test
      run: |
        sleep 10
        kubectl run smoke-test \
          --image=curlimages/curl \
          --rm --restart=Never \
          -n staging \
          -- curl -f http://mi-app-service/health

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}

    - name: Update image tag
      run: |
        IMAGE_TAG=sha-${GITHUB_SHA::7}
        cd k8s/overlays/production
        kustomize edit set image \
          app-image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${IMAGE_TAG}

    - name: Deploy to production
      run: |
        kubectl apply -k k8s/overlays/production/
        kubectl rollout status deployment/mi-app -n production --timeout=180s

    - name: Notify Slack on success
      if: success()
      uses: slackapi/slack-github-action@v1
      with:
        payload: |
          {
            "text": "Deploy a production exitoso: ${{ github.sha }}"
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 5. Configurar Secrets en GitHub

```bash
# Los secrets se configuran en:
# GitHub → Settings → Secrets and variables → Actions

# Secrets necesarios:
# KUBE_CONFIG_STAGING  → kubeconfig del cluster de staging
# KUBE_CONFIG_PROD     → kubeconfig del cluster de produccion
# SLACK_WEBHOOK        → URL del webhook de Slack (opcional)

# Obtener el kubeconfig del cluster kind local:
cat ~/.kube/config | base64

# Para EKS:
aws eks update-kubeconfig --name mi-cluster --region us-east-1
cat ~/.kube/config | base64
```

---

## 6. Workflow simplificado (todo en uno)

```yaml
# .github/workflows/build-deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set image tag
      id: tag
      run: echo "tag=sha-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT

    - name: Build Docker image
      run: |
        docker build -t ghcr.io/${{ github.repository }}:${{ steps.tag.outputs.tag }} .

    - name: Push to registry
      run: |
        echo ${{ secrets.GITHUB_TOKEN }} | \
          docker login ghcr.io -u ${{ github.actor }} --password-stdin
        docker push ghcr.io/${{ github.repository }}:${{ steps.tag.outputs.tag }}

    - name: Deploy to cluster
      env:
        KUBECONFIG_DATA: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBECONFIG_DATA" | base64 -d > /tmp/kubeconfig
        export KUBECONFIG=/tmp/kubeconfig

        # Actualizar la imagen del deployment
        kubectl set image deployment/mi-app \
          mi-app=ghcr.io/${{ github.repository }}:${{ steps.tag.outputs.tag }}

        # Esperar rollout
        kubectl rollout status deployment/mi-app --timeout=120s
```

---

## 7. Rollback automatico

```yaml
    - name: Deploy with rollback on failure
      run: |
        # Guardar el revision actual
        PREV_REVISION=$(kubectl rollout history deployment/mi-app \
          --output=jsonpath='{.metadata.generation}')

        # Intentar el deploy
        kubectl set image deployment/mi-app \
          mi-app=ghcr.io/${{ github.repository }}:${{ steps.tag.outputs.tag }}

        # Esperar y verificar
        if ! kubectl rollout status deployment/mi-app --timeout=120s; then
          echo "Deploy fallido, haciendo rollback..."
          kubectl rollout undo deployment/mi-app
          kubectl rollout status deployment/mi-app --timeout=60s
          exit 1
        fi
```

---

## 8. GitOps con ArgoCD

Una alternativa moderna al CD en GitHub Actions es usar **ArgoCD**:

```yaml
# ArgoCD sincroniza automaticamente el cluster con el repositorio Git
# Si el YAML en Git cambia → ArgoCD actualiza el cluster

# application.yaml (ArgoCD)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mi-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/mi-org/mi-app
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

```bash
# Instalar ArgoCD en kind
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Acceder a la UI
kubectl port-forward -n argocd service/argocd-server 8080:443 &
open https://localhost:8080

# Password inicial
kubectl get secret -n argocd argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 --decode
```

---

## Lab: Pipeline local con Act

Puedes probar los workflows de GitHub Actions localmente con `act`:

```bash
# Instalar act
brew install act

# Listar los jobs disponibles
act --list

# Ejecutar el workflow de CI
act push

# Ejecutar un job especifico
act push -j build-and-push

# Con variables de entorno
act push \
  -s GITHUB_TOKEN=tu-token \
  -s KUBE_CONFIG=tu-kubeconfig
```

---

## Resumen

- El flujo CI/CD: codigo → build → push imagen → deploy a K8s
- GitHub Actions: CI (build/test) y CD (deploy) en `.github/workflows/`
- Usar `kubectl set image` o `kustomize edit set image` para actualizar la imagen
- `kubectl rollout status` verifica que el deploy fue exitoso
- `kubectl rollout undo` hace rollback si falla
- GitOps (ArgoCD): el cluster se sincroniza automaticamente con Git

---

## Siguiente modulo

[11 - Proyecto Final: App completa en Kubernetes](./11-proyecto-final.md)
