import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas')

# Estilos externos
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
    'https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
]

# Configuración de colores y tema
THEME = {
    'primary': '#1f77b4',
    'secondary': '#2ca02c',
    'background': '#ffffff',
    'text': '#333333',
    'grid': '#e1e1e1'
}

# Añadir el token de Mapbox como variable global
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN', 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBtIVaj52w2yw-7ewLU6Q')

# Configuración del mapa
MAP_CONFIG = {
    'default_center': {'lat': 4.5709, 'lon': -74.2973},
    'default_zoom': 5,
    'style': 'carto-positron',
    'mapbox_token': MAPBOX_TOKEN
}

# Configuración de la tabla
TABLE_CONFIG = {
    'page_size': 15,
    'filter_action': 'native',
    'sort_action': 'native',
    'sort_mode': 'multi',
    'style_table': {
        'overflowX': 'auto',
        'boxShadow': '0 0 10px rgba(0,0,0,0.1)'
    },
    'style_cell': {
        'textAlign': 'left',
        'minWidth': '100px',
        'padding': '12px',
        'fontFamily': 'Roboto'
    },
    'style_header': {
        'backgroundColor': THEME['primary'],
        'color': 'white',
        'fontWeight': 'bold',
        'textAlign': 'center'
    },
    'style_data_conditional': [
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        }
    ]
}