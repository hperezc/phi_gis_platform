#!/usr/bin/env python3
"""
Script para actualizar la tabla sistema_alarmas desde shapefile
PHI GIS Platform - Actualización de Sistema de Alarmas
"""

import os
import sys
import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'update_alarmas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        # Cargar variables de entorno
        load_dotenv('.env.production')
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            logger.error("❌ No se encontró DATABASE_URL en las variables de entorno")
            return None
        
        # Crear engine de SQLAlchemy
        engine = create_engine(DATABASE_URL)
        return engine
        
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return None

def backup_current_table(engine):
    """Crear backup de la tabla actual"""
    try:
        logger.info("💾 Creando backup de la tabla sistema_alarmas actual...")
        
        # Crear tabla de backup
        backup_table_name = f"sistema_alarmas_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with engine.connect() as conn:
            # Crear tabla de backup
            conn.execute(text(f"CREATE TABLE {backup_table_name} AS SELECT * FROM sistema_alarmas"))
            conn.commit()
            
            # Contar registros en backup
            result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table_name}"))
            count = result.scalar()
            
            logger.info(f"✅ Backup creado: {backup_table_name} con {count} registros")
            return backup_table_name
            
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return None

def load_shapefile_to_dataframe(shapefile_path):
    """Cargar shapefile a GeoDataFrame"""
    try:
        logger.info(f"📁 Cargando shapefile: {shapefile_path}")
        
        # Cargar shapefile
        gdf = gpd.read_file(shapefile_path)
        
        logger.info(f"✅ Shapefile cargado: {len(gdf)} registros")
        logger.info(f"📋 Columnas: {list(gdf.columns)}")
        
        # Mostrar información de geometría
        logger.info(f"📍 Sistema de coordenadas: {gdf.crs}")
        logger.info(f"🔢 Tipos de geometría: {gdf.geometry.geom_type.unique()}")
        
        return gdf
        
    except Exception as e:
        logger.error(f"❌ Error cargando shapefile: {e}")
        return None

def update_sistema_alarmas_table(engine, gdf):
    """Actualizar la tabla sistema_alarmas"""
    try:
        logger.info("🔄 Actualizando tabla sistema_alarmas...")
        
        with engine.connect() as conn:
            # Eliminar tabla actual
            logger.info("🗑️ Eliminando tabla actual...")
            conn.execute(text("DROP TABLE IF EXISTS sistema_alarmas CASCADE"))
            conn.commit()
            
            # Cargar nuevos datos
            logger.info("📥 Cargando nuevos datos...")
            gdf.to_postgis('sistema_alarmas', engine, if_exists='replace', index=False)
            
            # Verificar carga
            result = conn.execute(text("SELECT COUNT(*) FROM sistema_alarmas"))
            count = result.scalar()
            
            logger.info(f"✅ Tabla actualizada: {count} registros cargados")
            
            # Crear índices espaciales
            logger.info("🔍 Creando índices espaciales...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sistema_alarmas_geometry ON sistema_alarmas USING GIST (geometry)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sistema_alarmas_departamento ON sistema_alarmas (departamento)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sistema_alarmas_municipio ON sistema_alarmas (municipio)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sistema_alarmas_estado ON sistema_alarmas (estado)"))
            conn.commit()
            
            logger.info("✅ Índices espaciales creados")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error actualizando tabla: {e}")
        return False

def verify_update(engine):
    """Verificar que la actualización fue exitosa"""
    try:
        logger.info("🔍 Verificando actualización...")
        
        with engine.connect() as conn:
            # Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM sistema_alarmas"))
            count = result.scalar()
            logger.info(f"📊 Total de alarmas: {count}")
            
            # Verificar estructura
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sistema_alarmas' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            logger.info("📋 Estructura de la tabla:")
            for col in columns:
                logger.info(f"   - {col[0]}: {col[1]}")
            
            # Mostrar algunos registros
            result = conn.execute(text("SELECT id, departamento, municipio, nombre_sat, estado FROM sistema_alarmas LIMIT 5"))
            records = result.fetchall()
            logger.info("📝 Primeros 5 registros:")
            for record in records:
                logger.info(f"   - ID: {record[0]}, {record[1]} - {record[2]}: {record[3]} ({record[4]})")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verificando actualización: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO ACTUALIZACIÓN DE SISTEMA DE ALARMAS")
    logger.info("=" * 60)
    
    # Verificar argumentos
    if len(sys.argv) != 2:
        logger.error("❌ Uso: python3 update_sistema_alarmas.py <ruta_al_shapefile>")
        logger.error("Ejemplo: python3 update_sistema_alarmas.py sistema_alarmas_actualizado.shp")
        sys.exit(1)
    
    shapefile_path = sys.argv[1]
    
    # Verificar que el shapefile existe
    if not os.path.exists(shapefile_path):
        logger.error(f"❌ Shapefile no encontrado: {shapefile_path}")
        sys.exit(1)
    
    # Conectar a la base de datos
    engine = get_db_connection()
    if not engine:
        sys.exit(1)
    
    try:
        # 1. Crear backup de la tabla actual
        backup_table = backup_current_table(engine)
        if not backup_table:
            logger.error("❌ No se pudo crear backup")
            sys.exit(1)
        
        # 2. Cargar shapefile
        gdf = load_shapefile_to_dataframe(shapefile_path)
        if gdf is None:
            sys.exit(1)
        
        # 3. Actualizar tabla
        if not update_sistema_alarmas_table(engine, gdf):
            logger.error("❌ Error actualizando tabla")
            sys.exit(1)
        
        # 4. Verificar actualización
        if not verify_update(engine):
            logger.error("❌ Error en verificación")
            sys.exit(1)
        
        logger.info("🎉 ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info(f"📁 Backup de tabla anterior: {backup_table}")
        logger.info(f"📁 Shapefile utilizado: {shapefile_path}")
        logger.info("✅ La tabla sistema_alarmas ha sido actualizada")
        logger.info("⚠️ Próximo paso: Integrar la capa al geoportal")
        
    except Exception as e:
        logger.error(f"❌ Error durante la actualización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 