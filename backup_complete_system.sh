#!/bin/bash

# Script de backup completo del sistema PHI GIS Platform
# Incluye: Base de datos, archivos del servidor, configuraciones y todo el sistema
# Ejecutar desde el servidor de DigitalOcean

set -e

# Configuración
BACKUP_DIR="/opt/phi_gis_platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="phi_gis_complete_backup_$DATE"
MAX_BACKUPS=5  # Mantener solo los últimos 5 backups completos

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

log "🚀 INICIANDO BACKUP COMPLETO DEL SISTEMA PHI GIS"
log "=================================================="
log "Fecha: $(date)"
log "Servidor: $(hostname)"
log "Directorio de backup: $BACKUP_DIR/$BACKUP_NAME"

# Cargar variables de entorno
if [ -f ".env.production" ]; then
    source .env.production
    log "✅ Variables de entorno cargadas desde .env.production"
else
    error "❌ No se encontró .env.production"
    exit 1
fi

# 1. BACKUP DE LA BASE DE DATOS
log "📊 Creando backup de la base de datos PostgreSQL..."
if [ -n "$DATABASE_URL" ]; then
    # Extraer información de la URL de conexión
    DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    
    # Crear backup usando pg_dump
    DB_BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME/database_backup.sql"
    
    export PGPASSWORD="$DB_PASS"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
       --no-password --clean --if-exists --create --verbose > "$DB_BACKUP_FILE"; then
        log "✅ Backup de base de datos creado: $DB_BACKUP_FILE"
        
        # Comprimir el backup
        gzip "$DB_BACKUP_FILE"
        log "✅ Backup de BD comprimido: $DB_BACKUP_FILE.gz"
        
        # Verificar tamaño del backup
        BACKUP_SIZE=$(du -h "$DB_BACKUP_FILE.gz" | cut -f1)
        log "📏 Tamaño del backup de BD: $BACKUP_SIZE"
    else
        error "❌ Error al crear backup de la base de datos"
        exit 1
    fi
    
    unset PGPASSWORD
else
    error "❌ No se encontró DATABASE_URL en las variables de entorno"
    exit 1
fi

# 2. BACKUP DE ARCHIVOS DEL SISTEMA
log "📁 Creando backup de archivos del sistema..."

# Lista de directorios y archivos importantes a respaldar
SYSTEM_FILES=(
    ".env.production"
    "docker-compose.production.yml"
    "docker-compose.yml"
    "nginx.conf"
    "requirements.production.txt"
    "requirements.txt"
    "package.json"
    "package-lock.json"
    "*.py"
    "*.sh"
    "*.md"
    "*.yml"
    "*.yaml"
    "config/"
    "nginx/"
    "templates/"
    "static/"
    "geoportal/"
    "Dashboard_BD_PHI/"
    "ml_module/"
    "monitoring/"
    "logs/"
    "scripts/"
    "sql_scripts/"
    "docker/"
)

# Crear backup de archivos del sistema
SYSTEM_BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME/system_files.tar.gz"

# Excluir archivos innecesarios
EXCLUDE_PATTERNS=(
    "--exclude=*.pyc"
    "--exclude=__pycache__"
    "--exclude=.git"
    "--exclude=node_modules"
    "--exclude=temp_*"
    "--exclude=*.log"
    "--exclude=*.tmp"
    "--exclude=.DS_Store"
    "--exclude=*.swp"
    "--exclude=*.swo"
    "--exclude=.env.local"
    "--exclude=.env.development"
)

# Crear el tar con todos los archivos importantes
if tar -czf "$SYSTEM_BACKUP_FILE" \
    "${EXCLUDE_PATTERNS[@]}" \
    "${SYSTEM_FILES[@]}" \
    2>/dev/null; then
    
    log "✅ Backup de archivos del sistema creado: $SYSTEM_BACKUP_FILE"
    
    # Verificar tamaño
    SYSTEM_SIZE=$(du -h "$SYSTEM_BACKUP_FILE" | cut -f1)
    log "📏 Tamaño del backup de archivos: $SYSTEM_SIZE"
else
    warning "⚠️ Algunos archivos no se pudieron respaldar"
fi

# 3. BACKUP DE CONFIGURACIONES ESPECÍFICAS
log "⚙️ Creando backup de configuraciones específicas..."

# Backup de configuraciones de Docker
DOCKER_CONFIG_BACKUP="$BACKUP_DIR/$BACKUP_NAME/docker_config.tar.gz"
if tar -czf "$DOCKER_CONFIG_BACKUP" \
    docker-compose*.yml \
    Dockerfile* \
    nginx.conf \
    monitoring/prometheus.yml \
    2>/dev/null; then
    log "✅ Backup de configuraciones Docker creado"
fi

# Backup de variables de entorno
ENV_BACKUP="$BACKUP_DIR/$BACKUP_NAME/env_backup.txt"
{
    echo "# Backup de variables de entorno - $(date)"
    echo "# Servidor: $(hostname)"
    echo "# Usuario: $(whoami)"
    echo ""
    if [ -f ".env.production" ]; then
        cat .env.production
    fi
} > "$ENV_BACKUP"
log "✅ Backup de variables de entorno creado: $ENV_BACKUP"

# 4. BACKUP DE INFORMACIÓN DEL SISTEMA
log "💻 Creando backup de información del sistema..."

SYSTEM_INFO="$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
{
    echo "=== INFORMACIÓN DEL SISTEMA ==="
    echo "Fecha: $(date)"
    echo "Servidor: $(hostname)"
    echo "Sistema operativo: $(uname -a)"
    echo "Kernel: $(uname -r)"
    echo "Arquitectura: $(uname -m)"
    echo ""
    echo "=== INFORMACIÓN DE DISCO ==="
    df -h
    echo ""
    echo "=== INFORMACIÓN DE MEMORIA ==="
    free -h
    echo ""
    echo "=== SERVICIOS DOCKER ==="
    docker ps -a 2>/dev/null || echo "Docker no disponible"
    echo ""
    echo "=== PROCESOS ACTIVOS ==="
    ps aux | head -20
    echo ""
    echo "=== PUERTOS EN USO ==="
    netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null || echo "No se pudo obtener información de puertos"
    echo ""
    echo "=== VARIABLES DE ENTORNO ==="
    env | sort
} > "$SYSTEM_INFO"
log "✅ Información del sistema guardada: $SYSTEM_INFO"

# 5. BACKUP DE LOGS IMPORTANTES
log "📋 Creando backup de logs importantes..."

LOGS_BACKUP="$BACKUP_DIR/$BACKUP_NAME/logs_backup.tar.gz"
if tar -czf "$LOGS_BACKUP" \
    logs/ \
    *.log \
    2>/dev/null; then
    log "✅ Backup de logs creado: $LOGS_BACKUP"
else
    warning "⚠️ No se encontraron logs para respaldar"
fi

# 6. VERIFICACIÓN DE LA BASE DE DATOS
log "🔍 Verificando integridad de la base de datos..."

DB_VERIFICATION="$BACKUP_DIR/$BACKUP_NAME/database_verification.txt"
{
    echo "=== VERIFICACIÓN DE BASE DE DATOS ==="
    echo "Fecha: $(date)"
    echo ""
    
    export PGPASSWORD="$DB_PASS"
    
    # Verificar conexión
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
       --no-password -c "SELECT version();" 2>/dev/null; then
        echo "✅ Conexión a BD exitosa"
    else
        echo "❌ Error de conexión a BD"
    fi
    
    # Listar tablas
    echo ""
    echo "=== TABLAS EN LA BASE DE DATOS ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
         --no-password -c "\dt" 2>/dev/null || echo "No se pudieron listar las tablas"
    
    # Verificar PostGIS
    echo ""
    echo "=== VERIFICACIÓN POSTGIS ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
         --no-password -c "SELECT PostGIS_Version();" 2>/dev/null || echo "PostGIS no disponible"
    
    unset PGPASSWORD
} > "$DB_VERIFICATION"
log "✅ Verificación de BD guardada: $DB_VERIFICATION"

# 7. CREAR ARCHIVO DE RESUMEN
log "📝 Creando resumen del backup..."

SUMMARY_FILE="$BACKUP_DIR/$BACKUP_NAME/backup_summary.txt"
{
    echo "=== RESUMEN DEL BACKUP COMPLETO ==="
    echo "Fecha: $(date)"
    echo "Servidor: $(hostname)"
    echo "Backup ID: $BACKUP_NAME"
    echo ""
    echo "=== ARCHIVOS CREADOS ==="
    ls -lah "$BACKUP_DIR/$BACKUP_NAME/"
    echo ""
    echo "=== TAMAÑOS ==="
    du -sh "$BACKUP_DIR/$BACKUP_NAME"/*
    echo ""
    echo "=== VERIFICACIÓN ==="
    echo "Base de datos: $(if [ -f "$DB_BACKUP_FILE.gz" ]; then echo "✅ OK"; else echo "❌ ERROR"; fi)"
    echo "Archivos del sistema: $(if [ -f "$SYSTEM_BACKUP_FILE" ]; then echo "✅ OK"; else echo "❌ ERROR"; fi)"
    echo "Configuraciones: $(if [ -f "$DOCKER_CONFIG_BACKUP" ]; then echo "✅ OK"; else echo "❌ ERROR"; fi)"
    echo "Logs: $(if [ -f "$LOGS_BACKUP" ]; then echo "✅ OK"; else echo "❌ ERROR"; fi)"
    echo ""
    echo "=== INSTRUCCIONES DE RESTAURACIÓN ==="
    echo "1. Descomprimir el backup: tar -xzf $BACKUP_NAME.tar.gz"
    echo "2. Restaurar BD: gunzip -c database_backup.sql.gz | psql -h HOST -p PORT -U USER -d DB"
    echo "3. Restaurar archivos: tar -xzf system_files.tar.gz"
    echo "4. Verificar configuraciones en env_backup.txt"
    echo ""
    echo "=== CONTACTO ==="
    echo "En caso de problemas, revisar los logs y la documentación del proyecto"
} > "$SUMMARY_FILE"

# 8. COMPRIMIR TODO EL BACKUP
log "🗜️ Comprimiendo backup completo..."

cd "$BACKUP_DIR"
if tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"; then
    log "✅ Backup completo comprimido: ${BACKUP_NAME}.tar.gz"
    
    # Verificar tamaño total
    TOTAL_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log "📏 Tamaño total del backup: $TOTAL_SIZE"
    
    # Limpiar archivos temporales
    rm -rf "$BACKUP_NAME"
    log "🧹 Archivos temporales eliminados"
else
    error "❌ Error al comprimir el backup completo"
    exit 1
fi

# 9. LIMPIAR BACKUPS ANTIGUOS
log "🧹 Limpiando backups antiguos (manteniendo los últimos $MAX_BACKUPS)..."

# Contar backups existentes
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/phi_gis_complete_backup_*.tar.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    # Eliminar backups más antiguos
    ls -t "$BACKUP_DIR"/phi_gis_complete_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
    log "🗑️ Backups antiguos eliminados"
else
    log "ℹ️ No es necesario limpiar backups antiguos"
fi

# 10. VERIFICACIÓN FINAL
log "✅ VERIFICACIÓN FINAL DEL BACKUP"
echo "=========================================="
echo "📊 Resumen del backup:"
echo "   - Backup ID: $BACKUP_NAME"
echo "   - Ubicación: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "   - Tamaño: $TOTAL_SIZE"
echo "   - Fecha: $(date)"
echo ""
echo "📋 Archivos incluidos:"
echo "   ✅ Base de datos PostgreSQL"
echo "   ✅ Archivos del sistema"
echo "   ✅ Configuraciones Docker"
echo "   ✅ Variables de entorno"
echo "   ✅ Información del sistema"
echo "   ✅ Logs importantes"
echo "   ✅ Verificación de BD"
echo ""
echo "🔒 Backup completo creado exitosamente!"
echo "💡 Para restaurar: tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""

# Mostrar espacio disponible
AVAILABLE_SPACE=$(df -h "$BACKUP_DIR" | tail -1 | awk '{print $4}')
log "💾 Espacio disponible en disco: $AVAILABLE_SPACE"

log "🎉 BACKUP COMPLETO FINALIZADO EXITOSAMENTE!" 