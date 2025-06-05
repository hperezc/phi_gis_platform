#!/bin/bash

# Script de despliegue para Digital Ocean usando IP directa
# PHI GIS Platform - Fase 1 (Sin Dominio)

set -e

echo "🚀 Iniciando despliegue PHI GIS Platform con IP directa..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    error "No se encontró main.py. Ejecuta este script desde el directorio raíz del proyecto."
fi

# Crear directorios necesarios
mkdir -p nginx/ssl
mkdir -p nginx/webroot
mkdir -p monitoring
mkdir -p logs
mkdir -p backups

# Verificar variables de entorno
if [ ! -f ".env.production" ]; then
    warning "No se encontró .env.production. Creando plantilla..."
    cat > .env.production << 'EOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:25060/database?sslmode=require
MAPBOX_TOKEN=pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBtIVaj52w2yw-7ewLU6Q
SECRET_KEY=cambiar_por_clave_secreta_segura
DOMAIN=tu_ip_del_vps
SSL_EMAIL=tu_email@domain.com
SSL_ENABLED=false
EOF
    error "Por favor, configura las variables en .env.production antes de continuar"
fi

# Cargar variables de entorno
source .env.production

# Validar variables críticas
if [ -z "$DATABASE_URL" ] || [ -z "$DOMAIN" ]; then
    error "Variables críticas no configuradas en .env.production"
fi

# Detectar si es IP o dominio
if [[ $DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    IS_IP=true
    log "Configurando para IP directa: $DOMAIN"
else
    IS_IP=false
    log "Configurando para dominio: $DOMAIN"
fi

# Crear configuración de nginx para IP directa
log "Creando configuración nginx para IP..."

cat > nginx/nginx-ip.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json application/xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream servers
    upstream main_app {
        server main_app:8050;
    }

    upstream streamlit_asistentes {
        server main_app:8501;
    }

    upstream streamlit_temporal {
        server main_app:8502;
    }

    upstream streamlit_geografico {
        server main_app:8503;
    }

    upstream grafana {
        server grafana:3000;
    }

    # Main HTTP server (sin SSL para IP)
    server {
        listen 80;
        server_name _;  # Acepta cualquier host/IP

        # Main application
        location / {
            proxy_pass http://main_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
        }

        # Dashboard routes
        location /dashboard/ {
            proxy_pass http://main_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Streamlit apps
        location /predictivos/asistentes/ {
            proxy_pass http://streamlit_asistentes/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /predictivos/temporal/ {
            proxy_pass http://streamlit_temporal/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /predictivos/geografico/ {
            proxy_pass http://streamlit_geografico/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Grafana monitoring
        location /monitoring/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Crear docker-compose simplificado para IP
log "Creando configuración Docker para IP..."

cat > docker-compose.ip.yml << 'EOF'
version: '3.8'

services:
  # Aplicación principal
  main_app:
    build: 
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8050:8050"
      - "8501:8501"
      - "8502:8502"
      - "8503:8503"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - MAPBOX_TOKEN=${MAPBOX_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env.production
    restart: unless-stopped
    depends_on:
      - redis
    networks:
      - phi_network
    volumes:
      - ./logs:/app/logs

  # Servicio Nginx simplificado
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx-ip.conf:/etc/nginx/nginx.conf
      - ./static:/app/static
    depends_on:
      - main_app
    restart: unless-stopped
    networks:
      - phi_network

  # Redis para cache y sesiones
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - phi_network

  # Servicio para monitoreo
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped
    networks:
      - phi_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - phi_network

volumes:
  grafana-storage:

networks:
  phi_network:
    driver: bridge
EOF

# Detener servicios existentes si están corriendo
log "Deteniendo servicios existentes..."
docker-compose -f docker-compose.ip.yml down --remove-orphans 2>/dev/null || true

# Limpiar imágenes antiguas
log "Limpiando imágenes Docker antiguas..."
docker system prune -f

# Construir imágenes
log "Construyendo imágenes Docker..."
docker-compose -f docker-compose.ip.yml build --no-cache

# Crear red si no existe
docker network create phi_network 2>/dev/null || true

# Iniciar servicios
log "Iniciando servicios..."
docker-compose -f docker-compose.ip.yml up -d

# Esperar a que los servicios estén listos
log "Esperando a que los servicios se inicien..."
sleep 30

# Verificar que los servicios estén corriendo
log "Verificando servicios..."
if ! docker-compose -f docker-compose.ip.yml ps | grep -q "Up"; then
    error "Algunos servicios no se iniciaron correctamente"
fi

# Verificar salud de la aplicación
log "Verificando salud de la aplicación..."
sleep 10

if curl -f http://localhost/health > /dev/null 2>&1; then
    log "✅ Aplicación desplegada exitosamente!"
    log "🌐 Accede en: http://$DOMAIN"
    log "📊 Dashboard: http://$DOMAIN/dashboard"
    log "🗺️  Geoportal: http://$DOMAIN/geoportal"  
    log "🤖 Predictivos: http://$DOMAIN/predictivos"
    log "📈 Monitoreo: http://$DOMAIN/monitoring"
else
    warning "La aplicación puede no estar completamente lista. Verifica los logs:"
    echo "docker-compose -f docker-compose.ip.yml logs"
fi

log "🎉 ¡Despliegue con IP completado!"

# Mostrar comandos útiles
echo
echo -e "${BLUE}Comandos útiles:${NC}"
echo "  Ver logs:     docker-compose -f docker-compose.ip.yml logs -f"
echo "  Reiniciar:    docker-compose -f docker-compose.ip.yml restart"
echo "  Detener:      docker-compose -f docker-compose.ip.yml down"
echo "  Estado:       docker-compose -f docker-compose.ip.yml ps"
echo
echo -e "${YELLOW}Para agregar dominio después:${NC}"
echo "  1. Configura DOMAIN en .env.production"
echo "  2. Ejecuta: ./deploy.sh" 