import os
import sys
from dash import Dash, dash_table
import dash_bootstrap_components as dbc
from dash import html

# Asegurar que Python puede encontrar los módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../..')
sys.path.append(project_root)

# Importaciones relativas
from .components.callbacks import register_callbacks
from .config.settings import external_stylesheets
from .components.layout import create_layout
from .components import callbacks

def create_dash_app():
    """Crea y configura la aplicación Dash"""
    app = Dash(
        __name__,
        requests_pathname_prefix='/dashboard/',
        suppress_callback_exceptions=True,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
        ],
        assets_folder='assets',
        serve_locally=True,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
        ],
        title='Dashboard BD PHI'
    )

    # Configuración del servidor
    app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Configurar el layout
    app.layout = create_layout()

    # Registrar los callbacks
    register_callbacks(app)

    return app

def create_navbar():
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/dashboard/assets/logo.png", height="30px"),
                    dbc.NavbarBrand("Dashboard de Actividades PHI", className="ms-2")
                ]),
            ]),
            dbc.Row([
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard")),
                    dbc.NavItem(
                        dbc.Button(
                            [html.I(className="fas fa-map-marked-alt me-2"), "Geoportal"],
                            href="/geoportal",
                            color="light",
                            className="ms-2"
                        )
                    )
                ])
            ])
        ])
    )

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
