import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def verificar_columnas_shapefile(gdf, nombre_shapefile):
    print(f"\nColumnas en {nombre_shapefile}:")
    print(gdf.columns.tolist())

def obtener_geometria(row, veredas_gdf, municipios_gdf, departamentos_gdf, cabeceras_gdf):
    try:
        # Primero intentar con vereda
        if pd.notnull(row['grupo_interes']) and not any(row['grupo_interes'].startswith(prefix) 
                for prefix in ['Barrio', 'CMGRD', 'I.E.']):
            vereda_match = veredas_gdf[
                (veredas_gdf['NOMBRE_VER'].str.lower() == row['grupo_interes'].lower()) &
                (veredas_gdf['NOMB_MPIO'].str.lower() == row['municipio'].lower())
            ]
            if not vereda_match.empty:
                return vereda_match.geometry.iloc[0], 'vereda'
        
        # Si es un barrio o CMGRD, intentar con cabecera municipal
        if pd.notnull(row['grupo_interes']) and any(row['grupo_interes'].startswith(prefix) 
                for prefix in ['Barrio', 'CMGRD']):
            cabecera_match = cabeceras_gdf[
                cabeceras_gdf['NOM_CPOB'].str.lower() == row['municipio'].lower()
            ]
            if not cabecera_match.empty:
                return cabecera_match.geometry.iloc[0], 'cabecera'
        
        # Si no se encuentra o es I.E., usar municipio
        municipio_match = municipios_gdf[
            municipios_gdf['MpNombre'].str.lower() == row['municipio'].lower()
        ]
        if not municipio_match.empty:
            return municipio_match.geometry.iloc[0], 'municipio'
        
        # Si no se encuentra municipio, usar departamento
        depto_match = departamentos_gdf[
            departamentos_gdf['DeNombre'].str.lower() == row['departamento'].lower()
        ]
        if not depto_match.empty:
            return depto_match.geometry.iloc[0], 'departamento'
        
        return None, None
    except Exception as e:
        print(f"Error procesando fila {row.name}: {str(e)}")
        return None, None

def limpiar_nombre(nombre):
    if pd.isnull(nombre):
        return nombre
    nombre = nombre.lower()
    nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    nombre = nombre.replace('ñ', 'n')
    return nombre

def crear_tabla_si_no_existe(engine):
    try:
        with engine.connect() as conn:
            # Habilitar PostGIS
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            
            # Crear la tabla con todas las columnas necesarias
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS actividades (
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
                    tipo_geometria TEXT,
                    geometry geometry(Geometry, 4326)
                );
            """))
            conn.commit()
            
            # Crear índices
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_fecha ON actividades(fecha);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_departamento ON actividades(departamento);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_municipio ON actividades(municipio);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_geometry ON actividades USING GIST(geometry);"))
            conn.commit()
            
            # Verificar si la tabla se creó
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'actividades');"))
            exists = result.scalar()
            
            if exists:
                print("Tabla 'actividades' creada exitosamente")
                # Mostrar las columnas de la tabla
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'actividades'
                    ORDER BY ordinal_position;
                """))
                print("\nColumnas en la tabla actividades:")
                for row in result:
                    print(f"- {row[0]}: {row[1]}")
            else:
                print("Error: La tabla no se creó correctamente")
            
    except Exception as e:
        print(f"Error creando la tabla: {str(e)}")

def importar_datos_excel():
    # Cargar variables de entorno
    load_dotenv()
    
    # Configurar la conexión a la base de datos
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        # PRIMERO: Crear la tabla si no existe
        with engine.connect() as conn:
            # Habilitar PostGIS
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            
            # Crear la tabla con todas las columnas necesarias
            conn.execute(text("""
                DROP TABLE IF EXISTS actividades;
                CREATE TABLE actividades (
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
                    tipo_geometria TEXT,
                    geometry geometry(Geometry, 4326)
                );
            """))
            conn.commit()
            print("Tabla creada exitosamente")

        # Cargar shapefiles
        print("Cargando shapefiles...")
        veredas_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Veredas.shp')
        municipios_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Municipios.shp')
        departamentos_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Departamentos.shp')
        cabeceras_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/MGN_URB_AREA_CENSAL.shp')
        
        # Leer el archivo Excel
        print("Leyendo archivo Excel...")
        df = pd.read_excel('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/data/Consolidado_BD_actividades_EPM_historico.xlsx', 
                          sheet_name='BD_Consolidada')
        
        # Convertir total_asistentes a entero
        print("Limpiando datos...")
        df['total_asistentes'] = df['total_asistentes'].fillna(0).astype(int)
        
        print("Procesando geometrías...")
        geometrias = []
        tipos_geometria = []
        total = len(df)
        
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"Procesando registro {idx + 1} de {total}")
            geom, tipo = obtener_geometria(row, veredas_gdf, municipios_gdf, departamentos_gdf, cabeceras_gdf)
            geometrias.append(geom)
            tipos_geometria.append(tipo)
        
        # Agregar la columna de tipo de geometría al DataFrame
        df['tipo_geometria'] = tipos_geometria
        
        # Crear GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=geometrias,
            crs="EPSG:4326"
        )
        
        # Guardar en la base de datos
        print("Guardando en la base de datos...")
        gdf.to_postgis(
            name='actividades',
            con=engine,
            if_exists='append',
            index=False
        )
        
        print("Datos importados exitosamente")
        print(f"Total de registros importados: {len(gdf)}")
        print(f"Registros con ubicación exitosa: {len(gdf.dropna(subset=['geometry']))}")
        
        # Mostrar resumen de tipos de geometría
        print("\nResumen de tipos de geometría:")
        print(gdf['tipo_geometria'].value_counts())
        
    except Exception as e:
        print(f"Error durante la importación: {str(e)}")
        raise

def verificar_excel(ruta_excel):
    print("Iniciando verificación del Excel...")
    # Leer el Excel especificando el nombre de la hoja
    df = pd.read_excel(ruta_excel, sheet_name='BD_Consolidada')
    
    # Primero, mostrar todas las columnas que tiene el Excel
    print("\nColumnas encontradas en el Excel:")
    print(df.columns.tolist())
    
    # 1. Verificar columnas requeridas
    columnas_requeridas = [
        'contrato', 'ano', 'mes', 'fecha', 'departamento', 
        'municipio', 'ubicacion', 'grupo_interes',
        'grupo_intervencion', 'descripcion_actividad', 
        'categoria_actividad', 'categoria_unica', 'total_asistentes'
    ]
    faltantes = [col for col in columnas_requeridas if col.lower() not in [c.lower() for c in df.columns]]
    if faltantes:
        print(f"\nERROR: Faltan las siguientes columnas: {faltantes}")
    
    # 2. Verificar valores nulos en campos críticos
    campos_criticos = ['departamento', 'municipio', 'fecha']
    for campo in campos_criticos:
        nulos = df[campo].isnull().sum()
        if nulos > 0:
            print(f"ADVERTENCIA: {nulos} registros tienen valores nulos en {campo}")
    
    print("\nVerificación completada!")

def verificar_shapefiles():
    print("\nVerificando shapefiles...")
    
    # Cargar shapefiles
    veredas_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Veredas.shp')
    municipios_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Municipios.shp')
    departamentos_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/Departamentos.shp')
    cabeceras_gdf = gpd.read_file('C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/shapefile/MGN_URB_AREA_CENSAL.shp')
    
    print("\nColumnas en Veredas:")
    print(veredas_gdf.columns.tolist())
    
    print("\nColumnas en Municipios:")
    print(municipios_gdf.columns.tolist())
    
    print("\nColumnas en Departamentos:")
    print(departamentos_gdf.columns.tolist())
    
    print("\nColumnas en Cabeceras:")
    print(cabeceras_gdf.columns.tolist())

if __name__ == "__main__":
    ruta_excel = 'C:/PHI_2025/Scripts_2025/Dashboard_BD_PHI/data/Consolidado_BD_actividades_EPM_historico.xlsx'
    verificar_excel(ruta_excel)
    print("\nIniciando importación de datos...")
    importar_datos_excel()
    verificar_shapefiles() 