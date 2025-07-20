#!/bin/bash

echo "=== SOLUCIONANDO PROBLEMA DOCKER UBUNTU 24.10 ==="

# 1. Detener y remover Docker completamente
echo ">>> Deteniendo Docker..."
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd

echo ">>> Removiendo Docker completamente..."
sudo apt-get remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /etc/docker

# 2. Limpiar sistema
echo ">>> Limpiando sistema..."
sudo apt-get autoremove -y
sudo apt-get autoclean

# 3. Reinstalar Docker con configuración específica para Ubuntu 24.10
echo ">>> Instalando Docker correctamente..."
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar repositorio oficial de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Configurar Docker para el problema de RLIMIT
echo ">>> Configurando Docker daemon..."
sudo mkdir -p /etc/docker

cat << EOF | sudo tee /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "storage-driver": "overlay2"
}
EOF

# 5. Crear configuración systemd específica
echo ">>> Configurando systemd..."
sudo mkdir -p /etc/systemd/system/docker.service.d

cat << EOF | sudo tee /etc/systemd/system/docker.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock --default-ulimit nofile=1024:4096
EOF

# 6. Reiniciar servicios
echo ">>> Reiniciando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl start containerd

# 7. Verificar instalación
echo ">>> Verificando Docker..."
sudo docker --version
sudo docker-compose --version

# 8. Probar con un contenedor simple
echo ">>> Probando Docker..."
sudo docker run --rm hello-world

if [ $? -eq 0 ]; then
    echo "✅ Docker instalado correctamente"
else
    echo "❌ Docker aún tiene problemas"
    
    # Alternativa: usar Podman
    echo ">>> Instalando Podman como alternativa..."
    sudo apt-get install -y podman
    
    # Crear alias para docker
    echo 'alias docker="podman"' >> ~/.bashrc
    echo 'alias docker-compose="podman-compose"' >> ~/.bashrc
    
    echo "Podman instalado. Usa 'podman' en lugar de 'docker'"
fi

echo "=== PROCESO COMPLETADO ===" 