# Guía: Instalación de NGINX Ingress Controller en Kind

## 🎯 Objetivo

Instalar NGINX Ingress Controller en kind y **asegurar que siempre corra en el control-plane** donde los puertos 80 y 443 están mapeados.

---

## ⚡ Instalación Rápida (Recomendada)

Usa el script automatizado que instala y configura todo:

```bash
cd ~/k8s-lab
chmod +x install-ingress-nginx.sh
./install-ingress-nginx.sh
```

Este script:
1. ✅ Instala NGINX Ingress Controller
2. ✅ Lo configura para correr en el control-plane
3. ✅ Espera a que esté listo
4. ✅ Verifica la instalación

---

## 📝 Instalación Manual (Paso a Paso)

### Paso 1: Instalar NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

### Paso 2: Forzar ejecución en control-plane

Tienes dos opciones:

#### Opción A: Usando el patch YAML

```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  --patch-file ~/k8s-lab/ingress-nginx-control-plane-patch.yaml
```

#### Opción B: Usando patch JSON directo

```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/hostname":"curso-k8s-control-plane"}}}}}'
```

### Paso 3: Esperar a que esté listo

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Paso 4: Verificar

```bash
# Ver en qué nodo está corriendo (debe ser control-plane)
kubectl get pods -n ingress-nginx -o wide

# Verificar el nodeSelector
kubectl get deployment ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.spec.template.spec.nodeSelector}' | jq .
```

Deberías ver:
```json
{
  "kubernetes.io/hostname": "curso-k8s-control-plane",
  "kubernetes.io/os": "linux"
}
```

---

## 🔄 ¿Es permanente esta configuración?

**SÍ**, el patch modifica la especificación del Deployment de forma permanente:

✅ El pod siempre se programará en el control-plane
✅ Si el pod se reinicia, volverá al control-plane
✅ Si actualizas el deployment, se mantiene el nodeSelector
✅ Sobrevive reinicios del cluster

**PERO** si **desinstalar y reinstalar** ingress-nginx, tendrás que volver a aplicar el patch.

---

## 🧹 Desinstalación

Si necesitas desinstalar ingress-nginx:

```bash
kubectl delete namespace ingress-nginx
```

Para reinstalar, usa nuevamente el script `install-ingress-nginx.sh` que automáticamente aplicará la configuración correcta.

---

## ❓ ¿Por qué es necesario esto?

En kind, los puertos del host (80, 443) solo están mapeados al nodo **control-plane**:

```yaml
# kind-config.yml
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80      # ← Solo el control-plane tiene este mapping
  - containerPort: 443
    hostPort: 443
```

Si el pod de ingress-nginx corre en un worker:
❌ No podrá recibir tráfico desde `localhost:80`
❌ Obtendrás error "Empty reply from server"
❌ Solo funcionará con port-forward

Con el nodeSelector forzado al control-plane:
✅ El pod recibe tráfico desde `localhost:80`
✅ Funcionan dominios como `http://app.local`
✅ Todo funciona correctamente

---

## 🔍 Troubleshooting

### Verificar que está en el control-plane

```bash
kubectl get pods -n ingress-nginx -o wide
```

Si el NODE no es `curso-k8s-control-plane`, algo salió mal.

### Verificar el nodeSelector

```bash
kubectl get deployment ingress-nginx-controller -n ingress-nginx -o yaml | grep -A 3 nodeSelector
```

Debe incluir:
```yaml
nodeSelector:
  kubernetes.io/hostname: curso-k8s-control-plane
  kubernetes.io/os: linux
```

### El pod no inicia o está en Pending

```bash
# Ver eventos
kubectl describe pod -n ingress-nginx <pod-name>

# Ver logs
kubectl logs -n ingress-nginx <pod-name>
```

---

## 📚 Referencias

- [NGINX Ingress Controller - kind](https://kind.sigs.k8s.io/docs/user/ingress/#ingress-nginx)
- [Kubernetes NodeSelector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)
- Documento relacionado: `SOLUCION-INGRESS.md`
