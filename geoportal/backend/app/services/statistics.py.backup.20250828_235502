from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from ..models.models import Activity
from typing import Dict, Optional
from datetime import date
import logging
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

class StatisticsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_activity_statistics(
        self,
        level: str,
        geometry_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Obtiene estadísticas de actividades para una geometría específica
        """
        try:
            print(f"Generando estadísticas para {level}/{geometry_id}")
            
            if level == 'veredas':
                # Consulta base para veredas
                base_query = """
                    SELECT 
                        COUNT(*) as total_actividades,
                        SUM(total_asistentes) as total_asistentes
                    FROM actividades
                    WHERE grupo_interes = :geometry_id
                    AND tipo_geometria = 'vereda'
                """

                # Análisis por municipio
                grupos_query = """
                    SELECT 
                        municipio as nombre,
                        COUNT(*) as total,
                        SUM(COALESCE(total_asistentes, 0)) as asistentes
                    FROM actividades
                    WHERE grupo_interes = :geometry_id
                    AND tipo_geometria = 'vereda'
                    GROUP BY municipio
                    ORDER BY total DESC
                """

                # Análisis temporal
                temporal_query = """
                    SELECT 
                        DATE_TRUNC('year', fecha) as mes,
                        COUNT(*) as total,
                        SUM(total_asistentes) as asistentes
                    FROM actividades
                    WHERE grupo_interes = :geometry_id
                    AND tipo_geometria = 'vereda'
                    GROUP BY DATE_TRUNC('year', fecha)
                    ORDER BY mes
                """

                # Análisis por categoría
                categoria_query = """
                    SELECT 
                        categoria_actividad as categoria,
                        COUNT(*) as total,
                        SUM(COALESCE(total_asistentes, 0)) as asistentes,
                        ROUND(COUNT(*)::numeric / NULLIF((
                            SELECT COUNT(*) 
                            FROM actividades 
                            WHERE grupo_interes = :geometry_id 
                            AND tipo_geometria = 'vereda'
                        ), 0) * 100, 2) as porcentaje
                    FROM actividades
                    WHERE grupo_interes = :geometry_id
                    AND tipo_geometria = 'vereda'
                    GROUP BY categoria_actividad
                    HAVING categoria_actividad IS NOT NULL
                    ORDER BY total DESC
                """

            else:
                # Seleccionar la tabla y campo según el nivel
                if level == 'departamentos':
                    table = 'actividades_departamentos'
                    id_field = 'departamento'
                elif level == 'municipios':
                    table = 'actividades_municipios'
                    id_field = 'municipio'
                else:
                    raise ValueError(f"Nivel no soportado: {level}")

                # Estadísticas generales
                base_query = f"""
                    SELECT 
                        COUNT(*) as total_actividades,
                        SUM(total_asistentes) as total_asistentes,
                        array_agg(DISTINCT categoria_actividad) as categorias,
                        array_agg(DISTINCT grupo_interes) as grupos_interes,
                        array_agg(DISTINCT grupo_intervencion) as grupos_intervencion
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {f"AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                """

                # Análisis temporal por mes
                temporal_query = f"""
                    SELECT 
                        DATE_TRUNC('year', fecha) as mes,
                        COUNT(*) as total,
                        SUM(total_asistentes) as asistentes
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {f"AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    GROUP BY DATE_TRUNC('year', fecha)
                    ORDER BY mes
                """

                # Análisis por grupo de interés
                grupos_query = f"""
                    SELECT 
                        COALESCE(grupo_interes, 'Sin especificar') as grupo_interes,
                        COUNT(*) as total,
                        SUM(COALESCE(total_asistentes, 0)) as asistentes
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {f"AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    GROUP BY grupo_interes
                    ORDER BY total DESC
                """

                # Análisis por grupo de intervención
                intervencion_query = f"""
                    SELECT 
                        grupo_intervencion,
                        COUNT(*) as total,
                        SUM(total_asistentes) as asistentes
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {f"AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    GROUP BY grupo_intervencion
                    ORDER BY total DESC
                """

                # Análisis por zona geográfica
                zona_query = f"""
                    SELECT 
                        zona_geografica,
                        COUNT(*) as total,
                        SUM(total_asistentes) as asistentes
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {f"AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    GROUP BY zona_geografica
                    ORDER BY total DESC
                """

                # Consulta base para categorías
                categoria_query = f"""
                    WITH total_stats AS (
                        SELECT COUNT(*) as total_count, 
                               SUM(total_asistentes) as total_asistentes
                        FROM {table}
                        WHERE {id_field} = :geometry_id
                        {" AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    )
                    SELECT 
                        categoria_actividad as categoria,
                        COUNT(*) as total,
                        COALESCE(SUM(total_asistentes), 0) as asistentes,
                        ROUND(COUNT(*)::numeric / NULLIF((SELECT total_count FROM total_stats), 0) * 100, 2) as porcentaje
                    FROM {table}
                    WHERE {id_field} = :geometry_id
                    {" AND fecha BETWEEN :start_date AND :end_date" if start_date and end_date else ""}
                    GROUP BY categoria_actividad
                    HAVING categoria_actividad IS NOT NULL
                    ORDER BY total DESC;
                """
            
            # Ejecutar consultas
            params = {
                "geometry_id": geometry_id,
                "start_date": start_date,
                "end_date": end_date
            }

            result = self.db.execute(text(base_query), params).first()
            temporal = self.db.execute(text(temporal_query), params).fetchall()
            grupos = self.db.execute(text(grupos_query), params).fetchall()
            categorias = self.db.execute(text(categoria_query), params).fetchall()

            # Construir respuesta
            response = {
                "total_actividades": result.total_actividades or 0,
                "total_asistentes": result.total_asistentes or 0,
                "temporal": [
                    {
                        "mes": mes.strftime("%Y-%m"),
                        "total": int(total or 0),
                        "asistentes": int(asistentes or 0)
                    } for mes, total, asistentes in temporal
                ],
                "grupos_interes": [
                    {
                        "nombre": str(nombre),
                        "total": int(total or 0),
                        "asistentes": int(asistentes or 0)
                    } for nombre, total, asistentes in grupos if nombre
                ],
                "categoria_actividad": [
                    {
                        "categoria": str(cat) if cat else "Sin categoría",
                        "total": int(total),
                        "asistentes": int(asistentes),
                        "porcentaje": float(porcentaje) if porcentaje else 0
                    } for cat, total, asistentes, porcentaje in categorias
                ]
            }

            # Validaciones de datos vacíos
            if not response["grupos_interes"]:
                response["grupos_interes"] = []
            
            if not response["categoria_actividad"]:
                response["categoria_actividad"] = [{
                    "categoria": "Sin datos",
                    "total": 0,
                    "asistentes": 0,
                    "porcentaje": 0
                }]

            return response

        except Exception as e:
            logger.error(f"Error en get_activity_statistics: {str(e)}")
            logger.exception(e)  # Esto imprimirá el stack trace completo
            raise Exception(f"Error al generar estadísticas: {str(e)}") 