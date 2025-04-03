from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import urllib.parse

# Cargar variables de entorno
load_dotenv()

# Obtener y codificar los parámetros de conexión
DB_USER = urllib.parse.quote_plus(os.getenv('DB_USER', 'postgres'))
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', '0000'))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bd_actividades_historicas')

# Construir la URL de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear el engine de SQLAlchemy con parámetros específicos
engine = create_engine(
    DATABASE_URL,
    client_encoding='utf8',
    connect_args={
        'client_encoding': 'utf8',
        'options': '-c timezone=utc -c client_encoding=utf8'
    }
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
        print(f"Error conectando a la base de datos: {e}")
        if db:
            db.close()
        raise 