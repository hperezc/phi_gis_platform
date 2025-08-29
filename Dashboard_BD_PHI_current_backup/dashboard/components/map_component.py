import plotly.graph_objects as go
from dash import html, dcc
import pandas as pd
import geopandas as gpd

def create_map_component():
    """Crea el componente del mapa interactivo"""
    return html.Div([
        # Controles del mapa
        html.Div([
            dcc.Checklist(
                id='layer-control',
                options=[
                    {'label': 'Departamentos', 'value': 'departamentos'},
                    {'label': 'Municipios', 'value': 'municipios'},
                    {'label': 'Veredas', 'value': 'veredas'},
                    {'label': 'Cabeceras', 'value': 'cabeceras'}
                ],
                value=['municipios'],
                inline=True,
                className='map-layers-control'
            ),
            dcc.RadioItems(
                id='map-style',
                options=[
                    {'label': 'Mapa de Calor', 'value': 'heat'},
                    {'label': 'Coroplético', 'value': 'choropleth'},
                    {'label': 'Puntos', 'value': 'points'}
                ],
                value='choropleth',
                inline=True,
                className='map-style-control'
            )
        ], className='map-controls'),
        
        # Contenedor del mapa
        dcc.Graph(
            id='interactive-map',
            config={
                'displayModeBar': True,
                'scrollZoom': True,
                'modeBarButtonsToRemove': ['select2d', 'lasso2d']
            },
            className='map-container'
        )
    ], className='map-component') 