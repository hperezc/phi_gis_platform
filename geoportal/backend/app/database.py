from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import urllib.parse
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener y codificar los parámetros de conexión para DigitalOcean
DB_USER = urllib.parse.quote_plus(os.getenv('DB_USER', 'postgres'))
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', '0000'))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bd_actividades_historicas')

# Construir la URL de conexión
if os.getenv('ENVIRONMENT') == 'production':
    # Configuración para DigitalOcean con SSL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    logger.info("Configurando geoportal para DigitalOcean")
else:
    # Configuración local
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("Configurando geoportal para desarrollo local")

# Crear el engine de SQLAlchemy con parámetros específicos para DigitalOcean
engine = create_engine(
    DATABASE_URL,
    client_encoding='utf8',
    connect_args={
        'client_encoding': 'utf8',
        'options': '-c timezone=utc -c client_encoding=utf8'
    } if os.getenv('ENVIRONMENT') != 'production' else {
        'sslmode': 'require',
        'client_encoding': 'utf8',
        'options': '-c timezone=utc -c client_encoding=utf8'
    },
    echo=False  # Cambiar a True para debug
)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Función para obtener una conexión a la base de datos.
    Se usa como dependencia en FastAPI.
    """
    db = None
    try:
        db = SessionLocal()
        return db
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        if db:
            db.close()
        raise

def test_connection():
    """Función para probar la conexión a la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        return False
