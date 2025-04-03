from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from ..config.settings import TABLE_CONFIG, THEME, MAP_CONFIG

def create_header():
    """Crea el encabezado de la aplicación"""
    return html.Div([
        # Contenido izquierdo (título y descripción)
        html.Div([
            html.H1('Dashboard de Actividades PHI', 
                   className='header-title'),
            html.P('Análisis y seguimiento de actividades territoriales', 
                  className='header-description')
        ], className='header-content'),
        
        # Contenido derecho (logos)
        html.Div([
            html.Button([
                html.I(className="fas fa-sync-alt me-2"),
                'Actualizar Datos'
            ], id='refresh-data', 
               className='btn btn-primary refresh-button')
        ], className='header-actions'),
        html.Div([
            html.Img(
                src='assets/logo-cruz-roja.png',
                className='header-logo cruz-roja'
            ),
            html.Img(
                src='assets/logo-epm.png',
                className='header-logo epm'
            )
        ], className='header-logos')
    ], className='header')


def create_filters():
    """Crea el panel de filtros mejorado"""
    return html.Div([
        html.Div([
            # Filtros de fecha (existente)
            html.Div([
                html.I(className="fas fa-calendar-alt text-primary me-2"),
                html.Label('Rango de Fechas', className='fw-bold'),
                dcc.DatePickerRange(
                    id='date-range',
                    start_date_placeholder_text="Fecha inicial",
                    end_date_placeholder_text="Fecha final",
                    display_format='DD/MM/YYYY',
                    first_day_of_week=1,
                    clearable=True,
                    with_portal=True,
                    className='date-picker-custom'
                ),
                dcc.Dropdown(
                    id='ano-filter',
                    placeholder="Año",
                    clearable=True
                ),
                dcc.Dropdown(
                    id='mes-filter',
                    placeholder="Mes",
                    options=[
                        {'label': 'Enero', 'value': 1},
                        {'label': 'Febrero', 'value': 2},
                        {'label': 'Marzo', 'value': 3},
                        {'label': 'Abril', 'value': 4},
                        {'label': 'Mayo', 'value': 5},
                        {'label': 'Junio', 'value': 6},
                        {'label': 'Julio', 'value': 7},
                        {'label': 'Agosto', 'value': 8},
                        {'label': 'Septiembre', 'value': 9},
                        {'label': 'Octubre', 'value': 10},
                        {'label': 'Noviembre', 'value': 11},
                        {'label': 'Diciembre', 'value': 12}
                    ],
                    clearable=True
                )
            ], className='filter-item date-range card p-3'),
            
            # Filtros de ubicación
            html.Div([
                html.I(className="fas fa-map-marker-alt"),
                html.Label('Ubicación'),
                dcc.Dropdown(
                    id='zona-filter',
                    placeholder="Zona Geográfica",
                    clearable=True
                ),
                dcc.Dropdown(
                    id='depto-filter',
                    placeholder="Departamento",
                    clearable=True
                ),
                dcc.Dropdown(
                    id='municipio-filter',
                    placeholder="Municipio",
                    clearable=True
                )
            ], className='filter-item location-filters'),
            
            # Filtros de clasificación
            html.Div([
                html.I(className="fas fa-tags"),
                html.Label('Clasificación'),
                dcc.Dropdown(
                    id='categoria-filter',
                    placeholder="Categoría",
                    clearable=True
                ),
                dcc.Dropdown(
                    id='grupo-interes-filter',
                    placeholder="Grupo de Interés",
                    clearable=True
                ),
                dcc.Dropdown(
                    id='grupo-intervencion-filter',
                    placeholder="Grupo de Intervención",
                    clearable=True
                )
            ], className='filter-item classification-filters'),
            
            # Filtros administrativos
            html.Div([
                html.I(className="fas fa-file-contract"),
                html.Label('Información Administrativa'),
                dcc.Dropdown(
                    id='contrato-filter',
                    placeholder="Contrato",
                    clearable=True
                )
            ], className='filter-item administrative-filters'),
            
            # Botones de control
            html.Div([
                html.Button('Limpiar Filtros', 
                           id='clear-filters', 
                           className='btn btn-outline-secondary me-2'),
                html.Button('Aplicar Filtros', 
                           id='apply-filters', 
                           className='btn btn-primary')
            ], className='filter-buttons mt-3')
        ], className='filters-content')
    ], className='filters-container')

def create_kpis():
    """Crea el panel de KPIs"""
    return html.Div([
        # KPIs originales con clases actualizadas
        html.Div([
            html.I(className="fas fa-chart-line"),
            html.H3(id='kpi-actividades'),
            html.P('Total Actividades')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-users"),
            html.H3(id='kpi-asistentes'),
            html.P('Total Asistentes')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-map-marked-alt"),
            html.H3(id='kpi-municipios'),
            html.P('Municipios Cubiertos')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-calendar-check"),
            html.H3(id='kpi-meses-activos'),
            html.P('Meses Activos')
        ], className='kpi-card'),
        # Nuevos KPIs
        html.Div([
            html.I(className="fas fa-globe-americas"),
            html.H3(id='kpi-zonas'),
            html.P('Zonas Geográficas')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-users-cog"),
            html.H3(id='kpi-grupos'),
            html.P('Grupos de Interés')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-user-friends"),
            html.H3(id='kpi-promedio-asistentes'),
            html.P('Promedio Asistentes')
        ], className='kpi-card'),
        html.Div([
            html.I(className="fas fa-file-contract"),
            html.H3(id='kpi-contratos'),
            html.P('Total Contratos')
        ], className='kpi-card')
    ], className='kpi-container')

def create_map_controls():
    """Crea los controles del mapa organizados en paneles"""
    return html.Div([
        html.Div([
            html.H6('Alcance Geográfico', className='control-panel-title'),
            dcc.RadioItems(
                id='map-level',
                options=[
                    {'label': 'Departamentos', 'value': 'departamentos'},
                    {'label': 'Municipios', 'value': 'municipios'},
                    {'label': 'Veredas', 'value': 'veredas'},
                    {'label': 'Cabeceras', 'value': 'cabeceras'}
                ],
                value='municipios',
                className='map-level-selector'
            ),
            html.H6('Tipo de Análisis', className='control-panel-title mt-3'),
            dcc.RadioItems(
                id='map-type',
                options=[
                    {'label': 'Mapa de Puntos', 'value': 'points'},
                    {'label': 'Mapa de Calor', 'value': 'heat'},
                    {'label': 'Mapa Coroplético', 'value': 'choropleth'}
                ],
                value='points',
                className='map-type-selector'
            ),
            html.H6('Mapa Base', className='control-panel-title mt-3'),
            dcc.Dropdown(
                id='basemap-style',
                options=[
                    {'label': 'Claro', 'value': 'carto-positron'},
                    {'label': 'Oscuro', 'value': 'carto-darkmatter'},
                    {'label': 'Satélite', 'value': 'mapbox://styles/mapbox/satellite-v9'},
                    {'label': 'Satélite con Calles', 'value': 'mapbox://styles/mapbox/satellite-streets-v12'},
                    {'label': 'Calles', 'value': 'mapbox://styles/mapbox/streets-v12'},
                    {'label': 'Navegación', 'value': 'mapbox://styles/mapbox/navigation-day-v1'},
                    {'label': 'Navegación Nocturna', 'value': 'mapbox://styles/mapbox/navigation-night-v1'},
                    {'label': 'Topográfico', 'value': 'stamen-terrain'},
                    {'label': 'OpenStreetMap', 'value': 'open-street-map'}
                ],
                value='carto-positron',
                clearable=False,
                className='basemap-selector'
            ),
        ], className='map-controls-panel'),
        
        
    ], className='map-controls-container')

def create_visualizations():
    """Crea los paneles de visualización en disposición vertical"""
    return html.Div([
        # Sección del mapa
        html.Section([
            html.Div([
                html.Div(className='card-icon', children=[
                    html.I(className="fas fa-map-marked-alt")
                ]),
                html.H3('Distribución Territorial'),
            ], className='panel-header'),
            html.Div([
                dcc.Graph(
                    id='mapa-actividades',
                    config={
                        'displayModeBar': True,
                        'scrollZoom': True,
                        'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                    },
                    className='map-graph'
                ),
                create_map_controls()
            ], className='map-container-with-controls card'),
            html.Div(id='fullscreen-map-container')
        ], className='map-section'),
        
        # Sección de Análisis Dinámico
        html.Section([
            html.Div([
                html.Div([
                    html.Div(className='card-icon', children=[
                        html.I(className="fas fa-chart-line")
                    ]),
                    html.H3('Evolución Temporal'),
                ], className='panel-header'),
                dcc.Tabs([
                    dcc.Tab(label='Evolución Temporal - burbujas', children=[
                        dcc.Graph(
                            id='grafico-animado',
                            style={'height': '1000px'}
                        )
                    ]),
                    dcc.Tab(label='Evolución Temporal - barras acumuladas', children=[
                        dcc.Graph(
                            id='grafico-barras-acumulado',
                            style={'height': '1000px'}
                        )
                    ])
                ], className='chart-tabs')
            ], className='chart-panel card')
        ], className='dynamic-analysis-section'),
        
        # Sección de gráficos
        html.Section([
            html.Div([
                html.Div([
                    html.Div(className='card-icon', children=[
                        html.I(className="fas fa-chart-bar")
                    ]),
                    html.H3('Análisis por Categorías'),
                ], className='panel-header'),
                dcc.Tabs([
                    dcc.Tab(label='Tendencia Temporal', children=[
                        html.Div([
                            dcc.Graph(
                                id='grafico-tendencia',
                                config={'displayModeBar': True}
                            )
                        ], className='chart-container')
                    ]),
                    dcc.Tab(label='Distribución por Zona y Departamento', children=[
                        html.Div([
                            html.Div([
                                dcc.Graph(id='grafico-grupos')
                            ], className='chart-column'),
                            html.Div([
                                dcc.Graph(id='grafico-departamentos')
                            ], className='chart-column')
                        ], className='chart-row')
                    ])
                ], className='chart-tabs')
            ], className='chart-panel card')
        ], className='charts-section')
    ], className='visualizations-container')

def create_advanced_analysis():
    """Crea el panel de análisis avanzado"""
    return html.Div([
        html.Div([
            html.Div(className='card-icon', children=[
                html.I(className="fas fa-microscope")
            ]),
            html.H3('Análisis Detallado'),
        ], className='panel-header'),
        dcc.Tabs([
            dcc.Tab(label='Análisis Temporal', children=[
                html.Div([
                    dcc.Graph(id='grafico-temporal-detallado'),
                    dcc.Graph(id='grafico-tendencia-acumulada')
                ], className='row')
            ]),
            dcc.Tab(label='Distribución de Asistentes', children=[
                html.Div([
                    dcc.Graph(id='grafico-distribucion-asistentes'),
                    dcc.Graph(id='grafico-boxplot-asistentes')
                ], className='row')
            ]),
            dcc.Tab(label='Análisis Comparativo', children=[
                html.Div([
                    dcc.Graph(id='grafico-comparativo-zonas'),
                    dcc.Graph(id='grafico-eficiencia-cobertura')
                ], className='row')
            ])
        ], className='custom-tabs')
    ], className='analysis-container')

def create_data_table():
    """Crea el componente de tabla de datos"""
    return html.Div([
        html.Div([
            html.Div(className='card-icon', children=[
                html.I(className="fas fa-table")
            ]),
            html.H3('Registro de Actividades'),
            html.Div([
                html.Button('Exportar a Excel', id='export-excel', className='export-button'),
                dcc.Input(id='search-input', type='text', placeholder='Buscar...', className='search-input'),
                dcc.Download(id='download-data')
            ], className='table-actions')
        ], className='table-header card'),
        dash_table.DataTable(
            id='tabla-datos',
            page_size=10,
            filter_action='native',
            sort_action='native',
            sort_mode='multi',
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'minWidth': '100px',
                'padding': '8px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], className='data-table-container card')

def create_loader():
    """Crea el componente de loader de página"""
    return html.Div([
        html.Div([
            html.Div(className='loader-spinner'),
            html.Div('Actualizando datos...', className='loader-text')
        ], className='loader-content')
    ], id='page-loader', className='page-loader', style={'display': 'none'})

def create_layout():
    """Crea el layout completo de la aplicación"""
    return html.Div([
        # Stores globales
        dcc.Store(id='selected-feature', storage_type='memory'),
        
        # Loader de página
        html.Div([
            html.Div([
                html.Div(className='loader-spinner'),
                html.Div('Cargando...', className='loader-text')
            ], className='loader-content')
        ], id='page-loader', className='page-loader', style={'display': 'none'}),
        
        # Contenedor de notificaciones
        html.Div(id='notification-container'),
        
        # Store para triggers de notificaciones
        dcc.Store(id='notification-trigger'),
        
        # Resto del layout existente...
        create_header(),
        html.Main([
            dcc.Tabs([
                dcc.Tab(
                    label='Dashboard',
                    children=[
                        create_filters(),
                        create_kpis(),
                        create_visualizations(),
                        create_advanced_analysis(),
                        create_data_table()
                    ],
                    className='custom-tab'
                ),
            ], className='custom-tabs')
        ], className='main-content', id='main-content'),
        dcc.Interval(id="scroll-trigger", interval=1000)
    ], className='dashboard-container')