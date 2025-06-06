FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Cambiar propietario de archivos
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Variables de entorno optimizadas
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_ARENA_MAX=2

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Exponer puerto
EXPOSE 8000

# Comando de inicio optimizado
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop"] 