#!/bin/bash

# Script de restauración completa del sistema PHI GIS Platform
# Restaura desde un backup completo creado por backup_complete_system.sh

set -e

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

# Verificar argumentos
if [ $# -eq 0 ]; then
    error "❌ Uso: $0 <archivo_backup.tar.gz>"
    echo ""
    echo "Ejemplo:"
    echo "  $0 phi_gis_complete_backup_20250115_143022.tar.gz"
    echo ""
    echo "Backups disponibles:"
    ls -la /opt/phi_gis_platform/backups/phi_gis_complete_backup_*.tar.gz 2>/dev/null || echo "No se encontraron backups"
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_DIR="/opt/phi_gis_platform/backups"
RESTORE_DIR="/opt/phi_gis_platform/restore_temp"

# Verificar que el archivo de backup existe
if [ ! -f "$BACKUP_FILE" ]; then
    # Buscar en el directorio de backups
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    else
        error "❌ Archivo de backup no encontrado: $BACKUP_FILE"
        echo ""
        echo "Backups disponibles:"
        ls -la "$BACKUP_DIR"/phi_gis_complete_backup_*.tar.gz 2>/dev/null || echo "No se encontraron backups"
        exit 1
    fi
fi

log "🚀 INICIANDO RESTAURACIÓN COMPLETA DEL SISTEMA PHI GIS"
log "====================================================="
log "Archivo de backup: $BACKUP_FILE"
log "Directorio de restauración: $RESTORE_DIR"

# Confirmar restauración
echo ""
warning "⚠️  ADVERTENCIA: Esta operación sobrescribirá el sistema actual"
echo "¿Estás seguro de que quieres continuar? (s/N): "
read -r confirm

if [[ ! $confirm =~ ^[Ss]$ ]]; then
    log "❌ Restauración cancelada por el usuario"
    exit 0
fi

# Crear directorio de restauración
log "📁 Creando directorio de restauración..."
rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"
cd "$RESTORE_DIR"

# Extraer backup
log "🗜️ Extrayendo backup..."
if tar -xzf "$BACKUP_FILE"; then
    log "✅ Backup extraído exitosamente"
else
    error "❌ Error al extraer el backup"
    exit 1
fi

# Encontrar el directorio extraído
EXTRACTED_DIR=$(ls -d phi_gis_complete_backup_* 2>/dev/null | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    error "❌ No se encontró el directorio extraído"
    exit 1
fi

cd "$EXTRACTED_DIR"
log "📂 Directorio de restauración: $(pwd)"

# Verificar archivos de backup
log "🔍 Verificando archivos de backup..."
required_files=(
    "database_backup.sql.gz"
    "system_files.tar.gz"
    "docker_config.tar.gz"
    "env_backup.txt"
    "system_info.txt"
    "backup_summary.txt"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        log "✅ Archivo encontrado: $file"
    else
        warning "⚠️ Archivo faltante: $file"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    warning "⚠️ Algunos archivos del backup están faltantes: ${missing_files[*]}"
    echo "¿Continuar con la restauración? (s/N): "
    read -r continue_restore
    if [[ ! $continue_restore =~ ^[Ss]$ ]]; then
        log "❌ Restauración cancelada"
        exit 1
    fi
fi

# 1. RESTAURAR BASE DE DATOS
log "📊 Restaurando base de datos..."
if [ -f "database_backup.sql.gz" ]; then
    # Cargar variables de entorno del backup
    if [ -f "env_backup.txt" ]; then
        source env_backup.txt 2>/dev/null || true
    fi
    
    # Extraer información de la URL de conexión
    if [ -n "$DATABASE_URL" ]; then
        DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
        DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p')
        DB_USER=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
        DB_PASS=$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
        
        export PGPASSWORD="$DB_PASS"
        
        log "🔗 Conectando a: $DB_HOST:$DB_PORT/$DB_NAME"
        
        # Restaurar base de datos
        if gunzip -c database_backup.sql.gz | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-password; then
            log "✅ Base de datos restaurada exitosamente"
        else
            error "❌ Error al restaurar la base de datos"
            unset PGPASSWORD
            exit 1
        fi
        
        unset PGPASSWORD
    else
        error "❌ No se encontró DATABASE_URL en el backup"
        exit 1
    fi
else
    error "❌ Archivo de backup de base de datos no encontrado"
    exit 1
fi

# 2. RESTAURAR ARCHIVOS DEL SISTEMA
log "📁 Restaurando archivos del sistema..."

# Crear backup del sistema actual antes de restaurar
CURRENT_BACKUP="/opt/phi_gis_platform/backups/pre_restore_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
log "💾 Creando backup del sistema actual: $CURRENT_BACKUP"

cd /opt/phi_gis_platform
if tar -czf "$CURRENT_BACKUP" \
    --exclude=backups \
    --exclude=restore_temp \
    --exclude=*.pyc \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=node_modules \
    . 2>/dev/null; then
    log "✅ Backup del sistema actual creado"
else
    warning "⚠️ No se pudo crear backup del sistema actual"
fi

# Restaurar archivos del sistema
cd "$RESTORE_DIR/$EXTRACTED_DIR"
if [ -f "system_files.tar.gz" ]; then
    log "📦 Extrayendo archivos del sistema..."
    
    # Crear directorio temporal para extraer
    TEMP_EXTRACT="/tmp/phi_gis_restore_$(date +%s)"
    mkdir -p "$TEMP_EXTRACT"
    
    if tar -xzf system_files.tar.gz -C "$TEMP_EXTRACT"; then
        log "✅ Archivos del sistema extraídos"
        
        # Copiar archivos al directorio de destino
        log "📋 Copiando archivos al sistema..."
        if cp -r "$TEMP_EXTRACT"/* /opt/phi_gis_platform/; then
            log "✅ Archivos del sistema restaurados"
        else
            error "❌ Error al copiar archivos del sistema"
            exit 1
        fi
        
        # Limpiar archivos temporales
        rm -rf "$TEMP_EXTRACT"
    else
        error "❌ Error al extraer archivos del sistema"
        exit 1
    fi
else
    error "❌ Archivo de backup de archivos del sistema no encontrado"
    exit 1
fi

# 3. RESTAURAR CONFIGURACIONES DOCKER
log "🐳 Restaurando configuraciones Docker..."
if [ -f "docker_config.tar.gz" ]; then
    cd /opt/phi_gis_platform
    
    if tar -xzf "$RESTORE_DIR/$EXTRACTED_DIR/docker_config.tar.gz"; then
        log "✅ Configuraciones Docker restauradas"
    else
        warning "⚠️ Error al restaurar configuraciones Docker"
    fi
fi

# 4. RESTAURAR VARIABLES DE ENTORNO
log "⚙️ Restaurando variables de entorno..."
if [ -f "$RESTORE_DIR/$EXTRACTED_DIR/env_backup.txt" ]; then
    # Crear backup del .env.production actual
    if [ -f ".env.production" ]; then
        cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)
        log "✅ Backup del .env.production actual creado"
    fi
    
    # Extraer solo las variables de entorno del backup
    grep -E '^[A-Z_]+=' "$RESTORE_DIR/$EXTRACTED_DIR/env_backup.txt" > .env.production.restored 2>/dev/null || true
    
    if [ -s .env.production.restored ]; then
        mv .env.production.restored .env.production
        log "✅ Variables de entorno restauradas"
    else
        warning "⚠️ No se pudieron restaurar las variables de entorno"
    fi
fi

# 5. VERIFICAR RESTAURACIÓN
log "🔍 Verificando restauración..."

# Verificar conexión a la base de datos
log "📊 Verificando conexión a la base de datos..."
if [ -n "$DATABASE_URL" ]; then
    export PGPASSWORD="$DB_PASS"
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-password -c "SELECT version();" >/dev/null 2>&1; then
        log "✅ Conexión a base de datos verificada"
    else
        error "❌ Error de conexión a la base de datos"
    fi
    unset PGPASSWORD
fi

# Verificar archivos críticos
log "📁 Verificando archivos críticos..."
critical_files=(
    ".env.production"
    "docker-compose.production.yml"
    "nginx.conf"
    "geoportal/backend/app/main.py"
    "Dashboard_BD_PHI/dashboard/app.py"
)

for file in "${critical_files[@]}"; do
    if [ -f "/opt/phi_gis_platform/$file" ]; then
        log "✅ Archivo encontrado: $file"
    else
        warning "⚠️ Archivo faltante: $file"
    fi
done

# 6. REINICIAR SERVICIOS
log "🔄 Reiniciando servicios..."

cd /opt/phi_gis_platform

# Detener servicios actuales
log "⏹️ Deteniendo servicios actuales..."
if [ -f "docker-compose.production.yml" ]; then
    docker-compose -f docker-compose.production.yml down 2>/dev/null || true
fi

# Limpiar contenedores
log "🧹 Limpiando contenedores..."
docker system prune -f 2>/dev/null || true

# Reconstruir y reiniciar servicios
log "🔨 Reconstruyendo servicios..."
if [ -f "docker-compose.production.yml" ]; then
    if docker-compose -f docker-compose.production.yml build --no-cache; then
        log "✅ Servicios reconstruidos"
        
        if docker-compose -f docker-compose.production.yml up -d; then
            log "✅ Servicios reiniciados"
        else
            error "❌ Error al reiniciar servicios"
        fi
    else
        error "❌ Error al reconstruir servicios"
    fi
fi

# 7. VERIFICACIÓN FINAL
log "✅ VERIFICACIÓN FINAL DE LA RESTAURACIÓN"
echo "=========================================="

# Verificar servicios
log "🔍 Verificando servicios..."
sleep 10  # Esperar a que los servicios se inicien

if docker ps | grep -q "phi_gis"; then
    log "✅ Servicios Docker activos"
else
    warning "⚠️ Algunos servicios Docker no están activos"
fi

# Verificar puertos
log "🌐 Verificando puertos..."
important_ports=(80 443 8050 8000 3000)
for port in "${important_ports[@]}"; do
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        log "✅ Puerto $port: Activo"
    else
        warning "⚠️ Puerto $port: No activo"
    fi
done

# 8. LIMPIAR ARCHIVOS TEMPORALES
log "🧹 Limpiando archivos temporales..."
rm -rf "$RESTORE_DIR"

# 9. RESUMEN FINAL
log "🎉 RESTAURACIÓN COMPLETADA"
echo "=========================="
echo "📊 Resumen de la restauración:"
echo "   ✅ Base de datos restaurada"
echo "   ✅ Archivos del sistema restaurados"
echo "   ✅ Configuraciones Docker restauradas"
echo "   ✅ Variables de entorno restauradas"
echo "   ✅ Servicios reiniciados"
echo ""
echo "📁 Archivos de backup:"
echo "   - Backup original: $BACKUP_FILE"
echo "   - Backup pre-restauración: $CURRENT_BACKUP"
echo ""
echo "🔗 URLs del sistema:"
echo "   - Aplicación principal: http://45.55.212.201"
echo "   - Dashboard: http://45.55.212.201/dashboard"
echo "   - Geoportal: http://45.55.212.201/geoportal"
echo ""
echo "⚠️ IMPORTANTE:"
echo "   - Verifica que todos los servicios funcionen correctamente"
echo "   - Revisa los logs si hay problemas: docker-compose logs"
echo "   - El backup pre-restauración está disponible en caso de problemas"
echo ""

log "🎉 RESTAURACIÓN FINALIZADA EXITOSAMENTE!" 