#!/bin/bash

# Configuración
MEMORY_LIMIT=1400000  # 1.4GB en KB (límite seguro)
SERVICE_NAME="phi-dashboard.service"
LOG_FILE="/var/log/phi_auto_restart.log"

# Obtener memoria actual del proceso main.py
CURRENT_MEMORY=$(ps aux | grep 'main.py' | grep -v grep | awk '{print $6}' | head -1)

# Si no se encuentra el proceso, intentar reiniciar
if [ -z "$CURRENT_MEMORY" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): ADVERTENCIA - Proceso main.py no encontrado. Reiniciando servicio..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Servicio reiniciado por proceso no encontrado" >> $LOG_FILE
    exit 0
fi

# Log del estado actual
echo "$(date '+%Y-%m-%d %H:%M:%S'): Memoria actual: ${CURRENT_MEMORY}KB (Límite: ${MEMORY_LIMIT}KB)" >> $LOG_FILE

# Verificar si excede el límite
if [ "$CURRENT_MEMORY" -gt "$MEMORY_LIMIT" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): ¡LÍMITE EXCEDIDO! Reiniciando servicio..." >> $LOG_FILE
    
    # Reiniciar el servicio
    systemctl restart $SERVICE_NAME
    
    # Esperar un momento y verificar
    sleep 10
    NEW_MEMORY=$(ps aux | grep 'main.py' | grep -v grep | awk '{print $6}' | head -1)
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Servicio reiniciado. Nueva memoria: ${NEW_MEMORY}KB" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Memoria dentro del límite normal" >> $LOG_FILE
fi
