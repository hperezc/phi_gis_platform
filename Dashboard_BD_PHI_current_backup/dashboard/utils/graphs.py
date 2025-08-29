import plotly.graph_objects as go
import plotly.express as px

def create_trend_graph(df):
    """Crea el gráfico de tendencia temporal"""
    if df.empty:
        return go.Figure()
    
    fig = px.line(df, 
                  x='fecha', 
                  y='total_actividades',
                  color='zona_geografica',
                  title='Tendencia de Actividades por Zona')
    return fig

def create_distribution_graph(df):
    """Crea el gráfico de distribución"""
    if df.empty:
        return go.Figure()
    
    fig = px.histogram(df, 
                      x='total_asistentes',
                      color='zona_geografica',
                      title='Distribución de Asistentes por Zona')
    return fig

def create_boxplot_graph(df):
    """Crea el gráfico de boxplot"""
    if df.empty:
        return go.Figure()
    
    fig = px.box(df, 
                 x='zona_geografica',
                 y='total_asistentes',
                 title='Distribución de Asistentes por Zona')
    return fig

def create_animation_graph(df):
    """Crea el gráfico animado"""
    if df.empty:
        return go.Figure()
    
    fig = px.scatter(df,
        x='total_actividades',
        y='total_asistentes',
        size='eficiencia',
        color='zona_geografica',
        hover_name='municipio',
        animation_frame='mes_ano',
        title='Evolución de Actividades y Asistentes por Municipio')
    return fig

# Funciones para gráficos avanzados
def create_detailed_temporal_graph(df):
    """Crea el gráfico temporal detallado"""
    if df.empty:
        return go.Figure()
    
    fig = px.line(df, 
                  x='fecha',
                  y=['total_actividades', 'total_asistentes'],
                  title='Análisis Temporal Detallado')
    return fig

def create_cumulative_trend_graph(df):
    """Crea el gráfico de tendencia acumulada"""
    if df.empty:
        return go.Figure()
    
    df['acumulado'] = df['total_actividades'].cumsum()
    fig = px.line(df,
                  x='fecha',
                  y='acumulado',
                  title='Tendencia Acumulada de Actividades')
    return fig

def create_attendees_distribution_graph(df):
    """Crea el gráfico de distribución de asistentes"""
    if df.empty:
        return go.Figure()
    
    fig = px.histogram(df,
                      x='total_asistentes',
                      title='Distribución de Asistentes')
    return fig

def create_attendees_boxplot_graph(df):
    """Crea el gráfico de boxplot de asistentes"""
    if df.empty:
        return go.Figure()
    
    fig = px.box(df,
                 y='total_asistentes',
                 title='Distribución de Asistentes (Boxplot)')
    return fig

def create_comparative_graph(df):
    """Crea el gráfico comparativo"""
    if df.empty:
        return go.Figure()
    
    fig = px.bar(df,
                 x='zona_geografica',
                 y='total_actividades',
                 title='Comparativo por Zonas')
    return fig

def create_efficiency_graph(df):
    """Crea el gráfico de eficiencia"""
    if df.empty:
        return go.Figure()
    
    fig = px.scatter(df,
                    x='total_actividades',
                    y='eficiencia',
                    color='zona_geografica',
                    title='Eficiencia por Zona')
    return fig 