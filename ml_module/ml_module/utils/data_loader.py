"""
Módulo para cargar y gestionar datos de la base de datos.
"""

import logging
from sqlalchemy import create_engine, text
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas')

class DataLoader:
    def __init__(self):
        """Inicializa el cargador de datos."""
        try:
            # Configurar la conexión a la base de datos
            self.engine = create_engine(DATABASE_URL)
            logger.info("DataLoader inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando DataLoader: {str(e)}")
            raise

    def get_zonas_geograficas(self) -> list:
        """Obtiene las zonas geográficas disponibles"""
        try:
            query = """
                SELECT DISTINCT zona_geografica 
                FROM actividades 
                WHERE zona_geografica IS NOT NULL 
                ORDER BY zona_geografica
            """
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error obteniendo zonas geográficas: {str(e)}")
            return []

    def get_departamentos_por_zona(self, zona_geografica: str) -> list:
        """Obtiene departamentos por zona geográfica"""
        try:
            query = """
                SELECT DISTINCT departamento 
                FROM actividades 
                WHERE zona_geografica = :zona
                AND departamento IS NOT NULL 
                ORDER BY departamento
            """
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {'zona': zona_geografica})
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error obteniendo departamentos: {str(e)}")
            return []

    def get_municipios(self, departamento: str = None, zona_geografica: str = None) -> list:
        """Obtiene municipios filtrados por departamento y/o zona geográfica"""
        try:
            query = """
                SELECT DISTINCT municipio 
                FROM actividades 
                WHERE municipio IS NOT NULL
            """
            params = {}
            
            if departamento:
                query += " AND departamento = :departamento"
                params['departamento'] = departamento
                
            if zona_geografica:
                query += " AND zona_geografica = :zona"
                params['zona'] = zona_geografica
                
            query += " ORDER BY municipio"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error obteniendo municipios: {str(e)}")
            return []

    def verify_table_structure(self):
        """Verifica la estructura exacta de las tablas"""
        try:
            queries = {
                'actividades': """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'actividades'
                    ORDER BY ordinal_position;
                """,
                'actividades_municipios': """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'actividades_municipios'
                    ORDER BY ordinal_position;
                """
            }
            
            with self.engine.connect() as conn:
                for table, query in queries.items():
                    result = conn.execute(text(query))
                    columns = [row for row in result]
                    logger.info(f"Estructura de tabla {table}:")
                    for col in columns:
                        logger.info(f"  - {col[0]}: {col[1]}")
                        
        except Exception as e:
            logger.error(f"Error verificando estructura: {str(e)}")

    def load_training_data(self, filters=None):
        """Carga datos de entrenamiento con filtros opcionales"""
        try:
            # Primero verificar la estructura de las tablas
            self.verify_table_structure()
            
            # Construir condiciones de filtro
            filter_conditions = []
            params = {}
            
            if filters:
                if filters.get('departamento'):
                    filter_conditions.append("a.departamento = :departamento")
                    params['departamento'] = filters['departamento']
                if filters.get('zona_geografica'):
                    filter_conditions.append("a.zona_geografica = :zona")
                    params['zona'] = filters['zona_geografica']
                if filters.get('municipio'):
                    filter_conditions.append("a.municipio = :municipio")
                    params['municipio'] = filters['municipio']
                if filters.get('fecha_inicio'):
                    filter_conditions.append("a.fecha >= :fecha_inicio")
                    params['fecha_inicio'] = filters['fecha_inicio']
                if filters.get('fecha_fin'):
                    filter_conditions.append("a.fecha <= :fecha_fin")
                    params['fecha_fin'] = filters['fecha_fin']
                if filters.get('tipo_actividad'):
                    filter_conditions.append("a.categoria_unica = :tipo")
                    params['tipo'] = filters['tipo_actividad']

            # Construir la consulta base
            base_query = """
                SELECT 
                    m.municipio,
                    m.departamento,
                    ST_X(ST_Centroid(m.geometry::geometry)) as longitud,
                    ST_Y(ST_Centroid(m.geometry::geometry)) as latitud,
                    COALESCE(act.num_actividades, 0) as num_actividades,
                    COALESCE(act.total_asistentes, 0) as total_asistentes,
                    CASE 
                        WHEN COALESCE(act.num_actividades, 0) > 0 
                        THEN COALESCE(act.total_asistentes, 0)::float / act.num_actividades
                        ELSE 0 
                    END as eficiencia_actividad
                FROM actividades_municipios m
                LEFT JOIN (
                    SELECT 
                        municipio,
                        departamento,
                        COUNT(*) as num_actividades,
                        SUM(total_asistentes) as total_asistentes
                    FROM actividades a
                    WHERE 1=1
                    {where_clause}
                    GROUP BY municipio, departamento
                ) act ON m.municipio = act.municipio AND m.departamento = act.departamento
                WHERE m.geometry IS NOT NULL
                AND COALESCE(act.num_actividades, 0) > 0
                ORDER BY m.departamento, m.municipio
            """
            
            # Agregar cláusula WHERE si hay filtros
            where_clause = f"AND {' AND '.join(filter_conditions)}" if filter_conditions else ""
            query = text(base_query.format(where_clause=where_clause))

            # Ejecutar la consulta
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            
            logger.info(f"Datos cargados: {len(df)} municipios")
            logger.info(f"Total actividades: {df['num_actividades'].sum()}")
            logger.info(f"Total asistentes: {df['total_asistentes'].sum()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error cargando datos de entrenamiento: {str(e)}")
            return pd.DataFrame()

    def verify_tables(self):
        """Verifica la estructura y contenido de las tablas principales"""
        try:
            # Verificar tabla actividades
            actividades_query = """
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT departamento) as total_departamentos,
                       COUNT(DISTINCT municipio) as total_municipios,
                       COUNT(DISTINCT grupo_interes) as total_grupos
                FROM actividades;
            """
            
            # Verificar tabla actividades_municipios
            municipios_query = """
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT departamento) as total_departamentos,
                       COUNT(DISTINCT municipio) as total_municipios
                FROM actividades_municipios;
            """
            
            # Verificar tabla actividades_departamentos
            departamentos_query = """
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT departamento) as total_departamentos
                FROM actividades_departamentos;
            """
            
            # Ejecutar las consultas
            with self.engine.connect() as conn:
                logger.info("Verificando tabla actividades...")
                act_stats = pd.read_sql(actividades_query, conn)
                
                logger.info("Verificando tabla actividades_municipios...")
                mun_stats = pd.read_sql(municipios_query, conn)
                
                logger.info("Verificando tabla actividades_departamentos...")
                dep_stats = pd.read_sql(departamentos_query, conn)
                
                return {
                    'actividades': {
                        'total': int(act_stats['total'].iloc[0]),
                        'total_departamentos': int(act_stats['total_departamentos'].iloc[0]),
                        'total_municipios': int(act_stats['total_municipios'].iloc[0]),
                        'total_grupos': int(act_stats['total_grupos'].iloc[0])
                    },
                    'actividades_municipios': {
                        'total': int(mun_stats['total'].iloc[0]),
                        'total_departamentos': int(mun_stats['total_departamentos'].iloc[0]),
                        'total_municipios': int(mun_stats['total_municipios'].iloc[0])
                    },
                    'actividades_departamentos': {
                        'total': int(dep_stats['total'].iloc[0]),
                        'total_departamentos': int(dep_stats['total_departamentos'].iloc[0])
                    }
                }
                
        except Exception as e:
            logger.error(f"Error verificando tablas: {str(e)}")
            raise 