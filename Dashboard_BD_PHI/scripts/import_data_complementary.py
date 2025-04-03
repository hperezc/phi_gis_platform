import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def crear_tablas_complementarias():
    # Cargar variables de entorno
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        # Crear tablas si no existen
        with engine.connect() as conn:
            # Tabla ríos principales (como MultiPolygon porque tiene ambos tipos)
            conn.execute(text("""
                DROP TABLE IF EXISTS rios_principales;
                CREATE TABLE rios_principales (
                    id SERIAL PRIMARY KEY,
                    nombre_geografico TEXT,
                    geometry geometry(MultiPolygonZ, 4326)
                );
            """))
            
            # Tabla vías (como MultiLineString porque tiene ambos tipos)
            conn.execute(text("""
                DROP TABLE IF EXISTS vias;
                CREATE TABLE vias (
                    id SERIAL PRIMARY KEY,
                    tipo_via TEXT,
                    geometry geometry(MultiLineStringZ, 4326)
                );
            """))
            conn.commit()
        
        # Cargar shapefiles y transformar a EPSG:4326
        print("Cargando shapefiles...")
        rios_gdf = gpd.read_file('C:/PHI_2025/SIG/PHI_IE/Shapefile/Drenaje_doble.shp')
        vias_gdf = gpd.read_file('C:/PHI_2025/SIG/PHI_IE/Shapefile/vias.shp')
        
        # Verificar tipos de geometría
        print("\nTipos de geometría en los shapefiles:")
        print(f"Ríos: {rios_gdf.geometry.type.unique()}")
        print(f"Vías: {vias_gdf.geometry.type.unique()}")
        
        # Verificar columnas en shapefiles
        print("\nColumnas en shapefile de Ríos Principales:")
        print(rios_gdf.columns.tolist())
        print("\nColumnas en shapefile de Vías:")
        print(vias_gdf.columns.tolist())
        
        # Establecer y transformar CRS
        print("\nTransformando coordenadas de shapefiles...")
        rios_gdf.set_crs(epsg=9377, inplace=True)
        vias_gdf.set_crs(epsg=9377, inplace=True)
        
        rios_gdf = rios_gdf.to_crs(epsg=4326)
        vias_gdf = vias_gdf.to_crs(epsg=4326)
        
        print(f"CRS Ríos: {rios_gdf.crs}")
        print(f"CRS Vías: {vias_gdf.crs}")
        
        # Convertir geometrías simples a multi
        print("\nConvirtiendo geometrías simples a multi...")
        rios_gdf.geometry = rios_gdf.geometry.apply(lambda geom: 
            geom if geom.type.startswith('Multi') else geom.buffer(0))
        
        vias_gdf.geometry = vias_gdf.geometry.apply(lambda geom: 
            geom if geom.type.startswith('Multi') else 
            gpd.GeoSeries([geom]).unary_union)
        
        # Seleccionar solo las columnas necesarias y renombrarlas
        rios_gdf = rios_gdf[['NOMBRE_GEO', 'geometry']].rename(columns={
            'NOMBRE_GEO': 'nombre_geografico'
        })
        
        vias_gdf = vias_gdf[['TIPO_VIA', 'geometry']].rename(columns={
            'TIPO_VIA': 'tipo_via'
        })
        
        # Verificar geometrías antes de guardar
        print("\nVerificando geometrías de ríos...")
        invalid_geoms_rios = rios_gdf[~rios_gdf.geometry.is_valid]
        if not invalid_geoms_rios.empty:
            print(f"Hay {len(invalid_geoms_rios)} geometrías de ríos inválidas")
            rios_gdf.geometry = rios_gdf.geometry.buffer(0)
        
        print("\nVerificando geometrías de vías...")
        invalid_geoms_vias = vias_gdf[~vias_gdf.geometry.is_valid]
        if not invalid_geoms_vias.empty:
            print(f"Hay {len(invalid_geoms_vias)} geometrías de vías inválidas")
            vias_gdf.geometry = vias_gdf.geometry.buffer(0)
        
        # Guardar en la base de datos
        print("\nGuardando tablas en la base de datos...")
        
        # Guardar ríos
        rios_gdf.to_postgis(
            name='rios_principales',
            con=engine,
            if_exists='append',
            index=False,
            dtype={'geometry': 'geometry(MultiPolygonZ, 4326)'}
        )
        
        # Guardar vías
        vias_gdf.to_postgis(
            name='vias',
            con=engine,
            if_exists='append',
            index=False,
            dtype={'geometry': 'geometry(MultiLineStringZ, 4326)'}
        )
        
        print("\nEstadísticas finales:")
        print(f"Total de registros en tabla ríos: {len(rios_gdf)}")
        print(f"Registros con geometría en ríos: {len(rios_gdf.dropna(subset=['geometry']))}")
        print(f"Total de registros en tabla vías: {len(vias_gdf)}")
        print(f"Registros con geometría en vías: {len(vias_gdf.dropna(subset=['geometry']))}")
        
        # Mostrar algunos ejemplos de los datos importados
        print("\nEjemplos de nombres de ríos importados:")
        print(rios_gdf['nombre_geografico'].head())
        print("\nEjemplos de tipos de vías importados:")
        print(vias_gdf['tipo_via'].value_counts().head())
        
    except Exception as e:
        print(f"Error durante la creación de tablas: {str(e)}")
        raise

if __name__ == "__main__":
    crear_tablas_complementarias() 