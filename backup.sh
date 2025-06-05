#!/bin/bash

# Script de backup para PHI GIS Platform
# Ejecutar con cron para backups automáticos

set -e

# Configuración
BACKUP_DIR="/opt/phi_gis_platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=7  # Mantener solo los últimos 7 backups

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Cargar variables de entorno
if [ -f ".env.production" ]; then
    source .env.production
else
    error "No se encontró .env.production"
    exit 1
fi

log "Iniciando backup de PHI GIS Platform..."

# Backup de la base de datos
if [ -n "$DATABASE_URL" ]; then
    log "Creando backup de la base de datos..."
    
    # Extraer información de la URL de conexión
    DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    
    # Crear backup usando pg_dump
    BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"
    
    export PGPASSWORD="$DB_PASS"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
       --no-password --clean --if-exists --create > "$BACKUP_FILE"; then
        log "Backup de base de datos creado: $BACKUP_FILE"
        
        # Comprimir el backup
        gzip "$BACKUP_FILE"
        log "Backup comprimido: $BACKUP_FILE.gz"
    else
        error "Error al crear backup de la base de datos"
        exit 1
    fi
    
    unset PGPASSWORD
fi

# Backup de archivos de configuración
log "Creando backup de configuración..."
CONFIG_BACKUP="$BACKUP_DIR/config_backup_$DATE.tar.gz"

tar -czf "$CONFIG_BACKUP" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='logs' \
    --exclude='temp_*' \
    .env.production \
    docker-compose.production.yml \
    nginx/ \
    config/ \
    requirements.production.txt \
    2>/dev/null || true

if [ -f "$CONFIG_BACKUP" ]; then
    log "Backup de configuración creado: $CONFIG_BACKUP"
else
    warning "No se pudo crear backup de configuración"
fi

# Backup de datos estáticos importantes
log "Creando backup de datos estáticos..."
STATIC_BACKUP="$BACKUP_DIR/static_backup_$DATE.tar.gz"

tar -czf "$STATIC_BACKUP" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='temp_*' \
    static/ \
    templates/ \
    ml_module/trained_models/ \
    ml_module/data/ \
    2>/dev/null || true

if [ -f "$STATIC_BACKUP" ]; then
    log "Backup de datos estáticos creado: $STATIC_BACKUP"
else
    warning "No se pudo crear backup de datos estáticos"
fi

# Limpiar backups antiguos
log "Limpiando backups antiguos (manteniendo los últimos $MAX_BACKUPS)..."

# Limpiar backups de BD
ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# Limpiar backups de config
ls -t "$BACKUP_DIR"/config_backup_*.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# Limpiar backups de static
ls -t "$BACKUP_DIR"/static_backup_*.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# Mostrar resumen
log "Resumen de backups:"
echo "Directorio: $BACKUP_DIR"
echo "Archivos actuales:"
ls -lah "$BACKUP_DIR"/*_$DATE* 2>/dev/null || echo "No se crearon archivos con fecha $DATE"

# Calcular tamaño total de backups
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Tamaño total de backups: $TOTAL_SIZE"

# Verificar espacio en disco
AVAILABLE_SPACE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')
log "Espacio disponible: $AVAILABLE_SPACE"

log "✅ Backup completado exitosamente!"

# Opcional: enviar notificación por email (requiere configurar sendmail o similar)
# echo "Backup PHI GIS Platform completado - $DATE" | mail -s "Backup Status" admin@yourdomain.com

exit 0 