import geopandas as gpd
from sqlalchemy import create_engine, text
import folium
from dotenv import load_dotenv
import os
import webbrowser
from branca.colormap import LinearColormap

def visualizar_todas_geometrias():
    # Cargar variables de entorno
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        print("Leyendo datos de las tablas...")
        
        # Leer datos de las tres tablas
        # 1. Geometrías detalladas (veredas y cabeceras)
        query_detallada = """
        SELECT grupo_interes, tipo_geometria, geometry, COUNT(*) as total_actividades
        FROM actividades 
        WHERE geometry IS NOT NULL 
        AND tipo_geometria IN ('vereda', 'cabecera')
        GROUP BY grupo_interes, tipo_geometria, geometry;
        """
        gdf_detallada = gpd.read_postgis(query_detallada, engine, geom_col='geometry')
        
        # 2. Municipios
        query_municipios = """
        SELECT municipio, departamento, geometry, COUNT(*) as total_actividades
        FROM actividades_municipios 
        WHERE geometry IS NOT NULL 
        GROUP BY municipio, departamento, geometry;
        """
        gdf_municipios = gpd.read_postgis(query_municipios, engine, geom_col='geometry')
        
        # 3. Departamentos
        query_departamentos = """
        SELECT departamento, geometry, COUNT(*) as total_actividades
        FROM actividades_departamentos 
        WHERE geometry IS NOT NULL 
        GROUP BY departamento, geometry;
        """
        gdf_departamentos = gpd.read_postgis(query_departamentos, engine, geom_col='geometry')
        
        # Imprimir estadísticas
        print("\n=== Estadísticas de geometrías ===")
        print(f"Geometrías detalladas: {len(gdf_detallada)}")
        print("Por tipo:", gdf_detallada['tipo_geometria'].value_counts().to_dict())
        print(f"Municipios únicos: {len(gdf_municipios)}")
        print(f"Departamentos únicos: {len(gdf_departamentos)}")
        
        # Crear mapa base
        m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
        
        # Crear colormaps
        colormap_veredas = LinearColormap(
            colors=['#fee8c8', '#fdbb84', '#e34a33'],
            vmin=gdf_detallada[gdf_detallada['tipo_geometria'] == 'vereda']['total_actividades'].min(),
            vmax=gdf_detallada[gdf_detallada['tipo_geometria'] == 'vereda']['total_actividades'].max(),
            caption='Actividades en veredas'
        )
        
        colormap_cabeceras = LinearColormap(
            colors=['#edf8fb', '#b2e2e2', '#066d7d'],
            vmin=gdf_detallada[gdf_detallada['tipo_geometria'] == 'cabecera']['total_actividades'].min(),
            vmax=gdf_detallada[gdf_detallada['tipo_geometria'] == 'cabecera']['total_actividades'].max(),
            caption='Actividades en cabeceras'
        )
        
        colormap_municipios = LinearColormap(
            colors=['#f7fcb9', '#addd8e', '#31a354'],
            vmin=gdf_municipios['total_actividades'].min(),
            vmax=gdf_municipios['total_actividades'].max(),
            caption='Actividades por municipio'
        )
        
        colormap_departamentos = LinearColormap(
            colors=['#fde0dd', '#fa9fb5', '#c51b8a'],
            vmin=gdf_departamentos['total_actividades'].min(),
            vmax=gdf_departamentos['total_actividades'].max(),
            caption='Actividades por departamento'
        )
        
        # Agregar capa de departamentos
        folium.GeoJson(
            gdf_departamentos.__geo_interface__,
            name='Departamentos',
            style_function=lambda x: {
                'fillColor': colormap_departamentos(x['properties']['total_actividades']),
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['departamento', 'total_actividades'],
                aliases=['Departamento:', 'Total Actividades:'],
                localize=True
            )
        ).add_to(m)
        
        # Agregar capa de municipios
        folium.GeoJson(
            gdf_municipios.__geo_interface__,
            name='Municipios',
            style_function=lambda x: {
                'fillColor': colormap_municipios(x['properties']['total_actividades']),
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['municipio', 'departamento', 'total_actividades'],
                aliases=['Municipio:', 'Departamento:', 'Total Actividades:'],
                localize=True
            )
        ).add_to(m)
        
        # Agregar capas detalladas
        # Veredas
        veredas = gdf_detallada[gdf_detallada['tipo_geometria'] == 'vereda']
        if not veredas.empty:
            folium.GeoJson(
                veredas.__geo_interface__,
                name='Veredas',
                style_function=lambda x: {
                    'fillColor': colormap_veredas(x['properties']['total_actividades']),
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['grupo_interes', 'total_actividades'],
                    aliases=['Vereda:', 'Total Actividades:'],
                    localize=True
                )
            ).add_to(m)
        
        # Cabeceras
        cabeceras = gdf_detallada[gdf_detallada['tipo_geometria'] == 'cabecera']
        if not cabeceras.empty:
            folium.GeoJson(
                cabeceras.__geo_interface__,
                name='Cabeceras',
                style_function=lambda x: {
                    'fillColor': colormap_cabeceras(x['properties']['total_actividades']),
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['grupo_interes', 'total_actividades'],
                    aliases=['Cabecera:', 'Total Actividades:'],
                    localize=True
                )
            ).add_to(m)
        
        # Agregar todas las leyendas
        colormap_departamentos.add_to(m)
        colormap_municipios.add_to(m)
        colormap_veredas.add_to(m)
        colormap_cabeceras.add_to(m)
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Guardar y abrir el mapa
        output_file = "mapa_todas_geometrias.html"
        m.save(output_file)
        
        print(f"\nAbriendo mapa en el navegador...")
        webbrowser.open('file://' + os.path.realpath(output_file))
        
    except Exception as e:
        print(f"Error durante la visualización: {str(e)}")
        raise

if __name__ == "__main__":
    visualizar_todas_geometrias() 