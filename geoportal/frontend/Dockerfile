FROM node:18-alpine AS base

# Instalar curl para health checks
RUN apk add --no-cache curl

# Instalar dependencias
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps --only=production && npm cache clean --force

# Build stage
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Optimizaciones de memoria para el build
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

# Production stage
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# Optimizaciones de memoria para producción
ENV NODE_OPTIONS="--max-old-space-size=2048"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"] 