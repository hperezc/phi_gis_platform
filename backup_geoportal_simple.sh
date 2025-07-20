#!/bin/bash

echo "🔒 BACKUP SIMPLE DEL GEOPORTAL"
echo "==============================="
echo "Fecha: $(date)"
echo ""

# Crear directorio de backup
BACKUP_DIR="/opt/phi_gis_platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="geoportal_simple_backup_$DATE"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

echo "📁 Copiando archivos críticos..."

# Lista de archivos importantes
FILES_TO_BACKUP=(
    "geoportal/backend/app/main.py"
    "geoportal/frontend/src/components/"
    "geoportal/frontend/src/services/"
    "geoportal/frontend/public/"
    "geoportal/frontend/package.json"
    "docker-compose.production.yml"
    ".env.production"
    "nginx/nginx.conf"
)

# Copiar archivos que existen
for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ Copiando: $file"
        cp -r "$file" "$BACKUP_DIR/$BACKUP_NAME/"
    else
        echo "⚠️ No encontrado: $file"
    fi
done

# Crear archivo de resumen
cat > "$BACKUP_DIR/$BACKUP_NAME/resumen.txt" << EOF
BACKUP SIMPLE DEL GEOPORTAL
===========================
Fecha: $(date)
Servidor: $(hostname)
Backup ID: $BACKUP_NAME

Archivos copiados:
$(ls -la "$BACKUP_DIR/$BACKUP_NAME/")

Servicios Docker:
$(docker ps 2>/dev/null || echo "Docker no disponible")

Puertos en uso:
$(netstat -tlnp 2>/dev/null | grep -E ":(80|443|3000|8000|8050)" || echo "No se pudo verificar")
EOF

# Comprimir
echo "🗜️ Comprimiendo..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo ""
echo "✅ BACKUP COMPLETADO"
echo "📦 Archivo: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "📏 Tamaño: $(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)"
echo "" 