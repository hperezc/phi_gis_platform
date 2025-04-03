import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Determinar el entorno
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configuración de la base de datos
if ENVIRONMENT == 'production':
    # Configuración para VPS
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@db:5432/bd_actividades_historicas')
else:
    # Configuración local
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas')

# Mantener tus configuraciones de mapbox
MAPBOX_TOKEN = os.getenv(
    'MAPBOX_TOKEN',
    'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBtIVaj52w2yw-7ewLU6Q'
)
