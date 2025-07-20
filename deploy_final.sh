#!/bin/bash

echo "=== DESPLIEGUE FINAL PHI GIS PLATFORM ==="
echo "Fecha: $(date)"

# 1. Detener todo lo que esté corriendo
echo ">>> Deteniendo servicios existentes..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
docker stop $(docker ps -q) 2>/dev/null || true

# 2. Limpiar sistema
echo ">>> Limpiando sistema Docker..."
docker system prune -f
docker image prune -f

# 3. Verificar recursos
echo ">>> Verificando recursos del sistema..."
echo "Memoria disponible:"
free -h
echo "Espacio en disco:"
df -h /

# 4. Iniciar servicios de forma escalonada
echo ">>> Iniciando servicios con docker-compose SIMPLE..."

# Iniciar Redis primero
echo "Iniciando Redis..."
docker-compose -f docker-compose.simple.yml up -d redis
sleep 5

# Verificar Redis
if docker-compose -f docker-compose.simple.yml ps redis | grep -q "Up"; then
    echo "✅ Redis iniciado correctamente"
else
    echo "❌ Error iniciando Redis"
    exit 1
fi

# Iniciar aplicación principal
echo "Iniciando aplicación principal..."
docker-compose -f docker-compose.simple.yml up -d main_app
sleep 15

# Verificar aplicación principal
if docker-compose -f docker-compose.simple.yml ps main_app | grep -q "Up"; then
    echo "✅ Aplicación principal iniciada"
else
    echo "❌ Error iniciando aplicación principal"
    echo "Logs de main_app:"
    docker-compose -f docker-compose.simple.yml logs main_app
fi

# Iniciar geoportal backend
echo "Iniciando Geoportal Backend..."
docker-compose -f docker-compose.simple.yml up -d geoportal-backend
sleep 10

# Verificar backend
if docker-compose -f docker-compose.simple.yml ps geoportal-backend | grep -q "Up"; then
    echo "✅ Geoportal Backend iniciado"
else
    echo "❌ Error iniciando Geoportal Backend"
    echo "Logs de geoportal-backend:"
    docker-compose -f docker-compose.simple.yml logs geoportal-backend
fi

# Iniciar geoportal frontend
echo "Iniciando Geoportal Frontend..."
docker-compose -f docker-compose.simple.yml up -d geoportal-frontend
sleep 15

# Verificar frontend
if docker-compose -f docker-compose.simple.yml ps geoportal-frontend | grep -q "Up"; then
    echo "✅ Geoportal Frontend iniciado"
else
    echo "❌ Error iniciando Geoportal Frontend"
    echo "Logs de geoportal-frontend:"
    docker-compose -f docker-compose.simple.yml logs geoportal-frontend
fi

# 5. Verificar estado final
echo ""
echo "=== ESTADO FINAL DE SERVICIOS ==="
docker-compose -f docker-compose.simple.yml ps

echo ""
echo "=== USO DE RECURSOS ==="
docker stats --no-stream

echo ""
echo "=== URLs DISPONIBLES ==="
echo "🌐 Aplicación Principal: http://45.55.212.201:8050"
echo "🗺️  Geoportal Frontend:   http://45.55.212.201:3000"
echo "🔧 Geoportal Backend:    http://45.55.212.201:8000"
echo "📚 API Docs:            http://45.55.212.201:8000/docs"

echo ""
echo "=== COMANDOS ÚTILES ==="
echo "Ver todos los servicios: docker-compose -f docker-compose.simple.yml ps"
echo "Ver logs de un servicio: docker-compose -f docker-compose.simple.yml logs -f [servicio]"
echo "Ver recursos en tiempo real: docker stats"
echo "Reiniciar un servicio: docker-compose -f docker-compose.simple.yml restart [servicio]"

echo ""
echo "=== DESPLIEGUE COMPLETADO ===" 