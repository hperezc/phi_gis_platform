import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Determinar el entorno
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configuración de la base de datos
if ENVIRONMENT == 'production':
    # Configuración para Digital Ocean - usar variables de entorno por seguridad
    DATABASE_URL = os.getenv('DATABASE_URL', 
        'postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require')
else:
    # Configuración local
    DATABASE_URL = 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas'

# Mantener tus configuraciones de mapbox
MAPBOX_TOKEN = os.getenv(
    'MAPBOX_TOKEN',
    'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'
)
