#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos de DigitalOcean
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de la base de datos de DigitalOcean
DB_CONFIG = {
    'host': 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com',
    'port': 25060,
    'database': 'defaultdb',
    'user': 'doadmin',
    'password': 'AVNS_nAsg-fcAlH1dOF3pzB_',
    'sslmode': 'require'
}

def test_basic_connection():
    """Prueba básica de conexión a la base de datos"""
    try:
        logger.info("🔄 Probando conexión básica a DigitalOcean PostgreSQL...")
        
        # Crear cadena de conexión
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        
        # Conectar
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Prueba básica
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Conexión exitosa! Versión PostgreSQL: {version[0]}")
        
        # Verificar PostGIS
        cursor.execute("SELECT PostGIS_version();")
        postgis_version = cursor.fetchone()
        logger.info(f"✅ PostGIS disponible! Versión: {postgis_version[0]}")
        
        # Listar tablas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"📋 Tablas existentes: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error de conexión: {e}")
        return False

def test_geometry_support():
    """Prueba el soporte para geometrías PostGIS"""
    try:
        logger.info("🔄 Probando soporte para geometrías...")
        
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Crear tabla de prueba
        cursor.execute("""
            DROP TABLE IF EXISTS test_geometry;
            CREATE TABLE test_geometry (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                geom GEOMETRY(POINT, 4326)
            );
        """)
        
        # Insertar punto de prueba
        cursor.execute("""
            INSERT INTO test_geometry (name, geom) 
            VALUES ('Punto de prueba', ST_GeomFromText('POINT(-74.0059 40.7128)', 4326));
        """)
        
        # Consultar datos
        cursor.execute("""
            SELECT id, name, ST_AsText(geom) as geom_text 
            FROM test_geometry;
        """)
        result = cursor.fetchone()
        logger.info(f"✅ Geometría creada correctamente: {result}")
        
        # Limpiar tabla de prueba
        cursor.execute("DROP TABLE test_geometry;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando geometrías: {e}")
        return False

def create_basic_schema():
    """Crea el esquema básico de tablas sin datos"""
    try:
        logger.info("🔄 Creando esquema básico de tablas...")
        
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Crear tabla principal de actividades (estructura básica)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actividades (
                id SERIAL PRIMARY KEY,
                fecha_inicio DATE,
                fecha_fin DATE,
                tipo_actividad VARCHAR(255),
                estado VARCHAR(100),
                descripcion TEXT,
                geom GEOMETRY(MULTIPOLYGON, 4326),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear tabla de departamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actividades_departamentos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255),
                codigo VARCHAR(10),
                geom GEOMETRY(MULTIPOLYGON, 4326),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear índices espaciales
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actividades_geom 
            ON actividades USING GIST (geom);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_departamentos_geom 
            ON actividades_departamentos USING GIST (geom);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Esquema básico creado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando esquema: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas de conexión a DigitalOcean...")
    
    # Prueba 1: Conexión básica
    if not test_basic_connection():
        logger.error("❌ Fallo en la prueba de conexión básica")
        return False
    
    # Prueba 2: Soporte de geometrías
    if not test_geometry_support():
        logger.error("❌ Fallo en la prueba de geometrías")
        return False
    
    # Prueba 3: Crear esquema básico
    if not create_basic_schema():
        logger.error("❌ Fallo creando el esquema básico")
        return False
    
    logger.info("🎉 ¡Todas las pruebas pasaron exitosamente!")
    logger.info("💡 La base de datos está lista para la aplicación")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 