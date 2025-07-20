#!/usr/bin/env python3
import geopandas as gpd
from sqlalchemy import create_engine, text
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Cargar variables de entorno
    load_dotenv('.env.production')
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    # Cargar shapefile
    logger.info("�� Cargando shapefile...")
    gdf = gpd.read_file('Sistema_Alarmas.shp')
    logger.info(f"✅ Shapefile cargado: {len(gdf)} registros")
    
    # Cargar directamente a la base de datos
    logger.info("📥 Cargando datos a la base de datos...")
    gdf.to_postgis('sistema_alarmas', engine, if_exists='replace', index=False)
    
    # Verificar
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM sistema_alarmas"))
        count = result.scalar()
        logger.info(f"✅ Tabla actualizada: {count} registros")
    
    logger.info("🎉 Actualización completada!")

if __name__ == "__main__":
    main()
