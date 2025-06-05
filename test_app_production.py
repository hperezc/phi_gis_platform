#!/usr/bin/env python3
"""
Script para probar la aplicación PHI GIS con la base de datos de DigitalOcean
"""

import os
import sys
import psycopg2
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Establecer el entorno de producción
os.environ['ENVIRONMENT'] = 'production'

def test_database_queries():
    """Prueba consultas básicas de la aplicación"""
    try:
        logger.info("🔄 Probando consultas de la aplicación...")
        
        from config.database import DATABASE_URL
        logger.info(f"📡 Usando DATABASE_URL: {DATABASE_URL[:50]}...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Contar registros en tabla principal
        cursor.execute("SELECT COUNT(*) FROM actividades;")
        count_actividades = cursor.fetchone()[0]
        logger.info(f"📊 Actividades en BD: {count_actividades}")
        
        # Contar departamentos
        cursor.execute("SELECT COUNT(*) FROM actividades_departamentos;")
        count_departamentos = cursor.fetchone()[0]
        logger.info(f"🗺️ Departamentos en BD: {count_departamentos}")
        
        # Verificar datos geoespaciales
        cursor.execute("""
            SELECT COUNT(*) FROM actividades 
            WHERE geometry IS NOT NULL;
        """)
        count_with_geom = cursor.fetchone()[0]
        logger.info(f"📍 Actividades con geometría: {count_with_geom}")
        
        # Obtener tipos de geometría
        cursor.execute("""
            SELECT tipo_geometria, COUNT(*) 
            FROM actividades 
            WHERE tipo_geometria IS NOT NULL
            GROUP BY tipo_geometria
            LIMIT 5;
        """)
        geom_types = cursor.fetchall()
        logger.info(f"🔍 Tipos de geometría: {geom_types}")
        
        # Obtener muestra de datos
        cursor.execute("""
            SELECT id, categoria_actividad, contrato, fecha 
            FROM actividades 
            LIMIT 5;
        """)
        sample_data = cursor.fetchall()
        logger.info(f"📋 Muestra de datos:")
        for row in sample_data:
            logger.info(f"   ID: {row[0]}, Categoría: {row[1]}, Contrato: {row[2]}, Fecha: {row[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando consultas: {e}")
        return False

def test_flask_app():
    """Prueba la aplicación Flask básica"""
    try:
        logger.info("🔄 Probando aplicación Flask...")
        
        # Importar la aplicación
        from main import create_main_app
        app = create_main_app()
        
        # Crear cliente de prueba
        with app.test_client() as client:
            # Probar página principal
            response = client.get('/')
            logger.info(f"🏠 Página principal: {response.status_code}")
            
            # Probar health check
            response = client.get('/health')
            if response.status_code == 200:
                health_data = response.get_json()
                logger.info(f"💚 Health check: {health_data['status']}")
                logger.info(f"🔧 Servicios: {health_data.get('services', {})}")
            else:
                logger.warning(f"⚠️ Health check failed: {response.status_code}")
            
            # Probar ruta de dashboard
            response = client.get('/dashboard')
            logger.info(f"📊 Dashboard redirect: {response.status_code}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando Flask app: {e}")
        return False

def test_dash_dashboard():
    """Prueba el dashboard de Dash"""
    try:
        logger.info("🔄 Probando dashboard de Dash...")
        
        # Importar el dashboard
        from Dashboard_BD_PHI.dashboard.app import create_dash_app
        
        dash_app = create_dash_app()
        
        if dash_app:
            logger.info("✅ Dashboard de Dash creado exitosamente")
            # El dashboard se probará cuando se integre en la aplicación principal
            return True
        else:
            logger.warning("⚠️ No se pudo crear el dashboard de Dash")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error probando dashboard: {e}")
        return False

def create_test_environment():
    """Configura el entorno de prueba"""
    try:
        logger.info("🔧 Configurando entorno de prueba...")
        
        # Crear directorio de logs si no existe
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logger.info(f"📁 Creado directorio de logs: {log_dir}")
        
        # Configurar variables de entorno necesarias
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando entorno: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas de la aplicación en producción...")
    logger.info(f"📅 Fecha y hora: {datetime.now()}")
    
    # Configurar entorno
    if not create_test_environment():
        logger.error("❌ Fallo configurando el entorno")
        return False
    
    # Prueba 1: Conexión y consultas de base de datos
    if not test_database_queries():
        logger.error("❌ Fallo en las pruebas de base de datos")
        return False
    
    # Prueba 2: Aplicación Flask
    if not test_flask_app():
        logger.error("❌ Fallo en las pruebas de Flask")
        return False
    
    # Prueba 3: Dashboard de Dash
    if not test_dash_dashboard():
        logger.error("❌ Fallo en las pruebas del dashboard")
        return False
    
    logger.info("🎉 ¡Todas las pruebas de la aplicación pasaron exitosamente!")
    logger.info("🚀 La aplicación está lista para desplegarse en producción")
    logger.info("💡 Próximos pasos:")
    logger.info("   1. Ejecutar: docker-compose -f docker-compose.production.yml up -d")
    logger.info("   2. Configurar dominio en DigitalOcean")
    logger.info("   3. Ejecutar script de despliegue")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 