import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from loguru import logger

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from predict_temporal import TemporalPredictor
from utils.data_loader import DataLoader

# Configuración de la página
st.set_page_config(
    page_title="Análisis Temporal de Actividades",
    page_icon="📊",
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
    .metric-card {
        background-color: #2C2C2C;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
        text-align: center;
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

def get_municipios(departamento: str) -> list:
    """Obtiene lista de municipios para un departamento"""
    data_loader = DataLoader()
    return data_loader.get_municipios(departamento)

def calculate_comparison_metrics(historical_data: dict) -> tuple:
    """Calcula métricas de comparación"""
    try:
        if not historical_data or not historical_data.get('dates') or not historical_data.get('activities'):
            logger.warning("No hay suficientes datos para calcular métricas de comparación")
            return 0, 0, 0
            
        df = pd.DataFrame({
            'fecha': pd.to_datetime(historical_data['dates']),
            'actividades': historical_data['activities']
        })
        
        if df.empty:
            return 0, 0, 0
        
        # Valor actual (promedio últimos 3 meses)
        current_value = df['actividades'].tail(3).mean()
        
        # Comparación con mismo período año anterior
        current_year = df['fecha'].max().year
        current_month = df['fecha'].max().month
        
        last_year_same_period = df[
            (df['fecha'].dt.year == current_year - 1) & 
            (df['fecha'].dt.month.isin([m for m in range(current_month-2, current_month+1) if m > 0]))
        ]
        
        if not last_year_same_period.empty:
            last_year_value = last_year_same_period['actividades'].mean()
            delta_percent = ((current_value - last_year_value) / last_year_value * 100) if last_year_value != 0 else 0
        else:
            delta_percent = 0
        
        # Comparación con promedio histórico
        historical_mean = df['actividades'].mean()
        hist_delta = ((current_value - historical_mean) / historical_mean * 100) if historical_mean != 0 else 0
        
        return current_value, delta_percent, hist_delta
        
    except Exception as e:
        logger.error(f"Error calculando métricas de comparación: {str(e)}")
        return 0, 0, 0

def create_comparison_chart(historical_data: dict) -> go.Figure:
    """Crea gráfico de comparación temporal avanzado"""
    try:
        if not historical_data or not historical_data.get('dates') or not historical_data.get('activities'):
            # Si no hay datos, devolver un gráfico vacío con mensaje
            fig = go.Figure()
            fig.add_annotation(
                text="No hay suficientes datos para mostrar el análisis comparativo",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color="white", size=14)
            )
            return fig
            
        df = pd.DataFrame({
            'fecha': pd.to_datetime(historical_data['dates']),
            'actividades': historical_data['activities']
        })
        
        if df.empty or len(df) < 3:  # Necesitamos al menos 3 registros para un análisis significativo
            fig = go.Figure()
            fig.add_annotation(
                text="No hay suficientes datos para mostrar el análisis comparativo",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color="white", size=14)
            )
            return fig
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Comparación Interanual',
                'Evolución por Períodos'
            ),
            vertical_spacing=0.15
        )
        
        # 1. Comparación Interanual
        df['año'] = df['fecha'].dt.year
        df['mes'] = df['fecha'].dt.month
        
        pivot_df = df.pivot(index='mes', columns='año', values='actividades')
        
        for año in pivot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
                    y=pivot_df[año],
                    name=str(año),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
        
        # 2. Evolución por Períodos
        # Verificar que tenemos suficientes datos para hacer cortes significativos
        if len(df['fecha'].dt.year.unique()) >= 2:
            df['periodo'] = pd.cut(
                df['fecha'].dt.year,
                bins=min(3, len(df['fecha'].dt.year.unique())),
                labels=['Inicial', 'Intermedio', 'Reciente'][:min(3, len(df['fecha'].dt.year.unique()))]
            )
            
            period_stats = df.groupby('periodo')['actividades'].agg(['mean', 'std']).reset_index()
            
            fig.add_trace(
                go.Bar(
                    x=period_stats['periodo'],
                    y=period_stats['mean'],
                    error_y=dict(
                        type='data',
                        array=period_stats['std'],
                        visible=True
                    ),
                    name='Promedio por Período'
                ),
                row=2, col=1
            )
        else:
            # Si no hay suficientes años, mostrar un mensaje
            fig.add_annotation(
                text="Se requieren datos de múltiples años para mostrar evolución por períodos",
                xref="x", yref="y",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color="white", size=12),
                row=2, col=1
            )
        
        # Actualizar layout
        fig.update_layout(
            height=800,
            showlegend=True,
            template='plotly_dark',
            title={
                'text': 'Análisis Comparativo Temporal',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            }
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text="Mes", row=1, col=1)
        fig.update_xaxes(title_text="Período", row=2, col=1)
        fig.update_yaxes(title_text="Actividades", row=1, col=1)
        fig.update_yaxes(title_text="Promedio de Actividades", row=2, col=1)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico de comparación: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error al crear gráfico comparativo: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="red", size=14)
        )
        return fig

def create_trend_analysis(historical_data: dict) -> go.Figure:
    """Crea análisis de tendencias y ciclos"""
    try:
        df = pd.DataFrame({
            'fecha': pd.to_datetime(historical_data['dates']),
            'actividades': historical_data['activities']
        })
        
        # Calcular componentes de tendencia
        df['MA3'] = df['actividades'].rolling(window=3).mean()
        df['MA6'] = df['actividades'].rolling(window=6).mean()
        df['MA12'] = df['actividades'].rolling(window=12).mean()
        
        # Crear figura
        fig = go.Figure()
        
        # Datos originales
        fig.add_trace(
            go.Scatter(
                x=df['fecha'],
                y=df['actividades'],
                name='Actividades',
                mode='lines+markers',
                line=dict(color='blue', width=1),
                marker=dict(size=4)
            )
        )
        
        # Medias móviles
        fig.add_trace(
            go.Scatter(
                x=df['fecha'],
                y=df['MA3'],
                name='Media Móvil 3 meses',
                line=dict(color='red', dash='dot')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['fecha'],
                y=df['MA6'],
                name='Media Móvil 6 meses',
                line=dict(color='green', dash='dash')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['fecha'],
                y=df['MA12'],
                name='Media Móvil 12 meses',
                line=dict(color='yellow', dash='longdash')
            )
        )
        
        # Actualizar layout
        fig.update_layout(
            title='Análisis de Tendencias y Ciclos',
            xaxis_title='Fecha',
            yaxis_title='Actividades',
            template='plotly_dark',
            height=400
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error en análisis de tendencias: {str(e)}")
        return go.Figure()

def create_correlation_analysis(historical_data: dict) -> go.Figure:
    """Crea análisis de correlaciones"""
    try:
        df = pd.DataFrame({
            'fecha': pd.to_datetime(historical_data['dates']),
            'actividades': historical_data['activities']
        })
        
        # Agregar variables temporales
        df['mes'] = df['fecha'].dt.month
        df['año'] = df['fecha'].dt.year
        df['dia_semana'] = df['fecha'].dt.dayofweek
        
        # Crear matriz de correlación
        corr_data = pd.DataFrame({
            'Mes': df.groupby('mes')['actividades'].mean(),
            'Día Semana': df.groupby('dia_semana')['actividades'].mean(),
            'Año': df.groupby('año')['actividades'].mean()
        }).corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_data,
            x=corr_data.columns,
            y=corr_data.columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1
        ))
        
        fig.update_layout(
            title='Correlación entre Variables Temporales',
            template='plotly_dark'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando análisis de correlaciones: {str(e)}")
        return go.Figure()

def main():
    st.title("📊 Análisis Temporal de Actividades")
    
    # Inicializar data loader
    data_loader = DataLoader()
    
    # Sidebar para filtros
    st.sidebar.header("🔍 Filtros")
    
    # Obtener departamentos
    departamentos = ["Antioquia", "Bolívar", "Córdoba", "Sucre"]
    departamento = st.sidebar.selectbox("Departamento", departamentos)
    
    # Obtener municipios según departamento
    municipios = get_municipios(departamento)
    municipio = st.sidebar.selectbox("Municipio", ["Todos"] + municipios)
    
    # Agregar más filtros
    categoria = st.sidebar.selectbox(
        "Categoría de Actividad",
        ["Todas", "Talleres", "Kits", "Divulgaciones", "Simulacros", "Asesoría especializada"]
    )
    
    # Período de predicción con explicación
    st.sidebar.markdown("### ⏳ Horizonte de Predicción")
    periodo = st.sidebar.slider(
        "Meses a predecir", 
        min_value=1, 
        max_value=12, 
        value=3,
        help="Seleccione cuántos meses hacia el futuro desea predecir"
    )
    
    # Botón para realizar predicción
    if st.sidebar.button("🔮 Realizar Predicción", type="primary"):
        with st.spinner("Analizando datos temporales..."):
            predictor = TemporalPredictor()
            
            # Preparar datos de entrada
            input_data = {
                'departamento': departamento,
                'municipio': municipio if municipio != "Todos" else None,
                'categoria': categoria if categoria != "Todas" else None,
                'periodo': periodo
            }
            
            # Realizar predicción
            resultados = predictor.predict(input_data)
            
            # Verificar si hay predicciones futuras
            tiene_predicciones_futuras = False
            if resultados.get('predicciones') and 'months_to_current' in resultados['predicciones']:
                months_to_current = resultados['predicciones']['months_to_current']
                if months_to_current < len(resultados['predicciones'].get('values', [])):
                    tiene_predicciones_futuras = True
            
            # Mostrar resultados en pestañas
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 Pronóstico", 
                "📊 Estadísticas", 
                "📉 Patrones",
                "🔍 Análisis Comparativo",
                "📋 Datos"
            ])
            
            with tab1:
                st.plotly_chart(resultados['grafico'], use_container_width=True)
                
                # Mostrar información adicional sobre las predicciones
                if not tiene_predicciones_futuras and 'predicciones' in resultados and resultados['predicciones']:
                    st.warning("⚠️ Los datos históricos son antiguos. Se recomienda aumentar el período de predicción para visualizar predicciones actuales.")
                
                with st.expander("ℹ️ Cómo interpretar este gráfico"):
                    st.markdown("""
                    ### 📈 Gráfico de Pronóstico

                    Este gráfico muestra la predicción de actividades futuras basada en datos históricos:

                    1. **Datos Históricos** (Línea Azul)
                       - Representa las actividades reales registradas
                       - Los puntos muestran valores mensuales exactos
                       - Ayuda a visualizar la tendencia histórica

                    2. **Predicción** (Línea Roja Punteada)
                       - Muestra la cantidad esperada de actividades
                       - Basada en patrones históricos y estacionalidad
                       - Actualizada con los datos más recientes

                    3. **Intervalo de Confianza** (Área Sombreada)
                       - Representa el rango probable de valores futuros
                       - Más amplio a medida que se aleja en el tiempo
                       - 95% de confianza en las predicciones

                    4. **Interpretación**:
                       - Si la línea sube: tendencia de crecimiento
                       - Si la línea baja: tendencia de disminución
                       - Patrones cíclicos indican estacionalidad
                    """)
            
            with tab2:
                # Métricas originales
                st.subheader("📊 Métricas de Predicción")
                col1, col2, col3 = st.columns(3)
                metricas = resultados['metricas']
                for i, (metric, value) in enumerate(metricas.items()):
                    with [col1, col2, col3][i % 3]:
                        st.metric(
                            label=metric,
                            value=f"{value:.1f}" if isinstance(value, (int, float)) else value,
                            delta=None
                        )
                
                # Nuevas métricas de desempeño
                st.subheader("📈 Métricas de Desempeño")
                if resultados.get('metricas_desempeno'):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        metrics_left = {
                            "🔢 Total Actividades": resultados['metricas_desempeno']['Actividades totales'],
                            "📊 Promedio Mensual": resultados['metricas_desempeno']['Promedio mensual'],
                            "⬆️ Máximo Mensual": resultados['metricas_desempeno']['Máximo mensual'],
                            "⬇️ Mínimo Mensual": resultados['metricas_desempeno']['Mínimo mensual']
                        }
                        for label, value in metrics_left.items():
                            st.metric(label=label, value=value)
                    
                    with col2:
                        metrics_right = {
                            "❌ Meses sin Actividad": resultados['metricas_desempeno']['Meses sin actividad'],
                            "📈 Crecimiento Anual": resultados['metricas_desempeno']['Crecimiento anual'],
                            "🎯 Estabilidad": resultados['metricas_desempeno']['Estabilidad']
                        }
                        for label, value in metrics_right.items():
                            st.metric(label=label, value=value)
                    
                    st.subheader("🏆 Meses más Activos")
                    for mes in resultados['metricas_desempeno']['Meses más activos']:
                        st.info(mes)
            
            with tab3:
                if resultados.get('grafico_patrones'):
                    st.plotly_chart(resultados['grafico_patrones'], use_container_width=True)
                    
                    with st.expander("ℹ️ Cómo interpretar estos patrones"):
                        st.markdown("""
                        ### 📊 Análisis Detallado de Patrones

                        Este conjunto de gráficos revela diferentes aspectos del comportamiento de las actividades:

                        1. **Actividades por Mes del Año**
                           - Barras: Promedio de actividades mensuales
                           - Números sobre barras: Cantidad de datos disponibles
                           - Uso: Identificar meses de alta/baja actividad
                           - Interpretación: Barras más altas indican meses más activos

                        2. **Actividades por Día de Semana**
                           - Barras: Promedio de actividades por día
                           - Números: Cantidad de observaciones por día
                           - Uso: Planificación semanal de recursos
                           - Interpretación: Identifica días pico de actividad

                        3. **Evolución Temporal**
                           - Puntos azules: Actividades reales
                           - Línea roja: Tendencia general
                           - Uso: Visualizar cambios a largo plazo
                           - Interpretación: 
                             * Pendiente positiva = Crecimiento
                             * Pendiente negativa = Decrecimiento
                             * Horizontal = Estabilidad

                        4. **Distribución de Frecuencias**
                           - Histograma: Frecuencia de niveles de actividad
                           - Uso: Entender la variabilidad típica
                           - Interpretación:
                             * Campana simétrica = Distribución normal
                             * Sesgada derecha = Eventos ocasionales de alta actividad
                             * Sesgada izquierda = Eventos ocasionales de baja actividad
                        """)
                else:
                    st.warning("Se requieren al menos 6 meses de datos para analizar patrones")
            
            with tab4:
                if resultados['historical_data']:
                    current_value, delta_percent, hist_delta = calculate_comparison_metrics(resultados['historical_data'])
                    
                    st.subheader("🔄 Comparación con Períodos Anteriores")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "Promedio Últimos 3 Meses",
                            f"{current_value:.1f}",
                            f"{delta_percent:.1f}% vs. Año Anterior",
                            delta_color="inverse" if delta_percent < 0 else "normal"
                        )
                        
                    with col2:
                        st.metric(
                            "vs. Promedio Histórico",
                            f"{current_value:.1f}",
                            f"{hist_delta:.1f}%",
                            delta_color="inverse" if hist_delta < 0 else "normal"
                        )
                    
                    # Gráfico de comparación
                    comparison_chart = create_comparison_chart(resultados['historical_data'])
                    st.plotly_chart(comparison_chart, use_container_width=True)
                    
                    # Análisis de Tendencias
                    st.subheader("📈 Análisis de Tendencias")
                    trend_fig = create_trend_analysis(resultados['historical_data'])
                    st.plotly_chart(trend_fig, use_container_width=True)
                    
                    with st.expander("ℹ️ Cómo interpretar este análisis"):
                        st.markdown("""
                        ### 📊 Análisis Comparativo Detallado

                        Esta sección permite comparar el desempeño actual con períodos anteriores:

                        1. **Comparación Interanual**
                           - Líneas de diferentes colores: Cada año
                           - Puntos: Valores mensuales específicos
                           - Uso: Comparar patrones entre años
                           - Interpretación:
                             * Líneas similares = Patrón estable
                             * Líneas divergentes = Cambio de patrón
                             * Picos coincidentes = Estacionalidad fuerte

                        2. **Evolución por Períodos**
                           - Barras: Promedio de actividades por período
                           - Barras de error: Variabilidad en cada período
                           - Uso: Identificar cambios estructurales
                           - Interpretación:
                             * Barras crecientes = Tendencia positiva
                             * Barras decrecientes = Tendencia negativa
                             * Barras de error grandes = Alta variabilidad

                        3. **Análisis de Tendencias**
                           - Línea azul: Datos originales
                           - Línea roja (3 meses): Tendencia corto plazo
                           - Línea verde (6 meses): Tendencia medio plazo
                           - Línea amarilla (12 meses): Tendencia largo plazo
                           - Uso: Identificar tendencias a diferentes escalas
                           - Interpretación:
                             * Líneas convergentes = Tendencia estable
                             * Líneas divergentes = Cambio de tendencia
                             * Cruces = Puntos de cambio importantes
                        """)

                    with st.expander("ℹ️ Cómo interpretar las Medias Móviles"):
                        st.markdown("""
                        ### 📈 Análisis de Tendencias con Medias Móviles

                        Las medias móviles son una herramienta poderosa para entender las tendencias eliminando el "ruido" de los datos:

                        1. **Datos Originales** (Línea Azul)
                           - Muestra las actividades reales mes a mes
                           - Incluye todas las fluctuaciones y variaciones
                           - Útil para ver los valores exactos pero puede ser "ruidoso"

                        2. **Media Móvil 3 meses** (Línea Roja Punteada)
                           - Promedio de los últimos 3 meses
                           - Elimina fluctuaciones muy cortas
                           - Mejor para ver tendencias a corto plazo
                           - Ejemplo: Si tienes 5, 8, 3 actividades, la media móvil será (5+8+3)/3 = 5.33

                        3. **Media Móvil 6 meses** (Línea Verde Discontinua)
                           - Promedio de los últimos 6 meses
                           - Suaviza fluctuaciones estacionales
                           - Muestra tendencias de medio plazo
                           - Útil para identificar ciclos semestrales

                        4. **Media Móvil 12 meses** (Línea Amarilla)
                           - Promedio del último año
                           - Elimina efectos estacionales
                           - Muestra la tendencia general/estructural
                           - Mejor para decisiones estratégicas

                        ### 🎯 Cómo Usarlo:

                        1. **Para Decisiones Inmediatas**
                           - Use la línea roja (3 meses)
                           - Si está subiendo: prepare más recursos
                           - Si está bajando: investigue las causas recientes

                        2. **Para Planificación Táctica**
                           - Use la línea verde (6 meses)
                           - Identifique patrones semestrales
                           - Útil para planificación de recursos

                        3. **Para Estrategia**
                           - Use la línea amarilla (12 meses)
                           - Evalúe el crecimiento real del programa
                           - Tome decisiones de largo plazo

                        ### 🔍 Señales Importantes:

                        1. **Cruces entre Líneas**
                           - Cuando una media más corta cruza una más larga hacia arriba = Señal de crecimiento
                           - Cuando cruza hacia abajo = Posible inicio de declive
                           - Ejemplo: Si la línea roja cruza la verde hacia arriba, podría indicar inicio de tendencia positiva

                        2. **Divergencia entre Líneas**
                           - Si las líneas se separan = Cambio significativo en curso
                           - Si se juntan = Estabilización de tendencia

                        3. **Pendientes**
                           - Todas las líneas subiendo = Crecimiento sólido
                           - Todas bajando = Declive generalizado
                           - Diferentes direcciones = Período de incertidumbre
                        """)
                else:
                    st.warning("No hay suficientes datos para el análisis comparativo")
            
            with tab5:
                if resultados['historical_data']:
                    df_hist = pd.DataFrame({
                        'Fecha': resultados['historical_data']['dates'],
                        'Actividades': resultados['historical_data']['activities']
                    })
                    st.dataframe(df_hist)
                else:
                    st.warning("No hay datos históricos disponibles")

    # Agregar información adicional
    with st.expander("ℹ️ Acerca de este análisis"):
        st.markdown("""
        Este dashboard permite realizar predicciones sobre el número de actividades futuras basándose en:
        - Datos históricos desde 2014
        - Patrones estacionales identificados
        - Tendencias por ubicación y tipo de actividad
        
        Los modelos utilizados combinan técnicas de series temporales (SARIMA) y aprendizaje automático (Prophet)
        para proporcionar predicciones más robustas.
        """)

if __name__ == "__main__":
    main() 