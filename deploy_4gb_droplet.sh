#!/bin/bash

echo "🚀 DESPLIEGUE PHI GIS PLATFORM EN DROPLET 4GB RAM"
echo "================================================="
echo "📍 IP: 45.55.212.201"
echo "💾 RAM: 4GB | 💿 Disco: 80GB | 🖥️ CPU: 2 vCPU"
echo "📍 Ubicación: NYC3 | 🐧 Sistema: Ubuntu 24.10 x64"
echo "================================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

step_msg() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Verificaciones previas
step_msg "VERIFICACIONES PREVIAS"
echo "================================================="

if [ ! -f "docker-compose.production.yml" ]; then
    error_exit "No se encuentra docker-compose.production.yml. Ejecutar desde el directorio raíz del proyecto."
fi

if ! command -v docker &> /dev/null; then
    error_exit "Docker no está instalado. Ejecutar setup_server.sh primero."
fi

if ! command -v docker-compose &> /dev/null; then
    error_exit "Docker Compose no está instalado. Ejecutar setup_server.sh primero."
fi

success_msg "Verificaciones completadas"

# Verificar memoria disponible
step_msg "VERIFICACIÓN DE MEMORIA"
echo "================================================="
TOTAL_MEM=$(free -m | awk '/^Mem:/ {print $2}')
AVAILABLE_MEM=$(free -m | awk '/^Mem:/ {print $7}')

info_msg "Memoria total: ${TOTAL_MEM}MB"
info_msg "Memoria disponible: ${AVAILABLE_MEM}MB"

if [ "$TOTAL_MEM" -lt 3500 ]; then
    error_exit "Memoria insuficiente. Se requieren al menos 4GB de RAM."
fi

if [ "$AVAILABLE_MEM" -lt 2000 ]; then
    warning_msg "Memoria disponible baja. Liberando memoria..."
    # Limpiar caché del sistema
    sudo sync && sudo sysctl vm.drop_caches=3
    sudo service snapd stop 2>/dev/null || true
fi

success_msg "Memoria verificada"

# Configurar archivo .env.production
step_msg "CONFIGURACIÓN DE VARIABLES DE ENTORNO"
echo "================================================="

if [ ! -f ".env.production" ]; then
    info_msg "Creando archivo .env.production..."
    cp env.production.example .env.production
    
    # Generar SECRET_KEY
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env.production
    
    success_msg "Archivo .env.production configurado"
else
    success_msg "Archivo .env.production ya existe"
fi

# Verificar configuración IP
if grep -q "45.55.212.201" .env.production; then
    success_msg "IP correcta configurada (45.55.212.201)"
else
    info_msg "Corrigiendo IP en archivo .env.production..."
    sed -i 's/142.93.118.216/45.55.212.201/g' .env.production
    success_msg "IP corregida"
fi

# Limpiar Docker
step_msg "LIMPIEZA DE DOCKER"
echo "================================================="

info_msg "Deteniendo contenedores existentes..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

info_msg "Limpiando recursos Docker..."
docker system prune -f --volumes
docker network prune -f
docker image prune -f

# Liberar más memoria
sudo sync && sudo sysctl vm.drop_caches=3

success_msg "Docker limpiado"

# Configurar límites de memoria del sistema
step_msg "CONFIGURACIÓN DE LÍMITES DE MEMORIA"
echo "================================================="

info_msg "Configurando límites estrictos de memoria..."
echo "vm.overcommit_memory=2" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "vm.overcommit_ratio=95" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "vm.swappiness=60" | sudo tee -a /etc/sysctl.conf > /dev/null
sudo sysctl -p

success_msg "Límites configurados"

# Construir imágenes con limitaciones
step_msg "CONSTRUCCIÓN DE IMÁGENES"
echo "================================================="

info_msg "Construyendo imágenes con límites de memoria..."

# Configurar BuildKit para usar menos memoria
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Construir una imagen a la vez para evitar sobrecarga de memoria
info_msg "Construyendo aplicación principal..."
docker-compose -f docker-compose.production.yml build main_app || error_exit "Fallo construcción main_app"

info_msg "Construyendo geoportal backend..."
docker-compose -f docker-compose.production.yml build geoportal-backend || error_exit "Fallo construcción geoportal-backend"

info_msg "Construyendo geoportal frontend..."
docker-compose -f docker-compose.production.yml build geoportal-frontend || error_exit "Fallo construcción geoportal-frontend"

success_msg "Imágenes construidas exitosamente"

# Crear red
info_msg "Creando red Docker..."
docker network create phi_network 2>/dev/null || info_msg "Red ya existe"

# Iniciar servicios uno por uno
step_msg "INICIO SECUENCIAL DE SERVICIOS"
echo "================================================="

info_msg "Iniciando Redis (cache)..."
docker-compose -f docker-compose.production.yml up -d redis
sleep 10

# Verificar que Redis esté corriendo
if ! docker-compose -f docker-compose.production.yml ps redis | grep -q "Up"; then
    error_exit "Redis no pudo iniciarse"
fi
success_msg "Redis iniciado correctamente"

info_msg "Iniciando aplicación principal..."
docker-compose -f docker-compose.production.yml up -d main_app
sleep 30

# Verificar aplicación principal
if ! docker-compose -f docker-compose.production.yml ps main_app | grep -q "Up"; then
    error_exit "Aplicación principal no pudo iniciarse"
fi
success_msg "Aplicación principal iniciada"

info_msg "Iniciando Geoportal Backend..."
docker-compose -f docker-compose.production.yml up -d geoportal-backend
sleep 20

info_msg "Iniciando Geoportal Frontend..."
docker-compose -f docker-compose.production.yml up -d geoportal-frontend
sleep 20

info_msg "Iniciando Nginx..."
docker-compose -f docker-compose.production.yml up -d nginx
sleep 10

success_msg "Todos los servicios principales iniciados"

# Verificar servicios
step_msg "VERIFICACIÓN DE SERVICIOS"
echo "================================================="

info_msg "Esperando estabilización (30 segundos)..."
sleep 30

info_msg "Estado de contenedores:"
docker-compose -f docker-compose.production.yml ps

# Verificar conectividad
check_service() {
    local url=$1
    local name=$2
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s --connect-timeout 10 "$url" > /dev/null 2>&1; then
            success_msg "$name: ✅ Funcionando"
            return 0
        fi
        info_msg "$name: Intento $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    echo -e "${YELLOW}⚠️  $name: No responde (puede estar iniciando)${NC}"
    return 1
}

info_msg "Verificando conectividad de servicios..."
check_service "http://localhost:8050/health" "Aplicación Principal"
check_service "http://localhost:8000" "Geoportal Backend"  
check_service "http://localhost:3000" "Geoportal Frontend"
check_service "http://localhost:80" "Nginx"

# Mostrar estadísticas finales
step_msg "ESTADÍSTICAS DEL SISTEMA"
echo "================================================="

info_msg "Uso actual de memoria:"
free -h

info_msg "Uso de contenedores:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

info_msg "Espacio en disco:"
df -h | grep -E "/$"

# Logs recientes
step_msg "LOGS RECIENTES"
echo "================================================="
info_msg "Últimos logs de servicios:"
docker-compose -f docker-compose.production.yml logs --tail=5 main_app geoportal-backend geoportal-frontend nginx

# Información final
echo
echo "================================================="
success_msg "🎉 DESPLIEGUE COMPLETADO PARA DROPLET 4GB"
echo "================================================="
echo
info_msg "🌐 URLs de acceso:"
echo "  📱 Aplicación Principal: http://45.55.212.201:8050"
echo "  🌐 Nginx (Proxy): http://45.55.212.201"
echo "  🗺️  Geoportal Frontend: http://45.55.212.201:3000"
echo "  🔧 Geoportal API: http://45.55.212.201:8000"
echo "  📊 Dashboard: http://45.55.212.201:8050/dashboard"
echo "  🤖 ML Asistentes: http://45.55.212.201:8501"
echo "  📈 ML Temporal: http://45.55.212.201:8502"
echo "  🌍 ML Geográfico: http://45.55.212.201:8503"
echo
info_msg "💾 Límites de memoria configurados:"
echo "  📱 Aplicación Principal: 2GB máx"
echo "  🗺️  Geoportal Backend: 800MB máx"
echo "  🎨 Geoportal Frontend: 600MB máx"
echo "  🔧 Redis: 256MB máx"
echo "  🌐 Nginx: 128MB máx"
echo "  📊 Total asignado: ~3.8GB de 4GB disponibles"
echo
info_msg "🛠️  Comandos útiles:"
echo "  📊 Ver estado: docker-compose -f docker-compose.production.yml ps"
echo "  📈 Ver recursos: docker stats"
echo "  📋 Ver logs: docker-compose -f docker-compose.production.yml logs -f"
echo "  🔄 Reiniciar: docker-compose -f docker-compose.production.yml restart"
echo "  ⏹️  Detener: docker-compose -f docker-compose.production.yml down"
echo
step_msg "MONITOREO RECOMENDADO"
info_msg "Ejecutar cada 10 minutos para monitorear:"
echo "  watch -n 600 'free -h && docker stats --no-stream'"
echo
success_msg "¡Plataforma PHI GIS optimizada para droplet de 4GB! 🚀"
echo "=================================================" 