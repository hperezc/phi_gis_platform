# Imagen base con Python y librerías geoespaciales
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.production.txt .
RUN pip install --no-cache-dir -r requirements.production.txt

# Copiar código de la aplicación
COPY . .

# Cambiar propietario de archivos
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Variables de entorno optimizadas
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_ARENA_MAX=2

# Crear directorio para logs
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

# Exponer puertos
EXPOSE 8050 8501 8502 8503

# Comando optimizado
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "--threads", "4", "--timeout", "120", "--worker-class", "gthread", "main:application"]
