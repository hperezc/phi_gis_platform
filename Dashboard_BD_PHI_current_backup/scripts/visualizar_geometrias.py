import geopandas as gpd
from sqlalchemy import create_engine, text
import folium
from dotenv import load_dotenv
import os
import webbrowser

def visualizar_geometrias():
    # Cargar variables de entorno
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        # Leer datos de las tablas con una consulta más específica
        print("Leyendo datos de las tablas...")
        
        # Verificar primero el contenido de las tablas
        with engine.connect() as conn:
            # Verificar municipios
            result = conn.execute(text("SELECT COUNT(*) FROM actividades_municipios WHERE geometry IS NOT NULL"))
            count_mun = result.scalar()
            print(f"Registros con geometría en tabla municipios: {count_mun}")
            
            # Verificar departamentos
            result = conn.execute(text("SELECT COUNT(*) FROM actividades_departamentos WHERE geometry IS NOT NULL"))
            count_dep = result.scalar()
            print(f"Registros con geometría en tabla departamentos: {count_dep}")
        
        # Leer los datos con transformación de coordenadas
        municipios = gpd.read_postgis(
            """
            SELECT municipio, 
                   ST_Transform(geometry, 4326) as geometry
            FROM actividades_municipios 
            WHERE geometry IS NOT NULL 
            GROUP BY municipio, geometry;
            """, 
            engine, 
            geom_col='geometry'
        )
        
        departamentos = gpd.read_postgis(
            """
            SELECT departamento, 
                   ST_Transform(geometry, 4326) as geometry
            FROM actividades_departamentos 
            WHERE geometry IS NOT NULL 
            GROUP BY departamento, geometry;
            """, 
            engine, 
            geom_col='geometry'
        )
        
        print(f"\nGeometrías cargadas:")
        print(f"Municipios únicos: {len(municipios)}")
        print(f"Departamentos únicos: {len(departamentos)}")
        
        # Verificar tipos de geometría
        print("\nTipos de geometría:")
        if not municipios.empty:
            print("Municipios:", municipios.geometry.type.unique())
        if not departamentos.empty:
            print("Departamentos:", departamentos.geometry.type.unique())
        
        # Verificar bounds (límites) de las geometrías
        print("\nLímites de las geometrías:")
        if not municipios.empty:
            print("Municipios:", municipios.total_bounds)
        if not departamentos.empty:
            print("Departamentos:", departamentos.total_bounds)
        
        # Crear mapa base centrado en Colombia
        m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
        
        # Agregar capa de departamentos
        if not departamentos.empty:
            folium.GeoJson(
                departamentos.__geo_interface__,
                name='Departamentos',
                style_function=lambda x: {
                    'fillColor': '#ff7800',
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.1
                },
                tooltip=folium.GeoJsonTooltip(fields=['departamento'])
            ).add_to(m)
        
        # Agregar capa de municipios
        if not municipios.empty:
            folium.GeoJson(
                municipios.__geo_interface__,
                name='Municipios',
                style_function=lambda x: {
                    'fillColor': '#0000ff',
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.3
                },
                tooltip=folium.GeoJsonTooltip(fields=['municipio'])
            ).add_to(m)
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Guardar el mapa
        output_file = "mapa_geometrias.html"
        m.save(output_file)
        
        print("\nMuestra de datos:")
        print("\nPrimeros 5 municipios:")
        print(municipios[['municipio']].head())
        print("\nPrimeros 5 departamentos:")
        print(departamentos[['departamento']].head())
        
        print(f"\nAbriendo mapa en el navegador...")
        webbrowser.open('file://' + os.path.realpath(output_file))
        
    except Exception as e:
        print(f"Error durante la visualización: {str(e)}")
        raise

if __name__ == "__main__":
    visualizar_geometrias() 