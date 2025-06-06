import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from streamlit_folium import folium_static, st_folium
import folium
from branca.colormap import LinearColormap
from folium import plugins
from folium.plugins import HeatMap
from folium.elements import Element
import logging
import scipy.stats as stats
from sqlalchemy import text
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

# Actualizar las importaciones
from predict_geographic import GeographicPredictor

try:
    from utils.data_loader import DataLoader
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.data_loader import DataLoader

logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Análisis Geográfico de Actividades",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: white;
    }
    .stPlotlyChart {
        background-color: #1E1E1E;
        border-radius: 5px;
        padding: 1rem;
    }
    .stats-box {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .cluster-card {
        background-color: #2C2C2C;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 14px;
        color: #CCCCCC;
    }
</style>
""", unsafe_allow_html=True)

def create_cluster_map(predictor, results):
    """Crea mapa interactivo con los clusters"""
    try:
        df = results['data']
        clusters = results['kmeans_results']['clusters']
        
        # Crear mapa base centrado en los datos
        m = create_base_map(df['latitud'].mean(), df['longitud'].mean())
        
        # Crear colormap para clusters
        n_clusters = len(set(clusters))
        
        # Asegurar que tenemos suficientes colores
        if n_clusters > 0:
            # Usar colores de Plotly y asegurar que hay suficientes
            if n_clusters <= 12:
                colors = px.colors.qualitative.Set3[:n_clusters]
            else:
                # Si hay más clusters que colores disponibles, repetir colores
                colors = []
                base_colors = px.colors.qualitative.Set3
                for i in range(n_clusters):
                    colors.append(base_colors[i % len(base_colors)])
        
        # Agregar marcadores por cluster
        for idx, row in df.iterrows():
            if idx < len(clusters):  # Verificar que el índice es válido
                cluster = clusters[idx]
                color_idx = int(cluster) % len(colors)  # Asegurar índice válido
                color = colors[color_idx]
                
                popup_html = f"""
                    <div style="font-family: Arial; width: 200px;">
                        <h4 style="color: {color};">{row['municipio']}</h4>
                        <b>Departamento:</b> {row['departamento']}<br>
                        <b>Cluster:</b> {cluster}<br>
                        <b>Actividades:</b> {int(row['num_actividades'])}<br>
                        <b>Asistentes:</b> {int(row['total_asistentes'])}<br>
                        <b>Promedio:</b> {row['promedio_asistentes'] if 'promedio_asistentes' in row else 0:.1f}/actividad
                    </div>
                """
                
                folium.CircleMarker(
                    location=[row['latitud'], row['longitud']],
                    radius=10 + (row['num_actividades'] / df['num_actividades'].max() * 20),
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color,
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)
        
        # Si no hay clusters, mostrar un mensaje
        if n_clusters == 0:
            logger.warning("No hay clusters para mostrar en el mapa")
        
        return m
    except Exception as e:
        logger.error(f"Error creando mapa de clusters: {str(e)}")
        # Devolver un mapa base en caso de error
        return create_base_map(4.570868, -74.297333)

def create_density_map(df: pd.DataFrame) -> folium.Map:
    """
    Crea un mapa de densidad (heatmap) de actividades
    
    Args:
        df: DataFrame con datos de actividades incluyendo latitud, longitud y num_actividades
        
    Returns:
        Mapa de folium con visualización de densidad
    """
    try:
        # Verificar que tenemos datos válidos
        if df.empty:
            logger.warning("DataFrame vacío en create_density_map")
            return folium.Map(location=[4.570868, -74.297333], zoom_start=6)
        
        # Asegurar que las coordenadas son números
        df = df.copy()
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df['num_actividades'] = pd.to_numeric(df['num_actividades'], errors='coerce')
        
        # Eliminar filas con coordenadas inválidas
        df = df.dropna(subset=['latitud', 'longitud', 'num_actividades'])
        
        if df.empty:
            logger.warning("No hay coordenadas válidas en create_density_map")
            return folium.Map(location=[4.570868, -74.297333], zoom_start=6)
            
        # Crear mapa base
        center_lat = float(df['latitud'].mean())
        center_lon = float(df['longitud'].mean())
        
        logger.info(f"Creando mapa con centro en: {center_lat}, {center_lon}")
        
        # Crear un mapa base optimizado para rendimiento
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='CartoDB positron',
            prefer_canvas=True  # Mejora el rendimiento
        )
        
        # Preparar datos para el heatmap de manera segura
        heat_data = []
        for _, row in df.iterrows():
            try:
                lat = float(row['latitud'])
                lon = float(row['longitud'])
                weight = float(row['num_actividades'])
                if not (pd.isna(lat) or pd.isna(lon) or pd.isna(weight)):
                    heat_data.append([lat, lon, weight])
            except (ValueError, TypeError) as e:
                continue
        
        logger.info(f"Agregando capa de calor con {len(heat_data)} puntos")
        
        # Añadir capa de heatmap de manera segura
        if heat_data:
            try:
                # Crear el heatmap con parámetros básicos
                heatmap = plugins.HeatMap(
                heat_data,
                    radius=15,
                    blur=10,
                    min_opacity=0.5
                )
                m.add_child(heatmap)
                logger.info("Capa de heatmap agregada exitosamente")
            except Exception as e:
                logger.error(f"Error agregando capa de heatmap: {str(e)}")
        
        # Añadir marcadores para municipios con más actividades
        try:
            # Mostrar solo los top 5 para no sobrecargar el mapa
            top_municipios = df.nlargest(5, 'num_actividades')
            for _, row in top_municipios.iterrows():
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=f"{row['municipio']}: {int(row['num_actividades'])} actividades",
                    icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            logger.info("Marcadores de municipios agregados exitosamente")
        except Exception as e:
            logger.error(f"Error agregando marcadores: {str(e)}")
            
        logger.info("Mapa de densidad creado exitosamente")
        return m
            
    except Exception as e:
        logger.error(f"Error creando mapa de densidad: {str(e)}")
        # Devolver un mapa vacío en caso de error
        return folium.Map(location=[4.570868, -74.297333], zoom_start=6)

def create_cluster_profile_chart(cluster_profiles):
    """
    Crea un gráfico de perfiles de cluster
    
    Args:
        cluster_profiles: Diccionario con perfiles de cluster
        
    Returns:
        Figura de plotly con el gráfico de perfiles
    """
    try:
        # Crear DataFrame con perfiles
        profiles_data = []
        
        for cluster_id, profile in cluster_profiles.items():
            profiles_data.append({
                'cluster': f"Cluster {cluster_id}",
                'tamaño': profile['size'],
                'actividades': profile['actividades_promedio'],
                'asistentes': profile['asistentes_promedio'],
                'eficiencia': profile['eficiencia_promedio'],
                'intensidad': profile.get('intensidad_mensual_promedio', 0)
            })
            
        df_profiles = pd.DataFrame(profiles_data)
        
        # Normalizar las métricas para que todas sean visibles en el gráfico radar
        # Esto asegura que cada métrica tenga un rango similar
        norm_df = df_profiles.copy()
        metrics = ['actividades', 'asistentes', 'eficiencia', 'intensidad', 'tamaño']
        
        for metric in metrics:
            max_val = norm_df[metric].max()
            if max_val > 0:  # Evitar división por cero
                # Normalizar valores a un rango de 0-100 para mejor visualización
                norm_df[metric] = (norm_df[metric] / max_val) * 100
        
        # Crear gráfico de radar normalizado
        fig = go.Figure()
        
        # Definir colores para clusters
        colors = px.colors.qualitative.Bold
        
        # Añadir una traza por cluster con valores normalizados
        for i, row in norm_df.iterrows():
            color = colors[i % len(colors)]
            orig_row = df_profiles.iloc[i]  # Valores originales para el hover
            
            fig.add_trace(go.Scatterpolar(
                r=[
                    row['actividades'], 
                    row['asistentes'], 
                    row['eficiencia'], 
                    row['intensidad'], 
                    row['tamaño']
                ],
                theta=['Actividades', 'Asistentes', 'Eficiencia', 'Intensidad', 'Tamaño'],
                fill='toself',
                name=row['cluster'],
                line_color=color,
                fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                hoverinfo='text',
                hovertext=[
                    f"Actividades: {orig_row['actividades']:.1f} (Normalizado: {row['actividades']:.1f}%)",
                    f"Asistentes: {orig_row['asistentes']:.1f} (Normalizado: {row['asistentes']:.1f}%)",
                    f"Eficiencia: {orig_row['eficiencia']:.1f} (Normalizado: {row['eficiencia']:.1f}%)",
                    f"Intensidad: {orig_row['intensidad']:.1f} (Normalizado: {row['intensidad']:.1f}%)",
                    f"Tamaño: {orig_row['tamaño']} (Normalizado: {row['tamaño']:.1f}%)"
                ]
            ))
        
        # Actualizar layout
        fig.update_layout(
            title={
                'text': 'Comparación de Perfiles de Cluster (Normalizado)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='white')
            },
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 110],  # Un poco más de 100 para dar espacio
                    ticksuffix='%'  # Añadir símbolo de porcentaje
                )
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(30, 30, 50, 0.5)',
                bordercolor='rgba(100, 100, 100, 0.8)',
                borderwidth=1
            ),
            template='plotly_dark',
            paper_bgcolor='rgba(30, 30, 50, 0.9)',
            height=600,
            margin=dict(l=80, r=80, t=100, b=100),
            annotations=[
                dict(
                    text="Valores normalizados a 0-100% para facilitar comparación",
                    x=0.5,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=12, color="gray")
                )
            ]
        )
        
        # El resto del código para el gráfico de barras se mantiene igual
        fig_bars = go.Figure()
        
        # Normalizar los datos para mejor comparación
        df_norm = df_profiles.copy()
        for col in ['actividades', 'asistentes', 'eficiencia', 'intensidad', 'tamaño']:
            max_val = df_norm[col].max()
            if max_val > 0:
                df_norm[col] = df_norm[col] / max_val
        
        # Añadir barras para cada métrica
        metrics = ['actividades', 'asistentes', 'eficiencia', 'intensidad', 'tamaño']
        metric_names = ['Actividades', 'Asistentes', 'Eficiencia', 'Intensidad', 'Tamaño']
        
        for i, (metric, name) in enumerate(zip(metrics, metric_names)):
            fig_bars.add_trace(go.Bar(
                x=df_profiles['cluster'],
                y=df_profiles[metric],
                name=name,
                marker_color=px.colors.sequential.Viridis[i],
                hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>"
            ))
        
        # Actualizar layout
        fig_bars.update_layout(
            title={
                'text': 'Métricas por Cluster',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='white')
            },
            barmode='group',
            template='plotly_dark',
            paper_bgcolor='rgba(30, 30, 50, 0.9)',
            plot_bgcolor='rgba(30, 30, 50, 0.9)',
            height=500,
            margin=dict(l=60, r=30, t=80, b=80),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            xaxis_title="",
            yaxis_title="Valor",
            hoverlabel=dict(
                bgcolor='rgba(50, 50, 70, 0.9)',
                font_size=12,
                font_family='Arial'
            )
        )
        
        return [fig, fig_bars]
        
    except Exception as e:
        st.error(f"Error creando gráfico de perfiles: {str(e)}")
        return None

def show_cluster_details(cluster_profiles):
    """
    Muestra detalles de los perfiles de cluster
    
    Args:
        cluster_profiles: Diccionario con perfiles de cluster
    """
    try:
        # Crear gráficos de perfiles
        profile_charts = create_cluster_profile_chart(cluster_profiles)
        
        if profile_charts:
            # Mostrar gráfico de radar con key única
            st.plotly_chart(profile_charts[0], use_container_width=True, key="cluster_radar_chart")
            
            # Mostrar gráfico de barras con key única
            st.plotly_chart(profile_charts[1], use_container_width=True, key="cluster_bar_chart")
        
        # Mostrar detalles de cada cluster en tarjetas
        st.subheader("Detalles de Clusters")
        
        # Crear columnas para mostrar clusters
        cols = st.columns(min(len(cluster_profiles), 3))
        
        for i, (cluster_id, profile) in enumerate(cluster_profiles.items()):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                # Crear tarjeta con estilo
                st.markdown(
                    f"""
                    <div style="
                        background-color: rgba(40, 40, 70, 0.8);
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 20px;
                        border-left: 5px solid {px.colors.qualitative.Bold[i % len(px.colors.qualitative.Bold)]};
                    ">
                        <h3 style="margin-top: 0;">Cluster {cluster_id}</h3>
                        <p><b>Municipios:</b> {profile['size']}</p>
                        <p><b>Actividades promedio:</b> {profile['actividades_promedio']:.2f}</p>
                        <p><b>Asistentes promedio:</b> {profile['asistentes_promedio']:.2f}</p>
                        <p><b>Eficiencia promedio:</b> {profile['eficiencia_promedio']:.2f}</p>
                        <p><b>Intensidad mensual:</b> {profile.get('intensidad_mensual_promedio', 0):.2f}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Mostrar lista desplegable con municipios SIN key
                with st.expander(f"Ver municipios del Cluster {cluster_id}"):
                    municipios = profile.get('municipios', [])
                    if municipios:
                        for municipio in sorted(municipios):
                            st.write(f"• {municipio}")
                    else:
                        st.write("No hay municipios en este cluster")
        
    except Exception as e:
        st.error(f"Error mostrando detalles de cluster: {str(e)}")

@st.cache_resource
def create_base_map(center_lat: float, center_lon: float) -> folium.Map:
    """
    Crea un mapa base para visualizaciones
    
    Args:
        center_lat: Latitud del centro del mapa
        center_lon: Longitud del centro del mapa
        
    Returns:
        Mapa base de folium
    """
    try:
        # Crear mapa base con estilo limpio
        m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
            tiles='CartoDB positron',
            control_scale=True
        )
        
        # Añadir control de escala
        folium.plugins.Fullscreen(
            position='topright',
            title='Pantalla completa',
            title_cancel='Salir de pantalla completa'
        ).add_to(m)
        
        # Añadir mini mapa para contexto
        minimap = folium.plugins.MiniMap(toggle_display=True)
        m.add_child(minimap)
        
        return m
        
    except Exception as e:
        logger.error(f"Error creando mapa base: {str(e)}")
        # Devolver un mapa simple en caso de error
        return folium.Map(location=[center_lat, center_lon], zoom_start=6)

@st.cache_data(ttl=1800)
def prepare_visualization_data(_results: dict) -> dict:
    """Prepara datos para visualización"""
    try:
        # Crear copia para no modificar el original
        results = _results.copy()
        
        # Verificar que hay datos
        if 'data' not in results or results['data'] is None or results['data'].empty:
            return {}
            
        # Obtener DataFrame y agrupar por municipio para evitar duplicados
        df = results['data'].groupby(['municipio', 'departamento']).agg({
            'num_actividades': 'first',
            'total_asistentes': 'first',
            'eficiencia_actividad': 'first',
            'latitud': 'first',
            'longitud': 'first',
            'zona_geografica': 'first'
        }).reset_index()
        
        # Preparar datos para visualizaciones
        viz_data = {}
        
        # Crear gráficos de resumen
        summary_charts = []
        
        # 1. Gráfico de barras de actividades por departamento (top 10)
        dept_counts = df.groupby('departamento').agg({
            'num_actividades': 'sum',
            'municipio': 'count'
        }).reset_index()
        dept_counts = dept_counts.sort_values('num_actividades', ascending=False).head(10)
        
        fig_dept = px.bar(
            dept_counts, 
            x='num_actividades', 
            y='departamento',
            orientation='h',
            title='Top 10 Departamentos por Número de Actividades',
            labels={
                'num_actividades': 'Número de Actividades', 
                'departamento': 'Departamento'
            },
            color='num_actividades',
            color_continuous_scale='viridis',
            text=dept_counts['municipio'].apply(lambda x: f'{x} municipios')  # Mostrar número de municipios
        )
        
        fig_dept.update_layout(
            template='plotly_dark',
            height=400,
            margin=dict(l=80, r=30, t=40, b=10),
            yaxis={'categoryorder': 'total ascending'},
            paper_bgcolor='rgba(30, 30, 50, 0.9)',
            plot_bgcolor='rgba(30, 30, 50, 0.9)'
        )
        
        summary_charts.append(fig_dept)
        
        # 2. Gráfico de dispersión de actividades vs asistentes
        fig_scatter = px.scatter(
            df, 
            x='num_actividades', 
            y='total_asistentes',
            size='eficiencia_actividad',
            color='departamento',
            hover_name='municipio',
            title='Actividades vs Asistentes por Municipio',
            labels={
                'num_actividades': 'Número de Actividades', 
                'total_asistentes': 'Total de Asistentes',
                'eficiencia_actividad': 'Eficiencia'
            }
        )
        
        fig_scatter.update_layout(
            template='plotly_dark',
            height=500,
            margin=dict(l=60, r=30, t=40, b=40),
            paper_bgcolor='rgba(30, 30, 50, 0.9)',
            plot_bgcolor='rgba(30, 30, 50, 0.9)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        summary_charts.append(fig_scatter)
        
        # 3. Gráfico de eficiencia por departamento (top 8)
        dept_metrics = df.groupby('departamento').agg({
            'num_actividades': 'sum',
            'total_asistentes': 'sum',
            'eficiencia_actividad': 'mean',
            'municipio': 'count'
        }).reset_index()
        
        dept_metrics.rename(columns={'municipio': 'num_municipios'}, inplace=True)
        dept_metrics = dept_metrics.sort_values('num_actividades', ascending=False).head(8)
        
        # Crear gráfico combinado de barras y puntos
        fig_dept_combined = go.Figure()
        
        # Añadir barras para actividades
        fig_dept_combined.add_trace(go.Bar(
            x=dept_metrics['num_actividades'],
            y=dept_metrics['departamento'],
            orientation='h',
            name='Actividades',
            marker=dict(
                color=dept_metrics['num_actividades'],
                colorscale='Viridis',
                showscale=False
            ),
            hovertemplate='<b>%{y}</b><br>Actividades: %{x}<br>Municipios: %{text}',
            text=dept_metrics['num_municipios']
        ))
        
        # Añadir puntos para eficiencia
        fig_dept_combined.add_trace(go.Scatter(
            x=dept_metrics['num_actividades'],
            y=dept_metrics['departamento'],
            mode='markers',
            name='Eficiencia',
            marker=dict(
                size=dept_metrics['eficiencia_actividad'] * 3,  # Tamaño proporcional a la eficiencia
                color=dept_metrics['eficiencia_actividad'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(
                    title="Eficiencia",
                    thickness=15,
                    len=0.5,
                    y=0.5
                )
            ),
            text=dept_metrics['eficiencia_actividad'].round(1),
            hovertemplate='<b>%{y}</b><br>Eficiencia: %{text} asistentes/actividad',
        ))
        
        # Añadir anotaciones para mostrar el número de municipios
        for i, row in dept_metrics.iterrows():
            fig_dept_combined.add_annotation(
                y=row['departamento'],
                x=0,
                text=f"{int(row['num_municipios'])} mun.",
                showarrow=False,
                xshift=-40,
                align='right',
                font=dict(size=10, color='rgba(255, 255, 255, 0.9)'),
                bgcolor='rgba(50, 50, 50, 0.7)',
                bordercolor='rgba(100, 100, 100, 0.8)',
                borderwidth=1,
                borderpad=3,
                opacity=0.9
            )
        
        # Actualizar diseño
        fig_dept_combined.update_layout(
            title={
                'text': 'Top 8 Departamentos: Actividades y Eficiencia',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='white')
            },
            template='plotly_dark',
            height=450,
            margin=dict(l=80, r=30, t=50, b=20),
            xaxis_title="Número de Actividades",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            paper_bgcolor='rgba(30, 30, 50, 0.9)',
            plot_bgcolor='rgba(30, 30, 50, 0.9)',
            hoverlabel=dict(
                bgcolor='rgba(50, 50, 70, 0.9)',
                font_size=12,
                font_family='Arial'
            ),
            xaxis=dict(
                gridcolor='rgba(80, 80, 100, 0.3)',
                zerolinecolor='rgba(80, 80, 100, 0.5)'
            )
        )
        
        summary_charts.append(fig_dept_combined)
        
        # 4. Nuevo gráfico: Distribución de eficiencia por zona geográfica
        if 'zona_geografica' in df.columns:
            zona_metrics = df.groupby('zona_geografica').agg({
                'num_actividades': 'sum',
                'total_asistentes': 'sum',
                'eficiencia_actividad': 'mean',
                'municipio': 'count'
            }).reset_index()
            
            zona_metrics.rename(columns={'municipio': 'num_municipios'}, inplace=True)
            
            # Crear gráfico de burbujas
            fig_zona = px.scatter(
                zona_metrics,
                x='num_actividades',
                y='eficiencia_actividad',
                size='total_asistentes',
                color='zona_geografica',
                hover_name='zona_geografica',
                text='zona_geografica',
                size_max=50,
                title='Distribución de Actividades y Eficiencia por Zona Geográfica',
                labels={
                    'num_actividades': 'Número de Actividades',
                    'eficiencia_actividad': 'Eficiencia (asistentes/actividad)',
                    'total_asistentes': 'Total de Asistentes',
                    'zona_geografica': 'Zona Geográfica'
                }
            )
            
            # Añadir etiquetas de texto
            fig_zona.update_traces(
                textposition='top center',
                textfont=dict(size=10, color='white')
            )
            
            # Actualizar diseño
            fig_zona.update_layout(
                template='plotly_dark',
                height=500,
                margin=dict(l=60, r=30, t=50, b=50),
                paper_bgcolor='rgba(30, 30, 50, 0.9)',
                plot_bgcolor='rgba(30, 30, 50, 0.9)',
                xaxis=dict(
                    gridcolor='rgba(80, 80, 100, 0.3)',
                    zerolinecolor='rgba(80, 80, 100, 0.5)'
                ),
                yaxis=dict(
                    gridcolor='rgba(80, 80, 100, 0.3)',
                    zerolinecolor='rgba(80, 80, 100, 0.5)'
                ),
                hoverlabel=dict(
                    bgcolor='rgba(50, 50, 70, 0.9)',
                    font_size=12,
                    font_family='Arial'
                )
            )
            
            # Añadir anotaciones para cada burbuja
            for i, row in zona_metrics.iterrows():
                fig_zona.add_annotation(
                    x=row['num_actividades'],
                    y=row['eficiencia_actividad'],
                    text=f"{int(row['num_municipios'])} mun.",
                    showarrow=False,
                    yshift=20,
                    font=dict(size=9, color='rgba(255, 255, 255, 0.8)'),
                    bgcolor='rgba(50, 50, 50, 0.6)',
                    bordercolor='rgba(100, 100, 100, 0.7)',
                    borderwidth=1,
                    borderpad=2,
                    opacity=0.8
                )
            
            summary_charts.append(fig_zona)
        
        viz_data['summary_charts'] = summary_charts
        
        # Crear gráfico de perfiles de cluster si hay resultados de clustering
        if 'kmeans_results' in results and 'cluster_profiles' in results['kmeans_results']:
            cluster_profiles = results['kmeans_results']['cluster_profiles']
            cluster_profile_charts = create_cluster_profile_chart(cluster_profiles)
            viz_data['cluster_profile_chart'] = cluster_profile_charts[0]
            viz_data['cluster_bar_chart'] = cluster_profile_charts[1]
        
        return viz_data
        
    except Exception as e:
        st.error(f"Error preparando datos para visualización: {str(e)}")
        return {}

def create_maps(results: dict, predictor=None) -> dict:
    """
    Crea todos los mapas necesarios para la visualización
    
    Args:
        results: Diccionario con resultados del análisis
        predictor: Instancia del predictor geográfico
        
    Returns:
        Diccionario con los mapas creados
    """
    try:
        maps = {}
        
        # Obtener datos
        df = results.get('data')
        if df is None or df.empty:
            st.warning("No hay datos disponibles para crear mapas")
            return {}
            
        # Crear mapa base
        center_lat = df['latitud'].mean()
        center_lon = df['longitud'].mean()
        base_map = create_base_map(center_lat, center_lon)
        maps['base_map'] = base_map
        
        # Crear mapa de clusters
        if 'kmeans_results' in results and results['kmeans_results']:
            cluster_map = create_cluster_map(predictor, results)
            maps['cluster_map'] = cluster_map
        
        # Crear mapa de densidad
        density_map = create_density_map(df)
        maps['density_map'] = density_map
        
        # Crear mapa de calor mejorado para actividades
        try:
            enhanced_heatmap_activities = create_enhanced_heatmap(
                df, 
                value_column='num_actividades',
                title='Mapa de Calor de Actividades'
            )
            if enhanced_heatmap_activities:
                maps['enhanced_heatmap_activities'] = enhanced_heatmap_activities
        except Exception as e:
            logger.error(f"Error creando mapa de calor de actividades: {str(e)}")
        
        # Crear mapa de calor mejorado para eficiencia
        try:
            if 'eficiencia_actividad' in df.columns:
                enhanced_heatmap_efficiency = create_enhanced_heatmap(
                    df, 
                    value_column='eficiencia_actividad',
                    title='Mapa de Calor de Eficiencia'
                )
                if enhanced_heatmap_efficiency:
                    maps['enhanced_heatmap_efficiency'] = enhanced_heatmap_efficiency
        except Exception as e:
            logger.error(f"Error creando mapa de calor de eficiencia: {str(e)}")
        
        return maps
            
    except Exception as e:
        st.error(f"Error creando mapas: {str(e)}")
        return {}

def show_analysis(results: dict, viz_data: dict, maps: dict):
    """Muestra el análisis geográfico completo"""
    try:
        # Verificar que hay datos
        if not results or not viz_data:
            st.warning("No hay datos disponibles para mostrar el análisis")
            return
            
        # Agrupar datos por municipio para evitar duplicados
        df = results['data'].groupby(['municipio', 'departamento']).agg({
            'num_actividades': 'first',
            'total_asistentes': 'first',
            'eficiencia_actividad': 'first',
            'latitud': 'first',
            'longitud': 'first',
            'zona_geografica': 'first'
        }).reset_index()
        
        # Mostrar KPIs en la parte superior
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Municipios", 
                f"{len(df)}", 
                delta=None,
                delta_color="normal",
                help="Número total de municipios con actividades"
            )
            
        with col2:
            st.metric(
                "Actividades", 
                f"{int(df['num_actividades'].sum())}", 
                delta=None,
                delta_color="normal",
                help="Número total de actividades realizadas"
            )
            
        with col3:
            st.metric(
                "Asistentes", 
                f"{int(df['total_asistentes'].sum())}", 
                delta=None,
                delta_color="normal",
                help="Número total de asistentes"
            )
            
        with col4:
            promedio_eficiencia = df['eficiencia_actividad'].mean()
            st.metric(
                "Eficiencia Promedio", 
                f"{promedio_eficiencia:.2f}", 
                delta=None,
                delta_color="normal",
                help="Promedio de asistentes por actividad"
            )
        
        # Mostrar gráficos de resumen
        if 'summary_charts' in viz_data:
            for chart in viz_data['summary_charts']:
                st.plotly_chart(chart, use_container_width=True)
        
        # ... resto del código de la función ...
        
    except Exception as e:
        logger.error(f"Error en show_analysis: {str(e)}")
        st.error(f"Error mostrando análisis: {str(e)}")

def show_statistics(stats: dict):
    """Muestra estadísticas generales"""
    if 'general' in stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total Municipios",
                stats['general']['total_municipios'],
                f"{stats['general']['total_actividades']} actividades"
            )
        with col2:
            st.metric(
                "Promedio Actividades",
                f"{stats['general']['promedio_actividades']:.1f}",
                "por municipio"
            )
        with col3:
            st.metric(
                "Promedio Asistentes",
                f"{stats['general']['promedio_asistentes']:.1f}",
                "por actividad"
            )

def show_expansion_analysis(expansion_data: pd.DataFrame):
    """Muestra análisis de expansión"""
    if not expansion_data.empty:
        high_priority = expansion_data[expansion_data['categoria_expansion'] == 'Alta Prioridad']
        if not high_priority.empty:
            for _, row in high_priority.iterrows():
                st.warning(f"""
                    ### 🎯 {row['municipio']}
                    - **Potencial de expansión:** {row['potencial_expansion']:.1f}%
                    - **Actividades actuales:** {int(row['num_actividades'])}
                    - **Actividades sugeridas:** {int(row['actividades_sugeridas'])}
                    - **Score de prioridad:** {row['prioridad_score']:.2f}
                """)

@st.cache_data(ttl=3600)
def get_municipal_details(df: pd.DataFrame, municipio: str) -> dict:
    """Obtiene análisis detallado de un municipio específico"""
    try:
        mun_data = df[df['municipio'] == municipio].iloc[0]
        
        # Calcular tendencias
        tendencia = {
            'crecimiento_actividades': 'positiva' if mun_data['num_actividades'] > df['num_actividades'].mean() else 'negativa',
            'eficiencia': 'alta' if mun_data['eficiencia_actividad'] > df['eficiencia_actividad'].mean() else 'baja',
            'cobertura': 'buena' if mun_data['meses_activos'] > 6 else 'necesita mejora'
        }
        
        # Calcular percentiles
        percentiles = {
            'actividades': stats.percentileofscore(df['num_actividades'], mun_data['num_actividades']),
            'asistentes': stats.percentileofscore(df['total_asistentes'], mun_data['total_asistentes']),
            'eficiencia': stats.percentileofscore(df['eficiencia_actividad'], mun_data['eficiencia_actividad'])
        }
        
        return {
            'datos_basicos': {
                'total_actividades': int(mun_data['num_actividades']),
                'total_asistentes': int(mun_data['total_asistentes']),
                'promedio_asistentes': float(mun_data['promedio_asistentes']),
                'meses_activos': int(mun_data['meses_activos'])
            },
            'tendencias': tendencia,
            'percentiles': percentiles,
            'comparacion_regional': {
                'vs_departamento': mun_data['num_actividades'] / df[df['departamento'] == mun_data['departamento']]['num_actividades'].mean(),
                'vs_nacional': mun_data['num_actividades'] / df['num_actividades'].mean()
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo detalles municipales: {str(e)}")
        return {}

def show_detailed_analysis(df: pd.DataFrame):
    """Muestra análisis detallado con gráficos mejorados e informativos"""
    try:
        # Agrupar datos por municipio para evitar duplicados
        df = df.groupby(['municipio', 'departamento']).agg({
            'num_actividades': 'first',
            'total_asistentes': 'first',
            'eficiencia_actividad': 'first',
            'latitud': 'first',
            'longitud': 'first',
            'zona_geografica': 'first',
            'meses_activos': 'first'
        }).reset_index()
        
        # Resto del código existente...
        
        # Crear dos columnas para mostrar métricas generales
        col1, col2 = st.columns(2)
        
        with col1:
            # Métricas generales
            st.write("### 📈 Métricas Generales")
            total_actividades = int(df['num_actividades'].sum())
            total_asistentes = int(df['total_asistentes'].sum())
            promedio_eficiencia = float(df['eficiencia_actividad'].mean())
            
            st.metric(
                "Total Actividades", 
                f"{total_actividades:,}",
                f"{len(df)} municipios"
            )
            st.metric(
                "Total Asistentes", 
                f"{total_asistentes:,}",
                f"{promedio_eficiencia:.1f} asistentes/actividad"
            )
            
            # Distribución por departamento
            st.write("### 🗺️ Distribución por Departamento")
            
            # Crear un DataFrame con métricas agregadas por departamento
            dept_metrics = df.groupby('departamento').agg({
                'num_actividades': 'sum',
                'total_asistentes': 'sum',
                'municipio': 'nunique',
                'eficiencia_actividad': 'mean'
            }).reset_index()
            
            # Renombrar columnas para mayor claridad
            dept_metrics.rename(columns={
                'municipio': 'num_municipios',
                'eficiencia_actividad': 'eficiencia_promedio'
            }, inplace=True)
            
            # Ordenar por número de actividades
            dept_metrics = dept_metrics.sort_values('num_actividades', ascending=False).head(8)
            
            # Calcular actividades por municipio
            dept_metrics['actividades_por_municipio'] = (
                dept_metrics['num_actividades'] / dept_metrics['num_municipios']
            ).round(1)
            
            # Crear gráfico de barras combinado
            fig_dept = go.Figure()
            
            # Añadir barras para número de actividades
            fig_dept.add_trace(go.Bar(
                y=dept_metrics['departamento'],
                x=dept_metrics['num_actividades'],
                name='Actividades',
                orientation='h',
                marker_color='#4C78A8',
                text=dept_metrics['num_actividades'],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Actividades: %{x}<br>Municipios: %{customdata[0]}<br>Eficiencia: %{customdata[1]:.1f}',
                customdata=dept_metrics[['num_municipios', 'eficiencia_promedio']]
            ))
            
            # Añadir indicadores de eficiencia como puntos
            fig_dept.add_trace(go.Scatter(
                y=dept_metrics['departamento'],
                x=dept_metrics['num_actividades'] + dept_metrics['num_actividades'].max() * 0.05,  # Desplazar a la derecha
                mode='markers',
                name='Eficiencia',
                marker=dict(
                    size=dept_metrics['eficiencia_promedio'] * 3,  # Tamaño proporcional a la eficiencia
                    color=dept_metrics['eficiencia_promedio'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(
                        title="Eficiencia",
                        thickness=15,
                        len=0.5,
                        y=0.5
                    )
                ),
                text=dept_metrics['eficiencia_promedio'].round(1),
                hovertemplate='<b>%{y}</b><br>Eficiencia: %{text} asistentes/actividad',
            ))
            
            # Añadir anotaciones para mostrar el número de municipios
            for i, row in dept_metrics.iterrows():
                fig_dept.add_annotation(
                    y=row['departamento'],
                    x=0,
                    text=f"{int(row['num_municipios'])} mun.",
                    showarrow=False,
                    xshift=-40,
                    align='right',
                    font=dict(size=10, color='rgba(255, 255, 255, 0.9)'),
                    bgcolor='rgba(50, 50, 50, 0.7)',
                    bordercolor='rgba(100, 100, 100, 0.8)',
                    borderwidth=1,
                    borderpad=3,
                    opacity=0.9
                )
            
            # Actualizar diseño
            fig_dept.update_layout(
                title={
                    'text': 'Top 8 Departamentos: Actividades y Eficiencia',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=18, color='white')
                },
                template='plotly_dark',
                height=450,
                margin=dict(l=80, r=30, t=50, b=20),
                xaxis_title="Número de Actividades",
                yaxis_title="",
                yaxis={'categoryorder': 'total ascending'},
                paper_bgcolor='rgba(30, 30, 50, 0.9)',
                plot_bgcolor='rgba(30, 30, 50, 0.9)',
                hoverlabel=dict(
                    bgcolor='rgba(50, 50, 70, 0.9)',
                    font_size=12,
                    font_family='Arial'
                ),
                xaxis=dict(
                    gridcolor='rgba(80, 80, 100, 0.3)',
                    zerolinecolor='rgba(80, 80, 100, 0.5)'
                )
            )
            
            st.plotly_chart(fig_dept, use_container_width=True, key="dept_metrics")
                        
            with col2:
                # Gráfico de barras mejorado para Top 10 municipios
                st.write("### 🏆 Top 10 Municipios por Actividades")
            
            top_municipios = df.nlargest(10, 'num_actividades')
            
            # Añadir información de departamento y eficiencia
            top_municipios['municipio_dept'] = top_municipios['municipio'] + ' (' + top_municipios['departamento'] + ')'
            top_municipios['eficiencia_str'] = top_municipios['eficiencia_actividad'].round(1).astype(str)
            
            # Crear gráfico de barras con color basado en eficiencia
            fig_activities = px.bar(
                top_municipios,
                y='municipio_dept',
                x='num_actividades',
                orientation='h',
                color='eficiencia_actividad',
                color_continuous_scale='RdYlGn',
                text='eficiencia_str',
                                        labels={
                    'municipio_dept': 'Municipio',
                    'num_actividades': 'Número de Actividades',
                    'eficiencia_actividad': 'Eficiencia'
                },
                title='Top 10 Municipios por Actividades'
            )
            
            fig_activities.update_traces(
                textposition='outside',
                texttemplate='%{text} asist/act',
                hovertemplate='<b>%{y}</b><br>Actividades: %{x}<br>Eficiencia: %{text} asistentes/actividad'
            )
            
            fig_activities.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(l=10, r=10, t=40, b=10),
                coloraxis_colorbar=dict(title="Eficiencia"),
                xaxis_title="Número de Actividades",
                yaxis_title="",
                yaxis={'categoryorder': 'total ascending'}
            )
            
        st.plotly_chart(fig_activities, use_container_width=True, key="top_municipios")
        
        # Gráfico de dispersión mejorado para eficiencia vs actividades
        st.write("### 🔍 Relación entre Actividades y Eficiencia")
        
        # Preparar datos para el gráfico de dispersión
        scatter_df = df.copy()
        scatter_df['tamaño_punto'] = np.sqrt(scatter_df['total_asistentes']) / 2
        scatter_df['tamaño_punto'] = scatter_df['tamaño_punto'].clip(5, 30)  # Limitar tamaño de puntos
        
        # Crear gráfico de dispersión con información adicional
        fig_efficiency = px.scatter(
            scatter_df,
            x='num_actividades',
            y='eficiencia_actividad',
            size='tamaño_punto',
            color='departamento',
            hover_name='municipio',
            hover_data={
                'num_actividades': True,
                'eficiencia_actividad': ':.1f',
                'total_asistentes': True,
                'tamaño_punto': False,
                'departamento': True
            },
                                        labels={
                'num_actividades': 'Número de Actividades',
                'eficiencia_actividad': 'Eficiencia (asistentes/actividad)',
                'departamento': 'Departamento'
            },
            title='Eficiencia vs Número de Actividades por Municipio'
        )
        
        # Añadir línea de tendencia
        fig_efficiency.update_layout(
                                    template='plotly_dark',
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        # Añadir línea de eficiencia promedio
        fig_efficiency.add_hline(
            y=df['eficiencia_actividad'].mean(),
            line_dash="dash",
            line_color="white",
            annotation_text=f"Eficiencia promedio: {df['eficiencia_actividad'].mean():.1f}",
            annotation_position="top right"
        )
        
        # Añadir anotaciones para municipios destacados
        top_efficiency = df.nlargest(3, 'eficiencia_actividad')
        top_activities = df.nlargest(3, 'num_actividades')
        
        for _, row in pd.concat([top_efficiency, top_activities]).drop_duplicates().iterrows():
            fig_efficiency.add_annotation(
                x=row['num_actividades'],
                y=row['eficiencia_actividad'],
                text=row['municipio'],
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-30
            )
        
        st.plotly_chart(fig_efficiency, use_container_width=True, key="efficiency_scatter")
        
        # Gráfico adicional: Distribución de eficiencia
        st.write("### 📊 Distribución de Eficiencia")
        
        # Crear histograma de eficiencia
        fig_hist = px.histogram(
            df,
            x='eficiencia_actividad',
            nbins=20,
            color_discrete_sequence=['#3366CC'],
            labels={'eficiencia_actividad': 'Eficiencia (asistentes/actividad)'},
            title='Distribución de Eficiencia entre Municipios'
        )
        
        fig_hist.update_layout(
            template='plotly_dark',
            height=400,
            bargap=0.1,
                                    margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Eficiencia (asistentes/actividad)",
            yaxis_title="Número de Municipios"
        )
        
        # Añadir línea vertical para la media
        fig_hist.add_vline(
            x=df['eficiencia_actividad'].mean(),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Media: {df['eficiencia_actividad'].mean():.1f}",
            annotation_position="top right"
        )
        
        # Añadir línea vertical para la mediana
        fig_hist.add_vline(
            x=df['eficiencia_actividad'].median(),
            line_dash="dot",
            line_color="green",
            annotation_text=f"Mediana: {df['eficiencia_actividad'].median():.1f}",
            annotation_position="top left"
        )
        
        st.plotly_chart(fig_hist, use_container_width=True, key="eficiencia_histogram")
        
        # Tabla detallada (opcional)
        with st.expander("📋 Ver Datos Detallados"):
            st.dataframe(
                df[[
                    'municipio', 'departamento', 'num_actividades',
                    'total_asistentes', 'eficiencia_actividad'
                ]].sort_values('num_actividades', ascending=False).style.format({
                    'eficiencia_actividad': '{:.1f}'
                }),
                use_container_width=True
            )
        
    except Exception as e:
        logger.error(f"Error en análisis detallado: {str(e)}")
        st.error(f"Error mostrando análisis detallado: {str(e)}")

def show_strategic_analysis(results: dict, target_activities: int = None, tipo_actividad: str = None, departamento: str = None):
    """Muestra análisis estratégico personalizado por tipo de actividad y ubicación"""
    try:
        st.subheader("📊 Análisis Estratégico de Actividades")
        
        # Obtener y validar datos
        if not results or 'data' not in results or results['data'] is None or results['data'].empty:
            st.warning("No hay datos disponibles para el análisis estratégico")
            return
            
        # Filtrar datos si es necesario
        df = results['data'].copy()
        
        # DIAGNÓSTICO: Imprimir las columnas disponibles en el log
        logger.info(f"Columnas disponibles en DataFrame original: {list(df.columns)}")
        
        if departamento and departamento != "Todos":
            df = df[df['departamento'] == departamento]
            if df.empty:
                st.warning(f"No hay datos para el departamento {departamento}")
                return

        # Obtener pesos del modelo
        weights = None
        if 'model_weights' in results:
            weights = results['model_weights']
            st.info(f"Usando pesos del modelo: {weights}")
        
        # Primero agrupar todos los datos por municipio y departamento para evitar duplicados
        municipios_df = df.groupby(['municipio', 'departamento']).agg({
            'num_actividades': 'sum',
            'total_asistentes': 'sum',
            'eficiencia_actividad': 'mean'
        }).reset_index()
        
        # Normalizar métricas para comparación justa
        metrics_to_normalize = ['num_actividades', 'total_asistentes', 'eficiencia_actividad']
            
        # Crear y ajustar un scaler para normalización
        scaler = StandardScaler()
        if len(municipios_df) > 1:  # Solo aplicar si hay más de un registro
            normalized_metrics = scaler.fit_transform(municipios_df[metrics_to_normalize])
        # Calcular score usando los pesos del modelo
        if weights:
            municipios_df['score'] = (
                normalized_metrics[:, 0] * weights.get('actividades', 0.33) +
                normalized_metrics[:, 1] * weights.get('asistentes', 0.33) +
                normalized_metrics[:, 2] * weights.get('eficiencia', 0.34)
            )
        else:
            # Si solo hay un registro, asignar un score directo
            municipios_df['score'] = 1.0

        # CORREGIDO: Calcular actividades sugeridas con mejor lógica
        # Si no se especifica un objetivo, usar el total actual como referencia
        actual_total_activities = municipios_df['num_actividades'].sum()
        
        if target_activities is None or target_activities == 0:
            effective_target = actual_total_activities
            st.info(f"No se especificó un objetivo de actividades. Usando el total actual ({int(actual_total_activities)}) como referencia.")
        else:
            effective_target = target_activities
        
        # Asegurar que los scores sean positivos para la distribución
        # Convertir scores a valores positivos sumando el mínimo si hay valores negativos
        min_score = municipios_df['score'].min()
        if min_score < 0:
            adjusted_scores = municipios_df['score'] - min_score + 0.1  # Sumamos 0.1 para evitar ceros
        else:
            adjusted_scores = municipios_df['score'] + 0.1  # Sumamos 0.1 para evitar ceros en caso de score = 0
        
        # Calcular la proporción de cada municipio basado en su score ajustado
        total_adjusted_score = adjusted_scores.sum()
        
        # Calcular las actividades sugeridas basadas en la proporción
        municipios_df['actividades_sugeridas'] = (
            adjusted_scores / total_adjusted_score * effective_target
        ).round().astype(int)
        
        # Ajustar para que el total coincida exactamente con el objetivo
        diff = effective_target - municipios_df['actividades_sugeridas'].sum()
        if diff != 0:
            # Distribuir la diferencia a los municipios con mayor score hasta que se ajuste exactamente
            indices_to_adjust = municipios_df.nlargest(abs(diff), 'score').index
            for idx in indices_to_adjust:
                municipios_df.at[idx, 'actividades_sugeridas'] += np.sign(diff)
                diff -= np.sign(diff)
                if diff == 0:
                    break
        
        # Calcular diferencia y acción recomendada
        municipios_df['diferencia'] = municipios_df['actividades_sugeridas'] - municipios_df['num_actividades']
        municipios_df['acción'] = municipios_df['diferencia'].apply(
            lambda x: "Incrementar" if x > 0 else 
                    ("Mantener" if x == 0 else "Reducir")
        )

        # Mostrar resumen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Municipios Analizados",
                len(municipios_df),
                help="Número de municipios con actividades registradas"
            )
        with col2:
            # Usamos el valor absoluto del score ajustado, que siempre es positivo
            score_medio = adjusted_scores.mean()
            st.metric(
                "Score Promedio",
                f"{score_medio:.2f}",
                help="Promedio de score de priorización (ajustado para ser positivo)"
            )
        with col3:
            st.metric(
                "Prioridad Alta",
                len(municipios_df[municipios_df['score'] > municipios_df['score'].mean()]),
                help="Municipios con score superior al promedio"
            )
        
        # Clasificar municipios por prioridad
        avg_score = municipios_df['score'].mean()
        municipios_df['prioridad'] = municipios_df['score'].apply(
            lambda x: "Alta" if x > avg_score + 0.5 else 
                     ("Media" if x > avg_score else "Baja")
        )
        
        # Modificar la sección después de calcular las actividades sugeridas
        # Justo después de calcular municipios_df['acción']

        # Agrupar por municipio y calcular los totales
        municipios_agrupados = municipios_df.groupby(['municipio', 'departamento']).agg({
            'num_actividades': 'sum',
            'actividades_sugeridas': 'sum',
            'eficiencia_actividad': 'mean',
            'score': 'mean'
        }).reset_index()

        # Recalcular diferencia y acción después de la agrupación
        municipios_agrupados['diferencia'] = municipios_agrupados['actividades_sugeridas'] - municipios_agrupados['num_actividades']
        municipios_agrupados['acción'] = municipios_agrupados['diferencia'].apply(
            lambda x: "Incrementar" if x > 0 else ("Mantener" if x == 0 else "Reducir")
        )

        # Reclasificar prioridad basada en el score medio
        avg_score = municipios_agrupados['score'].mean()
        municipios_agrupados['prioridad'] = municipios_agrupados['score'].apply(
            lambda x: "Alta" if x > avg_score + 0.5 else 
                     ("Media" if x > avg_score else "Baja")
        )
        
        # Preparar datos para mostrar
        display_cols = ['municipio', 'departamento', 'prioridad', 'score', 'num_actividades', 'eficiencia_actividad']
        display_cols.extend(['actividades_sugeridas', 'diferencia', 'acción'])
        
        # Ordenar por score descendente
        display_df = municipios_agrupados.sort_values('score', ascending=False)[display_cols].reset_index(drop=True)
        
        # Formatear columnas numéricas
        display_df['score'] = display_df['score'].round(2)
        display_df['eficiencia_actividad'] = display_df['eficiencia_actividad'].round(2)
        
        # Aplicar colores a la tabla basados en prioridad
        def highlight_prioridad(s):
            return ['background-color: #dc3545' if x == "Alta" else 
                   ('background-color: #ffc107' if x == "Media" else 
                    'background-color: #198754') for x in s]
        
        # Mostrar tabla con formato
        st.dataframe(
            display_df.style.apply(highlight_prioridad, subset=['prioridad']),
            use_container_width=True,
            height=400
        )
        
        # Opción para descargar datos completos
        csv = municipios_agrupados.to_csv(index=False)
        st.download_button(
            label="Descargar datos de priorización como CSV",
            data=csv,
            file_name="priorizacion_municipios.csv",
            mime="text/csv",
            help="Descarga los datos de priorización en formato CSV"
        )
        
        # Agregar separador visual
        st.markdown("---")
        
        # Agregar separador visual antes de los gráficos
        st.markdown("### 📊 Análisis Detallado de Priorización")

        # Crear columnas para los primeros gráficos
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de burbujas: Relación entre eficiencia, actividades y prioridad
            fig_bubble = px.scatter(
                display_df,
                x='num_actividades',
                y='eficiencia_actividad',
                size='actividades_sugeridas',
                color='prioridad',
                hover_name='municipio',
                hover_data={
                    'departamento': True,
                    'score': ':.2f',
                    'num_actividades': True,
                    'eficiencia_actividad': ':.2f',
                    'actividades_sugeridas': True
                },
                title='Distribución de Municipios por Eficiencia y Actividades',
                labels={
                    'num_actividades': 'Actividades Actuales',
                    'eficiencia_actividad': 'Eficiencia (asistentes/actividad)',
                    'actividades_sugeridas': 'Actividades Sugeridas'
                },
                color_discrete_map={
                    'Alta': '#dc3545',
                    'Media': '#ffc107',
                    'Baja': '#198754'
                }
            )
            fig_bubble.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_bubble, use_container_width=True)

        with col2:
            # Gráfico de radar para los municipios top 5
            top_5_municipios = display_df.nlargest(5, 'score')
            
            fig_radar = go.Figure()
            
            metrics = ['score', 'num_actividades', 'eficiencia_actividad', 'actividades_sugeridas']
            metric_names = ['Score', 'Act. Actuales', 'Eficiencia', 'Act. Sugeridas']
            
            for _, mun in top_5_municipios.iterrows():
                values = [mun[metric] for metric in metrics]
                # Normalizar valores para mejor visualización
                max_values = top_5_municipios[metrics].max()
                normalized_values = [(val/max_val)*100 for val, max_val in zip(values, max_values)]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=normalized_values + [normalized_values[0]],  # Cerrar el polígono
                    theta=metric_names + [metric_names[0]],  # Cerrar el polígono
                    name=mun['municipio'],
                    fill='toself',
                    hovertemplate="<b>%{theta}</b><br>" +
                                 "Valor normalizado: %{r:.1f}%<br>" +
                                 "<extra></extra>"
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                title="Comparación Top 5 Municipios Priorizados",
                template='plotly_dark',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Análisis de Grupos de Interés
        st.markdown("### 🎯 Análisis por Grupos de Interés")

        # Verificar y obtener la columna correcta de grupos de interés
        grupo_col = None
        if 'nombre_grupo_interes' in df.columns:
            grupo_col = 'nombre_grupo_interes'
        elif 'grupo_interes' in df.columns:
            grupo_col = 'grupo_interes'

        if grupo_col:
            # Preparar datos de grupos de interés incluyendo municipio
            gi_data = df.groupby([grupo_col, 'municipio']).agg({
                'num_actividades': 'sum',
                'total_asistentes': 'sum',
                'eficiencia_actividad': 'mean',
                'departamento': 'first'  # Añadir departamento para más contexto
            }).reset_index()

            # Crear etiqueta combinada para mejor visualización
            gi_data['gi_municipio'] = gi_data[grupo_col] + ' (' + gi_data['municipio'] + ')'

            # Crear columnas para los gráficos
            col3, col4 = st.columns(2)

            # Actualizar los gráficos con la nueva información
            with col3:
                # Gráfico de barras horizontales con los tres colores originales y leyenda
                fig_activities = go.Figure()
                
                # Calcular los rangos para los colores
                max_actividades = gi_data['num_actividades'].max()
                rangos = [
                    (0, max_actividades * 0.33),
                    (max_actividades * 0.33, max_actividades * 0.66),
                    (max_actividades * 0.66, max_actividades)
                ]
                colores = ['#198754', '#ffc107', '#dc3545']  # Verde, Amarillo, Rojo
                
                # Crear las categorías de actividades
                gi_data['categoria'] = pd.cut(
                    gi_data['num_actividades'],
                    bins=[0, rangos[0][1], rangos[1][1], max_actividades],
                    labels=['Bajo', 'Medio', 'Alto']
                )
                
                # Añadir barras con colores basados en el número de actividades
                for categoria, color in zip(['Bajo', 'Medio', 'Alto'], colores):
                    mask = gi_data['categoria'] == categoria
                    fig_activities.add_trace(go.Bar(
                        y=gi_data[mask][grupo_col] + ' (' + gi_data[mask]['municipio'] + ')',
                        x=gi_data[mask]['num_actividades'],
                        orientation='h',
                        name=f'Nivel {categoria}',
                        marker_color=color,
                        text=gi_data[mask]['num_actividades'],
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>' +
                                    'Actividades: %{x}<br>' +
                                    'Nivel: ' + categoria + '<extra></extra>'
                    ))

                fig_activities.update_layout(
                    title="Distribución de Actividades por Grupo de Interés",
                    xaxis_title="Número de Actividades",
                    yaxis_title="",
                    template='plotly_dark',
                    height=800,
                    margin=dict(l=20, r=20, t=40, b=20),
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        title="Nivel de Actividades"
                    )
                )
                st.plotly_chart(fig_activities, use_container_width=True)

            with col4:
                # Gráfico de dispersión con los mismos tres colores
                # Calcular rangos para eficiencia usando percentiles en lugar de divisiones fijas
                gi_data['categoria_eficiencia'] = pd.qcut(
                    gi_data['eficiencia_actividad'],
                    q=3,
                    labels=['Bajo', 'Medio', 'Alto']
                )
                
                fig_scatter = go.Figure()
                
                # Añadir puntos para cada categoría de eficiencia
                for categoria, color in zip(['Bajo', 'Medio', 'Alto'], colores):
                    mask = gi_data['categoria_eficiencia'] == categoria
                    fig_scatter.add_trace(go.Scatter(
                        x=gi_data[mask]['total_asistentes'],
                        y=gi_data[mask]['eficiencia_actividad'],
                        mode='markers',
                        name=f'Eficiencia {categoria}',
                        marker=dict(
                            size=gi_data[mask]['num_actividades']/2,
                            color=color,
                            opacity=0.8,  # Aumentar opacidad
                            sizemin=5,
                            sizeref=2.0 * gi_data['num_actividades'].max() / (40**2),
                            sizemode='area'
                        ),
                        text=gi_data[mask][grupo_col] + ' (' + gi_data[mask]['municipio'] + ')',
                        hovertemplate='<b>%{text}</b><br>' +
                                    'Asistentes: %{x}<br>' +
                                    'Eficiencia: %{y:.2f}<br>' +
                                    'Nivel: ' + categoria + '<extra></extra>'
                    ))
                
                fig_scatter.update_layout(
                    title='Relación entre Eficiencia y Asistencia por Grupo',
                    xaxis_title='Total de Asistentes',
                    yaxis_title='Eficiencia (asistentes/actividad)',
                    template='plotly_dark',
                    height=800,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        title="Nivel de Eficiencia"
                    )
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

        # Métricas de resumen en un formato más compacto
        st.markdown("### 📊 Métricas Clave por Grupo de Interés")
        
        # Crear una tabla estilizada para las métricas principales
        col_metrics = st.columns(4)
        
        with col_metrics[0]:
            top_gi = gi_data.nlargest(1, 'num_actividades')
            st.markdown(
                f"""
                <div style='background-color: rgba(40, 40, 70, 0.8); padding: 10px; border-radius: 5px; text-align: center;'>
                    <p style='color: #4CAF50; font-size: 14px; margin: 0;'>Grupo más Activo</p>
                    <h4 style='font-size: 16px; margin: 5px 0;'>{top_gi[grupo_col].iloc[0]}</h4>
                    <p style='color: #888; font-size: 12px; margin: 0;'>{int(top_gi['num_actividades'].iloc[0])} actividades</p>
                    <p style='color: #888; font-size: 12px; margin: 0;'>Municipio: {top_gi['municipio'].iloc[0]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_metrics[1]:
            top_efficient_gi = gi_data.nlargest(1, 'eficiencia_actividad')
            st.markdown(
                f"""
                <div style='background-color: rgba(40, 40, 70, 0.8); padding: 10px; border-radius: 5px; text-align: center;'>
                    <p style='color: #4CAF50; font-size: 14px; margin: 0;'>Grupo más Eficiente</p>
                    <h4 style='font-size: 16px; margin: 5px 0;'>{top_efficient_gi[grupo_col].iloc[0]}</h4>
                    <p style='color: #888; font-size: 12px; margin: 0;'>{top_efficient_gi['eficiencia_actividad'].iloc[0]:.2f} asist/act</p>
                    <p style='color: #888; font-size: 12px; margin: 0;'>Municipio: {top_efficient_gi['municipio'].iloc[0]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_metrics[2]:
            municipios_unicos = gi_data['municipio'].nunique()
            st.markdown(
                f"""
                <div style='background-color: rgba(40, 40, 70, 0.8); padding: 10px; border-radius: 5px; text-align: center;'>
                    <p style='color: #4CAF50; font-size: 14px; margin: 0;'>Total Grupos Activos</p>
                    <h4 style='font-size: 16px; margin: 5px 0;'>{len(gi_data)}</h4>
                    <p style='color: #888; font-size: 12px; margin: 0;'>en {municipios_unicos} municipios</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_metrics[3]:
            promedio_eficiencia_gi = gi_data['eficiencia_actividad'].mean()
            st.markdown(
                f"""
                <div style='background-color: rgba(40, 40, 70, 0.8); padding: 10px; border-radius: 5px; text-align: center;'>
                    <p style='color: #4CAF50; font-size: 14px; margin: 0;'>Eficiencia Promedio</p>
                    <h4 style='font-size: 16px; margin: 5px 0;'>{promedio_eficiencia_gi:.2f}</h4>
                    <p style='color: #888; font-size: 12px; margin: 0;'>asistentes/actividad</p>
                    <p style='color: #888; font-size: 12px; margin: 0;'>todos los grupos</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Agregar separador visual antes de la priorización por grupos de interés
        st.markdown("---")

        # Mantener la llamada original a show_interest_group_prioritization
        show_interest_group_prioritization({
            'data': df,
            'target_activities': target_activities
        })
        
    except Exception as e:
        logger.error(f"Error en análisis estratégico: {str(e)}")
        st.error(f"Error en el análisis estratégico: {str(e)}")

def main():
    try:
        # Inicializar variables de estado de sesión si no existen
        if 'analysis_done' not in st.session_state:
            st.session_state.analysis_done = False
            st.session_state.results = None
            st.session_state.maps = None
            st.session_state.viz_data = None
            st.session_state.map_html = None  # Estado para almacenar el HTML del mapa
        
        # Título principal con estilo
        st.title("🌎 Análisis Geográfico de Actividades")
        st.markdown("---")
        
        # Sidebar para filtros
        with st.sidebar:
            st.header("Filtros")
            
            # Cargar datos para filtros
            data_loader = DataLoader()
            
            # Filtro por zona geográfica
            zonas = ["Todas"] + data_loader.get_zonas_geograficas()
            zona = st.selectbox("Zona Geográfica", zonas)
            
            # Filtro por departamento
            if zona != "Todas":
                departamentos = ["Todos"] + data_loader.get_departamentos_por_zona(zona)
            else:
                departamentos = ["Todos"] + data_loader.get_departamentos_por_zona(None)
            
            departamento = st.selectbox("Departamento", departamentos)
            
            # Filtro por municipio
            if departamento != "Todos":
                municipios = ["Todos"] + data_loader.get_municipios(departamento)
            else:
                municipios = ["Todos"]
            
            municipio = st.selectbox("Municipio", municipios)
            
            # Filtro por fecha
            st.write("### Rango de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("Fecha Inicio", value=pd.to_datetime("2014-01-01"))
            with col2:
                fecha_fin = st.date_input("Fecha Fin", value=pd.to_datetime("now"))
            
            # Filtro por tipo de actividad
            st.write("### Tipo de Actividad")
            tipos_actividad = ["Todos", "Talleres", "Simulacros", "Divulgaciones", 
                              "Apoyo a simulacro", "Kits", "Planes comunitarios", 
                              "Asesoría especializada", "Simulaciones"]
            
            tipo_actividad = st.selectbox("Seleccionar", tipos_actividad)
            
            # Parámetros adicionales
            st.write("### Parámetros Avanzados")
            target_activities = st.number_input(
                "Actividades Objetivo", 
                min_value=0, 
                value=0,
                help="Número objetivo de actividades para análisis estratégico"
            )
            
            # Botón para ejecutar análisis
            st.markdown("---")
            if st.button("Ejecutar Análisis", type="primary", use_container_width=True):
                # Mostrar barra de progreso
                progress_bar = st.progress(0)
                
                try:
                    # Inicializar predictor
                    progress_bar.progress(10)
                    predictor = GeographicPredictor()
                    
                    # Preparar datos de entrada
                    progress_bar.progress(20)
                    
                    # Determinar tipo de actividad seleccionado
                    tipo_actividad_seleccionado = None
                    if tipo_actividad != "Todos":
                        tipo_actividad_seleccionado = tipo_actividad
                        logger.info(f"Tipo de actividad seleccionado: {tipo_actividad_seleccionado}")
                    
                    input_data = {
                        'zona_geografica': zona if zona != "Todas" else None,
                        'departamento': departamento if departamento != "Todos" else None,
                        'municipio': municipio if municipio != "Todos" else None,
                        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
                        'tipo_actividad': tipo_actividad_seleccionado if tipo_actividad_seleccionado != "Todos" else None
                    }
                    
                    # Mostrar datos de entrada para depuración
                    logger.info(f"Datos de entrada para predicción: {input_data}")
                    
                    # Realizar predicción
                    results = predictor.predict(input_data)
                    
                    # Mostrar información de depuración sobre resultados
                    if results.get('data') is not None:
                        logger.info(f"Tipos únicos en resultados: {results['data']['categoria_unica'].unique()}")
                        logger.info(f"Total de registros obtenidos: {len(results['data'])}")
                    
                    if results.get('error'):
                        st.error(results['error'])
                        return
                    
                    if results.get('data') is None or results['data'].empty:
                        st.warning("No se encontraron datos para los filtros seleccionados")
                        return
                    
                    # Preparar visualizaciones
                    progress_bar.progress(40)
                    viz_data = prepare_visualization_data(results)
                    
                    # Crear mapas
                    progress_bar.progress(60)
                    maps = create_maps(results, predictor)
                    
                    # Guardar HTML del mapa para asegurar que no desaparezca
                    if 'density_map' in maps:
                        try:
                            import tempfile
                            import os
                            
                            # Crear archivo temporal
                            temp_dir = tempfile.mkdtemp()
                            temp_path = os.path.join(temp_dir, "density_map.html")
                            
                            # Guardar mapa como HTML
                            maps['density_map'].save(temp_path)
                            
                            # Leer el HTML guardado
                            with open(temp_path, 'r', encoding='utf-8') as f:
                                st.session_state.map_html = f.read()
                            
                            # Limpiar archivo temporal
                            try:
                                os.remove(temp_path)
                                os.rmdir(temp_dir)
                            except:
                                pass
                        except Exception as e:
                            logger.error(f"Error guardando HTML del mapa: {str(e)}")
                    
                    progress_bar.progress(80)
                    
                    # Guardar en estado de sesión
                    st.session_state.results = results
                    st.session_state.maps = maps
                    st.session_state.viz_data = viz_data
                    st.session_state.analysis_done = True
                    
                    progress_bar.progress(100)
                    
                except Exception as e:
                    logger.error(f"Error en el análisis: {str(e)}")
                    st.error("Ocurrió un error durante el análisis. Por favor, intente de nuevo.")
                    progress_bar.empty()
        
        # Mostrar resultados si el análisis está hecho
        if st.session_state.analysis_done and st.session_state.results is not None:
            # Obtener resultados de la sesión
            results = st.session_state.results
            maps = st.session_state.maps
            viz_data = st.session_state.viz_data
            
            # Crear pestañas principales para la aplicación (eliminando la pestaña de análisis temporal)
            tab_geo, tab_estrategico, tab_detalle = st.tabs([
                "Análisis Geográfico", 
                "Análisis Estratégico", 
                "Análisis Detallado"
            ])
            
            # Pestaña 1: Análisis Geográfico
            with tab_geo:
                try:
                    show_analysis(results, viz_data, maps)
                except Exception as e:
                    logger.error(f"Error mostrando análisis geográfico: {str(e)}")
                    st.error(f"Error mostrando análisis geográfico: {str(e)}")
            
            # Pestaña 2: Análisis Estratégico (ahora como pestaña independiente)
            with tab_estrategico:
                try:
                    show_strategic_analysis(
                        results, 
                        target_activities=target_activities,
                        tipo_actividad=tipo_actividad if tipo_actividad != "Todos" else None,
                        departamento=None if departamento == "Todos" else departamento
                    )
                except Exception as e:
                    logger.error(f"Error mostrando análisis estratégico: {str(e)}")
                    st.error(f"Error mostrando análisis estratégico: {str(e)}")
            
            # Pestaña 3: Análisis Detallado
            with tab_detalle:
                try:
                    st.subheader("📋 Análisis Detallado por Municipio", divider="blue")
                    show_detailed_analysis(results['data'])
                except Exception as e:
                    logger.error(f"Error mostrando análisis detallado: {str(e)}")
                    st.error(f"Error mostrando análisis detallado: {str(e)}")
            
            st.success(f"Análisis completado: {len(results['data'])} municipios analizados")
                
    except Exception as e:
        logger.error(f"Error en la aplicación: {str(e)}")
        st.error("Ocurrió un error inesperado. Por favor, intenta de nuevo.")

    # Información adicional
    st.markdown("---")
    with st.expander("ℹ️ Acerca de este análisis"):
        st.markdown("""
        Este dashboard permite analizar patrones geográficos en la distribución de actividades:
        
        - **Clustering K-means**: Agrupa municipios con características similares
        - **Análisis de Densidad**: Identifica zonas de alta concentración de actividades
        - **Recomendaciones**: Sugiere áreas prioritarias y optimizaciones
        
        Los análisis consideran múltiples variables:
        - Ubicación geográfica
        - Número de actividades
        - Total de asistentes
        - Eficiencia de las actividades
        - Intensidad mensual
        """)

def show_interest_group_prioritization(results: dict):
    """Muestra la priorización por grupos de interés por municipio"""
    try:
        # Obtener datos
        df = results.get('data')
        if df is None or df.empty:
            st.warning("No hay datos disponibles para mostrar priorización por grupos de interés.")
            return
            
        st.header("🎯 Priorización por Grupo de Interés", help="Distribución de actividades entre grupos de interés por municipio")
        
        # Obtener el valor de actividades objetivo
        target_activities = 100  # Valor por defecto
        if 'target_activities' in results and results['target_activities'] is not None:
            try:
                target_activities = int(results['target_activities'])
            except:
                pass
        
        # PASO 1: Calcular actividades sugeridas por municipio
        # =======================================================
        # Primero agrupamos por municipio
        municipios_df = df.groupby(['municipio', 'departamento']).agg({
                        'num_actividades': 'sum',
                        'total_asistentes': 'sum',
                        'eficiencia_actividad': 'mean'
                    }).reset_index()
                    
        # Calcular score para cada municipio
        metrics = ['num_actividades', 'total_asistentes', 'eficiencia_actividad']
        
        # Normalizar métricas 
        municipios_df['score'] = 0.0
        
        if len(municipios_df) > 1:
            # Usamos un enfoque más simple sin dependencia externa
            for col in metrics:
                # Normalización manual: (x - min) / (max - min) si el rango > 0
                min_val = municipios_df[col].min()
                max_val = municipios_df[col].max()
                if max_val > min_val:
                    municipios_df[f'{col}_norm'] = (municipios_df[col] - min_val) / (max_val - min_val)
                else:
                    municipios_df[f'{col}_norm'] = 0.5  # Valor medio si no hay variación
            
            # Promedio simple de las métricas normalizadas
            norm_cols = [f'{col}_norm' for col in metrics]
            municipios_df['score'] = municipios_df[norm_cols].mean(axis=1)
        else:
            municipios_df['score'] = 1.0  # Si solo hay un municipio
        
        # Calcular actividades sugeridas (distribución proporcional)
        score_total = municipios_df['score'].sum()
        if score_total > 0:
            municipios_df['actividades_sugeridas'] = np.ceil(
                municipios_df['score'] / score_total * target_activities
            ).astype(int)
        else:
            # Si todos los scores son 0, distribuir equitativamente
            municipios_df['actividades_sugeridas'] = np.ceil(
                target_activities / len(municipios_df)
            ).astype(int)
            
        # Garantizar mínimo 1 actividad si el score es positivo
        municipios_df.loc[municipios_df['score'] > 0, 'actividades_sugeridas'] = \
            municipios_df.loc[municipios_df['score'] > 0, 'actividades_sugeridas'].clip(lower=1)
            
        # Filtrar solo municipios con actividades sugeridas
        municipios_priorizados = municipios_df[municipios_df['actividades_sugeridas'] > 0].copy()
        
        if municipios_priorizados.empty:
            st.warning("No hay municipios priorizados para asignar grupos de interés. Revise los criterios de priorización.")
            return
            
        # Ordenar por score de mayor a menor
        municipios_priorizados = municipios_priorizados.sort_values('score', ascending=False)
        
        # PASO 2: Calcular priorización por grupos de interés
        # =======================================================
        
        # Verificar columna de grupo de interés
        if 'nombre_grupo_interes' in df.columns:
            grupo_col = 'nombre_grupo_interes'
        elif 'grupo_interes' in df.columns:
            grupo_col = 'grupo_interes'
        else:
            st.error("No se encontró columna de grupos de interés en los datos.")
            return
        
        # Lista para almacenar resultados
        resultados_gi = []
        
        # Para cada municipio priorizado
        for _, municipio_row in municipios_priorizados.iterrows():
            municipio = municipio_row['municipio']
            departamento = municipio_row['departamento']
            actividades_asignadas = int(municipio_row['actividades_sugeridas'])
            score_municipio = municipio_row['score']
            
            # Filtrar datos solo para este municipio
            datos_municipio = df[df['municipio'] == municipio]
            
            # Si no hay datos para este municipio, continuar
            if datos_municipio.empty:
                continue
                
            # Agrupar por grupo de interés
            grupos_municipio = datos_municipio.groupby(grupo_col).agg({
                'eficiencia_actividad': 'mean',
                'num_actividades': 'sum',
                'total_asistentes': 'sum'
            }).reset_index()
            
            # Si no hay grupos, continuar
            if grupos_municipio.empty:
                continue
                
            # Calcular score para cada grupo de interés (normalización manual)
            gi_metrics = ['eficiencia_actividad', 'num_actividades', 'total_asistentes']
            
            # Normalizar cada métrica
            for col in gi_metrics:
                min_val = grupos_municipio[col].min()
                max_val = grupos_municipio[col].max()
                if max_val > min_val:
                    grupos_municipio[f'{col}_norm'] = (grupos_municipio[col] - min_val) / (max_val - min_val)
                else:
                    grupos_municipio[f'{col}_norm'] = 0.5
                    
            # Calcular score como promedio de las métricas normalizadas
            norm_cols = [f'{col}_norm' for col in gi_metrics]
            grupos_municipio['score_gi'] = grupos_municipio[norm_cols].mean(axis=1)
            
            # Ordenar por score
            grupos_municipio = grupos_municipio.sort_values('score_gi', ascending=False)
            
            # Seleccionar los mejores grupos hasta satisfacer las actividades asignadas
            num_grupos = min(len(grupos_municipio), actividades_asignadas)
            
            for i in range(num_grupos):
                grupo = grupos_municipio.iloc[i]
                resultados_gi.append({
                    'municipio': municipio,
                    'departamento': departamento,
                    'grupo_interes': grupo[grupo_col],
                    'eficiencia_actividad': grupo['eficiencia_actividad'],
                    'num_actividades': grupo['num_actividades'],
                    'score_gi': grupo['score_gi'],
                    'actividades_gi': 1,  # Una actividad por grupo
                    'total_actividades_municipio': actividades_asignadas
                })
        
        # PASO 3: Mostrar resultados
        # =======================================================
        
        # Verificar si hay resultados
        if not resultados_gi:
            st.warning("No se pudieron generar recomendaciones de grupos de interés. Verifique que los municipios priorizados tengan información de grupos de interés.")
            st.info(f"Hay {len(municipios_priorizados)} municipios priorizados pero no se pudo asociar información de grupos de interés.")
            return
        
        # Convertir a DataFrame y ordenar
        resultados_df = pd.DataFrame(resultados_gi)
        resultados_df = resultados_df.sort_values(['municipio', 'score_gi'], ascending=[True, False])
        
        # Categorizar eficiencia usando quantiles
        resultados_df['categoria_eficiencia'] = pd.qcut(
            resultados_df['eficiencia_actividad'],
            q=3,
            labels=['Baja', 'Media', 'Alta']
        )

        # Ordenar por eficiencia (de mayor a menor) y luego por municipio
        resultados_df = resultados_df.sort_values(
            ['eficiencia_actividad', 'municipio'], 
            ascending=[False, True]
        )

        # Formatear para mostrar (actualizar el rename para incluir la nueva columna)
        display_df = resultados_df.rename(columns={
            'municipio': 'Municipio',
            'departamento': 'Departamento',
            'grupo_interes': 'Grupo de Interés',
            'eficiencia_actividad': 'Eficiencia',
            'num_actividades': 'Actividades Actuales',
            'score_gi': 'Score GI',
            'actividades_gi': 'Actividades GI',
            'total_actividades_municipio': 'Total Actividades Municipio',
            'categoria_eficiencia': 'Nivel Eficiencia'
        })

        # Función para aplicar colores según la categoría de eficiencia
        def color_eficiencia(val):
            colors = {
                'Alta': 'background-color: #dc3545',    # Rojo para alta
                'Media': 'background-color: #ffc107',   # Amarillo se mantiene
                'Baja': 'background-color: #198754'     # Verde para baja
            }
            return colors.get(val, '')

        # Mostrar tabla con formato y colores
        st.dataframe(
            display_df.style
            .format({
                'Eficiencia': '{:.2f}',
                'Score GI': '{:.2f}'
            })
            .applymap(color_eficiencia, subset=['Nivel Eficiencia'])
            .set_properties(**{
                'color': 'white',
                'font-weight': 'bold'
            }, subset=['Nivel Eficiencia']),
            use_container_width=True,
            height=400
        )

        # Opción para descargar
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar priorización de grupos de interés",
            csv_data,
            "priorizacion_grupos_interes.csv",
            "text/csv",
            key="download-gi-csv"
        )
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.error(f"Error en priorización de grupos de interés: {str(e)}")
        logger.error(error_msg)
        st.error(f"Error en priorización de grupos de interés: {str(e)}")
        # Mostrar información adicional para depuración
        st.error("Verifique que los datos contengan la estructura esperada.")

def create_enhanced_heatmap(df: pd.DataFrame, value_column: str = 'num_actividades', title: str = 'Mapa de Calor de Actividades') -> folium.Map:
    """
    Crea un mapa de calor básico pero funcional.
    
    Args:
        df: DataFrame con datos geográficos
        value_column: Columna a utilizar para los valores del mapa de calor
        title: Título del mapa
        
    Returns:
        Mapa de folium con el mapa de calor
    """
    try:
        # Verificar y preparar datos de manera segura
        df = df.copy()
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        
        # Eliminar filas con datos faltantes
        df = df.dropna(subset=['latitud', 'longitud', value_column])
        
        if df.empty:
            logger.warning("No hay datos válidos para crear el mapa de calor")
            return None
            
        # Crear mapa base simple
        center_lat = df['latitud'].mean()
        center_lon = df['longitud'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='CartoDB positron',
            control_scale=True
        )
        
        # Preparar datos para el heatmap (solo coordenadas y valores)
        heat_data = []
        for _, row in df.iterrows():
            try:
                lat = float(row['latitud'])
                lon = float(row['longitud'])
                # Usamos el valor directamente sin normalización
                val = float(row[value_column])
                heat_data.append([lat, lon, val])
            except (ValueError, TypeError):
                continue
        
        # Crear heatmap simple sin componentes adicionales
        if heat_data:
            HeatMap(heat_data, radius=15, blur=10).add_to(m)
        
        # NO añadimos marcadores ni popups que podrían causar el error
        
        return m
        
    except Exception as e:
        logger.error(f"Error creando mapa de calor: {str(e)}")
        return None

if __name__ == "__main__":
    main() 