#!/bin/bash

# Script para hacer backup del geoportal actual
# Fecha: $(date)
# Propósito: Backup antes de agregar capa sistema_alarmas

echo "🔒 INICIANDO BACKUP DEL GEOPORTAL ACTUAL"
echo "=========================================="
echo "Fecha: $(date)"
echo "Servidor: $(hostname)"
echo ""

# Configuración
BACKUP_DIR="/opt/phi_gis_platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="geoportal_backup_$DATE"

# Crear directorio de backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

echo "📁 Creando backup de archivos del geoportal..."

# Backup de archivos críticos del geoportal
GEOPORTAL_FILES=(
    "geoportal/backend/app/main.py"
    "geoportal/backend/app/api/endpoints.py"
    "geoportal/frontend/src/components/"
    "geoportal/frontend/src/pages/"
    "geoportal/frontend/src/services/"
    "geoportal/frontend/src/utils/"
    "geoportal/frontend/public/"
    "geoportal/frontend/package.json"
    "geoportal/frontend/tsconfig.json"
    "docker-compose.production.yml"
    ".env.production"
    "nginx/nginx.conf"
)

# Copiar archivos críticos
for file in "${GEOPORTAL_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ Copiando: $file"
        cp -r "$file" "$BACKUP_DIR/$BACKUP_NAME/"
    else
        echo "⚠️ Archivo no encontrado: $file"
    fi
done

# Backup de configuraciones específicas
echo "⚙️ Backup de configuraciones..."

# Variables de entorno
if [ -f ".env.production" ]; then
    cp ".env.production" "$BACKUP_DIR/$BACKUP_NAME/env_backup.txt"
    echo "✅ Variables de entorno respaldadas"
fi

# Docker compose
if [ -f "docker-compose.production.yml" ]; then
    cp "docker-compose.production.yml" "$BACKUP_DIR/$BACKUP_NAME/"
    echo "✅ Docker compose respaldado"
fi

# Nginx config
if [ -f "nginx/nginx.conf" ]; then
    cp "nginx/nginx.conf" "$BACKUP_DIR/$BACKUP_NAME/"
    echo "✅ Nginx config respaldado"
fi

# Crear archivo de resumen
cat > "$BACKUP_DIR/$BACKUP_NAME/backup_summary.txt" << EOF
BACKUP DEL GEOPORTAL
===================
Fecha: $(date)
Servidor: $(hostname)
Backup ID: $BACKUP_NAME

ARCHIVOS RESPALDADOS:
$(find "$BACKUP_DIR/$BACKUP_NAME" -type f | wc -l) archivos

ESTRUCTURA:
$(tree "$BACKUP_DIR/$BACKUP_NAME" -I "node_modules" 2>/dev/null || find "$BACKUP_DIR/$BACKUP_NAME" -type f)

SERVICIOS ACTIVOS:
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker no disponible")

PUERTOS EN USO:
$(netstat -tlnp 2>/dev/null | grep -E ":(80|443|3000|8000|8050)" || echo "No se pudo verificar puertos")

ESPACIO EN DISCO:
$(df -h / | tail -1)
