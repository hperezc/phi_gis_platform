#!/bin/bash

echo "🚀 Iniciando despliegue de PHI GIS Platform en DigitalOcean..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar errores
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Función para mostrar éxito
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar información
info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Función para mostrar advertencias
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.production.yml" ]; then
    error_exit "No se encuentra docker-compose.production.yml. Ejecutar desde el directorio raíz del proyecto."
fi

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    error_exit "Docker no está instalado. Instalar Docker primero."
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    error_exit "Docker Compose no está instalado. Instalar Docker Compose primero."
fi

# Crear archivo .env.production si no existe
if [ ! -f ".env.production" ]; then
    info_msg "Creando archivo .env.production..."
    cp env.production.example .env.production
    warning_msg "¡IMPORTANTE! Edita .env.production con tus valores reales antes de continuar."
    read -p "¿Has editado el archivo .env.production? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error_exit "Edita .env.production primero y luego ejecuta el script nuevamente."
    fi
fi

# Detener contenedores existentes si están corriendo
info_msg "Deteniendo contenedores existentes..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

# Limpiar contenedores y volúmenes huérfanos
info_msg "Limpiando recursos Docker huérfanos..."
docker system prune -f

# Construir las imágenes
info_msg "Construyendo imágenes Docker..."
docker-compose -f docker-compose.production.yml build --no-cache || error_exit "Falló la construcción de imágenes"

# Verificar que las imágenes se construyeron
info_msg "Verificando imágenes construidas..."
docker images | grep -E "(phi_gis_platform|geoportal)" || warning_msg "Algunas imágenes pueden no haberse construido correctamente"

# Crear redes si no existen
info_msg "Creando redes Docker si no existen..."
docker network create phi_network 2>/dev/null || info_msg "Red phi_network ya existe"

# Iniciar los servicios
info_msg "Iniciando servicios en modo producción..."
docker-compose -f docker-compose.production.yml up -d || error_exit "Falló el inicio de servicios"

# Esperar un momento para que los servicios se inicien
info_msg "Esperando que los servicios se inicialicen (30 segundos)..."
sleep 30

# Verificar que los servicios están corriendo
info_msg "Verificando estado de los servicios..."
docker-compose -f docker-compose.production.yml ps

# Verificar conectividad de servicios
info_msg "Verificando conectividad de servicios..."

# Verificar aplicación principal
if curl -f http://localhost:8050/health &>/dev/null; then
    success_msg "Aplicación principal: ✅ Funcionando (puerto 8050)"
else
    warning_msg "Aplicación principal: ❌ No responde en puerto 8050"
fi

# Verificar geoportal backend
if curl -f http://localhost:8000 &>/dev/null; then
    success_msg "Geoportal Backend: ✅ Funcionando (puerto 8000)"
else
    warning_msg "Geoportal Backend: ❌ No responde en puerto 8000"
fi

# Verificar geoportal frontend
if curl -f http://localhost:3000 &>/dev/null; then
    success_msg "Geoportal Frontend: ✅ Funcionando (puerto 3000)"
else
    warning_msg "Geoportal Frontend: ❌ No responde en puerto 3000"
fi

# Verificar Nginx
if curl -f http://localhost:80 &>/dev/null; then
    success_msg "Nginx: ✅ Funcionando (puerto 80)"
else
    warning_msg "Nginx: ❌ No responde en puerto 80"
fi

# Mostrar logs recientes si hay problemas
echo
info_msg "Logs recientes de los servicios:"
docker-compose -f docker-compose.production.yml logs --tail=20 main_app geoportal-backend geoportal-frontend nginx

echo
success_msg "🎉 ¡Despliegue completado!"
echo
info_msg "URLs de acceso:"
echo "  🌐 Aplicación principal: http://142.93.118.216:8050"
echo "  🗺️  Geoportal: http://142.93.118.216:3000"
echo "  📊 Dashboard: http://142.93.118.216:8050/dashboard"
echo "  🤖 ML Asistentes: http://142.93.118.216:8501"
echo "  📈 ML Temporal: http://142.93.118.216:8502"
echo "  🌍 ML Geográfico: http://142.93.118.216:8503"
echo "  📊 Grafana: http://142.93.118.216:3001"
echo
info_msg "Para ver logs en tiempo real:"
echo "  docker-compose -f docker-compose.production.yml logs -f"
echo
info_msg "Para detener todos los servicios:"
echo "  docker-compose -f docker-compose.production.yml down"
echo
success_msg "¡Plataforma PHI GIS desplegada exitosamente! 🚀" 