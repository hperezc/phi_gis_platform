import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def crear_tablas_escalas():
    # Cargar variables de entorno
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        # Crear tablas si no existen
        with engine.connect() as conn:
            # Tabla municipios
            conn.execute(text("""
                DROP TABLE IF EXISTS actividades_municipios;
                CREATE TABLE actividades_municipios (
                    id SERIAL PRIMARY KEY,
                    contrato TEXT,
                    ano INTEGER,
                    mes TEXT,
                    fecha DATE,
                    zona_geografica TEXT,
                    departamento TEXT,
                    municipio TEXT,
                    grupo_interes TEXT,
                    ubicacion TEXT,
                    grupo_intervencion TEXT,
                    descripcion_actividad TEXT,
                    categoria_actividad TEXT,
                    categoria_unica TEXT,
                    total_asistentes INTEGER,
                    pais TEXT,
                    geometry geometry(Geometry, 4326)
                );
            """))
            
            # Tabla departamentos
            conn.execute(text("""
                DROP TABLE IF EXISTS actividades_departamentos;
                CREATE TABLE actividades_departamentos (
                    id SERIAL PRIMARY KEY,
                    contrato TEXT,
                    ano INTEGER,
                    mes TEXT,
                    fecha DATE,
                    zona_geografica TEXT,
                    departamento TEXT,
                    municipio TEXT,
                    grupo_interes TEXT,
                    ubicacion TEXT,
                    grupo_intervencion TEXT,
                    descripcion_actividad TEXT,
                    categoria_actividad TEXT,
                    categoria_unica TEXT,
                    total_asistentes INTEGER,
                    pais TEXT,
                    geometry geometry(Geometry, 4326)
                );
            """))
            conn.commit()
        
        # Cargar shapefiles y transformar a EPSG:4326
        print("Cargando shapefiles...")
        municipios_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Municipios.shp')
        departamentos_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Departamentos.shp')
        
        # Verificar columnas en shapefiles
        print("\nColumnas en shapefile de Municipios:")
        print(municipios_gdf.columns.tolist())
        print("\nColumnas en shapefile de Departamentos:")
        print(departamentos_gdf.columns.tolist())
        
        # Establecer y transformar CRS
        print("\nTransformando coordenadas de shapefiles...")
        municipios_gdf.set_crs(epsg=9377, inplace=True)
        departamentos_gdf.set_crs(epsg=9377, inplace=True)
        
        municipios_gdf = municipios_gdf.to_crs(epsg=4326)
        departamentos_gdf = departamentos_gdf.to_crs(epsg=4326)
        
        print(f"CRS Municipios: {municipios_gdf.crs}")
        print(f"CRS Departamentos: {departamentos_gdf.crs}")
        
        # Leer datos de la tabla original
        print("Leyendo datos de la tabla original...")
        query = "SELECT * FROM actividades;"
        df = gpd.read_postgis(query, engine, geom_col='geometry')
        
        # Función para normalizar texto
        def normalizar_texto(texto):
            import unicodedata
            if not isinstance(texto, str):
                return ''
            
            # Convertir a minúsculas y eliminar espacios extras
            texto = texto.lower().strip()
            
            # Eliminar tildes
            texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                          if unicodedata.category(c) != 'Mn')
            
            # Normalizar espacios en nombres compuestos
            texto = texto.replace('santa fe', 'santafe')
            texto = texto.replace('santafe', 'santa fe')
            
            return texto
        
        # Diccionario de correcciones manuales
        correcciones_municipios = {
            'bogota': 'bogota d.c.',
            'bogota d.c': 'bogota d.c.',
            'cartagena': 'cartagena de indias',
            'santafe de antioquia': 'santa fe de antioquia',
            'santafé de antioquia': 'santa fe de antioquia',
            # Agregar más correcciones según sea necesario
        }
        
        # Procesar tabla de municipios con verificación de departamento
        print("\nProcesando tabla de municipios...")
        municipios_geom = []
        municipios_no_encontrados = set()
        coincidencias_municipios = 0

        # Crear diccionario de municipios por departamento para búsqueda más rápida
        municipios_dict = {}
        for idx, row in municipios_gdf.iterrows():
            mun_norm = normalizar_texto(row['MpNombre'])
            dep_norm = normalizar_texto(row['Depto'])
            key = (mun_norm, dep_norm)
            municipios_dict[key] = row['geometry']
            
            # Agregar variantes del nombre
            if 'santa fe' in mun_norm:
                key_alt = (mun_norm.replace('santa fe', 'santafe'), dep_norm)
                municipios_dict[key_alt] = row['geometry']
            elif 'santafe' in mun_norm:
                key_alt = (mun_norm.replace('santafe', 'santa fe'), dep_norm)
                municipios_dict[key_alt] = row['geometry']

        for idx, row in df.iterrows():
            municipio = normalizar_texto(row['municipio'])
            departamento = normalizar_texto(row['departamento'])
            
            # Aplicar correcciones si existen
            municipio = correcciones_municipios.get(municipio, municipio)
            
            # Buscar coincidencia exacta con municipio y departamento
            if (municipio, departamento) in municipios_dict:
                municipios_geom.append(municipios_dict[(municipio, departamento)])
                coincidencias_municipios += 1
            else:
                # Intentar encontrar coincidencias parciales
                encontrado = False
                for (mun, dep), geom in municipios_dict.items():
                    if municipio in mun and departamento == dep:
                        municipios_geom.append(geom)
                        coincidencias_municipios += 1
                        encontrado = True
                        break
                
                if not encontrado:
                    municipios_geom.append(None)
                    municipios_no_encontrados.add(f"{row['municipio']} ({row['departamento']})")

        # Procesar tabla de departamentos con normalización
        print("\nProcesando tabla de departamentos...")
        departamentos_geom = []
        departamentos_no_encontrados = set()
        coincidencias_departamentos = 0

        # Crear diccionario de departamentos para búsqueda más rápida
        departamentos_dict = {normalizar_texto(row['DeNombre']): row['geometry'] 
                            for idx, row in departamentos_gdf.iterrows()}

        for idx, row in df.iterrows():
            departamento = normalizar_texto(row['departamento'])
            if departamento in departamentos_dict:
                departamentos_geom.append(departamentos_dict[departamento])
                coincidencias_departamentos += 1
            else:
                departamentos_geom.append(None)
                departamentos_no_encontrados.add(row['departamento'])

        # Imprimir estadísticas detalladas con más información
        print("\n=== Estadísticas de Municipios ===")
        print(f"Total de registros procesados: {len(df)}")
        print(f"Coincidencias encontradas: {coincidencias_municipios}")
        print(f"Porcentaje de éxito: {(coincidencias_municipios/len(df))*100:.2f}%")
        print("\nMunicipios no encontrados (con su departamento):")
        for mun in sorted(municipios_no_encontrados):
            print(f"- {mun}")

        print("\n=== Estadísticas de Departamentos ===")
        print(f"Total de registros procesados: {len(df)}")
        print(f"Coincidencias encontradas: {coincidencias_departamentos}")
        print(f"Porcentaje de éxito: {(coincidencias_departamentos/len(df))*100:.2f}%")
        print("\nDepartamentos no encontrados:")
        for dep in sorted(departamentos_no_encontrados):
            print(f"- {dep}")

        # Verificar nombres en shapefiles
        print("\n=== Nombres en Shapefiles ===")
        print("Municipios disponibles (primeros 10):")
        print(sorted(municipios_gdf['MpNombre'].unique())[:10])
        print("\nDepartamentos disponibles:")
        print(sorted(departamentos_gdf['DeNombre'].unique()))
        
        # Crear GeoDataFrame para municipios
        gdf_municipios = gpd.GeoDataFrame(
            df.drop(columns=['geometry', 'tipo_geometria']),
            geometry=municipios_geom,
            crs="EPSG:4326"
        )
        
        # Crear GeoDataFrame para departamentos
        gdf_departamentos = gpd.GeoDataFrame(
            df.drop(columns=['geometry', 'tipo_geometria']),
            geometry=departamentos_geom,
            crs="EPSG:4326"
        )
        
        # Verificar límites de las geometrías antes de guardar
        print("\nVerificando límites de las geometrías:")
        if not gdf_municipios.empty:
            bounds_mun = gdf_municipios.total_bounds
            print(f"Municipios: Lat [{bounds_mun[1]:.4f}, {bounds_mun[3]:.4f}], Lon [{bounds_mun[0]:.4f}, {bounds_mun[2]:.4f}]")
        
        if not gdf_departamentos.empty:
            bounds_dep = gdf_departamentos.total_bounds
            print(f"Departamentos: Lat [{bounds_dep[1]:.4f}, {bounds_dep[3]:.4f}], Lon [{bounds_dep[0]:.4f}, {bounds_dep[2]:.4f}]")
        
        # Guardar en la base de datos
        print("Guardando tablas en la base de datos...")
        
        # Verificar que las geometrías son válidas antes de guardar
        print("\nVerificando geometrías municipales...")
        invalid_geoms_mun = gdf_municipios[~gdf_municipios.geometry.is_valid]
        if not invalid_geoms_mun.empty:
            print(f"Hay {len(invalid_geoms_mun)} geometrías municipales inválidas")
            gdf_municipios.geometry = gdf_municipios.geometry.buffer(0)
        
        print("\nVerificando geometrías departamentales...")
        invalid_geoms_dep = gdf_departamentos[~gdf_departamentos.geometry.is_valid]
        if not invalid_geoms_dep.empty:
            print(f"Hay {len(invalid_geoms_dep)} geometrías departamentales inválidas")
            gdf_departamentos.geometry = gdf_departamentos.geometry.buffer(0)
        
        # Guardar con to_postgis especificando el tipo de geometría
        gdf_municipios.to_postgis(
            name='actividades_municipios',
            con=engine,
            if_exists='append',
            index=False,
            dtype={'geometry': 'geometry(MultiPolygon, 4326)'}
        )
        
        gdf_departamentos.to_postgis(
            name='actividades_departamentos',
            con=engine,
            if_exists='append',
            index=False,
            dtype={'geometry': 'geometry(MultiPolygon, 4326)'}
        )
        
        print("Tablas creadas exitosamente")
        print(f"Total de registros en tabla municipal: {len(gdf_municipios)}")
        print(f"Registros con geometría municipal: {len(gdf_municipios.dropna(subset=['geometry']))}")
        print(f"Total de registros en tabla departamental: {len(gdf_departamentos)}")
        print(f"Registros con geometría departamental: {len(gdf_departamentos.dropna(subset=['geometry']))}")
        
    except Exception as e:
        print(f"Error durante la creación de tablas: {str(e)}")
        raise

if __name__ == "__main__":
    crear_tablas_escalas()
