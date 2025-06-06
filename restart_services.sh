#!/bin/bash

echo "=== REINICIANDO SERVICIOS PHI GIS PLATFORM ==="
echo "Fecha: $(date)"
echo "Deteniendo servicios actuales..."

# Detener todos los servicios
docker-compose -f docker-compose.production.yml down

# Limpiar contenedores parados y volúmenes huérfanos
echo "Limpiando recursos..."
docker system prune -f
docker volume prune -f

# Verificar espacio en disco
echo "Espacio en disco disponible:"
df -h

# Verificar memoria disponible
echo "Memoria disponible:"
free -h

# Reiniciar servicios básicos primero (sin monitoring)
echo "Iniciando servicios principales..."
docker-compose -f docker-compose.production.yml up -d redis

# Esperar a que Redis esté listo
echo "Esperando Redis..."
sleep 10

# Iniciar aplicación principal
echo "Iniciando aplicación principal..."
docker-compose -f docker-compose.production.yml up -d main_app

# Esperar y verificar
sleep 15
echo "Verificando servicios principales..."
docker-compose -f docker-compose.production.yml ps

# Iniciar geoportal
echo "Iniciando Geoportal..."
docker-compose -f docker-compose.production.yml up -d geoportal-backend
sleep 10
docker-compose -f docker-compose.production.yml up -d geoportal-frontend

# Iniciar nginx
echo "Iniciando Nginx..."
docker-compose -f docker-compose.production.yml up -d nginx

# Verificar estado final
echo "=== ESTADO FINAL ==="
docker-compose -f docker-compose.production.yml ps
docker stats --no-stream

echo "=== URLs DISPONIBLES ==="
echo "Aplicación Principal: http://45.55.212.201:8050"
echo "Geoportal Frontend:   http://45.55.212.201:3000"
echo "Geoportal Backend:    http://45.55.212.201:8000"
echo "API Docs:            http://45.55.212.201:8000/docs"
echo "Nginx (Puerto 80):   http://45.55.212.201"

echo "=== MONITOREO ==="
echo "Para ver logs: docker-compose -f docker-compose.production.yml logs -f [servicio]"
echo "Para ver recursos: docker stats"
echo "Para ver servicios: docker-compose -f docker-compose.production.yml ps" 