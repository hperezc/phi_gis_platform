FROM node:18-alpine

WORKDIR /app

# Instalar curl para health checks
RUN apk add --no-cache curl

# Copiar package files
COPY package*.json ./

# Instalar TODAS las dependencias (incluyendo devDependencies para el build)
RUN npm install --legacy-peer-deps

# Copiar todo el código fuente
COPY . .

# Build de la aplicación (necesita tailwindcss que está en devDependencies)
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=1024"
RUN npm run build

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Exponer puerto
EXPOSE 3000

# Iniciar aplicación
CMD ["npm", "start"]
