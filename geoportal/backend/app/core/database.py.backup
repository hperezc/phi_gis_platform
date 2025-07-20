from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Configuración de la base de datos
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "0000")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bd_actividades_historicas")

# Construir URL con parámetros adicionales para codificación
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=True,  # Para ver las consultas SQL
        connect_args={
            'client_encoding': 'utf8',
            'options': '-c search_path=public'
        }
    )
    
    # Verificar conexión
    with engine.connect() as connection:
        connection.execute(text("SET client_encoding TO 'UTF8';"))
        connection.execute(text("SELECT 1"))
        print("✅ Conexión establecida correctamente")
        
        # Verificar PostGIS
        result = connection.execute(text("SELECT PostGIS_Version()"))
        print(f"✅ PostGIS versión: {result.scalar()}")

except Exception as e:
    print(f"❌ Error de conexión: {str(e)}")
    raise Exception(f"""
        Error al conectar con la base de datos: {str(e)}
        
        Configuración actual:
        Base de datos: {DB_NAME}
        Host: {DB_HOST}:{DB_PORT}
        Usuario: {DB_USER}
        
        Por favor verifica:
        1. Que PostgreSQL esté corriendo
        2. Las credenciales sean correctas
        3. La base de datos '{DB_NAME}' exista
        4. La extensión PostGIS esté instalada
    """)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 