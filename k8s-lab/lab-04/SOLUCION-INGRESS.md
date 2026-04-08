# Solución al problema "Empty reply from server" en Ingress

## 🐛 Problema

Al hacer `curl http://app.local` obteníamos el error:
```
curl: (52) Empty reply from server
```

Aunque el port-forward funcionaba correctamente, el acceso mediante hostname no funcionaba.

## 🔍 Diagnóstico

### Lo que estaba bien:
✅ El Ingress Controller estaba instalado y running
✅ Los pods de frontend y backend estaban corriendo
✅ Los Services tenían endpoints válidos
✅ El Ingress estaba configurado correctamente
✅ El `/etc/hosts` tenía las entradas correctas (`127.0.0.1 app.local api.local`)
✅ El cluster kind tenía los puertos 80 y 443 mapeados en el control-plane

### El problema real:
❌ **El pod del ingress-nginx-controller estaba corriendo en un worker node (`curso-k8s-worker2`) que NO tenía los puertos 80 y 443 mapeados.**

En kind, los puertos solo se mapean en los nodos especificados en el `kind-config.yml`. En este caso, solo el control-plane tenía el port mapping:

```yaml
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
```

Pero el pod se había programado en un worker debido a las tolerations y nodeSelector del deployment.

## ✅ Solución

### Opción 1: Forzar el pod al control-plane (implementada)

```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/hostname":"curso-k8s-control-plane"}}}}}'
```

Esto fuerza que el pod se ejecute específicamente en el nodo control-plane donde los puertos están mapeados.

### Opción 2: Mapear puertos en todos los workers

⚠️ **Esta opción NO es viable** porque kind no permite mapear el mismo puerto del host (e.g., 80) a múltiples nodos simultáneamente. Solo un nodo puede tener el port mapping.

Además, en la mayoría de las máquinas el puerto 443 ya está en uso por otros servicios.

**Por lo tanto, la Opción 1 (patch) es la solución correcta y recomendada.**

## 🧪 Validación

Después de aplicar la solución:

```bash
# Frontend
curl http://app.local
# ✅ Devuelve el HTML del frontend

# Backend health check
curl http://api.local/health
# ✅ {"status":"healthy","service":"backend"}

# Backend info endpoint
curl http://api.local/api/info
# ✅ {"service":"backend-api","version":"1.0.0","hostname":"backend-xxx","timestamp":"..."}
```

## 📚 Lecciones aprendidas

1. **En kind, los puertos solo se exponen en los nodos especificados** en `extraPortMappings`
2. **El ingress-controller debe correr en un nodo con puertos mapeados** para que el tráfico desde localhost llegue al cluster
3. **hostPort en el pod no es suficiente** si el nodo no tiene el puerto mapeado al host
4. **Verificar siempre dónde está corriendo el pod**: `kubectl get pods -n ingress-nginx -o wide`
5. **Los logs del ingress-controller** mostraban warnings pero el pod estaba healthy, el problema era de networking a nivel del nodo
6. **No se puede mapear el mismo puerto del host a múltiples nodos en kind** - solo un nodo puede tener el mapping de un puerto específico
7. **El patch del deployment es permanente** - el pod permanecerá en el control-plane incluso después de reinicios

## 🔧 Comandos útiles para debugging

```bash
# Ver en qué nodo corre el ingress controller
kubectl get pods -n ingress-nginx -o wide

# Ver qué puertos tiene mapeados el cluster kind
docker ps --filter name=curso-k8s

# Ver configuración del deployment
kubectl get deployment ingress-nginx-controller -n ingress-nginx -o yaml | grep -A 5 hostPort

# Verificar que el puerto 80 está escuchando
lsof -i :80

# Ver logs del ingress controller
kubectl logs -n ingress-nginx $(kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o name)

# Probar conectividad
curl -v http://app.local
```

---

**Fecha de resolución:** 31/03/2026  
**Tiempo de troubleshooting:** ~15 minutos  
**Cluster:** kind (curso-k8s) con 1 control-plane + 2 workers
