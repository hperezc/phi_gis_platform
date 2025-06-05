# Multi-stage build para optimizar el tamaño final
FROM python:3.9-slim as builder

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias Python
COPY requirements.production.txt .
RUN pip install --no-cache-dir --user -r requirements.production.txt

# Etapa final - imágen más liviana
FROM python:3.9-slim

# Instalar dependencias de runtime solamente
RUN apt-get update && apt-get install -y \
    libpq5 \
    libgdal28 \
    libproj19 \
    libgeos-c1v5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar dependencias instaladas desde la etapa builder
COPY --from=builder /root/.local /home/app/.local

# Copiar código de la aplicación
COPY . .

# Cambiar propietario de archivos
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Asegurar que el directorio local de Python esté en PATH
ENV PATH=/home/app/.local/bin:$PATH

# Variables de entorno para Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crear directorio para logs
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

# Exponer puertos
EXPOSE 8050 8501 8502 8503

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "4", "--timeout", "120", "--worker-class", "sync", "main:application"] 