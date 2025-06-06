import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from functools import lru_cache
import redis
import json
import hashlib

# Cargar variables de entorno
load_dotenv()

# Determinar el entorno y configurar DATABASE_URL
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
if ENVIRONMENT == 'production':
    # Configuración optimizada para DigitalOcean
    import urllib.parse
    DB_USER = urllib.parse.quote_plus(os.getenv('DB_USER', 'doadmin'))
    DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', ''))
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '25060')
    DB_NAME = os.getenv('DB_NAME', 'defaultdb')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require&connect_timeout=10&statement_timeout=30000"
else:
    # URL local para desarrollo
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas')

# Configurar Redis para cache (si está disponible)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_timeout=5)
    redis_client.ping()
    CACHE_ENABLED = True
    print("✅ Cache Redis habilitado")
except:
    redis_client = None
    CACHE_ENABLED = False
    print("⚠️ Cache Redis no disponible, usando cache en memoria")

@lru_cache(maxsize=1)
def get_db_engine():
    """
    Crea y retorna el engine de SQLAlchemy con optimizaciones para DigitalOcean
    """
    try:
        if ENVIRONMENT == 'production':
            # Configuración optimizada para DigitalOcean con pooling agresivo
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,  # Verificar conexión antes de usar
                pool_size=3,         # Reducido para 4GB RAM
                max_overflow=2,      # Reducido para 4GB RAM  
                pool_recycle=1800,   # Reciclar conexiones cada 30 min
                pool_timeout=10,     # Timeout de pool
                echo=False,          # Sin logs SQL en producción
                connect_args={
                    'connect_timeout': 10,
                    'command_timeout': 30,
                    'application_name': 'phi_dashboard'
                }
            )
        else:
            # En desarrollo mantener simple
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        return engine
    except Exception as e:
        print(f"Error creando engine de base de datos: {str(e)}")
        raise

def get_cache_key(query, params=None):
    """Genera una clave única para el cache basada en la query y parámetros"""
    key_data = f"{query}_{str(params) if params else ''}"
    return f"phi_cache_{hashlib.md5(key_data.encode()).hexdigest()}"

def get_from_cache(cache_key, ttl=300):
    """Obtiene datos del cache con TTL (Time To Live) en segundos"""
    if not CACHE_ENABLED:
        return None
    try:
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
    except:
        pass
    return None

def set_to_cache(cache_key, data, ttl=300):
    """Guarda datos en el cache con TTL"""
    if not CACHE_ENABLED:
        return
    try:
        if redis_client:
            redis_client.setex(cache_key, ttl, json.dumps(data, default=str))
    except:
        pass

def execute_cached_query(query, params=None, ttl=300):
    """Ejecuta una query con cache automático"""
    cache_key = get_cache_key(query, params)
    
    # Intentar obtener del cache primero
    cached_result = get_from_cache(cache_key, ttl)
    if cached_result is not None:
        return pd.DataFrame(cached_result)
    
    # Si no está en cache, ejecutar query
    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            if params:
                result = pd.read_sql(query, connection, params=params)
            else:
                result = pd.read_sql(query, connection)
            
            # Guardar en cache
            set_to_cache(cache_key, result.to_dict('records'), ttl)
            return result
    except Exception as e:
        print(f"Error ejecutando query: {str(e)}")
        return pd.DataFrame()

def execute_query(query, params=None):
    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            if params:
                result = connection.execute(query, params)
            else:
                result = connection.execute(query)
            return result
    except Exception as e:
        print(f"Error ejecutando query: {str(e)}")
        return None

def get_filter_options():
    """Obtiene todas las opciones para los filtros desde la base de datos"""
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            options = {
                'anos': pd.read_sql("""
                    SELECT DISTINCT ano 
                    FROM actividades 
                    WHERE ano IS NOT NULL 
                    ORDER BY ano DESC""", conn),
                    
                'meses': pd.read_sql("""
                    SELECT DISTINCT EXTRACT(MONTH FROM fecha) as mes,
                           TO_CHAR(fecha, 'Month') as nombre_mes
                    FROM actividades 
                    WHERE fecha IS NOT NULL 
                    ORDER BY mes""", conn),
                    
                'zonas': pd.read_sql("""
                    SELECT DISTINCT zona_geografica 
                    FROM actividades 
                    WHERE zona_geografica IS NOT NULL 
                    ORDER BY zona_geografica""", conn),
                    
                'departamentos': pd.read_sql("""
                    SELECT DISTINCT departamento 
                    FROM actividades 
                    WHERE departamento IS NOT NULL 
                    ORDER BY departamento""", conn),
                    
                'municipios': pd.read_sql("""
                    SELECT DISTINCT municipio, departamento
                    FROM actividades 
                    WHERE municipio IS NOT NULL 
                    ORDER BY departamento, municipio""", conn),
                    
                'categorias': pd.read_sql("""
                    SELECT DISTINCT categoria_unica 
                    FROM actividades 
                    WHERE categoria_unica IS NOT NULL 
                    ORDER BY categoria_unica""", conn),
                    
                'grupos_interes': pd.read_sql("""
                    SELECT DISTINCT grupo_interes 
                    FROM actividades 
                    WHERE grupo_interes IS NOT NULL 
                    ORDER BY grupo_interes""", conn),
                    
                'grupo_intervencion': pd.read_sql("""
                    SELECT DISTINCT grupo_intervencion 
                    FROM actividades 
                    WHERE grupo_intervencion IS NOT NULL 
                    ORDER BY grupo_intervencion""", conn),
                    
                'ubicacion': pd.read_sql("""
                    SELECT DISTINCT ubicacion 
                    FROM actividades 
                    WHERE ubicacion IS NOT NULL 
                    ORDER BY ubicacion""", conn),
                    
                'contratos': pd.read_sql("""
                    SELECT DISTINCT contrato 
                    FROM actividades 
                    WHERE contrato IS NOT NULL 
                    ORDER BY contrato""", conn),
                    
                'tipo_geometria': pd.read_sql("""
                    SELECT DISTINCT tipo_geometria 
                    FROM actividades 
                    WHERE tipo_geometria IS NOT NULL 
                    ORDER BY tipo_geometria""", conn)
            }
            return options
    except Exception as e:
        print(f"Error obteniendo opciones de filtros: {str(e)}")
        return {}

def get_kpi_data(start_date=None, end_date=None, ano=None, zona=None, 
                 depto=None, municipio=None, categoria=None, grupo=None, contrato=None):
    """Obtiene los datos para los KPIs con los filtros aplicados - CON CACHE"""
    query = """
        SELECT 
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            COUNT(DISTINCT municipio) as total_municipios,
            COUNT(DISTINCT DATE_TRUNC('month', fecha)) as total_meses_activos,
            COUNT(DISTINCT zona_geografica) as total_zonas,
            COUNT(DISTINCT grupo_interes) as total_grupos_interes,
            ROUND(AVG(total_asistentes)::numeric, 2) as promedio_asistentes,
            COUNT(DISTINCT contrato) as total_contratos
        FROM actividades
        WHERE 1=1
    """
    
    params = []
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:  # Agregamos el filtro de municipio
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    try:
        # Usar cache de 3 minutos para KPIs (son consultas costosas)
        df = execute_cached_query(query, tuple(params) if params else None, ttl=180)
        return df.iloc[0].to_dict() if not df.empty else {
            'total_actividades': 0,
            'total_asistentes': 0,
            'total_municipios': 0,
            'total_meses_activos': 0,
            'total_zonas': 0,
            'total_grupos_interes': 0,
            'promedio_asistentes': 0,
            'total_contratos': 0
        }
    except Exception as e:
        print(f"Error obteniendo KPIs: {str(e)}")
        return {
            'total_actividades': 0,
            'total_asistentes': 0,
            'total_municipios': 0,
            'total_meses_activos': 0,
            'total_zonas': 0,
            'total_grupos_interes': 0,
            'promedio_asistentes': 0,
            'total_contratos': 0
        }

def get_map_data(start_date=None, end_date=None, ano=None, zona=None, 
                depto=None, municipio=None, categoria=None, grupo=None):
    """
    Obtiene datos del mapa con optimizaciones específicas
    """
    engine = get_db_engine()
    
    # Query optimizada con índices específicos
    query = """
        SELECT 
            departamento,
            municipio,
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            ROUND(AVG(total_asistentes)::numeric, 2) as promedio_asistentes,
            geometry
        FROM actividades 
        WHERE geometry IS NOT NULL
    """
    
    # Construir filtros dinámicamente
    conditions = []
    params = []
    
    if start_date and end_date:
        conditions.append("fecha BETWEEN %s AND %s")
        params.extend([start_date, end_date])
    if ano:
        conditions.append("ano = %s")
        params.append(ano)
    if zona:
        conditions.append("zona_geografica = %s")
        params.append(zona)
    if depto:
        conditions.append("departamento = %s")
        params.append(depto)
    if municipio:
        conditions.append("municipio = %s")
        params.append(municipio)
    if categoria:
        conditions.append("categoria_unica = %s")
        params.append(categoria)
    if grupo:
        conditions.append("grupo_interes = %s")
        params.append(grupo)
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " GROUP BY departamento, municipio, geometry ORDER BY total_actividades DESC LIMIT 1000"
    
    try:
        return gpd.read_postgis(query, engine, geom_col='geometry', params=tuple(params) if params else None)
    except Exception as e:
        print(f"Error obteniendo datos del mapa: {str(e)}")
        return gpd.GeoDataFrame()

def get_detailed_data(start_date=None, end_date=None, ano=None, mes=None, zona=None, 
                     depto=None, municipio=None, categoria=None, grupo=None, 
                     grupo_intervencion=None, contrato=None):
    """Obtiene los datos detallados con todos los filtros"""
    engine = get_db_engine()
    query = """
        SELECT *
        FROM actividades
        WHERE 1=1
    """
    params = []
    
    # Aplicar todos los filtros
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if mes:
        query += " AND EXTRACT(MONTH FROM fecha) = %s"
        params.append(mes)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:  # Nuevo filtro
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if grupo_intervencion:  # Nuevo filtro
        query += " AND grupo_intervencion = %s"
        params.append(grupo_intervencion)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=tuple(params) if params else None)
    except Exception as e:
        print(f"Error obteniendo datos detallados: {str(e)}")
        return pd.DataFrame()

def get_chart_data(chart_type, start_date=None, end_date=None, ano=None, zona=None, 
                  depto=None, municipio=None, categoria=None, grupo=None, contrato=None):
    """Obtiene datos para los gráficos"""
    engine = get_db_engine()
    
    if chart_type == 'categorias':
        query = """
            SELECT 
                id,
                categoria_unica, 
                categoria_actividad,
                descripcion_actividad,
                total_asistentes
            FROM actividades
            WHERE categoria_unica IS NOT NULL 
            AND categoria_actividad IS NOT NULL
            AND descripcion_actividad IS NOT NULL
        """
    elif chart_type == 'tendencia':
        query = """
            SELECT DATE_TRUNC('month', fecha) as mes, COUNT(*) as total_actividades
            FROM actividades
            WHERE 1=1
        """
    elif chart_type == 'grupos':
        query = """
            SELECT grupo_interes, COUNT(*) as total_actividades
            FROM actividades
            WHERE 1=1
        """
    elif chart_type == 'departamentos':
        query = """
            SELECT departamento, COUNT(*) as total_actividades
            FROM actividades
            WHERE 1=1
        """
    
    # Aplicar filtros
    params = []
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:  # Agregamos el filtro de municipio
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params=tuple(params) if params else None)
            if chart_type == 'tendencia':
                # Asegurarnos de que la columna mes sea de tipo datetime
                df['mes'] = pd.to_datetime(df['mes'])
            return df
    except Exception as e:
        print(f"Error obteniendo datos para gráfico {chart_type}: {str(e)}")
        return pd.DataFrame()

def get_temporal_analysis(start_date=None, end_date=None, ano=None, zona=None, 
                         depto=None, municipio=None, categoria=None, grupo=None, contrato=None):
    """Obtiene análisis temporal detallado"""
    engine = get_db_engine()
    query = """
        SELECT 
            DATE_TRUNC('week', fecha)::date as semana,
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            COUNT(DISTINCT municipio) as municipios_cubiertos,
            COUNT(DISTINCT grupo_interes) as grupos_atendidos,
            AVG(total_asistentes) as promedio_asistentes
        FROM actividades
        WHERE 1=1
    """
    
    params = []
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    query += " GROUP BY DATE_TRUNC('week', fecha) ORDER BY semana"
    
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=tuple(params) if params else None)
    except Exception as e:
        print(f"Error en análisis temporal: {str(e)}")
        return pd.DataFrame()

def get_distribution_analysis(start_date=None, end_date=None, ano=None, zona=None, 
                            depto=None, municipio=None, categoria=None, grupo=None, contrato=None):
    """Obtiene análisis de distribución de asistentes por municipio"""
    engine = get_db_engine()
    query = """
        SELECT 
            municipio,
            departamento,
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            AVG(total_asistentes) as promedio_asistentes,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_asistentes) as mediana_asistentes,
            MIN(total_asistentes) as min_asistentes,
            MAX(total_asistentes) as max_asistentes,
            STDDEV(total_asistentes) as desviacion_asistentes
        FROM actividades
        WHERE municipio IS NOT NULL
    """
    
    params = []
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    query += " GROUP BY municipio, departamento ORDER BY total_actividades DESC"
    
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=tuple(params) if params else None)
    except Exception as e:
        print(f"Error en análisis de distribución: {str(e)}")
        return pd.DataFrame()

def get_comparative_analysis(start_date=None, end_date=None, ano=None, zona=None, 
                           depto=None, municipio=None, categoria=None, grupo=None, contrato=None):
    """Obtiene análisis comparativo por zona geográfica"""
    engine = get_db_engine()
    query = """
        SELECT 
            zona_geografica,
            departamento,
            categoria_unica,
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            COUNT(DISTINCT municipio) as total_municipios,
            COUNT(DISTINCT grupo_interes) as total_grupos,
            COUNT(DISTINCT contrato) as total_contratos,
            ROUND(AVG(total_asistentes)::numeric, 2) as eficiencia
        FROM actividades
        WHERE zona_geografica IS NOT NULL 
        AND departamento IS NOT NULL
        AND categoria_unica IS NOT NULL
    """
    
    params = []
    if start_date and end_date:
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if zona:
        query += " AND zona_geografica = %s"
        params.append(zona)
    if depto:
        query += " AND departamento = %s"
        params.append(depto)
    if municipio:
        query += " AND municipio = %s"
        params.append(municipio)
    if categoria:
        query += " AND categoria_unica = %s"
        params.append(categoria)
    if grupo:
        query += " AND grupo_interes = %s"
        params.append(grupo)
    if contrato:
        query += " AND contrato = %s"
        params.append(contrato)
    
    query += " GROUP BY zona_geografica, departamento, categoria_unica ORDER BY zona_geografica, departamento, total_actividades DESC"
    
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=tuple(params) if params else None)
    except Exception as e:
        print(f"Error en análisis comparativo: {str(e)}")
        return pd.DataFrame()

def apply_filters(query, params, filters):
    """Aplica filtros comunes a las consultas"""
    if filters.get('start_date') and filters.get('end_date'):
        query += " AND fecha BETWEEN %s AND %s"
        params.extend([filters['start_date'], filters['end_date']])
    
    if filters.get('ano'):
        query += " AND ano = %s"
        params.append(filters['ano'])
        
    if filters.get('mes'):
        query += " AND EXTRACT(MONTH FROM fecha) = %s"
        params.append(filters['mes'])
        
    if filters.get('zona'):
        query += " AND zona_geografica = %s"
        params.append(filters['zona'])
        
    if filters.get('depto'):
        query += " AND departamento = %s"
        params.append(filters['depto'])
        
    if filters.get('municipio'):
        query += " AND municipio = %s"
        params.append(filters['municipio'])
        
    if filters.get('categoria'):
        query += " AND categoria_unica = %s"
        params.append(filters['categoria'])
        
    if filters.get('grupo'):
        query += " AND grupo_interes = %s"
        params.append(filters['grupo'])
        
    if filters.get('grupo_intervencion'):
        query += " AND grupo_intervencion = %s"
        params.append(filters['grupo_intervencion'])
        
    if filters.get('ubicacion'):
        query += " AND ubicacion = %s"
        params.append(filters['ubicacion'])
        
    if filters.get('contrato'):
        query += " AND contrato = %s"
        params.append(filters['contrato'])
        
    if filters.get('tipo_geometria'):
        query += " AND tipo_geometria = %s"
        params.append(filters['tipo_geometria'])
        
    return query, params

def get_geometry_data(layer_type):
    """Obtiene los datos geométricos según el tipo de capa"""
    engine = get_db_engine()
    
    try:
        if layer_type == 'departamentos':
            query = """
                SELECT 
                    departamento as nombre,
                    geometry,
                    COUNT(*) as total_actividades,
                    SUM(total_asistentes) as total_asistentes
                FROM actividades_departamentos
                GROUP BY departamento, geometry
            """
            params = None
        elif layer_type == 'municipios':
            query = """
                SELECT 
                    municipio as nombre,
                    departamento,
                    geometry,
                    COUNT(*) as total_actividades,
                    SUM(total_asistentes) as total_asistentes
                FROM actividades_municipios
                GROUP BY municipio, departamento, geometry
            """
            params = None
        else:
            return gpd.GeoDataFrame()
            
        gdf = gpd.read_postgis(query, engine, geom_col='geometry', params=params)
        return gdf
        
    except Exception as e:
        print(f"Error en get_geometry_data: {str(e)}")
        return gpd.GeoDataFrame()