#!/bin/bash

echo "=== PRUEBA MINIMAL PHI GIS ==="

# Detener todo
echo "Deteniendo servicios..."
docker stop $(docker ps -q) 2>/dev/null || true
docker system prune -f

# Verificar Docker
echo "Verificando Docker..."
docker --version
docker-compose --version

# Probar solo Redis primero
echo "Probando solo Redis..."
docker run -d --name test-redis -p 6379:6379 redis:alpine

sleep 5

if docker ps | grep -q test-redis; then
    echo "✅ Redis funciona"
    docker stop test-redis
    docker rm test-redis
else
    echo "❌ Redis no funciona"
    exit 1
fi

# Probar construcción de imagen
echo "Construyendo imagen principal..."
docker build -f docker/Dockerfile.simple -t phi-test .

if [ $? -eq 0 ]; then
    echo "✅ Imagen construida exitosamente"
else
    echo "❌ Error construyendo imagen"
    exit 1
fi

# Probar contenedor
echo "Probando contenedor..."
docker run -d --name phi-test -p 8050:8050 -e ENVIRONMENT=test phi-test

sleep 10

if docker ps | grep -q phi-test; then
    echo "✅ Contenedor iniciado"
    docker logs phi-test
else
    echo "❌ Contenedor falló"
    docker logs phi-test 2>&1
fi

# Limpiar
docker stop phi-test 2>/dev/null || true
docker rm phi-test 2>/dev/null || true

echo "=== PRUEBA COMPLETADA ===" 