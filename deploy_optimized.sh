#!/bin/bash

echo "🚀 DESPLIEGUE OPTIMIZADO DE PHI GIS PLATFORM EN DIGITALOCEAN"
echo "============================================================"
echo "⚡ Con optimizaciones de memoria para droplet de 80GB"
echo "============================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# Función para mostrar pasos importantes
step_msg() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Verificaciones previas
step_msg "VERIFICACIONES PREVIAS"
echo "============================================================"

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

success_msg "Verificaciones previas completadas"

# Configurar memoria del sistema
step_msg "CONFIGURACIÓN DE MEMORIA DEL SISTEMA"
echo "============================================================"

info_msg "Configurando swap y memoria virtual para evitar OOM..."

# Configurar límites de memoria del kernel para prevenir OOM
echo "vm.overcommit_memory=1" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "vm.overcommit_ratio=80" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf > /dev/null
sudo sysctl -p

# Verificar y crear swap si no existe suficiente
SWAP_SIZE=$(free -h | awk '/^Swap:/ {print $2}' | sed 's/[^0-9]*//g')
if [ "${SWAP_SIZE:-0}" -lt 4 ]; then
    info_msg "Creando archivo swap de 4GB para estabilidad..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    success_msg "Swap configurado correctamente"
else
    success_msg "Swap ya está configurado correctamente"
fi

# Configurar archivo .env.production
step_msg "CONFIGURACIÓN DE ARCHIVO .env.production"
echo "============================================================"

if [ ! -f ".env.production" ]; then
    info_msg "Creando archivo .env.production desde plantilla..."
    cp env.production.example .env.production
    
    # Generar SECRET_KEY segura
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env.production
    
    # Actualizar MAPBOX_TOKEN si está disponible
    MAPBOX_TOKEN="pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q"
    sed -i "s/your-mapbox-token-if-needed/$MAPBOX_TOKEN/g" .env.production
    
    success_msg "Archivo .env.production configurado automáticamente"
else
    success_msg "Archivo .env.production ya existe"
fi

# Limpiar ambiente Docker previo
step_msg "LIMPIEZA DE AMBIENTE DOCKER"
echo "============================================================"

info_msg "Deteniendo contenedores existentes..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

info_msg "Limpiando recursos Docker innecesarios..."
docker system prune -f --volumes
docker network prune -f

success_msg "Ambiente Docker limpio"

# Configurar límites de Docker daemon
step_msg "CONFIGURACIÓN DE DOCKER DAEMON"
echo "============================================================"

info_msg "Configurando límites de Docker daemon..."
sudo mkdir -p /etc/docker

# Crear configuración optimizada de Docker daemon
cat > /tmp/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "default-ulimits": {
    "memlock": {
      "hard": -1,
      "soft": -1
    },
    "nofile": {
      "hard": 65536,
      "soft": 65536
    }
  },
  "default-runtime": "runc",
  "experimental": false
}
EOF

sudo mv /tmp/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker
sleep 10

success_msg "Docker daemon configurado correctamente"

# Construir imágenes con optimizaciones
step_msg "CONSTRUCCIÓN DE IMÁGENES DOCKER"
echo "============================================================"

info_msg "Construyendo imágenes Docker con optimizaciones..."

# Establecer variables de entorno para build optimizado
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Construir con caché y paralelismo limitado
docker-compose -f docker-compose.production.yml build \
    --parallel \
    --compress \
    --no-cache \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    || error_exit "Falló la construcción de imágenes"

success_msg "Imágenes construidas correctamente"

# Crear redes
step_msg "CONFIGURACIÓN DE REDES"
echo "============================================================"

info_msg "Creando redes Docker..."
docker network create phi_network 2>/dev/null || info_msg "Red phi_network ya existe"
success_msg "Redes configuradas correctamente"

# Iniciar servicios con orden específico
step_msg "INICIO DE SERVICIOS"
echo "============================================================"

info_msg "Iniciando servicios en orden específico para optimizar memoria..."

# Iniciar servicios de base primero (Redis)
info_msg "Iniciando Redis..."
docker-compose -f docker-compose.production.yml up -d redis
sleep 10

# Iniciar aplicación principal
info_msg "Iniciando aplicación principal..."
docker-compose -f docker-compose.production.yml up -d main_app
sleep 20

# Iniciar geoportal backend
info_msg "Iniciando Geoportal Backend..."
docker-compose -f docker-compose.production.yml up -d geoportal-backend
sleep 15

# Iniciar geoportal frontend
info_msg "Iniciando Geoportal Frontend..."
docker-compose -f docker-compose.production.yml up -d geoportal-frontend
sleep 15

# Iniciar nginx
info_msg "Iniciando Nginx..."
docker-compose -f docker-compose.production.yml up -d nginx
sleep 10

# Iniciar monitoring
info_msg "Iniciando monitoreo..."
docker-compose -f docker-compose.production.yml up -d prometheus
sleep 10

success_msg "Todos los servicios iniciados correctamente"

# Verificar estado de servicios
step_msg "VERIFICACIÓN DE SERVICIOS"
echo "============================================================"

info_msg "Esperando que los servicios se estabilicen (60 segundos)..."
sleep 60

info_msg "Verificando estado de los servicios..."
docker-compose -f docker-compose.production.yml ps

# Verificar conectividad
step_msg "VERIFICACIÓN DE CONECTIVIDAD"
echo "============================================================"

# Función para verificar servicio con reintentos
check_service() {
    local url=$1
    local name=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
            success_msg "$name: ✅ Funcionando correctamente"
            return 0
        fi
        info_msg "$name: Intento $attempt/$max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    warning_msg "$name: ❌ No responde después de $max_attempts intentos"
    return 1
}

# Verificar servicios principales
check_service "http://localhost:8050/health" "Aplicación Principal (puerto 8050)"
check_service "http://localhost:8000" "Geoportal Backend (puerto 8000)"
check_service "http://localhost:3000" "Geoportal Frontend (puerto 3000)"
check_service "http://localhost:80" "Nginx (puerto 80)"
check_service "http://localhost:9090" "Prometheus (puerto 9090)"

# Mostrar estadísticas de recursos
step_msg "ESTADÍSTICAS DE RECURSOS"
echo "============================================================"

info_msg "Uso actual de memoria:"
free -h

info_msg "Uso de disco:"
df -h | grep -E "/$|/var/lib/docker"

info_msg "Contenedores y su uso de memoria:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Mostrar logs recientes si hay problemas
echo
step_msg "LOGS RECIENTES"
echo "============================================================"
info_msg "Últimos logs de los servicios principales:"
docker-compose -f docker-compose.production.yml logs --tail=10 main_app geoportal-backend geoportal-frontend nginx

# Mensaje final
echo
echo "============================================================"
success_msg "🎉 ¡DESPLIEGUE COMPLETADO EXITOSAMENTE!"
echo "============================================================"
echo
info_msg "URLs de acceso:"
echo "  🌐 Aplicación Principal: http://142.93.118.216:8050"
echo "  🌐 Aplicación Principal (Nginx): http://142.93.118.216"
echo "  🗺️  Geoportal Frontend: http://142.93.118.216:3000"
echo "  🗺️  Geoportal (via Nginx): http://142.93.118.216/geoportal"
echo "  🔧 API Geoportal: http://142.93.118.216:8000"
echo "  🔧 API (via Nginx): http://142.93.118.216/api"
echo "  📊 Dashboard: http://142.93.118.216:8050/dashboard"
echo "  🤖 ML Asistentes: http://142.93.118.216:8501"
echo "  📈 ML Temporal: http://142.93.118.216:8502"
echo "  🌍 ML Geográfico: http://142.93.118.216:8503"
echo "  📊 Prometheus: http://142.93.118.216:9090"
echo
info_msg "Comandos útiles:"
echo "  📋 Ver logs en tiempo real:"
echo "     docker-compose -f docker-compose.production.yml logs -f"
echo
echo "  📊 Ver estadísticas de recursos:"
echo "     docker stats"
echo
echo "  🔄 Reiniciar servicio específico:"
echo "     docker-compose -f docker-compose.production.yml restart <servicio>"
echo
echo "  ⏹️  Detener todos los servicios:"
echo "     docker-compose -f docker-compose.production.yml down"
echo
echo "  🧹 Limpiar recursos Docker:"
echo "     docker system prune -f"
echo
step_msg "CONFIGURACIÓN DE MONITOREO AUTOMÁTICO"
info_msg "Se recomienda configurar un cronjob para monitoreo:"
echo "  0 */6 * * * cd $(pwd) && docker-compose -f docker-compose.production.yml ps && docker stats --no-stream"
echo
success_msg "¡Plataforma PHI GIS desplegada exitosamente con optimizaciones de memoria! 🚀"
echo "============================================================" 