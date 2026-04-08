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
