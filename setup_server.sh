#!/bin/bash

echo "🔧 CONFIGURACIÓN INICIAL DEL SERVIDOR DIGITALOCEAN"
echo "=================================================="
echo "⚡ Optimizando servidor para PHI GIS Platform"
echo "=================================================="

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

# Verificar que somos root o tenemos sudo
if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
    error_exit "Este script necesita permisos de root o sudo"
fi

# Actualizar sistema
step_msg "ACTUALIZACIÓN DEL SISTEMA"
echo "=================================================="
info_msg "Actualizando paquetes del sistema..."
sudo apt update && sudo apt upgrade -y
success_msg "Sistema actualizado"

# Instalar dependencias básicas
step_msg "INSTALACIÓN DE DEPENDENCIAS BÁSICAS"
echo "=================================================="
info_msg "Instalando herramientas esenciales..."
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    python3 \
    python3-pip \
    python3-venv

success_msg "Dependencias básicas instaladas"

# Configurar límites del sistema
step_msg "CONFIGURACIÓN DE LÍMITES DEL SISTEMA"
echo "=================================================="
info_msg "Configurando límites de archivos y procesos..."

# Configurar límites en /etc/security/limits.conf
cat >> /etc/security/limits.conf << EOF
# PHI GIS Platform optimizations
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
root soft nofile 65536
root hard nofile 65536
root soft nproc 32768
root hard nproc 32768
EOF

# Configurar límites en systemd
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/limits.conf << EOF
[Manager]
DefaultLimitNOFILE=65536
DefaultLimitNPROC=32768
EOF

success_msg "Límites del sistema configurados"

# Optimizar kernel para aplicaciones web
step_msg "OPTIMIZACIÓN DEL KERNEL"
echo "=================================================="
info_msg "Configurando parámetros del kernel..."

cat >> /etc/sysctl.conf << EOF

# PHI GIS Platform kernel optimizations
# Memoria
vm.overcommit_memory=1
vm.overcommit_ratio=80
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5

# Red
net.core.somaxconn=65535
net.core.netdev_max_backlog=5000
net.ipv4.tcp_max_syn_backlog=65535
net.ipv4.tcp_keepalive_time=600
net.ipv4.tcp_keepalive_intvl=60
net.ipv4.tcp_keepalive_probes=10
net.ipv4.tcp_fin_timeout=30

# Archivos
fs.file-max=2097152
fs.inotify.max_user_watches=524288
EOF

sysctl -p
success_msg "Kernel optimizado"

# Configurar swap
step_msg "CONFIGURACIÓN DE SWAP"
echo "=================================================="
SWAP_SIZE=$(free -h | awk '/^Swap:/ {print $2}' | sed 's/[^0-9]*//g')
if [ "${SWAP_SIZE:-0}" -lt 2 ]; then
    info_msg "Creando archivo swap de 2GB para droplet de 4GB RAM..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    success_msg "Swap de 2GB configurado correctamente"
else
    success_msg "Swap ya está configurado"
fi

# Instalar Docker
step_msg "INSTALACIÓN DE DOCKER"
echo "=================================================="
if ! command -v docker &> /dev/null; then
    info_msg "Instalando Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Agregar usuario actual al grupo docker
    sudo usermod -aG docker $USER
    
    success_msg "Docker instalado correctamente"
else
    success_msg "Docker ya está instalado"
fi

# Instalar Docker Compose
step_msg "INSTALACIÓN DE DOCKER COMPOSE"
echo "=================================================="
if ! command -v docker-compose &> /dev/null; then
    info_msg "Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    success_msg "Docker Compose instalado"
else
    success_msg "Docker Compose ya está instalado"
fi

# Configurar Docker daemon
step_msg "CONFIGURACIÓN DE DOCKER DAEMON"
echo "=================================================="
info_msg "Configurando Docker daemon para optimización..."

sudo mkdir -p /etc/docker
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
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "data-root": "/var/lib/docker"
}
EOF

sudo mv /tmp/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker
sudo systemctl enable docker

success_msg "Docker daemon configurado"

# Configurar firewall básico
step_msg "CONFIGURACIÓN DE FIREWALL"
echo "=================================================="
info_msg "Configurando UFW (firewall)..."

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Puertos necesarios para PHI GIS Platform
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8050/tcp  # Aplicación principal
sudo ufw allow 8000/tcp  # Geoportal backend
sudo ufw allow 3000/tcp  # Geoportal frontend
sudo ufw allow 8501/tcp  # Streamlit ML Asistentes
sudo ufw allow 8502/tcp  # Streamlit ML Temporal
sudo ufw allow 8503/tcp  # Streamlit ML Geográfico
sudo ufw allow 9090/tcp  # Prometheus

sudo ufw --force enable
success_msg "Firewall configurado"

# Instalar herramientas de monitoreo
step_msg "INSTALACIÓN DE HERRAMIENTAS DE MONITOREO"
echo "=================================================="
info_msg "Instalando herramientas de monitoreo..."

sudo pip3 install psutil docker-compose

# Crear script de monitoreo del sistema
cat > /usr/local/bin/phi-monitor << 'EOF'
#!/bin/bash
echo "=== PHI GIS Platform System Monitor ==="
echo "Fecha: $(date)"
echo "Uptime: $(uptime)"
echo ""
echo "=== Memoria ==="
free -h
echo ""
echo "=== Disco ==="
df -h
echo ""
echo "=== CPU ==="
top -bn1 | grep "Cpu(s)"
echo ""
echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Docker Stats ==="
timeout 5 docker stats --no-stream
EOF

sudo chmod +x /usr/local/bin/phi-monitor
success_msg "Herramientas de monitoreo instaladas"

# Configurar logrotate para logs de Docker
step_msg "CONFIGURACIÓN DE ROTACIÓN DE LOGS"
echo "=================================================="
cat > /etc/logrotate.d/docker << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
EOF

success_msg "Rotación de logs configurada"

# Crear directorio para la aplicación
step_msg "PREPARACIÓN DEL DIRECTORIO DE APLICACIÓN"
echo "=================================================="
APP_DIR="/opt/phi_gis_platform"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
info_msg "Directorio de aplicación creado en: $APP_DIR"

# Configurar cron para monitoreo automático
step_msg "CONFIGURACIÓN DE MONITOREO AUTOMÁTICO"
echo "=================================================="
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/phi-monitor >> /var/log/phi-monitor.log 2>&1") | crontab -
success_msg "Monitoreo automático configurado (cada 15 minutos)"

# Reiniciar servicios necesarios
step_msg "REINICIO DE SERVICIOS"
echo "=================================================="
sudo systemctl restart systemd-logind
sudo systemctl daemon-reload

# Mostrar información final
echo ""
echo "=================================================="
success_msg "🎉 CONFIGURACIÓN DEL SERVIDOR COMPLETADA"
echo "=================================================="
echo ""
info_msg "Información del sistema:"
echo "  💾 Memoria total: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  💿 Disco disponible: $(df -h / | awk 'NR==2 {print $4}')"
echo "  🔥 Swap configurado: $(free -h | awk '/^Swap:/ {print $2}')"
echo "  🐳 Docker versión: $(docker --version)"
echo "  🐙 Docker Compose versión: $(docker-compose --version)"
echo ""
info_msg "Comandos útiles:"
echo "  📊 Monitoreo del sistema: phi-monitor"
echo "  🔍 Ver logs de monitoreo: tail -f /var/log/phi-monitor.log"
echo "  🐳 Estado de Docker: systemctl status docker"
echo "  🔥 Estado del firewall: ufw status"
echo ""
info_msg "Próximos pasos:"
echo "  1. Cerrar sesión y volver a conectar para aplicar cambios de grupo"
echo "  2. Clonar el repositorio de PHI GIS Platform"
echo "  3. Ejecutar el script de despliegue optimizado"
echo ""
success_msg "¡Servidor listo para el despliegue de PHI GIS Platform! 🚀"
echo "==================================================" 