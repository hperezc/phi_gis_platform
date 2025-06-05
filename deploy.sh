#!/bin/bash

# Script de despliegue para Digital Ocean
# PHI GIS Platform

set -e

echo "🚀 Iniciando despliegue de PHI GIS Platform en Digital Ocean..."

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

# Crear directorio nginx si no existe
mkdir -p nginx/ssl
mkdir -p nginx/webroot
mkdir -p monitoring

# Verificar variables de entorno
if [ ! -f ".env.production" ]; then
    warning "No se encontró .env.production. Creando plantilla..."
    cat > .env.production << 'EOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:25060/database?sslmode=require
MAPBOX_TOKEN=your_mapbox_token
SECRET_KEY=your_secret_key_here
DOMAIN=your_domain.com
SSL_EMAIL=your_email@domain.com
EOF
    error "Por favor, configura las variables en .env.production antes de continuar"
fi

# Cargar variables de entorno
source .env.production

# Validar variables críticas
if [ -z "$DATABASE_URL" ] || [ -z "$DOMAIN" ] || [ -z "$SSL_EMAIL" ]; then
    error "Variables críticas no configuradas en .env.production"
fi

log "Configurando nginx para el dominio: $DOMAIN"

# Actualizar configuración de nginx con el dominio real
sed -i "s/your_domain.com/$DOMAIN/g" nginx/nginx.conf

# Detener servicios existentes si están corriendo
log "Deteniendo servicios existentes..."
docker-compose -f docker-compose.production.yml down --remove-orphans 2>/dev/null || true

# Limpiar imágenes antiguas
log "Limpiando imágenes Docker antiguas..."
docker system prune -f

# Construir imágenes
log "Construyendo imágenes Docker..."
docker-compose -f docker-compose.production.yml build --no-cache

# Crear red si no existe
docker network create phi_network 2>/dev/null || true

# Iniciar servicios
log "Iniciando servicios..."
docker-compose -f docker-compose.production.yml up -d

# Esperar a que los servicios estén listos
log "Esperando a que los servicios se inicien..."
sleep 30

# Verificar que los servicios estén corriendo
log "Verificando servicios..."
if ! docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
    error "Algunos servicios no se iniciaron correctamente"
fi

# Generar certificados SSL
log "Configurando SSL con Let's Encrypt..."
docker-compose -f docker-compose.production.yml run --rm certbot

# Recargar nginx con SSL
log "Recargando nginx con configuración SSL..."
docker-compose -f docker-compose.production.yml restart nginx

# Verificar salud de la aplicación
log "Verificando salud de la aplicación..."
sleep 10

if curl -f http://localhost/health > /dev/null 2>&1; then
    log "✅ Aplicación desplegada exitosamente!"
    log "📊 Dashboard: https://$DOMAIN/dashboard"
    log "🗺️  Geoportal: https://$DOMAIN/geoportal"
    log "🤖 Predictivos: https://$DOMAIN/predictivos"
    log "📈 Monitoreo: https://$DOMAIN/monitoring"
else
    warning "La aplicación puede no estar completamente lista. Verifica los logs:"
    echo "docker-compose -f docker-compose.production.yml logs"
fi

log "🎉 ¡Despliegue completado!"

# Mostrar comandos útiles
echo
echo -e "${BLUE}Comandos útiles:${NC}"
echo "  Ver logs:     docker-compose -f docker-compose.production.yml logs -f"
echo "  Reiniciar:    docker-compose -f docker-compose.production.yml restart"
echo "  Detener:      docker-compose -f docker-compose.production.yml down"
echo "  Estado:       docker-compose -f docker-compose.production.yml ps"
echo "  SSL renovar:  docker-compose -f docker-compose.production.yml run --rm certbot renew" 