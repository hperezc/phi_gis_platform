# 🚀 Guía de Despliegue PHI GIS Platform en Digital Ocean

Esta guía te llevará paso a paso para desplegar tu plataforma PHI GIS completa en un VPS de Digital Ocean.

## 📋 Requisitos Previos

### 1. VPS Digital Ocean
- **Mínimo recomendado**: 4GB RAM, 2 vCPUs, 80GB SSD
- **Sistema operativo**: Ubuntu 20.04 LTS o superior
- **IP pública** asignada

### 2. Base de Datos
- **Digital Ocean Managed PostgreSQL** (recomendado)
- O PostgreSQL instalado en el VPS

### 3. Dominio
- Un nombre de dominio apuntando a tu IP del VPS
- Acceso para configurar registros DNS

## 🛠️ Configuración Inicial del VPS

### 1. Conectar al VPS
```bash
ssh root@tu_ip_del_vps
```

### 2. Actualizar el sistema
```bash
apt update && apt upgrade -y
```

### 3. Instalar Docker y Docker Compose
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

### 4. Instalar herramientas adicionales
```bash
apt install -y git curl nano htop ufw
```

### 5. Configurar firewall
```bash
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
```

## 📦 Desplegar la Aplicación

### 1. Clonar el repositorio
```bash
cd /opt
git clone tu_repositorio phi_gis_platform
cd phi_gis_platform
```

### 2. Configurar variables de entorno
```bash
# Copiar y editar el archivo de configuración
cp .env.production.example .env.production
nano .env.production
```

**Configurar estas variables en `.env.production`:**
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://usuario:password@host:25060/database?sslmode=require
MAPBOX_TOKEN=tu_token_de_mapbox
SECRET_KEY=una_clave_secreta_segura
DOMAIN=tu_dominio.com
SSL_EMAIL=tu_email@dominio.com
```

### 3. Hacer ejecutable el script de deploy
```bash
chmod +x deploy.sh
```

### 4. Ejecutar el despliegue
```bash
./deploy.sh
```

## 🗄️ Configuración de Base de Datos Digital Ocean

### 1. Crear la base de datos
1. Ve al panel de Digital Ocean
2. Crea un **Managed PostgreSQL Database**
3. Anota la cadena de conexión

### 2. Configurar la base de datos
```bash
# Ejecutar migraciones si es necesario
docker-compose -f docker-compose.production.yml exec main_app python migrate_db.py
```

## 🔧 Configuración DNS

Configura estos registros en tu proveedor de DNS:

```
A     tu_dominio.com          tu_ip_del_vps
A     www.tu_dominio.com      tu_ip_del_vps
CNAME *.tu_dominio.com        tu_dominio.com
```

## 🔐 SSL/TLS (Certificados Gratuitos)

El script de despliegue configurará automáticamente SSL con Let's Encrypt. Si necesitas renovar manualmente:

```bash
docker-compose -f docker-compose.production.yml run --rm certbot renew
docker-compose -f docker-compose.production.yml restart nginx
```

## 📊 Verificación del Despliegue

### 1. Verificar servicios corriendo
```bash
docker-compose -f docker-compose.production.yml ps
```

### 2. Ver logs en tiempo real
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### 3. Probar endpoints
- **Aplicación principal**: https://tu_dominio.com
- **Dashboard**: https://tu_dominio.com/dashboard
- **Geoportal**: https://tu_dominio.com/geoportal
- **Predictivos**: https://tu_dominio.com/predictivos
- **Monitoreo**: https://tu_dominio.com/monitoring

## 🔄 Mantenimiento

### Actualizar la aplicación
```bash
cd /opt/phi_gis_platform
git pull
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### Backup de la base de datos
```bash
# Si usas base de datos local
docker-compose -f docker-compose.production.yml exec db pg_dump -U postgres bd_actividades_historicas > backup_$(date +%Y%m%d).sql
```

### Monitoreo de recursos
```bash
# Ver uso de recursos
htop
df -h
docker stats
```

## 🆘 Solución de Problemas

### Servicio no inicia
```bash
# Ver logs específicos
docker-compose -f docker-compose.production.yml logs nombre_servicio

# Reiniciar servicio específico
docker-compose -f docker-compose.production.yml restart nombre_servicio
```

### Problemas de SSL
```bash
# Regenerar certificados
docker-compose -f docker-compose.production.yml run --rm certbot certonly --webroot --webroot-path=/var/www/html --email tu_email@dominio.com --agree-tos --no-eff-email --force-renewal -d tu_dominio.com
```

### Problemas de memoria
```bash
# Limpiar imágenes no utilizadas
docker system prune -a

# Verificar uso de memoria
free -h
```

## 📈 Optimización para Producción

### 1. Configurar backups automáticos
```bash
# Agregar a crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * cd /opt/phi_gis_platform && ./backup.sh
```

### 2. Configurar monitoreo
- **Grafana**: https://tu_dominio.com/monitoring
- Usuario: admin / Contraseña: admin123 (cambiar inmediatamente)

### 3. Configurar alertas
Configura alertas en Grafana para:
- Uso de CPU > 80%
- Uso de memoria > 85%
- Espacio en disco < 20%
- Servicios caídos

## 📞 Soporte

Para problemas específicos:
1. Revisa los logs: `docker-compose -f docker-compose.production.yml logs`
2. Verifica el estado de servicios: `docker-compose -f docker-compose.production.yml ps`
3. Consulta este README
4. Contacta al equipo de desarrollo

## 🎯 URLs Importantes

Después del despliegue exitoso:

- **🏠 Página principal**: https://tu_dominio.com
- **📊 Dashboard**: https://tu_dominio.com/dashboard  
- **🗺️ Geoportal**: https://tu_dominio.com/geoportal
- **🤖 Predictivos**: https://tu_dominio.com/predictivos
  - Asistentes: https://tu_dominio.com/predictivos/asistentes
  - Temporal: https://tu_dominio.com/predictivos/temporal
  - Geográfico: https://tu_dominio.com/predictivos/geografico
- **📈 Monitoreo**: https://tu_dominio.com/monitoring
- **🔍 Health Check**: https://tu_dominio.com/health

¡Tu plataforma PHI GIS estará lista para usar en producción! 🚀 