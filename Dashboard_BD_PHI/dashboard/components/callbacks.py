from dash import Input, Output, State, callback_context
import plotly.graph_objects as go
from ..utils.database import (
    get_db_engine, 
    get_filter_options, 
    get_kpi_data,
    get_map_data, 
    get_detailed_data, 
    get_temporal_analysis,
    get_distribution_analysis, 
    get_comparative_analysis
)
from ..config.settings import DATABASE_URL, MAPBOX_TOKEN, THEME
import io
import pandas as pd
import dash
from datetime import datetime, timedelta
from dash import dcc
import folium
from branca.colormap import LinearColormap
import webbrowser
import os
import tempfile
from dash import html
import geopandas as gpd
import plotly.express as px
from plotly.subplots import make_subplots
import json
import numpy as np

MAPBOX_TOKEN = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBtIVaj52w2yw-7ewLU6Q'  # Reemplaza con tu token de Mapbox

# Definir el common_layout sin height
common_layout = {
    'paper_bgcolor': 'white',
    'plot_bgcolor': 'white',
    'margin': dict(l=10, r=10, t=40, b=10),
    'showlegend': False,
    'font': {'family': 'Roboto'},
    'xaxis': dict(
        showgrid=True,
        gridwidth=1,
        gridcolor=THEME['grid']
    ),
    'yaxis': dict(
        showgrid=True,
        gridwidth=1,
        gridcolor=THEME['grid']
    )
}

def update_map(map_type, map_level, basemap_style, df):
    """Crea diferentes tipos de visualizaciones de mapa según el tipo seleccionado"""
    if df.empty:
        return go.Figure().update_layout(
            title="No hay datos disponibles para los filtros seleccionados",
            title_x=0.5
        )

    try:
        # Definir zoom_level al inicio de la función
        zoom_level = 8 if map_level in ['veredas', 'cabeceras'] else 5
        
        # Proyectar las geometrías a Web Mercator para mejor visualización
        df_proj = df.to_crs(epsg=3857)
        fig = go.Figure()

        if map_type == 'points':
            # Mapa de puntos con tamaño variable según actividades
            centroids = df_proj.geometry.centroid.to_crs(epsg=4326)
            marker_sizes = normalize_sizes(df['total_actividades'], min_size=5, max_size=20)
            
            fig.add_trace(go.Scattermapbox(
                lat=centroids.y,
                lon=centroids.x,
                mode='markers',
                marker=dict(
                    size=marker_sizes,
                    color=df['total_asistentes'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Total Asistentes')
                ),
                text=create_hover_text(df),
                hoverinfo='text'
            ))
        elif map_type == 'heat':
            # Mapa de calor
            centroids = df_proj.geometry.centroid.to_crs(epsg=4326)
            fig.add_trace(go.Densitymapbox(
                lat=centroids.y,
                lon=centroids.x,
                z=df['total_actividades'],
                radius=20,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Densidad de Actividades')
            ))
        else:  # choropleth
            # Convertir a GeoJSON en WGS84 (4326)
            df_4326 = df_proj.to_crs(epsg=4326)
            
            # Agregar el mapa coroplético
            fig.add_trace(go.Choroplethmapbox(
                geojson=json.loads(df_4326.to_json()),
                locations=df_4326.index,
                z=df_4326['total_actividades'],
                colorscale='Viridis',
                marker=dict(
                    opacity=0.7,
                    line_width=1,
                    line_color='white'
                ),
                text=[
                    f"Ubicación: {row['nombre']}<br>"
                    f"Departamento: {row['departamento']}<br>"
                    f"Total Actividades: {row['total_actividades']}<br>"
                    f"Total Asistentes: {row['total_asistentes']}"
                    for _, row in df_4326.iterrows()
                ],
                hoverinfo='text',
                showscale=True,
                colorbar=dict(title='Total Actividades')
            ))

        # Configuración del mapa
        mapbox_config = {
            'style': basemap_style,
            'center': dict(lat=4.5709, lon=-74.2973),
            'zoom': zoom_level
        }

        if 'mapbox://' in str(basemap_style):
            mapbox_config['accesstoken'] = MAPBOX_TOKEN

        fig.update_layout(
            mapbox=mapbox_config,
            margin=dict(l=0, r=0, t=30, b=0),
            height=600,
            title=f"Distribución de Actividades - {map_level.capitalize()}"
        )

        return fig

    except Exception as e:
        print(f"Error en update_map: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure().update_layout(
            title=f"Error al generar el mapa: {str(e)}",
            title_x=0.5
        )

def create_hover_text(df):
    """Crea el texto para el hover del mapa"""
    hover_text = []
    for idx, row in df.iterrows():
        if 'municipio' in row and row['municipio']:
            location = f"Municipio: {row['municipio']}"
        else:
            location = f"Ubicación: {row['nombre']}"
            
        text = (
            f"{location}<br>"
            f"Departamento: {row['departamento']}<br>"
            f"Total Actividades: {row['total_actividades']}<br>"
            f"Total Asistentes: {row['total_asistentes']}<br>"
            f"Promedio Asistentes: {row['promedio_asistentes']:.1f}<br>"
            f"Total Grupos: {row['total_grupos']}"
        )
        hover_text.append(text)
    return hover_text

def normalize_sizes(series, min_size=5, max_size=20):
    """
    Normaliza los valores de una serie para usar como tamaños de marcadores
    """
    if len(series) == 0 or series.max() == series.min():
        return [min_size] * len(series)
    return min_size + (series - series.min()) * (max_size - min_size) / (series.max() - series.min())

def create_charts(df):
    """Crea los gráficos básicos mejorados"""
    if df.empty:
        print("DataFrame está vacío")
        return [go.Figure()] * 4
    
    try:
        # Debug: Verificar las columnas disponibles
        print("Columnas disponibles:", df.columns.tolist())
        
        # 1. Gráfico de Categorías: Treemap con etiquetas únicas
        try:
            # Agregación de datos
            df_cat = df.groupby(['categoria_unica', 'categoria_actividad'], 
                              as_index=False)['id'].count()
            df_cat.columns = ['categoria_unica', 'categoria_actividad', 'total']
            
            # Definir colores base (oscuros) para categorías únicas
            color_map = {
                'Talleres': {
                    'base': '#1a237e',  # Azul oscuro
                    'light': '#7986cb'   # Azul claro
                },
                'Simulacros': {
                    'base': '#b71c1c',  # Rojo oscuro
                    'light': '#ef5350'   # Rojo claro
                },
                'Divulgaciones': {
                    'base': '#1b5e20',  # Verde oscuro
                    'light': '#81c784'   # Verde claro
                },
                'Kits': {
                    'base': '#e65100',  # Naranja oscuro
                    'light': '#ffb74d'   # Naranja claro
                },
                'Planes comunitarios': {
                    'base': '#006064',  # Cyan oscuro
                    'light': '#4dd0e1'   # Cyan claro
                },
                'Apoyo a simulacro': {
                    'base': '#4a148c',  # Púrpura oscuro
                    'light': '#ab47bc'   # Púrpura claro
                }
            }
            
            # Crear IDs únicos
            df_cat['id'] = df_cat.apply(
                lambda x: f"{x['categoria_unica']}_{x['categoria_actividad']}", 
                axis=1
            )
            
            # Preparar las listas para el treemap
            labels = []
            parents = []
            values = []
            ids = []
            colors = []
            
            # Primero agregar las categorías únicas (nivel 1) con colores oscuros
            for cat in df_cat['categoria_unica'].unique():
                labels.append(cat)
                parents.append('')
                values.append(df_cat[df_cat['categoria_unica'] == cat]['total'].sum())
                ids.append(cat)
                colors.append(color_map.get(cat, {'base': '#37474f'})['base'])  # Color oscuro
            
            # Luego agregar las categorías de actividad (nivel 2) con colores claros
            for _, row in df_cat.iterrows():
                labels.append(row['categoria_actividad'])
                parents.append(row['categoria_unica'])
                values.append(row['total'])
                ids.append(row['id'])
                # Usar el color claro correspondiente a la categoría única
                colors.append(color_map.get(row['categoria_unica'], 
                                         {'light': '#90a4ae'})['light'])
            
            # Crear el treemap
            fig_cat = go.Figure(go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues='total',
                textinfo='label+value',
                hovertemplate='<b>%{label}</b><br>' +
                            'Total: %{value}<br>' +
                            '<extra></extra>',
                marker=dict(
                    colors=colors,
                    line=dict(width=2, color='white')
                ),
                pathbar=dict(
                    visible=True,
                    thickness=20
                )
            ))

            # Configuración del layout con márgenes ajustados
            fig_cat.update_layout(
                title={
                    'text': 'Distribución de Actividades por Categoría',
                    'y': 0.98,  # Subimos un poco el título
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=16)
                },
                height=600,
                margin=dict(
                    t=70,  # Aumentamos el margen superior para la barra de navegación
                    l=25,
                    r=25,
                    b=25
                ),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

        except Exception as e:
            print(f"\n!!! Error en la creación del treemap: {str(e)}")
            import traceback
            traceback.print_exc()
            fig_cat = go.Figure()
        
        print("\nVerificación de figuras:")
        print("fig_cat data:", bool(fig_cat.data))
        print("fig_cat layout:", bool(fig_cat.layout))
        
        # 2. Gráfico Temporal: Corregir el warning de deprecación
        df['fecha'] = pd.to_datetime(df['fecha'])
        df_trend = df.groupby(pd.Grouper(key='fecha', freq='ME')).agg({  # Cambiado de 'M' a 'ME'
            'id': 'count',
            'total_asistentes': 'sum'
        }).reset_index()
        
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_trend.add_trace(
            go.Bar(
                x=df_trend['fecha'],
                y=df_trend['id'],
                name="Actividades",
                marker_color=THEME['primary'],
                opacity=0.7
            ),
            secondary_y=False
        )
        
        fig_trend.add_trace(
            go.Scatter(
                x=df_trend['fecha'],
                y=df_trend['total_asistentes'],
                name="Asistentes",
                line=dict(color=THEME['secondary'], width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig_trend.update_layout(
            title='Tendencia de Actividades y Asistentes',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig_trend.update_yaxes(
            title_text="Número de Actividades",
            secondary_y=False
        )
        fig_trend.update_yaxes(
            title_text="Número de Asistentes",
            secondary_y=True
        )
        
        # 3. Gráfico de Grupos: Sunburst
        df_groups = df.groupby(['zona_geografica', 'grupo_interes'], as_index=False).agg({
            'id': 'count',
            'total_asistentes': 'sum'
        }).rename(columns={'id': 'total_actividades'})
        
        fig_groups = go.Figure(go.Sunburst(
            ids=[f"{row['zona_geografica']}_{row['grupo_interes']}" for _, row in df_groups.iterrows()] + 
                list(df_groups['zona_geografica'].unique()),
            labels=list(df_groups['grupo_interes']) + list(df_groups['zona_geografica'].unique()),
            parents=[row['zona_geografica'] for _, row in df_groups.iterrows()] + 
                    [''] * len(df_groups['zona_geografica'].unique()),
            values=list(df_groups['total_actividades']) + 
                   [df_groups[df_groups['zona_geografica'] == zona]['total_actividades'].sum() 
                    for zona in df_groups['zona_geografica'].unique()],
            branchvalues='total',
            hovertemplate='<b>%{label}</b><br>' +
                         'Actividades: %{value}<br>' +
                         '<extra></extra>'
        ))
        
        fig_groups.update_layout(
            title='Distribución de Grupos de Interés por Zona',
            margin=dict(t=50, l=25, r=25, b=25)
        )
        
        # 4. Gráfico de Departamentos: Mapa de calor
        df_dept = df.pivot_table(
            index='departamento',
            columns=pd.Grouper(key='fecha', freq='M'),
            values='id',
            aggfunc='count',
            fill_value=0
        )
        
        fig_dept = go.Figure(go.Heatmap(
            z=df_dept.values,
            x=df_dept.columns.strftime('%Y-%m'),
            y=df_dept.index,
            colorscale='Blues',
            hoverongaps=False,
            hovertemplate='<b>Departamento:</b> %{y}<br>' +
                         '<b>Fecha:</b> %{x}<br>' +
                         '<b>Actividades:</b> %{z}<br>' +
                         '<extra></extra>'
        ))
        
        fig_dept.update_layout(
            title='Intensidad de Actividades por Departamento y Mes',
            xaxis_title='Mes',
            yaxis_title='Departamento',
            margin=dict(l=150)
        )
        
        return [fig_cat, fig_trend, fig_groups, fig_dept]
        
    except Exception as e:
        print(f"Error en create_charts: {str(e)}")
        import traceback
        traceback.print_exc()
        return [go.Figure()] * 4

def get_fullscreen_map_data(start_date, end_date, ano, zona, depto, categoria, grupo):
    """Obtiene los datos de todas las geometrías para el mapa en pantalla completa"""
    engine = get_db_engine()
    
    # Query para departamentos
    query_departamentos = """
    SELECT d.departamento, d.geometry, COUNT(*) as total_actividades
    FROM actividades_departamentos d
    JOIN actividades a ON d.departamento = a.departamento
    WHERE d.geometry IS NOT NULL 
    AND (%(start_date)s IS NULL OR a.fecha >= %(start_date)s)
    AND (%(end_date)s IS NULL OR a.fecha <= %(end_date)s)
    AND (%(ano)s IS NULL OR EXTRACT(YEAR FROM a.fecha) = %(ano)s)
    AND (%(zona)s IS NULL OR a.zona_geografica = %(zona)s)
    AND (%(depto)s IS NULL OR a.departamento = %(depto)s)
    AND (%(categoria)s IS NULL OR a.categoria_unica = %(categoria)s)
    AND (%(grupo)s IS NULL OR a.grupo_interes = %(grupo)s)
    GROUP BY d.departamento, d.geometry;
    """
    
    # Query para municipios
    query_municipios = """
    SELECT m.municipio, m.departamento, m.geometry, COUNT(*) as total_actividades
    FROM actividades_municipios m
    JOIN actividades a ON m.municipio = a.municipio AND m.departamento = a.departamento
    WHERE m.geometry IS NOT NULL 
    AND (%(start_date)s IS NULL OR a.fecha >= %(start_date)s)
    AND (%(end_date)s IS NULL OR a.fecha <= %(end_date)s)
    AND (%(ano)s IS NULL OR EXTRACT(YEAR FROM a.fecha) = %(ano)s)
    AND (%(zona)s IS NULL OR a.zona_geografica = %(zona)s)
    AND (%(depto)s IS NULL OR a.departamento = %(depto)s)
    AND (%(categoria)s IS NULL OR a.categoria_unica = %(categoria)s)
    AND (%(grupo)s IS NULL OR a.grupo_interes = %(grupo)s)
    GROUP BY m.municipio, m.departamento, m.geometry;
    """
    
    # Query para geometrías detalladas (veredas y cabeceras)
    query_detallada = """
    SELECT a.grupo_interes, a.tipo_geometria, a.geometry, COUNT(*) as total_actividades
    FROM actividades a
    WHERE a.geometry IS NOT NULL 
    AND a.tipo_geometria IN ('vereda', 'cabecera')
    AND (%(start_date)s IS NULL OR a.fecha >= %(start_date)s)
    AND (%(end_date)s IS NULL OR a.fecha <= %(end_date)s)
    AND (%(ano)s IS NULL OR EXTRACT(YEAR FROM a.fecha) = %(ano)s)
    AND (%(zona)s IS NULL OR a.zona_geografica = %(zona)s)
    AND (%(depto)s IS NULL OR a.departamento = %(depto)s)
    AND (%(categoria)s IS NULL OR a.categoria_unica = %(categoria)s)
    AND (%(grupo)s IS NULL OR a.grupo_interes = %(grupo)s)
    GROUP BY a.grupo_interes, a.tipo_geometria, a.geometry;
    """
    
    params = {
        'start_date': start_date,
        'end_date': end_date,
        'ano': ano,
        'zona': zona,
        'depto': depto,
        'categoria': categoria,
        'grupo': grupo
    }
    
    # Leer datos de las tres tablas
    gdf_departamentos = gpd.read_postgis(query_departamentos, engine, geom_col='geometry', params=params)
    gdf_municipios = gpd.read_postgis(query_municipios, engine, geom_col='geometry', params=params)
    gdf_detallada = gpd.read_postgis(query_detallada, engine, geom_col='geometry', params=params)
    
    return gdf_departamentos, gdf_municipios, gdf_detallada

def create_fullscreen_map(df_departamentos, df_municipios, df_detallada):
    """Crea un mapa de Folium con todas las capas y controles"""
    m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
    
    # Crear colormaps
    colormap_departamentos = LinearColormap(
        colors=['#fde0dd', '#fa9fb5', '#c51b8a'],
        vmin=df_departamentos['total_actividades'].min(),
        vmax=df_departamentos['total_actividades'].max(),
        caption='Actividades por departamento'
    )
    
    colormap_municipios = LinearColormap(
        colors=['#f7fcb9', '#addd8e', '#31a354'],
        vmin=df_municipios['total_actividades'].min(),
        vmax=df_municipios['total_actividades'].max(),
        caption='Actividades por municipio'
    )
    
    # Colormaps para veredas y cabeceras si existen datos
    if not df_detallada.empty:
        veredas = df_detallada[df_detallada['tipo_geometria'] == 'vereda']
        cabeceras = df_detallada[df_detallada['tipo_geometria'] == 'cabecera']
        
        if not veredas.empty:
            colormap_veredas = LinearColormap(
                colors=['#fee8c8', '#fdbb84', '#e34a33'],
                vmin=veredas['total_actividades'].min(),
                vmax=veredas['total_actividades'].max(),
                caption='Actividades en veredas'
            )
        
        if not cabeceras.empty:
            colormap_cabeceras = LinearColormap(
                colors=['#edf8fb', '#b2e2e2', '#066d7d'],
                vmin=cabeceras['total_actividades'].min(),
                vmax=cabeceras['total_actividades'].max(),
                caption='Actividades en cabeceras'
            )
    
    # Agregar capas al mapa
    # 1. Departamentos
    folium.GeoJson(
        df_departamentos.__geo_interface__,
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
    
    # 2. Municipios
    folium.GeoJson(
        df_municipios.__geo_interface__,
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
    
    # 3. Veredas y Cabeceras
    if not df_detallada.empty:
        # Veredas
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
    
    # Agregar leyendas
    colormap_departamentos.add_to(m)
    colormap_municipios.add_to(m)
    if not df_detallada.empty:
        if not veredas.empty:
            colormap_veredas.add_to(m)
        if not cabeceras.empty:
            colormap_cabeceras.add_to(m)
    
    # Agregar control de capas
    folium.LayerControl().add_to(m)
    
    return m

def create_temporal_charts(df_temporal):
    """Crea los gráficos de análisis temporal"""
    if df_temporal.empty:
        return [go.Figure()] * 2
    
    common_layout = {
        'height': 400,
        'margin': dict(l=50, r=20, t=50, b=30),
        'paper_bgcolor': 'white',
        'plot_bgcolor': 'white',
        'hovermode': 'x unified',
        'hoverlabel': dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        'xaxis': dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211,211,211,0.3)',
            zeroline=False
        ),
        'yaxis': dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211,211,211,0.3)',
            zeroline=False
        )
    }
    
    # Gráfico de tendencia detallada
    fig_temporal = go.Figure()
    fig_temporal.add_trace(go.Scatter(
        x=df_temporal['semana'],
        y=df_temporal['total_actividades'],
        name='Actividades',
        line=dict(color=THEME['primary'], width=2),
        hovertemplate="<b>Semana:</b> %{x|%d/%m/%Y}<br>" +
                     "<b>Actividades:</b> %{y:,.0f}<br>" +
                     "<extra></extra>"
    ))
    fig_temporal.add_trace(go.Scatter(
        x=df_temporal['semana'],
        y=df_temporal['municipios_cubiertos'],
        name='Municipios',
        line=dict(color=THEME['secondary'], width=2),
        hovertemplate="<b>Semana:</b> %{x|%d/%m/%Y}<br>" +
                     "<b>Municipios:</b> %{y:,.0f}<br>" +
                     "<extra></extra>"
    ))
    fig_temporal.update_layout(
        title=dict(
            text='Evolución Temporal de Actividades y Cobertura',
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=16)
        ),
        xaxis_title='Fecha',
        yaxis_title='Cantidad',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(211,211,211,0.5)',
            borderwidth=1
        ),
        **common_layout
    )
    
    # Gráfico de tendencia acumulada
    fig_acumulada = go.Figure()
    fig_acumulada.add_trace(go.Scatter(
        x=df_temporal['semana'],
        y=df_temporal['total_asistentes'].cumsum(),
        name='Asistentes Acumulados',
        fill='tonexty',
        line=dict(color=THEME['primary'], width=2),
        hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                     "<b>Total Asistentes:</b> %{y:,.0f}<br>" +
                     "<extra></extra>"
    ))
    fig_acumulada.update_layout(
        title=dict(
            text='Asistentes Acumulados en el Tiempo',
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=16)
        ),
        xaxis_title='Fecha',
        yaxis_title='Total Asistentes Acumulados',
        **common_layout
    )
    
    return [fig_temporal, fig_acumulada]

def create_distribution_charts(df_dist):
    """Crea los gráficos de distribución y relación de variables"""
    if df_dist.empty:
        return [go.Figure()] * 2
    
    # Gráfico de caja y violín combinado por departamento
    fig_box = go.Figure()
    
    # Ordenar departamentos por mediana de asistentes
    dept_stats = df_dist.groupby('departamento').agg({
        'total_asistentes': ['median', 'count'],
        'total_actividades': 'sum'
    }).sort_values(('total_asistentes', 'median'), ascending=False)
    
    for dept in dept_stats.index:
        dept_data = df_dist[df_dist['departamento'] == dept]
        
        # Agregar violín
        fig_box.add_trace(go.Violin(
            x=[dept] * len(dept_data),
            y=dept_data['total_asistentes'],
            name=dept,
            side='positive',
            line_color=THEME['primary'],
            fillcolor=THEME['primary'],
            opacity=0.3,
            showlegend=False
        ))
        
        # Agregar caja
        fig_box.add_trace(go.Box(
            x=[dept] * len(dept_data),
            y=dept_data['total_asistentes'],
            name=dept,
            boxpoints='outliers',
            marker_color=THEME['primary'],
            line_color=THEME['primary'],
            showlegend=False,
            hovertemplate=(
                f"<b>{dept}</b><br>" +
                "Mediana: %{median:,.0f}<br>" +
                "Q1: %{q1:,.0f}<br>" +
                "Q3: %{q3:,.0f}<br>" +
                "Mínimo: %{min:,.0f}<br>" +
                "Máximo: %{max:,.0f}<br>" +
                f"Total Actividades: {dept_stats.loc[dept, ('total_actividades', 'sum')]:,.0f}<br>" +
                f"Municipios: {dept_stats.loc[dept, ('total_asistentes', 'count')]:,.0f}" +
                "<extra></extra>"
            )
        ))
    
    layout_box = {
        **common_layout,
        'title': 'Distribución de Asistentes por Departamento',
        'yaxis_title': 'Número de Asistentes',
        'xaxis_title': 'Departamento',
        'xaxis_tickangle': -45,
        'height': 500,
        'margin': dict(b=150, l=50, r=20, t=50),
        'showlegend': False,
        'violinmode': 'overlay',
        'boxmode': 'overlay'
    }
    
    fig_box.update_layout(layout_box)
    
    # Gráfico de burbujas mejorado
    fig_bubble = go.Figure()
    
    # Calcular métricas normalizadas para mejor visualización
    df_dist['eficiencia'] = df_dist['total_asistentes'] / df_dist['total_actividades']
    max_eficiencia = df_dist['eficiencia'].max()
    
    # Normalizar la eficiencia para controlar mejor el tamaño de las burbujas
    df_dist['tamaño_burbuja'] = (df_dist['eficiencia'] / max_eficiencia) * 100
    
    # Definir una paleta de colores más suave
    colors = px.colors.qualitative.Pastel
    
    # Agregar burbujas por departamento con diferentes colores
    for i, dept in enumerate(df_dist['departamento'].unique()):
        dept_data = df_dist[df_dist['departamento'] == dept]
        
        fig_bubble.add_trace(go.Scatter(
            x=dept_data['total_actividades'],
            y=dept_data['total_asistentes'],
            mode='markers',
            name=dept,
            marker=dict(
                size=dept_data['tamaño_burbuja'] * 0.4,  # Factor muy reducido
                sizemin=3,  # Tamaño mínimo más pequeño
                sizemode='area',
                sizeref=0.1,  # Referencia de tamaño más pequeña
                opacity=0.7,
                color=colors[i % len(colors)],
                line=dict(width=0.5, color='white')  # Borde más delgado
            ),
            text=dept_data['municipio'],
            hovertemplate=(
                "<b>%{text}</b><br>" +
                f"Departamento: {dept}<br>" +
                "Actividades: %{x:,.0f}<br>" +
                "Total Asistentes: %{y:,.0f}<br>" +
                "Promedio por actividad: %{customdata:,.1f}<br>" +
                "<extra></extra>"
            ),
            customdata=dept_data['eficiencia']
        ))
    
    layout_bubble = {
        **common_layout,
        'title': 'Relación entre Actividades y Asistentes por Municipio',
        'xaxis_title': 'Total de Actividades',
        'yaxis_title': 'Total de Asistentes',
        'height': 600,
        'margin': dict(l=50, r=50, t=50, b=50),
        'showlegend': True,
        'legend': dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        'hovermode': 'closest',
        'plot_bgcolor': 'rgba(240,240,240,0.2)',
        'xaxis': {
            **common_layout['xaxis'],
            'zeroline': True,
            'zerolinewidth': 1,
            'zerolinecolor': 'lightgray',
            'gridcolor': 'rgba(128,128,128,0.2)',
            'showline': True,
            'linewidth': 1,
            'linecolor': 'gray'
        },
        'yaxis': {
            **common_layout['yaxis'],
            'zeroline': True,
            'zerolinewidth': 1,
            'zerolinecolor': 'lightgray',
            'gridcolor': 'rgba(128,128,128,0.2)',
            'showline': True,
            'linewidth': 1,
            'linecolor': 'gray'
        }
    }
    
    fig_bubble.update_layout(layout_bubble)
    
    return [fig_box, fig_bubble]

def create_comparative_charts(df_comp):
    """Crea los gráficos comparativos mejorados"""
    if df_comp.empty:
        return [go.Figure()] * 2

    try:
        # 1. Gráfico de radar por zona
        fig_radar = go.Figure()
        
        # Agrupar por zona para el gráfico de radar
        df_zona = df_comp.groupby('zona_geografica').agg({
            'total_actividades': 'sum',
            'total_asistentes': 'sum',
            'total_municipios': 'max',
            'total_grupos': 'max',
            'total_contratos': 'max',
            'eficiencia': 'mean'
        }).reset_index()
        
        # Normalizar valores para el radar
        for zona in df_zona['zona_geografica']:
            values = []
            for col in ['total_actividades', 'total_asistentes', 'total_municipios', 
                       'total_grupos', 'total_contratos', 'eficiencia']:
                max_val = df_zona[col].max()
                val = df_zona[df_zona['zona_geografica'] == zona][col].iloc[0]
                values.append((val/max_val)*100 if max_val != 0 else 0)
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=['Actividades', 'Asistentes', 'Municipios', 
                       'Grupos', 'Contratos', 'Eficiencia'],
                name=zona,
                fill='toself',
                opacity=0.7
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title='Comparación de Métricas por Zona',
            height=500
        )
        
        # 2. Gráfico Sankey mejorado
        source = []
        target = []
        value = []
        
        # Preparar los nodos
        zonas = df_comp['zona_geografica'].unique()
        deptos = df_comp['departamento'].unique()
        categorias = df_comp['categoria_unica'].unique()  # Usamos categoria_unica en lugar de grupo_categoria
        
        # Mapear índices
        zona_idx = {zona: idx for idx, zona in enumerate(zonas)}
        depto_idx = {depto: idx + len(zonas) for idx, depto in enumerate(deptos)}
        cat_idx = {cat: idx + len(zonas) + len(deptos) for idx, cat in enumerate(categorias)}
        
        # Conexiones Zona -> Departamento
        for _, row in df_comp.groupby(['zona_geografica', 'departamento'])['total_actividades'].sum().reset_index().iterrows():
            source.append(zona_idx[row['zona_geografica']])
            target.append(depto_idx[row['departamento']])
            value.append(row['total_actividades'])
        
        # Conexiones Departamento -> Categoría
        for _, row in df_comp.groupby(['departamento', 'categoria_unica'])['total_actividades'].sum().reset_index().iterrows():
            source.append(depto_idx[row['departamento']])
            target.append(cat_idx[row['categoria_unica']])
            value.append(row['total_actividades'])
        
        # Crear el gráfico Sankey con etiquetas más pequeñas
        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=list(zonas) + list(deptos) + list(categorias),
                color=["#1f77b4"] * len(zonas) + 
                      ["#ff7f0e"] * len(deptos) + 
                      ["#2ca02c"] * len(categorias)
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=[f"rgba(169,169,169,{0.3 + (v/max(value))*0.7})" for v in value],
                hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>" +
                             "Actividades: %{value:,.0f}<br>" +
                             "<extra></extra>"
            )
        )])
        
        fig_sankey.update_layout(
            title=dict(
                text='Flujo de Actividades: Zonas → Departamentos → Categorías',
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            ),
            height=600,
            margin=dict(l=50, r=50, t=50, b=20)
        )
        
        return [fig_radar, fig_sankey]
        
    except Exception as e:
        print(f"Error en create_comparative_charts: {str(e)}")
        import traceback
        traceback.print_exc()
        return [go.Figure()] * 2

def create_animated_chart(df):
    """Crea un gráfico animado de burbujas que muestra la evolución acumulada de actividades por municipio"""
    if df.empty:
        return go.Figure()

    try:
        # Preparar los datos para la animación
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['año'] = df['fecha'].dt.year
        
        # Obtener todos los años y municipios únicos
        años = sorted(df['año'].unique())
        municipios = df[['municipio', 'departamento']].drop_duplicates()
        
        # Crear un DataFrame con todas las combinaciones de municipios y años
        index = pd.MultiIndex.from_product([
            municipios['municipio'],
            años
        ], names=['municipio', 'año'])
        
        # Crear DataFrame base con todas las combinaciones
        df_base = pd.DataFrame(index=index).reset_index()
        
        # Agregar departamento
        df_base = df_base.merge(municipios, on='municipio', how='left')
        
        # Agregar datos de actividades
        df_agg = df.groupby(['municipio', 'año']).agg({
            'id': 'count',
            'total_asistentes': 'sum',
            'grupo_interes': 'nunique'
        }).reset_index()
        
        # Combinar con el DataFrame base
        df_anim = df_base.merge(
            df_agg,
            on=['municipio', 'año'],
            how='left'
        ).fillna(0)  # Llenar NaN con 0
        
        # Renombrar columnas
        df_anim.columns = ['municipio', 'año', 'departamento', 'total_actividades', 
                          'total_asistentes', 'grupos_unicos']
        
        # Calcular valores acumulados por municipio
        df_anim = df_anim.sort_values(['municipio', 'año'])
        df_anim['total_actividades_acum'] = df_anim.groupby('municipio')['total_actividades'].cumsum()
        df_anim['total_asistentes_acum'] = df_anim.groupby('municipio')['total_asistentes'].cumsum()
        df_anim['grupos_unicos_acum'] = df_anim.groupby('municipio')['grupos_unicos'].cumsum()
        
        # Crear etiqueta personalizada para el hover
        df_anim['municipio_depto'] = df_anim['municipio'] + ' (' + df_anim['departamento'] + ')'
        
        # Asignar un color único a cada municipio
        municipios_unicos = df_anim['municipio'].unique()
        colores = px.colors.qualitative.Set3 * (len(municipios_unicos) // len(px.colors.qualitative.Set3) + 1)
        color_map = dict(zip(municipios_unicos, colores[:len(municipios_unicos)]))
        
        # Crear el gráfico animado con valores acumulados
        fig = px.scatter(
            df_anim,
            x='total_actividades_acum',
            y='total_asistentes_acum',
            animation_frame='año',
            animation_group='municipio',
            size='grupos_unicos_acum',
            color='municipio',
            hover_name='municipio_depto',
            color_discrete_map=color_map,
            hover_data={
                'total_actividades_acum': ':,.0f',
                'total_asistentes_acum': ':,.0f',
                'grupos_unicos_acum': True,
                'departamento': True,
                'año': True,
                'municipio': False,
                'municipio_depto': False
            },
            size_max=40,
            range_x=[0, df_anim['total_actividades_acum'].max() * 1.1],
            range_y=[0, df_anim['total_asistentes_acum'].max() * 1.1],
            labels={
                'total_actividades_acum': 'Total Actividades Acumuladas',
                'total_asistentes_acum': 'Total Asistentes Acumulados',
                'grupos_unicos_acum': 'Grupos de Interés Acumulados',
                'municipio': 'Municipio',
                'año': 'Año'
            }
        )

        # Personalizar la apariencia
        fig.update_layout(
            title={
                'text': 'Evolución Acumulada de Actividades y Asistentes por Municipio',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=16)
            },
            xaxis_title='Total Actividades Acumuladas',
            yaxis_title='Total Asistentes Acumulados',
            showlegend=True,
            paper_bgcolor='white',
            plot_bgcolor='rgba(240,240,240,0.2)',
            height=550,
            # Ajustar la posición y estilo de la leyenda
            legend=dict(
                title='Municipios',
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1,
                itemsizing='constant',
                font=dict(size=10)
            ),
            margin=dict(r=150, b=100),  # Aumentar margen inferior para el slider
            # Configurar un único botón de control de animación
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'y': 0,      # Ajustado para estar más arriba
                'x': 0.5,    # Centrado
                'xanchor': 'center',
                'yanchor': 'bottom',
                'pad': {'b': 10},  # Agregar padding inferior
                'buttons': [{
                    'label': '▶️ Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 1000, 'redraw': True},
                        'fromcurrent': True,
                        'transition': {'duration': 500, 'easing': 'quadratic-in-out'}
                    }]
                }]
            }],
            # Ajustar la posición del slider
            sliders=[{
                'currentvalue': {
                    'prefix': 'Año: ',
                    'visible': True,
                    'xanchor': 'right'
                },
                'pad': {'t': 40, 'b': 10},  # Ajustar padding
                'len': 0.9,
                'x': 0.1,
                'y': -0.2,
                'steps': [
                    {
                        'method': 'animate',
                        'label': str(year),
                        'args': [[str(year)], {
                            'frame': {'duration': 1000, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 500}
                        }]
                    } for year in sorted(años)
                ]
            }]
        )

        # Mejorar el formato del hover
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>" +
                         "Actividades Acumuladas: %{x:,.0f}<br>" +
                         "Asistentes Acumulados: %{y:,.0f}<br>" +
                         "Grupos de Interés Acumulados: %{marker.size:,.0f}<br>" +
                         "Año: %{customdata[4]}<br>" +
                         "<extra></extra>"
        )

        # Asegurarse de que solo haya un botón de play
        fig.layout.updatemenus[0].buttons = [fig.layout.updatemenus[0].buttons[0]]

        return fig
        
    except Exception as e:
        print(f"Error en create_animated_chart: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure()

def create_trend_chart(df):
    """Crea un gráfico de tendencia animado de actividades y asistentes"""
    if df.empty:
        return go.Figure()

    try:
        # Preparar los datos
        df['fecha'] = pd.to_datetime(df['fecha'])
        df_mensual = df.groupby(pd.Grouper(key='fecha', freq='M')).agg({
            'id': 'count',
            'total_asistentes': 'sum'
        }).reset_index()
        
        # Asegurarse de que las fechas estén ordenadas
        df_mensual = df_mensual.sort_values('fecha')
        
        # Crear el gráfico base
        fig = go.Figure()
        
        # Crear los frames para la animación
        frames = []
        for i in range(1, len(df_mensual) + 1):
            frame_data = df_mensual.iloc[:i]
            
            frame = go.Frame(
                data=[
                    go.Bar(
                        x=frame_data['fecha'],
                        y=frame_data['id'],
                        name='Actividades',
                        yaxis='y',
                        marker_color=THEME['primary'],
                        opacity=0.7
                    ),
                    go.Scatter(
                        x=frame_data['fecha'],
                        y=frame_data['total_asistentes'],
                        name='Asistentes',
                        yaxis='y2',
                        line=dict(color=THEME['success'], width=2),
                        mode='lines+markers',
                        marker=dict(size=6)
                    )
                ],
                name=str(frame_data['fecha'].iloc[-1].strftime('%Y-%m'))
            )
            frames.append(frame)
        
        # Agregar los datos iniciales
        fig.add_trace(go.Bar(
            x=[df_mensual['fecha'].iloc[0]],
            y=[df_mensual['id'].iloc[0]],
            name='Actividades',
            yaxis='y',
            marker_color=THEME['primary'],
            opacity=0.7
        ))
        
        fig.add_trace(go.Scatter(
            x=[df_mensual['fecha'].iloc[0]],
            y=[df_mensual['total_asistentes'].iloc[0]],
            name='Asistentes',
            yaxis='y2',
            line=dict(color=THEME['success'], width=2),
            mode='lines+markers',
            marker=dict(size=6)
        ))
        
        # Agregar los frames al gráfico
        fig.frames = frames
        
        # Configurar el layout
        fig.update_layout(
            title={
                'text': 'Tendencia de Actividades y Asistentes',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis=dict(
                title='Fecha',
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True,
                tickangle=-45,
                range=[df_mensual['fecha'].min(), df_mensual['fecha'].max()]
            ),
            yaxis=dict(
                title='Número de Actividades',
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True,
                side='left',
                range=[0, df_mensual['id'].max() * 1.1]
            ),
            yaxis2=dict(
                title='Número de Asistentes',
                overlaying='y',
                side='right',
                range=[0, df_mensual['total_asistentes'].max() * 1.1]
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.8)'
            ),
            hovermode='x unified',
            plot_bgcolor='rgba(240,240,240,0.2)',
            height=400,
            margin=dict(l=50, r=50, t=50, b=100),
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'y': 0,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'bottom',
                'pad': {'b': 10},
                'buttons': [{
                    'label': '▶️ Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 100, 'redraw': True},
                        'fromcurrent': True,
                        'transition': {'duration': 50}
                    }]
                }]
            }],
            sliders=[{
                'currentvalue': {
                    'prefix': 'Fecha: ',
                    'visible': True,
                    'xanchor': 'right'
                },
                'pad': {'t': 40, 'b': 10},
                'len': 0.9,
                'x': 0.1,
                'y': -0.2,
                'steps': [
                    {
                        'method': 'animate',
                        'label': date.strftime('%Y-%m'),
                        'args': [[date.strftime('%Y-%m')], {
                            'frame': {'duration': 100, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 50}
                        }]
                    } for date in df_mensual['fecha']
                ]
            }]
        )

        return fig
        
    except Exception as e:
        print(f"Error en create_trend_chart: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure()

def create_bar_race_chart(df):
    """Crea un gráfico de barras animado que muestra la evolución anual acumulada de actividades por municipio"""
    if df.empty:
        return go.Figure()

    try:
        # Preparar los datos
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['año'] = df['fecha'].dt.year
        
        # Calcular actividades acumuladas por municipio y año
        df_anual = df.groupby(['año', 'municipio']).size().reset_index(name='actividades')
        
        # Calcular acumulado para cada municipio por año
        años = sorted(df_anual['año'].unique())
        municipios = sorted(df_anual['municipio'].unique())  # Aseguramos que tengamos todos los municipios
        
        # Crear DataFrame con valores acumulados
        datos_acumulados = []
        for año in años:
            for municipio in municipios:
                actividades_previas = df_anual[
                    (df_anual['municipio'] == municipio) & 
                    (df_anual['año'] <= año)
                ]['actividades'].sum()
                
                datos_acumulados.append({
                    'año': año,
                    'municipio': municipio,
                    'actividades_acumuladas': actividades_previas
                })
        
        df_acum = pd.DataFrame(datos_acumulados)
        
        # Generar una paleta de colores variada para cada municipio
        colores_base = (
            px.colors.qualitative.Set1 +
            px.colors.qualitative.Set2 +
            px.colors.qualitative.Set3 +
            px.colors.qualitative.Pastel1 +
            px.colors.qualitative.Pastel2 +
            px.colors.qualitative.Bold
        )
        
        # Asegurar que tenemos suficientes colores
        while len(colores_base) < len(municipios):
            colores_base = colores_base * 2
        
        # Crear el mapa de colores para cada municipio
        color_map = dict(zip(municipios, colores_base[:len(municipios)]))
        
        # Crear figura base
        fig = go.Figure()
        
        # Crear el primer frame
        primer_año = años[0]
        datos_iniciales = df_acum[df_acum['año'] == primer_año].sort_values('actividades_acumuladas', ascending=True)
        
        fig.add_trace(
            go.Bar(
                x=datos_iniciales['actividades_acumuladas'],
                y=datos_iniciales['municipio'],
                orientation='h',
                text=datos_iniciales['actividades_acumuladas'].astype(int).astype(str),
                textposition='inside',
                textfont=dict(size=12, color='black'),
                marker_color=[color_map[m] for m in datos_iniciales['municipio']],
                hovertemplate="<b>%{y}</b><br>" +
                            "Actividades acumuladas: %{x:,.0f}<br>" +
                            "<extra></extra>"
            )
        )
        
        # Crear frames para cada año
        frames = []
        for año in años:
            datos_año = df_acum[df_acum['año'] == año].sort_values('actividades_acumuladas', ascending=True)
            
            frame = go.Frame(
                data=[
                    go.Bar(
                        x=datos_año['actividades_acumuladas'],
                        y=datos_año['municipio'],
                        orientation='h',
                        text=datos_año['actividades_acumuladas'].astype(int).astype(str),
                        textposition='inside',
                        textfont=dict(size=12, color='black'),
                        marker_color=[color_map[m] for m in datos_año['municipio']]
                    )
                ],
                name=str(año)
            )
            frames.append(frame)
        
        fig.frames = frames
        
        # Calcular altura necesaria basada en el número de municipios
        altura_por_municipio = 40  # Aumentamos el espacio por municipio
        altura_minima = 800
        altura_calculada = max(altura_minima, len(municipios) * altura_por_municipio)
        
        # Actualizar layout
        fig.update_layout(
            title={
                'text': 'Evolución Acumulada de Actividades por Municipio',
                'y':0.98,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=16)
            },
            xaxis=dict(
                title='Número de Actividades Acumuladas',
                gridcolor='rgba(128,128,128,0.2)',
                range=[0, df_acum['actividades_acumuladas'].max() * 1.1]
            ),
            yaxis=dict(
                title='',
                gridcolor='rgba(128,128,128,0.2)',
                autorange='reversed',
                tickfont=dict(size=11),  # Aumentado tamaño de fuente
                tickmode='array',
                ticktext=municipios,
                tickvals=municipios
            ),
            updatemenus=[dict(
                type='buttons',
                showactive=False,
                buttons=[
                    dict(
                        label='▶️ Play',
                        method='animate',
                        args=[None, dict(
                            frame=dict(duration=1500, redraw=True),
                            fromcurrent=True,
                            transition=dict(
                                duration=1500,
                                easing='cubic-in-out'
                            )
                        )]
                    ),
                    dict(
                        label='⏸️ Pause',
                        method='animate',
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode='immediate',
                            transition=dict(duration=0)
                        )]
                    )
                ],
                x=0.1,
                y=1.1,
                xanchor='right',
                yanchor='top'
            )],
            sliders=[dict(
                currentvalue=dict(
                    font=dict(size=16),
                    prefix='Año: ',
                    visible=True,
                    xanchor='right'
                ),
                len=0.9,
                x=0.1,
                y=0,
                steps=[dict(
                    args=[[str(año)], dict(
                        frame=dict(duration=1500, redraw=True),
                        mode='immediate',
                        transition=dict(duration=1500)
                    )],
                    label=str(año),
                    method='animate'
                ) for año in años]
            )],
            showlegend=False,
            margin=dict(l=200, r=50, t=100, b=50),  # Aumentado el margen izquierdo
            height=altura_calculada,  # Altura dinámica
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Actualizar estilo de las barras
        fig.update_traces(
            marker_line_color='white',
            marker_line_width=1.5,
            opacity=0.9
        )
        
        return fig

    except Exception as e:
        print(f"Error en create_bar_race_chart: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure()

def register_callbacks(app):
    """Registra todos los callbacks de la aplicación"""
    
    # Callback para cargar las opciones de los filtros
    @app.callback(
        [
            Output('ano-filter', 'options'),
            Output('zona-filter', 'options'),
            Output('depto-filter', 'options'),
            Output('categoria-filter', 'options'),
            Output('grupo-interes-filter', 'options'),
            Output('contrato-filter', 'options')
        ],
        Input('refresh-data', 'n_clicks')
    )
    def load_filter_options(n_clicks):
        """Carga las opciones para todos los filtros"""
        options = get_filter_options()
        return [
            [{'label': str(x), 'value': x} for x in options['anos'].ano],
            [{'label': str(x), 'value': x} for x in options['zonas'].zona_geografica],
            [{'label': str(x), 'value': x} for x in options['departamentos'].departamento],
            [{'label': str(x), 'value': x} for x in options['categorias'].categoria_unica],
            [{'label': str(x), 'value': x} for x in options['grupos_interes'].grupo_interes],
            [{'label': str(x), 'value': x} for x in options['contratos'].contrato]
        ]

    # Callback para actualizar municipios según departamento
    @app.callback(
        Output('municipio-filter', 'options'),
        Input('depto-filter', 'value')
    )
    def update_municipios(departamento):
        """Actualiza las opciones de municipios según el departamento seleccionado"""
        engine = get_db_engine()
        
        try:
            if not departamento:
                query = """
                    SELECT DISTINCT municipio as value, municipio as label
                    FROM actividades
                    WHERE municipio IS NOT NULL
                    ORDER BY municipio
                """
                params = None
            else:
                query = """
                    SELECT DISTINCT municipio as value, municipio as label
                    FROM actividades
                    WHERE departamento = %s AND municipio IS NOT NULL
                    ORDER BY municipio
                """
                params = (departamento,)
            
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
                return [{'label': row['label'], 'value': row['value']} for _, row in df.iterrows()]
                
        except Exception as e:
            print(f"Error actualizando municipios: {str(e)}")
            return []

    # Callback para limpiar filtros
    @app.callback(
        [Output(f"{filter_id}-filter", "value") for filter_id in 
         ['ano', 'mes', 'zona', 'depto', 'municipio', 'categoria', 
          'grupo-interes', 'grupo-intervencion', 'contrato']],
        Input('clear-filters', 'n_clicks'),
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def clear_all_filters(n_clicks):
        """Limpia todos los filtros"""
        if callback_context.triggered_id == 'clear-filters':
            return [None] * 9
        return dash.no_update

    # Callback principal para actualizar todos los componentes
    @app.callback(
        [
            Output('kpi-actividades', 'children'),
            Output('kpi-asistentes', 'children'),
            Output('kpi-municipios', 'children'),
            Output('kpi-meses-activos', 'children'),
            Output('kpi-zonas', 'children'),
            Output('kpi-grupos', 'children'),
            Output('kpi-promedio-asistentes', 'children'),
            Output('kpi-contratos', 'children'),
            Output('mapa-actividades', 'figure'),
            Output('grafico-tendencia', 'figure'),
            Output('grafico-grupos', 'figure'),
            Output('grafico-departamentos', 'figure'),
            Output('grafico-temporal-detallado', 'figure'),
            Output('grafico-tendencia-acumulada', 'figure'),
            Output('grafico-distribucion-asistentes', 'figure'),
            Output('grafico-boxplot-asistentes', 'figure'),
            Output('grafico-comparativo-zonas', 'figure'),
            Output('grafico-eficiencia-cobertura', 'figure'),
            Output('tabla-datos', 'data'),
            Output('tabla-datos', 'columns'),
            Output('grafico-animado', 'figure'),
            Output('grafico-barras-acumulado', 'figure')
        ],
        [
            Input('date-range', 'start_date'),
            Input('date-range', 'end_date'),
            Input('ano-filter', 'value'),
            Input('mes-filter', 'value'),
            Input('zona-filter', 'value'),
            Input('depto-filter', 'value'),
            Input('municipio-filter', 'value'),
            Input('categoria-filter', 'value'),
            Input('grupo-interes-filter', 'value'),
            Input('grupo-intervencion-filter', 'value'),
            Input('contrato-filter', 'value'),
            Input('map-type', 'value'),
            Input('map-level', 'value'),
            Input('basemap-style', 'value'),
            Input('search-input', 'value')
        ]
    )
    def update_all_components(start_date, end_date, ano, mes, zona, depto, municipio, 
                            categoria, grupo, grupo_intervencion, contrato, map_type, map_level, basemap_style, search):
        """Actualiza todos los componentes según los filtros seleccionados"""
        try:
            print(f"Actualizando componentes con filtros: depto={depto}, municipio={municipio}")
            
            if start_date:
                start_date = pd.to_datetime(start_date).date()
            if end_date:
                end_date = pd.to_datetime(end_date).date()
                
            # Obtener datos detallados primero
            df = get_detailed_data(
                start_date=start_date, 
                end_date=end_date,
                ano=ano,
                mes=mes,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                grupo_intervencion=grupo_intervencion,
                contrato=contrato
            )
            
            # Obtener datos para KPIs
            kpi_data = get_kpi_data(
                start_date=start_date, 
                end_date=end_date,
                ano=ano,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                contrato=contrato
            )
            
            # Formatear KPIs
            kpis = [
                f"{int(kpi_data['total_actividades']):,}",
                f"{int(kpi_data['total_asistentes']):,}",
                f"{int(kpi_data['total_municipios']):,}",
                f"{int(kpi_data['total_meses_activos']):,}",
                f"{int(kpi_data['total_zonas']):,}",
                f"{int(kpi_data['total_grupos_interes']):,}",
                f"{float(kpi_data['promedio_asistentes']):,.0f}",
                f"{int(kpi_data['total_contratos']):,}"
            ]
            
            # Obtener datos para análisis temporal y comparativo
            df_temporal = get_temporal_analysis(
                start_date=start_date, 
                end_date=end_date,
                ano=ano,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                contrato=contrato
            )
            
            df_distribucion = get_distribution_analysis(
                start_date=start_date, 
                end_date=end_date,
                ano=ano,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                contrato=contrato
            )
            
            df_comparativo = get_comparative_analysis(
                start_date=start_date, 
                end_date=end_date,
                ano=ano,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                contrato=contrato
            )
            
            # Crear todos los gráficos
            map_data = get_map_data(
                start_date=start_date,
                end_date=end_date,
                ano=ano,
                zona=zona,
                depto=depto,
                municipio=municipio,
                categoria=categoria,
                grupo=grupo,
                contrato=contrato,
                nivel=map_level
            )
            map_fig = update_map(map_type, map_level, basemap_style, map_data)
            basic_charts = create_charts(df)
            temporal_charts = create_temporal_charts(df_temporal)
            distribution_charts = create_distribution_charts(df_distribucion)
            comparative_charts = create_comparative_charts(df_comparativo)
            
            # Preparar datos para la tabla
            if search:
                df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
            table_data = df.to_dict('records')
            columns = [{"name": i, "id": i} for i in df.columns]
            
            # Crear el gráfico animado
            animated_fig = create_animated_chart(df)
            bar_race_fig = create_bar_race_chart(df)
            
            # Combinar todos los componentes en una lista
            all_components = (
                kpis +  # Lista de KPIs
                [map_fig] +  # Figura del mapa
                [basic_charts[0]] +  # grafico-tendencia-1
                [basic_charts[1]] +  # grafico-grupos
                [basic_charts[2]] +  # grafico-departamentos
                temporal_charts +  # Lista de gráficos temporales
                distribution_charts +  # Lista de gráficos de distribución
                comparative_charts +  # Lista de gráficos comparativos
                [table_data, columns] +  # Datos de la tabla
                [animated_fig, bar_race_fig]  # Nuevo gráfico animado y gráfico de barras animado
            )
            
            return all_components
            
        except Exception as e:
            print(f"Error en update_all_components: {str(e)}")
            import traceback
            traceback.print_exc()
            return ["Error"] * 8 + [go.Figure()] * 11 + [[], []] + [go.Figure()] * 2

    # Callback para exportar datos
    @app.callback(
        Output("download-data", "data"),
        Input("export-excel", "n_clicks"),
        [
            State('date-range', 'start_date'),
            State('date-range', 'end_date'),
            State('ano-filter', 'value'),
            State('zona-filter', 'value'),
            State('depto-filter', 'value'),
            State('categoria-filter', 'value'),
            State('grupo-interes-filter', 'value'),
            State('contrato-filter', 'value')
        ],
        prevent_initial_call=True
    )
    def export_data(n_clicks, start_date, end_date, ano, zona, depto, categoria, grupo, contrato):
        """Exporta los datos filtrados a Excel"""
        if n_clicks:
            try:
                df = get_detailed_data(start_date, end_date, ano, zona, depto, categoria, grupo, contrato)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Actividades', index=False)
                
                output.seek(0)
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                return dcc.send_bytes(output.getvalue(), f'actividades_{fecha}.xlsx')
            except Exception as e:
                print(f"Error al exportar datos: {str(e)}")
                return None
    # Modificamos el callback del mapa en pantalla completa
    @app.callback(
        Output("fullscreen-map-container", "children"),
        Input("open-fullscreen-map", "n_clicks"),
        [
            State('date-range', 'start_date'),
            State('date-range', 'end_date'),
            State('ano-filter', 'value'),
            State('zona-filter', 'value'),
            State('depto-filter', 'value'),
            State('categoria-filter', 'value'),
            State('grupo-interes-filter', 'value')
        ],
        prevent_initial_call=True
    )
    def open_fullscreen_map(n_clicks, start_date, end_date, ano, zona, depto, categoria, grupo):
        """Abre el mapa existente en una nueva ventana"""
        if n_clicks:
            try:
                # Ruta al archivo HTML existente
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                output_file = os.path.join(base_path, '..', 'mapa_todas_geometrias.html')
                
                if os.path.exists(output_file):
                    print(f"Abriendo mapa existente: {output_file}")
                    webbrowser.open('file://' + os.path.realpath(output_file))
                else:
                    print("El archivo del mapa no existe. Ejecute primero visualizar_todas_geometrias.py")
                    return html.Div("Error: Mapa no encontrado. Ejecute primero el script de visualización.")
                
                return ""
                
            except Exception as e:
                print(f"Error al abrir el mapa: {str(e)}")
                return html.Div(f"Error al abrir el mapa: {str(e)}")
        return ""

    # Callback para controlar la animación
    @app.callback(
        Output('animation-interval', 'disabled'),
        Input('play-animation', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_animation(n_clicks):
        if n_clicks is None:
            return True
        return False
