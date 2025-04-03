import geopandas as gpd
from sqlalchemy import create_engine, text
import folium
from dotenv import load_dotenv
import os
import webbrowser
from branca.colormap import LinearColormap

def visualizar_geometrias_detalladas():
    # Cargar variables de entorno
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    try:
        # Leer datos de la tabla actividades con geometrías
        print("Leyendo datos de las tablas...")
        
        # Consulta para obtener actividades por tipo de geometría
        query = """
        SELECT grupo_interes, tipo_geometria, geometry, COUNT(*) as total_actividades
        FROM actividades 
        WHERE geometry IS NOT NULL 
        AND tipo_geometria IN ('vereda', 'cabecera')
        GROUP BY grupo_interes, tipo_geometria, geometry;
        """
        
        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        print(f"\nTotal de geometrías únicas: {len(gdf)}")
        print("\nDistribución por tipo de geometría:")
        print(gdf['tipo_geometria'].value_counts())
        
        # Crear mapa base centrado en Colombia
        m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
        
        # Crear colormaps para cada tipo de geometría
        colormap_veredas = LinearColormap(
            colors=['#fee8c8', '#fdbb84', '#e34a33'],
            vmin=gdf[gdf['tipo_geometria'] == 'vereda']['total_actividades'].min(),
            vmax=gdf[gdf['tipo_geometria'] == 'vereda']['total_actividades'].max(),
            caption='Número de actividades en veredas'
        )
        
        colormap_cabeceras = LinearColormap(
            colors=['#edf8fb', '#b2e2e2', '#066d7d'],
            vmin=gdf[gdf['tipo_geometria'] == 'cabecera']['total_actividades'].min(),
            vmax=gdf[gdf['tipo_geometria'] == 'cabecera']['total_actividades'].max(),
            caption='Número de actividades en cabeceras'
        )
        
        # Agregar capa de veredas
        veredas = gdf[gdf['tipo_geometria'] == 'vereda']
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
            colormap_veredas.add_to(m)
        
        # Agregar capa de cabeceras
        cabeceras = gdf[gdf['tipo_geometria'] == 'cabecera']
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
            colormap_cabeceras.add_to(m)
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Guardar el mapa
        output_file = "mapa_geometrias_detalladas.html"
        m.save(output_file)
        
        print(f"\nAbriendo mapa en el navegador...")
        webbrowser.open('file://' + os.path.realpath(output_file))
        
    except Exception as e:
        print(f"Error durante la visualización: {str(e)}")
        raise

if __name__ == "__main__":
    visualizar_geometrias_detalladas() 