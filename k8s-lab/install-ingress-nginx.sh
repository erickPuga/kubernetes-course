#!/bin/bash
# Script para instalar NGINX Ingress Controller en kind
# Configurado para correr SIEMPRE en el control-plane

set -e

echo "🚀 Instalando NGINX Ingress Controller para kind..."

# Instalar ingress-nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "⏳ Esperando a que el namespace ingress-nginx esté listo..."
sleep 5

# Esperar a que el deployment esté creado
echo "⏳ Esperando a que el deployment esté disponible..."
kubectl wait --namespace ingress-nginx \
  --for=condition=available deployment/ingress-nginx-controller \
  --timeout=90s || true

echo "🔧 Configurando nodeSelector para forzar ejecución en control-plane..."

# Parchear el deployment para que SIEMPRE corra en el control-plane
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/hostname":"curso-k8s-control-plane"}}}}}'

echo "⏳ Esperando a que el pod esté listo en el control-plane..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo ""
echo "✅ NGINX Ingress Controller instalado correctamente"
echo ""
echo "📍 Verificación:"
kubectl get pods -n ingress-nginx -o wide

echo ""
echo "🎯 El ingress-nginx-controller está corriendo en: $(kubectl get pods -n ingress-nginx -o jsonpath='{.items[0].spec.nodeName}')"
echo ""
echo "💡 Tip: Este pod siempre se programará en el control-plane donde los puertos 80 y 443 están mapeados"
