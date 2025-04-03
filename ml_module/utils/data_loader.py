from sqlalchemy import create_engine, text
import pandas as pd
import logging
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
        self.engine = create_engine(DATABASE_URL)
        
    def load_training_data(self):
        """Carga los datos de entrenamiento desde la base de datos"""
        query = """
            WITH actividades_stats AS (
                SELECT 
                    departamento,
                    municipio,
                    COUNT(*) as actividades_previas,
                    AVG(total_asistentes) as promedio_asistentes_historico
                FROM actividades
                GROUP BY departamento, municipio
            )
            SELECT 
                a.id,
                a.contrato,
                a.ano,
                a.mes,
                a.fecha,
                a.zona_geografica,
                a.departamento,
                a.municipio,
                a.grupo_interes,
                a.ubicacion,
                a.grupo_intervencion,
                a.descripcion_actividad,
                a.categoria_actividad,
                a.categoria_unica,
                a.total_asistentes,
                stats.actividades_previas,
                stats.promedio_asistentes_historico,
                EXTRACT(DOW FROM a.fecha) as dia_semana,
                EXTRACT(MONTH FROM a.fecha) as mes_numero,
                EXTRACT(YEAR FROM a.fecha) as year
            FROM actividades a
            LEFT JOIN actividades_stats stats 
                ON a.departamento = stats.departamento 
                AND a.municipio = stats.municipio
            WHERE a.total_asistentes IS NOT NULL
            AND a.fecha IS NOT NULL
            ORDER BY a.fecha
        """
        
        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"Datos cargados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            raise
    
    def load_geographical_stats(self):
        """Carga estadísticas por ubicación desde las tablas geográficas"""
        query = """
            SELECT 
                d.departamento,
                COUNT(DISTINCT m.municipio) as total_municipios,
                COUNT(DISTINCT a.grupo_interes) as total_grupos_interes,
                AVG(a.total_asistentes) as promedio_asistentes_depto,
                COUNT(DISTINCT a.categoria_unica) as total_categorias
            FROM actividades_departamentos d
            LEFT JOIN actividades_municipios m ON d.departamento = m.departamento
            LEFT JOIN actividades a ON d.departamento = a.departamento
            GROUP BY d.departamento
        """
        
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Error cargando estadísticas geográficas: {str(e)}")
            raise
    
    def load_recent_activities(self, limit=100):
        """Carga las actividades más recientes con estadísticas adicionales"""
        query = f"""
            WITH recent_stats AS (
                SELECT 
                    zona_geografica,
                    categoria_unica,
                    AVG(total_asistentes) as promedio_categoria,
                    COUNT(*) as total_actividades_categoria
                FROM actividades
                GROUP BY zona_geografica, categoria_unica
            )
            SELECT 
                a.*,
                rs.promedio_categoria,
                rs.total_actividades_categoria,
                EXTRACT(DOW FROM a.fecha) as dia_semana,
                EXTRACT(MONTH FROM a.fecha) as mes_numero
            FROM actividades a
            LEFT JOIN recent_stats rs 
                ON a.zona_geografica = rs.zona_geografica 
                AND a.categoria_unica = rs.categoria_unica
            ORDER BY a.fecha DESC
            LIMIT {limit}
        """
        
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Error cargando actividades recientes: {str(e)}")
            raise
    
    def get_unique_values(self):
        """Obtiene los valores únicos de las columnas categóricas"""
        try:
            queries = {
                'departamentos': "SELECT DISTINCT departamento FROM actividades ORDER BY departamento",
                'municipios': "SELECT DISTINCT municipio FROM actividades ORDER BY municipio",
                'zonas': "SELECT DISTINCT zona_geografica FROM actividades ORDER BY zona_geografica",
                'categorias': "SELECT DISTINCT categoria_unica FROM actividades ORDER BY categoria_unica",
                'grupos': "SELECT DISTINCT grupo_interes FROM actividades ORDER BY grupo_interes"
            }
            
            results = {}
            for key, query in queries.items():
                results[key] = pd.read_sql(query, self.engine)['departamento' if key == 'departamentos' else 
                                                              'municipio' if key == 'municipios' else
                                                              'zona_geografica' if key == 'zonas' else
                                                              'categoria_unica' if key == 'categorias' else
                                                              'grupo_interes'].tolist()
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo valores únicos: {str(e)}")
            raise
    
    def serialize_for_json(self, obj):
        """Convierte objetos especiales a formato serializable para JSON"""
        if hasattr(obj, 'isoformat'):  # Para fechas y datetimes
            return obj.isoformat()
        elif hasattr(obj, 'hex'):  # Para datos binarios/geometrías
            return f"0x{obj.hex()}"
        return str(obj)  # Para cualquier otro tipo no serializable

    def verify_tables(self):
        """Verifica la estructura y contenido de las tres tablas principales"""
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
                
                # Mostrar muestra de cada tabla
                logger.info("\nMuestra de actividades:")
                sample_act = pd.read_sql("SELECT * FROM actividades LIMIT 5", conn)
                logger.info(f"\nColumnas en actividades: {sample_act.columns.tolist()}")
                logger.info(f"Registros totales: {act_stats['total'].iloc[0]}")
                logger.info(f"Departamentos únicos: {act_stats['total_departamentos'].iloc[0]}")
                logger.info(f"Municipios únicos: {act_stats['total_municipios'].iloc[0]}")
                logger.info(f"Grupos de interés únicos: {act_stats['total_grupos'].iloc[0]}")
                
                logger.info("\nMuestra de actividades_municipios:")
                sample_mun = pd.read_sql("SELECT * FROM actividades_municipios LIMIT 5", conn)
                logger.info(f"\nColumnas en actividades_municipios: {sample_mun.columns.tolist()}")
                logger.info(f"Registros totales: {mun_stats['total'].iloc[0]}")
                logger.info(f"Departamentos únicos: {mun_stats['total_departamentos'].iloc[0]}")
                logger.info(f"Municipios únicos: {mun_stats['total_municipios'].iloc[0]}")
                
                logger.info("\nMuestra de actividades_departamentos:")
                sample_dep = pd.read_sql("SELECT * FROM actividades_departamentos LIMIT 5", conn)
                logger.info(f"\nColumnas en actividades_departamentos: {sample_dep.columns.tolist()}")
                logger.info(f"Registros totales: {dep_stats['total'].iloc[0]}")
                logger.info(f"Departamentos únicos: {dep_stats['total_departamentos'].iloc[0]}")
                
                # Procesar los datos para JSON
                def process_records(df):
                    records = []
                    for record in df.to_dict('records'):
                        processed_record = {}
                        for key, value in record.items():
                            processed_record[key] = self.serialize_for_json(value)
                        records.append(processed_record)
                    return records

                return {
                    'actividades': {
                        'total': int(act_stats['total'].iloc[0]),
                        'columnas': sample_act.columns.tolist(),
                        'muestra': process_records(sample_act)
                    },
                    'actividades_municipios': {
                        'total': int(mun_stats['total'].iloc[0]),
                        'columnas': sample_mun.columns.tolist(),
                        'muestra': process_records(sample_mun)
                    },
                    'actividades_departamentos': {
                        'total': int(dep_stats['total'].iloc[0]),
                        'columnas': sample_dep.columns.tolist(),
                        'muestra': process_records(sample_dep)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error verificando tablas: {str(e)}")
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

    def get_zona_from_departamento(self, departamento: str) -> str:
        """Obtiene la zona geográfica de un departamento"""
        try:
            query = """
                SELECT DISTINCT zona_geografica 
                FROM actividades 
                WHERE departamento = :departamento 
                AND zona_geografica IS NOT NULL
                LIMIT 1
            """
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {'departamento': departamento})
                zona = result.scalar()
                logger.info(f"Zona geográfica para {departamento}: {zona}")
                return zona or 'Desconocida'
        except Exception as e:
            logger.error(f"Error obteniendo zona geográfica para {departamento}: {str(e)}")
            return 'Desconocida' 

    def get_tipos_actividades(self) -> list:
        """Obtiene los tipos de actividades disponibles"""
        try:
            with self.engine.connect() as conn:
                query = """
                    SELECT DISTINCT categoria_actividad 
                    FROM actividades 
                    WHERE categoria_actividad IS NOT NULL 
                    ORDER BY categoria_actividad
                """
                result = conn.execute(text(query))
                tipos = [row[0] for row in result if row[0]]
                return tipos if tipos else ["Simulacro", "Simulación", "Taller", "Capacitación"]
        except Exception as e:
            logger.error(f"Error obteniendo tipos de actividades: {str(e)}")
            return ["Simulacro", "Simulación", "Taller", "Capacitación"] 