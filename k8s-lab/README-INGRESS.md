# 🚀 Ingress NGINX - Configuración para Kind

Este directorio contiene herramientas para instalar y configurar correctamente NGINX Ingress Controller en kind.

## 📁 Archivos disponibles

### Scripts y configuración
- **`install-ingress-nginx.sh`** - Script automatizado de instalación ⭐ RECOMENDADO
- **`ingress-nginx-control-plane-patch.yaml`** - Patch para forzar ejecución en control-plane
- **`lab-04/INSTALACION-INGRESS.md`** - Guía completa de instalación
- **`lab-04/SOLUCION-INGRESS.md`** - Troubleshooting del error "Empty reply from server"

---

## ⚡ Quick Start

### Instalación automática (1 comando)

```bash
cd ~/k8s-lab
chmod +x install-ingress-nginx.sh
./install-ingress-nginx.sh
```

Este script:
1. Instala NGINX Ingress Controller
2. Lo configura para correr en el control-plane
3. Espera a que esté listo
4. Verifica que funciona correctamente

### Instalación manual

```bash
# 1. Instalar ingress-nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# 2. Forzar ejecución en control-plane
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/hostname":"curso-k8s-control-plane"}}}}}'

# 3. Esperar a que esté listo
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

---

## ❓ ¿Por qué es necesario forzar al control-plane?

En kind, los puertos 80 y 443 **solo están mapeados en el nodo control-plane**:

```yaml
# kind-config.yml
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80      # ← Solo aquí
  - containerPort: 443
    hostPort: 443
```

**Si el pod corre en un worker:**
- ❌ No recibe tráfico desde `localhost:80`
- ❌ Error "Empty reply from server" al hacer curl
- ❌ Solo funciona con port-forward

**Con el pod en control-plane:**
- ✅ Recibe tráfico desde `localhost:80`
- ✅ Funcionan dominios como `http://app.local`
- ✅ Todo funciona correctamente

---

## 🔍 Verificación

```bash
# Ver en qué nodo está corriendo (debe ser control-plane)
kubectl get pods -n ingress-nginx -o wide

# Verificar el nodeSelector
kubectl get deployment ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.spec.template.spec.nodeSelector}' | jq .

# Probar conectividad (necesitas configurar /etc/hosts primero)
curl http://app.local
```

---

## 📚 Documentación completa

- **Instalación:** `lab-04/INSTALACION-INGRESS.md`
- **Troubleshooting:** `lab-04/SOLUCION-INGRESS.md`
- **Lab 4 completo:** Ver `../kubernetes-course/04-networking-ingress.md`

---

## 🔄 ¿Es permanente?

**SÍ**, mientras no desinstales ingress-nginx:
- ✅ El pod siempre se programará en el control-plane
- ✅ Sobrevive reinicios del pod
- ✅ Sobrevive reinicios del cluster

**NO**, si desinstalar y reinstalar ingress-nginx:
- ⚠️ Necesitarás volver a aplicar el patch
- 💡 Usa el script `install-ingress-nginx.sh` para reinstalar correctamente

---

## 🆘 ¿Problemas?

### Error "Empty reply from server"
Ver guía completa: `lab-04/SOLUCION-INGRESS.md`

### El pod está en un worker
```bash
# Aplicar el patch
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  --patch-file ~/k8s-lab/ingress-nginx-control-plane-patch.yaml
```

### Reinstalar desde cero
```bash
# Desinstalar
kubectl delete namespace ingress-nginx

# Reinstalar correctamente
cd ~/k8s-lab
./install-ingress-nginx.sh
```

---

**Última actualización:** 31/03/2026  
**Cluster:** kind (curso-k8s) - 1 control-plane + 2 workers
