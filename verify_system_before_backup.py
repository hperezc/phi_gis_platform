#!/usr/bin/env python3
"""
Script de verificación del sistema antes del backup
PHI GIS Platform - Verificación pre-backup
"""

import os
import sys
import psycopg2
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'pre_backup_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Verificar conexión a la base de datos"""
    logger.info("🔍 Verificando conexión a la base de datos...")
    
    try:
        # Cargar variables de entorno
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            logger.error("❌ No se encontró DATABASE_URL en las variables de entorno")
            return False
        
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar versión de PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✅ PostgreSQL: {version.split(',')[0]}")
        
        # Verificar PostGIS
        cursor.execute("SELECT PostGIS_Version();")
        postgis_version = cursor.fetchone()[0]
        logger.info(f"✅ PostGIS: {postgis_version}")
        
        # Listar tablas importantes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"✅ Tablas encontradas: {len(tables)}")
        
        # Verificar tablas críticas
        critical_tables = ['actividades', 'actividades_departamentos', 'actividades_municipios']
        for table in critical_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"✅ Tabla {table}: {count} registros")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando base de datos: {e}")
        return False

def check_docker_services():
    """Verificar servicios Docker"""
    logger.info("🐳 Verificando servicios Docker...")
    
    try:
        # Verificar si Docker está corriendo
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("❌ Docker no está corriendo")
            return False
        
        # Listar contenedores
        containers = result.stdout.strip().split('\n')[1:]  # Excluir header
        logger.info(f"✅ Contenedores activos: {len(containers)}")
        
        # Verificar contenedores específicos
        expected_containers = ['nginx', 'main_app', 'geoportal']
        for container in expected_containers:
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container}'], 
                                 capture_output=True, text=True)
            if container in result.stdout:
                logger.info(f"✅ Contenedor {container}: Activo")
            else:
                logger.warning(f"⚠️ Contenedor {container}: No encontrado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando Docker: {e}")
        return False

def check_disk_space():
    """Verificar espacio en disco"""
    logger.info("💾 Verificando espacio en disco...")
    
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Excluir header
                parts = line.split()
                if len(parts) >= 6:
                    filesystem = parts[0]
                    size = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4]
                    mount_point = parts[5]
                    
                    if mount_point == '/':
                        logger.info(f"✅ Disco principal: {size} total, {available} disponible, {use_percent} usado")
                        
                        # Verificar si hay suficiente espacio
                        use_percent_int = int(use_percent.replace('%', ''))
                        if use_percent_int > 90:
                            logger.error(f"❌ Disco casi lleno: {use_percent} usado")
                            return False
                        elif use_percent_int > 80:
                            logger.warning(f"⚠️ Disco con poco espacio: {use_percent} usado")
                        else:
                            logger.info(f"✅ Espacio en disco OK: {use_percent} usado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando espacio en disco: {e}")
        return False

def check_memory_usage():
    """Verificar uso de memoria"""
    logger.info("🧠 Verificando uso de memoria...")
    
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                memory_line = lines[1].split()
                if len(memory_line) >= 7:
                    total = memory_line[1]
                    used = memory_line[2]
                    free = memory_line[3]
                    available = memory_line[6]
                    
                    logger.info(f"✅ Memoria: {total} total, {available} disponible")
                    
                    # Calcular porcentaje de uso
                    try:
                        used_mb = float(used.replace('Gi', '').replace('Mi', ''))
                        total_mb = float(total.replace('Gi', '').replace('Mi', ''))
                        if 'Gi' in used:
                            used_mb *= 1024
                        if 'Gi' in total:
                            total_mb *= 1024
                        
                        use_percent = (used_mb / total_mb) * 100
                        if use_percent > 90:
                            logger.error(f"❌ Memoria crítica: {use_percent:.1f}% usado")
                            return False
                        elif use_percent > 80:
                            logger.warning(f"⚠️ Memoria alta: {use_percent:.1f}% usado")
                        else:
                            logger.info(f"✅ Memoria OK: {use_percent:.1f}% usado")
                    except:
                        logger.info("ℹ️ No se pudo calcular porcentaje de memoria")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando memoria: {e}")
        return False

def check_critical_files():
    """Verificar archivos críticos"""
    logger.info("📁 Verificando archivos críticos...")
    
    critical_files = [
        '.env.production',
        'docker-compose.production.yml',
        'nginx.conf',
        'requirements.production.txt',
        'geoportal/backend/app/main.py',
        'Dashboard_BD_PHI/dashboard/app.py',
        'ml_module/app.py'
    ]
    
    missing_files = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            logger.info(f"✅ Archivo encontrado: {file_path}")
        else:
            logger.warning(f"⚠️ Archivo faltante: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"⚠️ Archivos faltantes: {len(missing_files)}")
        return False
    
    return True

def check_network_connectivity():
    """Verificar conectividad de red"""
    logger.info("🌐 Verificando conectividad de red...")
    
    try:
        # Verificar conectividad a internet
        result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ Conectividad a internet: OK")
        else:
            logger.warning("⚠️ Problemas de conectividad a internet")
        
        # Verificar puertos importantes
        important_ports = [80, 443, 8050, 8000, 3000]
        for port in important_ports:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            if str(port) in result.stdout:
                logger.info(f"✅ Puerto {port}: En uso")
            else:
                logger.warning(f"⚠️ Puerto {port}: No encontrado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando conectividad: {e}")
        return False

def check_backup_directory():
    """Verificar directorio de backup"""
    logger.info("📦 Verificando directorio de backup...")
    
    backup_dir = "/opt/phi_gis_platform/backups"
    
    try:
        # Crear directorio si no existe
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directorio de backup: {backup_dir}")
        
        # Verificar permisos
        if os.access(backup_dir, os.W_OK):
            logger.info("✅ Permisos de escritura: OK")
        else:
            logger.error("❌ Sin permisos de escritura en directorio de backup")
            return False
        
        # Verificar espacio disponible
        result = subprocess.run(['df', '-h', backup_dir], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    available = parts[3]
                    logger.info(f"✅ Espacio disponible para backup: {available}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando directorio de backup: {e}")
        return False

def main():
    """Función principal de verificación"""
    logger.info("🚀 INICIANDO VERIFICACIÓN PRE-BACKUP DEL SISTEMA")
    logger.info("=" * 60)
    
    checks = [
        ("Base de datos", check_database_connection),
        ("Servicios Docker", check_docker_services),
        ("Espacio en disco", check_disk_space),
        ("Uso de memoria", check_memory_usage),
        ("Archivos críticos", check_critical_files),
        ("Conectividad de red", check_network_connectivity),
        ("Directorio de backup", check_backup_directory)
    ]
    
    results = {}
    all_passed = True
    
    for check_name, check_function in checks:
        logger.info(f"\n🔍 Verificando: {check_name}")
        try:
            result = check_function()
            results[check_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"❌ Error en verificación {check_name}: {e}")
            results[check_name] = False
            all_passed = False
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE VERIFICACIÓN PRE-BACKUP")
    logger.info("=" * 60)
    
    for check_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{status}: {check_name}")
    
    if all_passed:
        logger.info("\n🎉 TODAS LAS VERIFICACIONES PASARON")
        logger.info("✅ El sistema está listo para el backup")
        return True
    else:
        logger.error("\n⚠️ ALGUNAS VERIFICACIONES FALLARON")
        logger.error("❌ Se recomienda resolver los problemas antes del backup")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 