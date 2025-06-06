# 🚀 Instrucciones de Despliegue - PHI GIS Platform

## 📋 Prerequisitos en el Droplet de DigitalOcean

### 1. Conectar al Droplet
```bash
ssh root@142.93.118.216
```

### 2. Actualizar el sistema
```bash
apt update && apt upgrade -y
```

### 3. Instalar Docker
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Iniciar Docker
systemctl start docker
systemctl enable docker

# Verificar instalación
docker --version
```

### 4. Instalar Docker Compose
```bash
# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker-compose --version
```

### 5. Instalar Git
```bash
apt install git -y
```

## 📁 Desplegar la Aplicación

### 1. Clonar el repositorio
```bash
cd /opt
git clone [URL_DE_TU_REPOSITORIO] phi_gis_platform
cd phi_gis_platform
```

### 2. Configurar variables de entorno
```bash
# Copiar archivo de ejemplo
cp env.production.example .env.production

# Editar variables (especialmente SECRET_KEY y SSL_EMAIL)
nano .env.production
```

**Variables importantes a cambiar:**
- `SECRET_KEY`: Generar una clave secreta fuerte
- `SSL_EMAIL`: Tu email para certificados SSL
- `DOMAIN`: Si tienes un dominio, cambiar por tu dominio real

### 3. Ejecutar el script de despliegue
```bash
# Hacer el script ejecutable
chmod +x deploy_to_digitalocean.sh

# Ejecutar despliegue
./deploy_to_digitalocean.sh
```

## 🔧 Configuración de Firewall

### Abrir puertos necesarios
```bash
# Instalar UFW si no está instalado
apt install ufw -y

# Configurar reglas básicas
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH
ufw allow ssh

# Permitir HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Permitir puertos específicos de la aplicación
ufw allow 8050/tcp  # Aplicación principal
ufw allow 3000/tcp  # Geoportal Frontend
ufw allow 8000/tcp  # Geoportal Backend
ufw allow 8501/tcp  # ML Asistentes
ufw allow 8502/tcp  # ML Temporal
ufw allow 8503/tcp  # ML Geográfico
ufw allow 3001/tcp  # Grafana

# Activar firewall
ufw enable

# Verificar estado
ufw status
```

## 🌐 URLs de Acceso

Una vez desplegado, la aplicación estará disponible en:

- **🌐 Aplicación Principal**: http://142.93.118.216:8050
- **🗺️ Geoportal**: http://142.93.118.216:3000
- **📊 Dashboard**: http://142.93.118.216:8050/dashboard
- **🤖 ML Asistentes**: http://142.93.118.216:8501
- **📈 ML Temporal**: http://142.93.118.216:8502
- **🌍 ML Geográfico**: http://142.93.118.216:8503
- **📊 Monitoreo (Grafana)**: http://142.93.118.216:3001

## 🔧 Comandos Útiles

### Ver estado de los servicios
```bash
docker-compose -f docker-compose.production.yml ps
```

### Ver logs en tiempo real
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose -f docker-compose.production.yml logs -f main_app
docker-compose -f docker-compose.production.yml logs -f geoportal-backend
docker-compose -f docker-compose.production.yml logs -f geoportal-frontend
```

### Reiniciar servicios
```bash
docker-compose -f docker-compose.production.yml restart
```

### Detener todos los servicios
```bash
docker-compose -f docker-compose.production.yml down
```

### Actualizar la aplicación
```bash
# Bajar cambios del repositorio
git pull

# Reconstruir y reiniciar
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

## 🐛 Solución de Problemas

### Si el geoportal no carga las capas:
1. Verificar que el backend esté corriendo:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Ver logs del backend:
   ```bash
   docker-compose -f docker-compose.production.yml logs geoportal-backend
   ```

3. Verificar conexión a la base de datos:
   ```bash
   docker-compose -f docker-compose.production.yml exec geoportal-backend python -c "from app.database import engine; print('DB OK' if engine else 'DB Error')"
   ```

### Si los servicios no inician:
1. Verificar recursos del sistema:
   ```bash
   free -h  # Memoria
   df -h    # Disco
   ```

2. Limpiar recursos Docker:
   ```bash
   docker system prune -a -f
   ```

### Para debugging avanzado:
```bash
# Entrar a un contenedor
docker-compose -f docker-compose.production.yml exec main_app bash
docker-compose -f docker-compose.production.yml exec geoportal-backend bash

# Ver uso de recursos
docker stats
```

## 🔐 Configuración SSL (Opcional)

Para configurar SSL con Let's Encrypt:

1. Asegúrate de tener un dominio apuntando a tu IP
2. Actualiza `DOMAIN` en `.env.production`
3. El certificado se generará automáticamente con Certbot

## 📈 Monitoreo

- **Grafana** está disponible en puerto 3001
- Usuario: admin / Contraseña: admin123
- **Prometheus** recolecta métricas en puerto 9090

---

## ✅ Checklist de Despliegue

- [ ] Droplet configurado y accesible
- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado
- [ ] Variables de entorno configuradas
- [ ] Firewall configurado
- [ ] Script de despliegue ejecutado
- [ ] Todos los servicios funcionando
- [ ] URLs accesibles desde internet
- [ ] Base de datos conectada (4,960 actividades)
- [ ] Geoportal cargando capas correctamente

---

**🎉 ¡Tu plataforma PHI GIS está lista para el mundo!** 