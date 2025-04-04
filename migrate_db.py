import os
import geopandas as gpd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar conexiones
LOCAL_DB = "postgresql://postgres:0000@localhost:5432/bd_actividades_historicas"
ALWAYSDATA_DB = "postgresql://hperezc97:geoHCP97@postgresql-hperezc97.alwaysdata.net:5432/hperezc97_actividades_phi"

def get_spatial_tables(engine):
    """Obtener todas las tablas con geometría"""
    query = text("""
        SELECT f_table_name, f_geometry_column
        FROM geometry_columns
        WHERE f_table_schema = 'public'
        AND f_table_name NOT IN ('spatial_ref_sys');
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        return [(row[0], row[1]) for row in result]

def migrate_data():
    try:
        # Crear conexiones
        print("Conectando a las bases de datos...")
        local_engine = create_engine(LOCAL_DB)
        remote_engine = create_engine(ALWAYSDATA_DB)
        
        # Crear extensión PostGIS en AlwaysData
        print("Creando extensión PostGIS...")
        with remote_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        
        # Obtener todas las tablas espaciales
        tables = get_spatial_tables(local_engine)
        print(f"\nTablas espaciales encontradas: {len(tables)}")
        
        # Migrar cada tabla
        for table_name, geom_column in tables:
            print(f"\nMigrando tabla {table_name}...")
            
            try:
                # Leer datos usando GeoDataFrame
                gdf = gpd.read_postgis(
                    f"SELECT * FROM {table_name}",
                    local_engine,
                    geom_col=geom_column
                )
                
                print(f"- Registros leídos: {len(gdf)}")
                
                # Convertir a EPSG:4326 si no lo está
                if gdf.crs != 'EPSG:4326':
                    print("- Convirtiendo a EPSG:4326...")
                    gdf = gdf.to_crs('EPSG:4326')
                
                # Migrar a AlwaysData
                print("- Escribiendo en AlwaysData...")
                gdf.to_postgis(
                    name=table_name,
                    con=remote_engine,
                    if_exists='replace',
                    index=False
                )
                
                print(f"✓ Tabla {table_name} migrada exitosamente")
                
            except Exception as table_error:
                print(f"Error migrando tabla {table_name}: {str(table_error)}")
                continue
        
        print("\n¡Migración completada!")
        
    except Exception as e:
        print(f"Error durante la migración: {str(e)}")

if __name__ == "__main__":
    migrate_data()
