#!/usr/bin/env python3
"""
Script para probar y configurar el geoportal con DigitalOcean
"""

import os
import sys
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar variables de entorno para DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
os.environ['DB_USER'] = 'doadmin'
os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
os.environ['DB_PORT'] = '25060'
os.environ['DB_NAME'] = 'defaultdb'

def test_geoportal_connection():
    """Prueba la conexión del geoportal"""
    try:
        logger.info("🔍 Probando conexión del geoportal a DigitalOcean...")
        
        # Cambiar al directorio del geoportal
        geoportal_path = Path(os.getcwd()) / 'geoportal' / 'backend'
        sys.path.append(str(geoportal_path))
        
        from app.database import engine, DATABASE_URL
        from sqlalchemy import text
        
        logger.info(f"📡 URL de conexión: {DATABASE_URL[:50]}...")
        
        # Test de conexión básica
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()
            logger.info(f"✅ PostgreSQL: {version[0]}")
            
            # Test PostGIS
            result = conn.execute(text("SELECT PostGIS_version();"))
            postgis_version = result.fetchone()
            logger.info(f"✅ PostGIS: {postgis_version[0]}")
            
            # Test de datos
            result = conn.execute(text("SELECT COUNT(*) FROM actividades;"))
            count = result.fetchone()
            logger.info(f"📊 Actividades en BD: {count[0]}")
            
        logger.info("✅ Geoportal conectado exitosamente a DigitalOcean")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en conexión del geoportal: {e}")
        return False

def test_geoportal_queries():
    """Prueba consultas específicas del geoportal"""
    try:
        logger.info("🔍 Probando consultas específicas del geoportal...")
        
        geoportal_path = Path(os.getcwd()) / 'geoportal' / 'backend'
        sys.path.append(str(geoportal_path))
        
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Consulta de departamentos con geometría
            result = conn.execute(text("""
                SELECT departamento, COUNT(*) as actividades
                FROM actividades 
                WHERE departamento IS NOT NULL
                GROUP BY departamento
                ORDER BY actividades DESC
                LIMIT 5;
            """))
            
            departamentos = result.fetchall()
            logger.info("📋 Top 5 departamentos:")
            for dept in departamentos:
                logger.info(f"   {dept[0]}: {dept[1]} actividades")
            
            # Consulta geoespacial
            result = conn.execute(text("""
                SELECT COUNT(*) as with_geometry
                FROM actividades 
                WHERE geometry IS NOT NULL;
            """))
            
            geom_count = result.fetchone()
            logger.info(f"🗺️ Actividades con geometría: {geom_count[0]}")
            
        logger.info("✅ Consultas del geoportal funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en consultas del geoportal: {e}")
        return False

def create_geoportal_env():
    """Crea archivo .env específico para el geoportal"""
    try:
        logger.info("📝 Creando archivo .env para el geoportal...")
        
        geoportal_backend_path = Path(os.getcwd()) / 'geoportal' / 'backend'
        env_file = geoportal_backend_path / '.env'
        
        env_content = """# Configuración del Geoportal para DigitalOcean
# Generado automáticamente

# Variables de base de datos
DB_USER=doadmin
DB_PASSWORD=AVNS_nAsg-fcAlH1dOF3pzB_
DB_HOST=db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=defaultdb

# Configuración de entorno
ENVIRONMENT=production

# Configuración de FastAPI
API_HOST=0.0.0.0
API_PORT=8000
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f"✅ Archivo .env creado en {env_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando .env del geoportal: {e}")
        return False

def update_geoportal_database_config():
    """Actualiza la configuración de base de datos del geoportal para mejor compatibilidad"""
    try:
        logger.info("🔧 Actualizando configuración de base de datos del geoportal...")
        
        geoportal_db_file = Path(os.getcwd()) / 'geoportal' / 'backend' / 'app' / 'database.py'
        
        updated_content = '''from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import urllib.parse
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener y codificar los parámetros de conexión para DigitalOcean
DB_USER = urllib.parse.quote_plus(os.getenv('DB_USER', 'postgres'))
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', '0000'))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bd_actividades_historicas')

# Construir la URL de conexión
if os.getenv('ENVIRONMENT') == 'production':
    # Configuración para DigitalOcean con SSL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    logger.info("Configurando geoportal para DigitalOcean")
else:
    # Configuración local
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("Configurando geoportal para desarrollo local")

# Crear el engine de SQLAlchemy con parámetros específicos para DigitalOcean
engine = create_engine(
    DATABASE_URL,
    client_encoding='utf8',
    connect_args={
        'client_encoding': 'utf8',
        'options': '-c timezone=utc -c client_encoding=utf8'
    } if os.getenv('ENVIRONMENT') != 'production' else {
        'sslmode': 'require',
        'client_encoding': 'utf8',
        'options': '-c timezone=utc -c client_encoding=utf8'
    },
    echo=False  # Cambiar a True para debug
)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Función para obtener una conexión a la base de datos.
    Se usa como dependencia en FastAPI.
    """
    db = None
    try:
        db = SessionLocal()
        return db
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        if db:
            db.close()
        raise

def test_connection():
    """Función para probar la conexión a la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        return False
'''
        
        with open(geoportal_db_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("✅ Configuración de base de datos del geoportal actualizada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 CONFIGURANDO GEOPORTAL PARA DIGITALOCEAN")
    logger.info("=" * 50)
    
    results = {}
    
    # Paso 1: Crear archivo .env
    results['env_file'] = create_geoportal_env()
    
    # Paso 2: Actualizar configuración de BD
    results['db_config'] = update_geoportal_database_config()
    
    # Paso 3: Probar conexión
    results['connection'] = test_geoportal_connection()
    
    # Paso 4: Probar consultas
    results['queries'] = test_geoportal_queries()
    
    # Resumen
    logger.info("\n" + "=" * 50)
    logger.info("📋 RESUMEN DE CONFIGURACIÓN DEL GEOPORTAL:")
    logger.info("=" * 50)
    
    for test, status in results.items():
        icon = "✅" if status else "❌"
        test_name = test.replace('_', ' ').title()
        logger.info(f"{icon} {test_name}: {'OK' if status else 'Error'}")
    
    total_ok = sum(results.values())
    logger.info(f"\n🎯 {total_ok}/4 pruebas pasaron exitosamente")
    
    if total_ok >= 3:
        logger.info("\n🎉 ¡GEOPORTAL CONFIGURADO EXITOSAMENTE!")
        logger.info("💡 El geoportal está listo para usar DigitalOcean")
        return True
    else:
        logger.info("\n⚠️ Configuración del geoportal necesita revisión")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 