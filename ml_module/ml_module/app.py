import sys
from pathlib import Path
import time

# Ajustar el cálculo del directorio raíz
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import streamlit as st
import pandas as pd
from datetime import datetime
from predict import (
    AttendancePredictor,
    show_prediction_details,
    create_historical_trend,
    create_comparison_chart,
    create_distribution_plot
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats
import numpy as np

# Ajustar el layout principal para usar todo el ancho
st.set_page_config(
    page_title="Predictor de Asistencia",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ajustar los estilos CSS para mejor uso del espacio
st.markdown("""
<style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
    }
    .stats-box {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .main {
        color: white;
    }
    
    /* Estilos para el botón del sidebar */
    .sidebar-toggle {
        position: fixed;
        top: 0;
        left: 0;
        padding: 10px;
        background-color: #1E1E1E;
        border-radius: 0 0 5px 0;
        color: white;
        z-index: 1000;
        cursor: pointer;
    }
    
    /* Ocultar el botón por defecto de Streamlit */
    button[kind="header"] {
        display: none;
    }
    
    /* Barra de navegación */
    .navbar {
        padding: 1rem;
        background: linear-gradient(90deg, #1E1E1E 0%, #2C2C2C 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Contenedores con efecto hover */
    .styledContainer {
        background: #1E1E1E;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border: 1px solid #2C2C2C;
    }
    .styledContainer:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        border-color: #4CAF50;
    }
    
    /* Loader personalizado */
    .custom-loader {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    .custom-loader::after {
        content: "";
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #4CAF50;
        border-radius: 50%;
        animation: spinner 1s linear infinite;
    }
    @keyframes spinner {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Botones mejorados */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    
    /* Tooltips personalizados */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #2C2C2C;
        color: white;
        text-align: center;
        padding: 5px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Ajuste para el título de la card */
    .card-title {
        margin: 0;
        padding-bottom: 1rem;
        border-bottom: 1px solid #2C2C2C;
        color: #ffffff;
    }
    
    /* Ajuste para el contenedor principal */
    .main-container {
        padding: 1rem;
        background: #1E1E1E;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Footer fijo */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        padding: 0.75rem;
        background: rgba(30, 30, 30, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        text-align: center;
        font-size: 0.8rem;
        border-top: 1px solid rgba(44, 44, 44, 0.8);
        z-index: 1000;
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Asegurar que el contenido no se oculte detrás del footer */
    .main {
        padding-bottom: 4rem !important;
    }
    
    /* Ajustar el padding del contenedor principal */
    .block-container {
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        max-width: 100rem !important;  /* Aumentar el ancho máximo */
    }
    
    /* Mejorar el layout de las cards */
    .styledContainer {
        margin: 0.5rem 0;
        padding: 1rem;
    }
    
    /* Optimizar el espacio en los gráficos */
    .plotly-graph-div {
        margin: 0 auto;
    }
    
    /* Mejorar el layout de las columnas */
    [data-testid="column"] {
        padding: 0 0.5rem;
    }
    
    /* Ajustar el espaciado vertical */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > div {
        margin-bottom: 0.5rem;
    }
</style>

<script>
    // JavaScript para manejar el toggle del sidebar
    const toggleSidebar = () => {
        const sidebar = document.querySelector('.css-1d391kg');
        if (sidebar) {
            sidebar.style.display = sidebar.style.display === 'none' ? 'block' : 'none';
        }
    }
</script>
""", unsafe_allow_html=True)

# Agregar botón personalizado para mostrar/ocultar sidebar
st.markdown("""
<div class="sidebar-toggle" onclick="toggleSidebar()">
    ☰ Info Municipios
</div>
""", unsafe_allow_html=True)

# Mover el loader al inicio antes de cualquier otro contenido
with st.spinner('Inicializando...'):
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.005)  # Reducir el tiempo de carga
        progress_bar.progress(i + 1)
    progress_bar.empty()

# Barra de navegación (única)
st.markdown("""
<div class="navbar">
    <h1 style="margin:0">🎯 Predictor de Asistencia</h1>
    <p style="margin:0;opacity:0.7">Sistema de Predicción Inteligente</p>
</div>
""", unsafe_allow_html=True)

# Descripción breve
st.markdown("""
Esta aplicación predice el número esperado de asistentes para una actividad basándose en características históricas y el modelo de machine learning entrenado.
""")

# Cargar datos históricos para las opciones
historical_stats = pd.read_csv(root_dir / 'models' / 'historical_stats.csv')

# Cargar todos los municipios desde la base de datos
def get_municipios_from_db():
    try:
        predictor = AttendancePredictor()
        query = """
            SELECT DISTINCT departamento, municipio 
            FROM actividades 
            WHERE municipio IS NOT NULL 
            ORDER BY departamento, municipio
        """
        df = pd.read_sql(query, predictor.data_loader.engine)
        
        # Crear diccionario de municipios por departamento
        municipios_dict = {}
        for dept, group in df.groupby('departamento'):
            municipios_dict[dept] = sorted(group['municipio'].unique().tolist())
        
        return municipios_dict
    except Exception as e:
        st.error(f"Error cargando municipios: {str(e)}")
        return {
            'Antioquia': [
                'Valdivia', 'Caucasia', 'Cáceres', 'Tarazá', 'Nechí', 
                'El Bagre', 'Zaragoza', 'Segovia', 'Remedios'
            ],
            'Bolívar': [
                'Achí', 'Magangué', 'San Jacinto del Cauca', 
                'Montecristo', 'San Pablo', 'Tiquisio', 'Pinillos'
            ],
            'Córdoba': [
                'Ayapel', 'Pueblo Nuevo', 'Planeta Rica', 
                'Buenavista', 'La Apartada'
            ],
            'Sucre': [
                'Sucre', 'Majagual', 'Guaranda', 'San Marcos',
                'San Benito Abad', 'Caimito'
            ]
        }

# Definir mapeo de zonas geográficas y sus departamentos
ZONAS_GEOGRAFICAS = {
    'Antioquia': ['Antioquia'],
    'La Mojana': ['Bolívar', 'Córdoba', 'Sucre']
}

# Obtener municipios de la base de datos
MUNICIPIOS = get_municipios_from_db()

# Mostrar información sobre los municipios cargados
with st.sidebar:
    st.markdown("### 📊 Información de Municipios")
    for dept, municipios in MUNICIPIOS.items():
        st.markdown(f"**{dept}**: {len(municipios)} municipios")
        if st.checkbox(f"Ver municipios de {dept}"):
            st.write(", ".join(municipios))

# Crear dos columnas principales para el formulario y el gauge
col_form, col_gauge = st.columns([1, 1])

with col_form:
    with st.container():
        
        # Título dentro de la card
        st.markdown('<h2 class="card-title">📝 Datos de la Actividad</h2>', unsafe_allow_html=True)
        
        # Agregar tooltips a los selectores
        st.markdown("""
        <div class="tooltip">
            Zona Geográfica
            <span class="tooltiptext">Seleccione la región general del evento</span>
        </div>
        """, unsafe_allow_html=True)
        zona = st.selectbox(
            "",  # Label vacío porque ya lo pusimos en el tooltip
            options=sorted(ZONAS_GEOGRAFICAS.keys()),
            key='zona_geografica'
        )
        
        # Filtrar departamentos según zona
        departamentos_disponibles = ZONAS_GEOGRAFICAS[zona]
        departamento = st.selectbox(
            "Departamento",
            options=sorted(departamentos_disponibles),
            key='departamento'
        )
        
        # Filtrar municipios según departamento
        municipios_disponibles = MUNICIPIOS.get(departamento, [])
        municipio = st.selectbox(
            "Municipio",
            options=sorted(municipios_disponibles),
            key='municipio'
        )
        
        # Mostrar información sobre la selección actual
        st.info(f"""
        📍 Zona seleccionada: {zona}
        🏢 Departamentos disponibles: {', '.join(departamentos_disponibles)}
        🏘️ Municipios disponibles: {len(municipios_disponibles)}
        """)
        
        # Formulario para los datos finales y predicción
        with st.form("prediction_form"):
            # Filtrar categorías según el departamento y limpiar NaN
            categorias = [
                cat for cat in historical_stats[
                    historical_stats['departamento'] == departamento
                ]['categoria_unica'].unique()
                if pd.notna(cat)
            ]
            
            categoria = st.selectbox(
                "Categoría de Actividad",
                options=sorted(categorias)
            )
            
            # Fecha
            fecha = st.date_input(
                "Fecha de la Actividad",
                min_value=datetime.now()
            )
            
            # Botón de predicción
            submitted = st.form_submit_button("🔮 Realizar Predicción")

        st.markdown('</div>', unsafe_allow_html=True)

# Mover el gauge chart aquí, pero inicializarlo vacío
with col_gauge:
    st.subheader("📈 Predicción")
    gauge_placeholder = st.empty()

# Si hay predicción, mostrar resultados
if submitted:
    if not municipio:
        st.error("Por favor seleccione un municipio")
    elif not categoria:
        st.error("Por favor seleccione una categoría")
    else:
        # Preparar datos
        input_data = {
            'departamento': departamento,
            'municipio': municipio,
            'zona_geografica': zona,
            'categoria_unica': categoria,
            'fecha': fecha.strftime('%Y-%m-%d')
        }
        
        # Realizar predicción
        predictor = AttendancePredictor()
        
        # Usar st.empty() de manera más simple
        loader_placeholder = st.empty()
        loader_placeholder.markdown('<div class="custom-loader"></div>', unsafe_allow_html=True)
        
        try:
            with st.spinner('Calculando predicción...'):
                result = predictor.predict(input_data)
        finally:
            loader_placeholder.empty()  # Asegurarse de que el loader se elimine
            
            # Actualizar el gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=result['prediccion_asistentes'],
                delta={
                    'reference': result['promedio_historico'],
                    'position': 'top',
                    'valueformat': '.0f',
                    'font': {'size': 14, 'color': 'white'}
                },
                title={
                    'text': f"Asistentes Predichos<br><span style='font-size:0.8em;color:gray'>Rango histórico: {result.get('min_historico', 0):.0f} - {result.get('max_historico', 0):.0f}</span>",
                    'font': {'size': 16, 'color': 'white'}
                },
                number={
                    'font': {'size': 40, 'color': 'white'},
                    'valueformat': '.0f',
                    'suffix': ' personas'
                },
                gauge={
                    'axis': {
                        'range': [None, result['promedio_historico'] * 2],
                        'tickwidth': 1,
                        'tickcolor': "white",
                        'tickfont': {'color': 'white'}
                    },
                    'bar': {'color': "#4CAF50"},  # Verde más atractivo
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "white",
                    'steps': [
                        {'range': [0, result['promedio_historico'] * 0.5], 'color': "#1E1E1E"},
                        {'range': [result['promedio_historico'] * 0.5, result['promedio_historico']], 'color': "#2C2C2C"},
                        {'range': [result['promedio_historico'], result['promedio_historico'] * 1.5], 'color': "#3C3C3C"},
                        {'range': [result['promedio_historico'] * 1.5, result['promedio_historico'] * 2], 'color': "#4C4C4C"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': result['promedio_historico']
                    }
                }
            ))

            # Mejorar el layout
            fig.update_layout(
                paper_bgcolor='#0E1117',
                plot_bgcolor='#0E1117',
                font={'color': 'white'},
                height=350,
                margin=dict(t=100, b=0, l=40, r=40)
            )

            # Mostrar el gráfico
            gauge_placeholder.plotly_chart(fig, use_container_width=True)
            
            # Agregar explicación debajo del gauge
            with st.expander("ℹ️ Cómo interpretar este gráfico", expanded=False):
                st.markdown("""
                ### Interpretación del Gauge Chart
                
                Este gráfico muestra la predicción de asistentes en contexto con los datos históricos:
                
                🎯 **Número Principal**: 
                - Muestra la predicción exacta de asistentes
                - El valor +/- arriba indica la diferencia con el promedio histórico
                
                📊 **Escala del Gauge**:
                - La línea roja marca el promedio histórico
                - Zonas oscuras a claras representan rangos de asistencia:
                  * 0-50% del promedio: Asistencia baja
                  * 50-100% del promedio: Asistencia normal-baja
                  * 100-150% del promedio: Asistencia normal-alta
                  * 150-200% del promedio: Asistencia alta
                
                📈 **Rango Histórico**:
                - Se muestra el rango mínimo y máximo de asistentes registrados
                - Ayuda a contextualizar la predicción dentro de los límites históricos
                
                💡 **Interpretación**:
                - Si el indicador está en verde, la predicción es favorable
                - La posición relativa a la línea roja indica qué tan por encima o por debajo del promedio está la predicción
                """)
            
            # Modificar la sección de análisis para mantener los insights debajo
            st.write("---")  # Separador visual

            # Usar dos columnas para los análisis principales
            col_basic, col_advanced = st.columns(2)

            with col_basic:
                st.subheader("📊 Análisis Básico")
                tab1, tab2, tab3 = st.tabs(["Comparación", "Tendencia", "Distribución"])
                
                with tab1:
                    st.plotly_chart(create_comparison_chart(result), use_container_width=True)
                    with st.expander("ℹ️ Cómo interpretar el Gráfico de Comparación"):
                        st.markdown("""
                        Este gráfico compara la predicción con datos históricos:
                        - Mínimo: El valor más bajo registrado
                        - Promedio: La media histórica de asistentes
                        - Predicción: El número esperado para esta actividad
                        - Máximo: El valor más alto registrado
                        """)
                
                with tab2:
                    historical_data = result.get('historical_data', {})
                    if historical_data and historical_data.get('asistentes_previos'):
                        fig_trend = create_historical_trend(
                            historical_data, 
                            input_data['fecha'],
                            result['prediccion_asistentes']
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                        with st.expander("ℹ️ Cómo interpretar la Tendencia"):
                            st.markdown("""
                            La gráfica muestra la evolución de asistentes en el tiempo:
                            - Línea azul: Asistencia histórica
                            - Área sombreada: Rango de variación
                            - Línea roja punteada: Promedio histórico
                            - Estrella roja: Predicción actual
                            - Útil para identificar tendencias y patrones temporales
                            """)
                    else:
                        st.warning("No hay suficientes datos históricos para mostrar la tendencia")
                
                with tab3:
                    if historical_data and historical_data.get('asistentes_previos'):
                        fig_dist = create_distribution_plot(
                            historical_data,
                            result['prediccion_asistentes']
                        )
                        st.plotly_chart(fig_dist, use_container_width=True)
                        with st.expander("ℹ️ Cómo interpretar la Distribución"):
                            st.markdown("""
                            El gráfico muestra la distribución de asistentes:
                            - Violín azul: Forma de la distribución de datos
                            - Puntos verdes: Valores históricos individuales
                            - Línea roja: Predicción actual
                            - Forma: Indica si los datos son simétricos o sesgados
                            - Ayuda a entender qué tan común es el valor predicho
                            """)
                    else:
                        st.warning("No hay suficientes datos históricos para mostrar la distribución")

            with col_advanced:
                st.subheader("🔍 Análisis Detallado")
                tab4, tab5, tab6 = st.tabs(["Análisis de Distribución", "Análisis de Normalidad", "Importancia de Factores"])
                
                with tab4:
                    st.subheader("Análisis Estadístico Detallado")
                    
                    # Obtener datos históricos
                    asistentes = historical_data.get('asistentes_previos', [])
                    if len(asistentes) > 0:
                        # Calcular estadísticas
                        stats_data = pd.Series(asistentes).describe()
                        
                        # Crear gráfico combinado: Violin + Box + Puntos
                        fig = go.Figure()
                        
                        # Agregar violin plot
                        fig.add_trace(go.Violin(
                            y=asistentes,
                            name='Distribución',
                            side='positive',
                            line_color='#2196F3',
                            fillcolor='rgba(33, 150, 243, 0.3)',
                            points=False,
                            meanline_visible=True,
                            showlegend=False
                        ))
                        
                        # Agregar box plot superpuesto
                        fig.add_trace(go.Box(
                            y=asistentes,
                            name='Estadísticas',
                            boxpoints='outliers',
                            marker_color='#FF9800',
                            line_width=1,
                            showlegend=False
                        ))
                        
                        # Agregar puntos de datos
                        fig.add_trace(go.Scatter(
                            y=asistentes,
                            x=[0] * len(asistentes),
                            mode='markers',
                            name='Datos',
                            marker=dict(
                                color='#4CAF50',
                                size=4,
                                opacity=0.5
                            ),
                            showlegend=False
                        ))
                        
                        # Agregar línea de predicción
                        fig.add_hline(
                            y=result['prediccion_asistentes'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Predicción"
                        )
                        
                        fig.update_layout(
                            title='Distribución Detallada de Asistentes',
                            yaxis_title='Número de Asistentes',
                            template='plotly_white',
                            paper_bgcolor='#0E1117',
                            plot_bgcolor='#0E1117',
                            font=dict(color='white'),
                            showlegend=False,
                            height=400
                        )
                        
                        # Mostrar gráfico y estadísticas
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.markdown("""
                            <div class="stats-box">
                            <h4>📊 Estadísticas Clave</h4>
                            
                            - **Promedio**: {:.1f}
                            - **Mediana**: {:.1f}
                            - **Desv. Est**: {:.1f}
                            - **Mínimo**: {:.0f}
                            - **Máximo**: {:.0f}
                            - **Muestras**: {:d}
                            </div>
                            """.format(
                                stats_data['mean'],
                                stats_data['50%'],
                                stats_data['std'],
                                stats_data['min'],
                                stats_data['max'],
                                int(stats_data['count'])
                            ), unsafe_allow_html=True)
                        
                        with st.expander("ℹ️ Cómo interpretar este Análisis"):
                            st.markdown("""
                            Este gráfico combina tres visualizaciones complementarias:
                            
                            **🎻 Violin Plot (Azul):**
                            - Muestra la forma completa de la distribución
                            - Las partes más anchas indican valores más frecuentes
                            
                            **📦 Box Plot (Naranja):**
                            - La caja muestra el rango intercuartil (IQR)
                            - La línea central es la mediana
                            - Los puntos son valores atípicos
                            
                            **🟢 Puntos (Verde):**
                            - Cada punto representa una actividad histórica
                            - Útil para ver la dispersión real de los datos
                            
                            **📍 Línea Roja:**
                            - Indica dónde se ubica la predicción actual
                            """)
                    else:
                        st.warning("No hay suficientes datos históricos para este análisis")
                
                with tab5:
                    # Q-Q Plot y Gráfico de Probabilidad Acumulada
                    if len(asistentes) > 0:
                        fig = make_subplots(
                            rows=1, cols=2,
                            subplot_titles=('Q-Q Plot (Normalidad)', 'Probabilidad Acumulada')
                        )
                        
                        # Q-Q Plot
                        qq_data = stats.probplot(asistentes)
                        fig.add_trace(
                            go.Scatter(
                                x=qq_data[0][0],
                                y=qq_data[0][1],
                                mode='markers',
                                name='Datos',
                                marker=dict(color='#4CAF50')
                            ),
                            row=1, col=1
                        )
                        
                        # Línea de referencia Q-Q
                        fig.add_trace(
                            go.Scatter(
                                x=qq_data[0][0],
                                y=qq_data[0][0] * qq_data[1][0] + qq_data[1][1],
                                mode='lines',
                                name='Línea Normal',
                                line=dict(color='red', dash='dash')
                            ),
                            row=1, col=1
                        )
                        
                        # Gráfico de Probabilidad Acumulada
                        sorted_data = np.sort(asistentes)
                        cumulative_prob = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
                        
                        fig.add_trace(
                            go.Scatter(
                                x=sorted_data,
                                y=cumulative_prob,
                                mode='lines',
                                name='Prob. Acumulada',
                                line=dict(color='#2196F3')
                            ),
                            row=1, col=2
                        )
                        
                        # Agregar línea vertical de predicción en prob. acumulada
                        fig.add_vline(
                            x=result['prediccion_asistentes'],
                            line_dash="dash",
                            line_color="red",
                            row=1, col=2
                        )
                        
                        fig.update_layout(
                            height=400,
                            showlegend=True,
                            template='plotly_white',
                            paper_bgcolor='#0E1117',
                            plot_bgcolor='#0E1117',
                            font=dict(color='white')
                        )
                        
                        # Actualizar títulos de ejes
                        fig.update_xaxes(title_text="Cuantiles Teóricos", row=1, col=1)
                        fig.update_yaxes(title_text="Cuantiles Observados", row=1, col=1)
                        fig.update_xaxes(title_text="Número de Asistentes", row=1, col=2)
                        fig.update_yaxes(title_text="Probabilidad Acumulada", row=1, col=2)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        with st.expander("ℹ️ Cómo interpretar estos Gráficos"):
                            st.markdown("""
                            **Q-Q Plot (Gráfico de Normalidad):**
                            - Los puntos sobre la línea roja indican distribución normal
                            - Desviaciones hacia arriba: más valores altos de lo esperado
                            - Desviaciones hacia abajo: más valores bajos de lo esperado
                            - Forma de S: datos con sesgo
                            
                            **Probabilidad Acumulada:**
                            - Muestra la probabilidad de tener X o menos asistentes
                            - La línea roja indica la predicción actual
                            - Pendiente pronunciada: datos concentrados
                            - Pendiente suave: datos dispersos
                            """)
                    else:
                        st.warning("No hay suficientes datos históricos para este análisis")
                
                with tab6:
                    # Gráfico de importancia relativa usando valores reales del modelo
                    importancia = result.get('importancia_variables', {})
                    if importancia:
                        # Ordenar por importancia
                        importancia = dict(sorted(importancia.items(), key=lambda x: x[1], reverse=True))
                        
                        fig = go.Figure(go.Bar(
                            x=list(importancia.keys()),
                            y=list(importancia.values()),
                            marker_color=['#FF4B4B', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0'],
                            text=[f'{v:.0%}' for v in importancia.values()],
                            textposition='auto',
                        ))
                        
                        fig.update_layout(
                            title='Importancia Relativa de Factores',
                            yaxis_title='Influencia en la Predicción',
                            yaxis=dict(
                                tickformat='.0%',
                                range=[0, 1]
                            ),
                            template='plotly_white',
                            paper_bgcolor='#0E1117',
                            plot_bgcolor='#0E1117',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        with st.expander("ℹ️ Cómo interpretar la Importancia de Factores"):
                            st.markdown("""
                            Este gráfico muestra qué tanto influye cada factor en la predicción:
                            
                            - **Histórico**: Impacto de los datos históricos y tendencias pasadas
                            - **Categoría**: Influencia del tipo de actividad
                            - **Municipio**: Efecto de la ubicación específica
                            - **Día Semana**: Importancia del día de la semana
                            - **Mes**: Influencia del mes del año
                            
                            Los porcentajes indican el peso relativo de cada factor en el modelo.
                            """)

            # Separador para los insights
            st.write("---")

            # Insights en dos columnas debajo de los gráficos
            col_insights1, col_insights2 = st.columns(2)

            with col_insights1:
                st.subheader("💡 Insights")
               
                # Actualizar insights con datos dinámicos
                mejor_dia = result.get('mejor_dia', {})
                tendencia = result.get('tendencia_mensual', 0)
                confianza = result.get('confianza_prediccion', 0)
                
                st.markdown(f"""
                <div class="stats-box">
                <h4>Patrones Detectados</h4>
                                
                - 📅 Mejor día de la semana: {mejor_dia.get('dia', 'No disponible')} (+{abs(mejor_dia.get('incremento', 0)):.0%} asistencia)
                - 📈 Tendencia mensual: {'Creciente' if tendencia > 0 else 'Decreciente'} ({abs(tendencia):.0%})
                - 🎯 Confiabilidad: {'Alta' if confianza > 0.7 else 'Media' if confianza > 0.4 else 'Baja'} ({confianza:.0%})
                </div>
                """, unsafe_allow_html=True)

            with col_insights2:
                st.subheader("📋 Recomendaciones")
                recomendaciones = result.get('recomendaciones', {})
                factores = recomendaciones.get('factores_clave', ['Categoría', 'histórico'])
                st.markdown(f"""
                <div class="stats-box">
                <h4>Recomendaciones Avanzadas</h4>
                
                - 📅 Mejor mes: {recomendaciones.get('mejor_mes', 'No disponible')}
                - 📈 Potencial de mejora: +{recomendaciones.get('potencial_mejora', 20):.0f}% con ajustes
                - 🎯 Factores clave: {' y '.join(factores)}
                </div>
                """, unsafe_allow_html=True)

# Reemplazar la sección de información adicional
st.markdown("---")
st.markdown("### ℹ️ Información Adicional")

# Crear dos columnas para la información
col_modelo, col_factores = st.columns(2)

with col_modelo:
    st.markdown("""
    #### Modelo de Machine Learning
    El sistema utiliza un conjunto de modelos predictivos:

    - **Modelos Utilizados**:
        - XGBoost como modelo principal
        - Random Forest para validación
        - Modelos estadísticos de apoyo
    
    - **Datos de Entrenamiento**:
        - Histórico de actividades 2014-2024
        - Aproximadamente 5,000 actividades analizadas hasta la fecha
        - Actualización mensual con nuevos datos
        - Validación continua de predicciones
    
    > **Nota**: Las predicciones son estimaciones basadas en datos históricos y deben usarse como apoyo a la toma de decisiones.
    """)

with col_factores:
    # Obtener importancias ordenadas
    predictor = AttendancePredictor()
    
    st.markdown("""
    #### Factores Considerados en la Predicción
    """)
    
    # Crear dos columnas manteniendo el orden específico
    col_f1, col_f2 = st.columns(2)
    
    # Primera columna: Contextuales y Actividad (los más importantes)
    with col_f1:
        st.markdown(f"""
        **Factores Contextuales** ({predictor.get_feature_importances()['Contextuales']:.0f}%)
        - Promedios históricos de asistencia
        - Ratios de asistencia vs promedio
        - Percentiles y medianas históricas
        - Tendencias recientes de asistencia
        
        **Factores de Actividad** ({predictor.get_feature_importances()['Actividad']:.0f}%)
        - Total de actividades por categoría
        - Frecuencia de la categoría
        - Ranking de asistencia por categoría
        - Patrones de categorías similares
        """)
    
    # Segunda columna: solo Geográficos
    with col_f2:
        st.markdown(f"""
        **Factores Geográficos** ({predictor.get_feature_importances()['Geográficos']:.0f}%)
        - Frecuencia de actividades por zona
        - Características del departamento
        - Patrones regionales específicos
        """)

# Agregar la nota sobre la versión en una línea al final
st.markdown("""
<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #2C2C2C; font-size: 0.8em; color: #666; text-align: center;">
    <strong>Versión del Modelo:</strong> 1.0.0 | <strong>Última Actualización:</strong> Febrero 2025 | <strong>Precisión Promedio:</strong> 85% | <strong>Margen de Error:</strong> ±15%
</div>
""", unsafe_allow_html=True)

def create_distribution_plot(historical_data, prediction):
    """Crea gráfico de distribución con la predicción"""
    # Obtener datos históricos
    hist_values = historical_data.get('asistentes_previos', [])
    if not hist_values or all(v == 0 for v in hist_values):
        return go.Figure().add_annotation(
            text="No hay suficientes datos históricos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Crear figura
    fig = go.Figure()
    
    # Convertir a numpy array y eliminar valores nulos o 0
    hist_values = np.array([float(x) for x in hist_values if float(x) > 0])
    
    # Crear datos para la distribución de puntos
    x_jitter = np.random.normal(0, 0.1, size=len(hist_values))
    
    # Agregar violin plot
    fig.add_trace(go.Violin(
        x=np.zeros(len(hist_values)),
        y=hist_values,
        name='Distribución',
        side='positive',
        width=0.8,
        line_color='#2196F3',
        fillcolor='rgba(33, 150, 243, 0.3)',
        meanline_visible=True,
        showlegend=False
    ))
    
    # Agregar puntos individuales
    fig.add_trace(go.Scatter(
        x=x_jitter,
        y=hist_values,
        mode='markers',
        name='Datos individuales',
        marker=dict(
            color='#4CAF50',
            size=8,
            opacity=0.6,
            line=dict(color='white', width=1)
        ),
        showlegend=False
    ))
    
    # Agregar línea de predicción
    fig.add_hline(
        y=prediction,
        line_dash="dash",
        line_color="red",
        annotation=dict(
            text="Predicción",
            xref="paper",
            x=1,
            showarrow=False,
            font=dict(color='white')
        )
    )
    
    # Actualizar layout
    fig.update_layout(
        title='Distribución de Asistentes',
        yaxis_title='Número de Asistentes',
        template='plotly_white',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white'),
        height=400,
        showlegend=False,
        xaxis=dict(
            title='',
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='#2C2C2C',
            zeroline=False
        )
    )
    
    return fig

def create_historical_trend(historical_data, fecha_seleccionada, prediccion=None):
    """Crea gráfico de tendencia histórica"""
    asistentes = historical_data.get('asistentes_previos', [])
    if not asistentes or all(v == 0 for v in asistentes):
        return go.Figure().add_annotation(
            text="No hay suficientes datos históricos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Crear fechas correspondientes
    fecha_fin = pd.to_datetime(fecha_seleccionada)
    fechas = pd.date_range(
        end=fecha_fin,
        periods=len(asistentes),
        freq='D'
    )
    
    df = pd.DataFrame({
        'Fecha': fechas,
        'Asistentes': asistentes
    })
    
    fig = go.Figure()
    
    # Agregar área sombreada
    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Asistentes'],
        fill='tozeroy',
        fillcolor='rgba(33, 150, 243, 0.3)',
        line=dict(color='rgba(33, 150, 243, 0.1)'),
        name='Rango',
        showlegend=False
    ))
    
    # Agregar línea principal
    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Asistentes'],
        mode='lines+markers',
        name='Asistentes históricos',
        line=dict(color='#2196F3', width=2),
        marker=dict(
            size=8,
            color='#2196F3',
            line=dict(color='white', width=1)
        )
    ))
    
    # Agregar predicción
    if prediccion is not None:
        fig.add_trace(go.Scatter(
            x=[df['Fecha'].iloc[-1]],
            y=[prediccion],
            mode='markers',
            name='Predicción',
            marker=dict(
                color='red',
                size=12,
                symbol='star'
            )
        ))
    
    # Agregar línea de promedio
    promedio = historical_data.get('promedio_categoria', 0)
    fig.add_hline(
        y=promedio,
        line_dash="dash",
        line_color="red",
        annotation=dict(
            text="Promedio histórico",
            xref="paper",
            x=1.02,
            showarrow=False,
            font=dict(color='white')
        )
    )
    
    # Actualizar layout
    fig.update_layout(
        title='Tendencia de Asistentes',
        template='plotly_white',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white'),
        xaxis=dict(
            title='Fecha',
            gridcolor='#2C2C2C',
            showgrid=True
        ),
        yaxis=dict(
            title='Asistentes',
            gridcolor='#2C2C2C',
            showgrid=True,
            zeroline=False
        ),
        height=400,
        margin=dict(r=100)
    )
    
    return fig 

# Footer al final del archivo
st.markdown("""
<div class="footer">
    Desarrollado por el equipo técnico del Proyecto Hidroituango de la Cruz Roja Colombiana Seccional Antioquia | v1.0.0
</div>
""", unsafe_allow_html=True) 