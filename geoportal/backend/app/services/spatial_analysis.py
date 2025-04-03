import geopandas as gpd
from sqlalchemy import text
from ..models.models import Activity, MunicipalActivity, DepartmentalActivity
from ..core.database import engine  # Importar el engine directamente
import logging
import json
from shapely import wkb
import pandas as pd
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpatialAnalysisService:
    def __init__(self):
        self.engine = engine  # Usar el engine global
        self.table_mappings = {
            'departamentos': 'actividades_departamentos',
            'municipios': 'actividades_municipios',
            'veredas': 'actividades',
            'puntos_encuentro': 'puntos_encuentro',
            'senales_evacuacion': 'senales_evacuacion',
            'rutas_evacuacion': 'rutas_evacuacion',
            'drenaje_doble': 'drenaje_doble',
            'drenaje_sencillo': 'drenaje_sencillo',
            'mancha_inundacion': 'mancha_inundacion',
            'embalse': 'embalse',
            'obra_principal': 'obra_principal',
            'rios_principales': 'rios_principales',
            'vias': 'vias'
        }

    async def get_geometries(self, level='departamentos', filters=None):
        """Obtiene las geometrías según el nivel especificado"""
        try:
            logger.info(f"Obteniendo geometrías para nivel: {level}")
            
            # Separar la lógica para capas administrativas y operativas
            admin_layers = ['departamentos', 'municipios', 'veredas']
            operational_layers = {
                'senales_evacuacion': 'senales_evacuacion',
                'puntos_encuentro': 'puntos_encuentro',
                'rutas_evacuacion': 'rutas_evacuacion',
                'drenaje_doble': 'drenaje_doble',
                'drenaje_sencillo': 'drenaje_sencillo',
                'mancha_inundacion': 'mancha_inundacion',
                'embalse': 'embalse',
                'obra_principal': 'obra_principal',
                'rios_principales': 'rios_principales',
                'vias': 'vias'
            }

            if level in admin_layers:
                # Mantener la lógica existente para capas administrativas
                if level == 'departamentos':
                    query = """
                        SELECT 
                            departamento as nombre,
                            ST_AsGeoJSON(ST_SimplifyPreserveTopology(geometry, 0.001))::json as geom
                        FROM actividades_departamentos
                        GROUP BY departamento, geometry;
                    """
                elif level == 'municipios':
                    query = """
                        SELECT 
                            municipio as nombre,
                            departamento,
                            ST_AsGeoJSON(ST_SimplifyPreserveTopology(geometry, 0.001))::json as geom
                        FROM actividades_municipios
                        GROUP BY municipio, departamento, geometry;
                    """
                else:  # veredas
                    query = """
                        SELECT DISTINCT ON (grupo_interes, municipio)
                            grupo_interes as nombre,
                            municipio,
                            departamento,
                            ST_AsGeoJSON(ST_Union(geometry))::json as geom
                        FROM actividades
                        WHERE tipo_geometria = 'vereda'
                        GROUP BY grupo_interes, municipio, departamento;
                    """
            
            elif level in operational_layers:
                if level == 'puntos_encuentro':
                    query = """
                        SELECT 
                            json_build_object(
                                'type', 'FeatureCollection',
                                'features', json_agg(
                                    json_build_object(
                                        'type', 'Feature',
                                        'geometry', ST_AsGeoJSON(geometry)::json,
                                        'properties', json_build_object(
                                            'id', id,
                                            'nombre_pe', nombre_pe,
                                            'codigo_pe', codigo_pe,
                                            'nombre_mun', nombre_mun,
                                            'ruta_de_evacuacion', ruta_de_evacuacion,
                                            'tiempo_de_llegada', tiempo_de_llegada,
                                            'recorrido_maximo', recorrido_maximo
                                        )
                                    )
                                )
                            ) as geojson
                        FROM puntos_encuentro
                        WHERE geometry IS NOT NULL;
                    """
                    
                    with self.engine.connect() as connection:
                        try:
                            result = connection.execute(text(query))
                            row = result.fetchone()
                            
                            if row and row.geojson:
                                logger.info(f"Datos obtenidos para puntos_encuentro: {row.geojson}")
                                return row.geojson
                            
                            logger.warning("No se encontraron puntos de encuentro")
                            return {
                                "type": "FeatureCollection",
                                "features": []
                            }
                        except Exception as e:
                            logger.error(f"Error procesando puntos de encuentro: {str(e)}")
                            raise e
                elif level == 'senales_evacuacion':
                    query = """
                        SELECT 
                            json_build_object(
                                'type', 'FeatureCollection',
                                'features', json_agg(
                                    json_build_object(
                                        'type', 'Feature',
                                        'geometry', ST_AsGeoJSON(geometry)::json,
                                        'properties', json_build_object(
                                            'id', id,
                                            'tipo_senal', COALESCE(tipo_señal::text, ''),
                                            'cod_senal', COALESCE(cod_señal::text, ''),
                                            'nombre_mun', COALESCE(nombre_mun::text, ''),
                                            'nombre_sec', COALESCE(nombre_sec::text, ''),
                                            'estado', COALESCE(estado::text, ''),
                                            'cod_pe', COALESCE(cod_pe::text, ''),
                                            'cod_sector', COALESCE(cod_sector::text, ''),
                                            'jurisdiccion', COALESCE(jurisdiccion::text, '')
                                        )
                                    )
                                )
                            ) as geojson
                        FROM senales_evacuacion
                        WHERE geometry IS NOT NULL;
                    """
                    
                    with self.engine.connect() as connection:
                        try:
                            result = connection.execute(text(query))
                            row = result.fetchone()
                            
                            if row and row.geojson:
                                logger.info(f"Datos obtenidos para senales_evacuacion: {row.geojson}")
                                return row.geojson
                            
                            logger.warning("No se encontraron señales de evacuación")
                            return {
                                "type": "FeatureCollection",
                                "features": []
                            }
                        except Exception as e:
                            logger.error(f"Error procesando señales de evacuación: {str(e)}")
                            raise e
                elif level == 'rutas_evacuacion':
                    query = """
                        SELECT 
                            json_build_object(
                                'type', 'FeatureCollection',
                                'features', json_agg(
                                    json_build_object(
                                        'type', 'Feature',
                                        'geometry', ST_AsGeoJSON(geometry)::json,
                                        'properties', json_build_object(
                                            'id', id,
                                            'estado_rut', COALESCE(estado_rut::text, ''),
                                            'nombre_rut', COALESCE(nombre_rut::text, ''),
                                            'nombre_mun', COALESCE(nombre_mun::text, ''),
                                            'nombre_sec', COALESCE(nombre_sec::text, ''),
                                            'cod_ruta', COALESCE(cod_ruta::text, ''),
                                            'longitud_rut', COALESCE(longitud_rut::text, ''),
                                            'tiempo_rut', COALESCE(tiempo_rut::text, ''),
                                            'codigo_pe', COALESCE(codigo_pe::text, ''),
                                            'descrip_rut', COALESCE(descrip_rut::text, ''),
                                            'orden_geo_re', COALESCE(orden_geo_re::text, ''),
                                            'cod_sector', COALESCE(cod_sector::text, '')
                                        )
                                    )
                                )
                            ) as geojson
                        FROM rutas_evacuacion
                        WHERE geometry IS NOT NULL;
                    """
                    
                    with self.engine.connect() as connection:
                        try:
                            result = connection.execute(text(query))
                            row = result.fetchone()
                            
                            if row and row.geojson:
                                logger.info(f"Datos obtenidos para rutas_evacuacion: {row.geojson}")
                                return row.geojson
                            
                            logger.warning("No se encontraron rutas de evacuación")
                            return {
                                "type": "FeatureCollection",
                                "features": []
                            }
                        except Exception as e:
                            logger.error(f"Error procesando rutas de evacuación: {str(e)}")
                            raise e
                elif level == 'rios_principales':
                    query = """
                        SELECT json_build_object(
                            'type', 'FeatureCollection',
                            'features', COALESCE(
                                json_agg(
                                    json_build_object(
                                        'type', 'Feature',
                                        'geometry', ST_AsGeoJSON(geometry)::json,
                                        'properties', json_build_object(
                                            'id', id,
                                            'nombre_geografico', COALESCE(nombre_geografico, '')
                                        )
                                    )
                                ),
                                '[]'
                            )
                        ) as geojson
                        FROM rios_principales
                        WHERE geometry IS NOT NULL;
                    """
                    
                    with self.engine.connect() as connection:
                        try:
                            result = connection.execute(text(query))
                            row = result.fetchone()
                            
                            if row and row.geojson:
                                logger.info(f"Datos obtenidos para rios_principales")
                                return row.geojson
                            
                            logger.warning("No se encontraron ríos principales")
                            return {
                                "type": "FeatureCollection",
                                "features": []
                            }
                        except Exception as e:
                            logger.error(f"Error procesando rios_principales: {str(e)}")
                            logger.error(f"Query: {query}")
                            raise e
                elif level == 'vias':
                    query = """
                        SELECT json_build_object(
                            'type', 'FeatureCollection',
                            'features', COALESCE(
                                json_agg(
                                    json_build_object(
                                        'type', 'Feature',
                                        'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(geometry, 0.00001))::json,
                                        'properties', json_build_object(
                                            'id', id,
                                            'tipo_via', COALESCE(tipo_via, '')
                                        )
                                    )
                                ),
                                '[]'
                            )
                        ) as geojson
                        FROM vias
                        WHERE geometry IS NOT NULL;
                    """
                    
                    with self.engine.connect() as connection:
                        try:
                            result = connection.execute(text(query))
                            row = result.fetchone()
                            
                            if row and row.geojson:
                                logger.info(f"Datos obtenidos para vias")
                                return row.geojson
                            
                            logger.warning("No se encontraron vías")
                            return {
                                "type": "FeatureCollection",
                                "features": []
                            }
                        except Exception as e:
                            logger.error(f"Error procesando vias: {str(e)}")
                            logger.error(f"Query: {query}")
                            raise e
                else:
                    # Mantener consulta original para otras capas operativas
                    query = f"""
                        SELECT 
                            ST_AsGeoJSON(geometry)::json as geom
                        FROM {operational_layers[level]}
                        WHERE geometry IS NOT NULL;
                    """
            else:
                raise ValueError(f"Nivel no soportado: {level}")

            logger.info(f"Ejecutando consulta para {level}")
            
            with self.engine.connect() as connection:
                try:
                    result = connection.execute(text(query))
                    rows = result.fetchall()
                    
                    features = []
                    for row in rows:
                        if level in admin_layers:
                            # Propiedades para capas administrativas
                            properties = {
                                "nombre": row.nombre,
                                **({"departamento": row.departamento} if hasattr(row, 'departamento') else {}),
                                **({"municipio": row.municipio} if hasattr(row, 'municipio') else {})
                            }
                        else:
                            # Para capas operativas, solo incluir un id genérico
                            properties = {"id": len(features) + 1}
                        
                        feature = {
                            "type": "Feature",
                            "properties": properties,
                            "geometry": row.geom
                        }
                        features.append(feature)

                    geojson = {
                        "type": "FeatureCollection",
                        "features": features
                    }
                    
                    logger.info(f"GeoJSON generado con {len(features)} features para {level}")
                    logger.debug(f"Ejemplo de feature: {features[0] if features else 'No features'}")
                    
                    return geojson

                except Exception as e:
                    logger.error(f"Error ejecutando consulta para {level}: {str(e)}")
                    return {
                        "type": "FeatureCollection",
                        "features": []
                    }

        except Exception as e:
            logger.error(f"Error en get_geometries para {level}: {str(e)}")
            return {
                "type": "FeatureCollection",
                "features": []
            }

    async def get_geometries_with_filters(self, level: str, filters: dict):
        """Obtiene las geometrías según el nivel y filtros especificados"""
        try:
            if level == 'departamentos':
                query = """
                SELECT d.departamento, d.geometry, COUNT(*) as total_actividades
                FROM actividades_departamentos d
                JOIN actividades a ON d.departamento = a.departamento
                WHERE 1=1
                """
            elif level == 'municipios':
                query = """
                SELECT m.municipio, m.departamento, m.geometry, COUNT(*) as total_actividades
                FROM actividades_municipios m
                JOIN actividades a ON m.municipio = a.municipio
                WHERE 1=1
                """
            else:  # veredas o cabeceras
                query = """
                SELECT ubicacion, tipo_geometria, geometry, COUNT(*) as total_actividades
                FROM actividades
                WHERE tipo_geometria = :nivel
                """

            # Aplicar filtros
            params = {'nivel': level}
            if filters.get('start_date'):
                query += " AND fecha >= :start_date"
                params['start_date'] = filters['start_date']
            if filters.get('end_date'):
                query += " AND fecha <= :end_date"
                params['end_date'] = filters['end_date']
            
            # Agrupar por geometría
            if level == 'departamentos':
                query += " GROUP BY d.departamento, d.geometry"
            elif level == 'municipios':
                query += " GROUP BY m.municipio, m.departamento, m.geometry"
            else:
                query += " GROUP BY ubicacion, tipo_geometria, geometry"

            # Leer datos con GeoPandas
            gdf = gpd.read_postgis(query, self.engine, geom_col='geometry', params=params)
            return gdf

        except Exception as e:
            print(f"Error en get_geometries: {str(e)}")
            return gpd.GeoDataFrame()

    async def get_table_fields(self, layer_name: str):
        """Obtiene los campos disponibles de una tabla"""
        try:
            # Obtener el nombre real de la tabla
            table_name = self.table_mappings.get(layer_name)
            if not table_name:
                logger.error(f"Capa no encontrada: {layer_name}")
                raise ValueError(f"Capa no encontrada: {layer_name}")

            # Validar que la tabla existe
            check_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                );
            """
            
            with self.engine.connect() as connection:
                result = connection.execute(
                    text(check_query), 
                    {"table_name": table_name}
                ).scalar()
                
                if not result:
                    logger.error(f"Tabla no encontrada: {table_name}")
                    raise ValueError(f"Tabla no encontrada: {table_name}")

                # Obtener campos - consulta simplificada
                query = """
                    SELECT 
                        column_name,
                        data_type
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                    AND column_name NOT IN ('id', 'geometry')
                    ORDER BY ordinal_position;
                """
                
                result = connection.execute(text(query), {"table_name": table_name})
                
                # Mapeo de nombres amigables para los campos
                field_labels = {
                    'departamento': 'Departamento',
                    'municipio': 'Municipio',
                    'cod_depto': 'Código DANE Departamento',
                    'cod_mpio': 'Código DANE Municipio',
                    'nombre': 'Nombre',
                    'grupo_interes': 'Grupo de Interés',
                    'nombre_pe': 'Nombre Punto',
                    'codigo_pe': 'Código',
                    'nombre_mun': 'Municipio',
                    'tipo_señal': 'Tipo de Señal',
                    'cod_señal': 'Código Señal',
                    'estado': 'Estado',
                    'nombre_rut': 'Nombre Ruta',
                    'estado_rut': 'Estado',
                    'tiempo_rut': 'Tiempo',
                    'longitud_rut': 'Longitud'
                }

                fields = [
                    {
                        "id": row.column_name,
                        "label": field_labels.get(row.column_name, row.column_name.replace('_', ' ').title()),
                        "type": row.data_type
                    }
                    for row in result
                ]
                
                logger.info(f"Campos obtenidos para {table_name}: {fields}")
                return fields
                
        except Exception as e:
            logger.error(f"Error obteniendo campos de {layer_name}: {str(e)}")
            raise e

    async def get_field_values(self, layer_name: str, field_name: str):
        """Obtiene los valores únicos de un campo"""
        try:
            # Obtener el nombre real de la tabla
            table_name = self.table_mappings.get(layer_name)
            if not table_name:
                raise ValueError(f"Capa no encontrada: {layer_name}")

            query = f"""
                SELECT DISTINCT {field_name}
                FROM {table_name}
                WHERE {field_name} IS NOT NULL
                ORDER BY {field_name};
            """
            
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                values = [row[0] for row in result]
                return values
        except Exception as e:
            logger.error(f"Error obteniendo valores de {field_name}: {str(e)}")
            raise e

    async def execute_filter_query(self, query_template: str, field: str, value: str):
        """Ejecuta una consulta de filtro y devuelve los resultados"""
        try:
            # Formatear la consulta reemplazando el campo
            query = query_template.format(field=field)
            
            with self.engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {"value": value}
                )
                row = result.fetchone()
                
                if row and row.geojson:
                    return row.geojson
                
                # Si no hay resultados, devolver una colección vacía
                return {
                    "type": "FeatureCollection",
                    "features": []
                }
                
        except Exception as e:
            logger.error(f"Error ejecutando consulta de filtro: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parámetros: field={field}, value={value}")
            raise e

class SpatialService:
    def __init__(self, db: Session):
        self.db = db

    async def get_department_geometries(self):
        try:
            departments = self.db.query(DepartmentalActivity).all()
            
            features = []
            for dept in departments:
                geom = to_shape(dept.geometry)
                feature = {
                    "type": "Feature",
                    "geometry": mapping(geom),
                    "properties": {
                        "id": dept.id,
                        "nombre": dept.departamento
                    }
                }
                features.append(feature)

            return {
                "type": "FeatureCollection",
                "features": features
            }
        except Exception as e:
            logger.error(f"Error al obtener geometrías departamentales: {str(e)}")
            raise Exception(f"Error al obtener geometrías departamentales: {str(e)}")

    async def get_municipal_geometries(self):
        try:
            municipalities = self.db.query(MunicipalActivity).all()
            
            features = []
            for mun in municipalities:
                geom = to_shape(mun.geometry)
                feature = {
                    "type": "Feature",
                    "geometry": mapping(geom),
                    "properties": {
                        "id": mun.id,
                        "nombre": mun.municipio,
                        "departamento": mun.departamento
                    }
                }
                features.append(feature)

            return {
                "type": "FeatureCollection",
                "features": features
            }
        except Exception as e:
            logger.error(f"Error al obtener geometrías municipales: {str(e)}")
            raise Exception(f"Error al obtener geometrías municipales: {str(e)}") 