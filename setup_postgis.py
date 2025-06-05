#!/usr/bin/env python3
"""
Script para configurar PostGIS en la base de datos de producción
PHI GIS Platform - Setup PostGIS en Digital Ocean
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def setup_postgis(conn):
    """Instalar y configurar PostGIS en la base de datos"""
    try:
        cur = conn.cursor()
        
        # Verificar si PostGIS ya está instalado
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        postgis_exists = cur.fetchone()[0]
        
        if postgis_exists:
            logger.info("PostGIS ya está instalado")
        else:
            logger.info("Instalando PostGIS...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            logger.info("SUCCESS: PostGIS instalado")
        
        # Instalar extensión topology si está disponible
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
            logger.info("SUCCESS: PostGIS Topology instalado")
        except Exception as e:
            logger.warning(f"PostGIS Topology no disponible: {e}")
        
        # Verificar instalación
        cur.execute("SELECT PostGIS_Version();")
        version = cur.fetchone()[0]
        logger.info(f"PostGIS Version: {version}")
        
        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error configurando PostGIS: {e}")
        return False

def main():
    """Función principal"""
    logger.info("Configurando PostGIS en base de datos de producción...")
    
    # Cargar variables de entorno
    load_dotenv('.env.production')
    
    PRODUCTION_DB_URL = os.getenv('DATABASE_URL')
    
    if not PRODUCTION_DB_URL:
        logger.error("ERROR: No se encontró DATABASE_URL en .env.production")
        sys.exit(1)
    
    logger.info("Conectando a base de datos de producción...")
    
    try:
        conn = psycopg2.connect(PRODUCTION_DB_URL)
        logger.info("SUCCESS: Conectado a la base de datos")
        
        if setup_postgis(conn):
            logger.info("SUCCESS: PostGIS configurado correctamente")
        else:
            logger.error("ERROR: Fallo en la configuración de PostGIS")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"ERROR: Error conectando a la base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 