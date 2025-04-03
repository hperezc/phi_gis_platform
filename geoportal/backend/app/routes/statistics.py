from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from ..database import get_db
from sqlalchemy import func, and_
from ..services import StatisticsService
from fastapi import HTTPException

router = APIRouter()

@router.get("/statistics/{level}/{geometry_id}")
async def get_statistics(
    level: str,
    geometry_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        db = get_db()
        stats_service = StatisticsService(db)
        
        # Convertir fechas si están presentes
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        statistics = await stats_service.get_activity_statistics(
            level=level,
            geometry_id=geometry_id,
            start_date=start,
            end_date=end
        )
        
        # Validar específicamente los datos de categorías
        if not statistics.get("categoria_actividad"):
            statistics["categoria_actividad"] = []
            
        # Asegurar que los datos estén en el formato correcto
        for cat in statistics["categoria_actividad"]:
            cat["total"] = int(cat.get("total", 0))
            cat["asistentes"] = int(cat.get("asistentes", 0))
            cat["categoria"] = str(cat.get("categoria", "Sin categoría"))
            
        return statistics
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

@router.get("/statistics")
async def get_statistics(
    geometry_id: Optional[str] = None,
    geometry_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categoria: Optional[str] = None
):
    db = get_db()
    
    # Construir la consulta base según el tipo de geometría
    if geometry_type == 'departamento':
        table = 'actividades_departamentos'
    elif geometry_type == 'municipio':
        table = 'actividades_municipios'
    else:
        table = 'actividades'

    # Construir las condiciones del filtro
    conditions = []
    if geometry_id:
        conditions.append(f"id = '{geometry_id}'")
    if start_date:
        conditions.append(f"fecha >= '{start_date}'")
    if end_date:
        conditions.append(f"fecha <= '{end_date}'")
    if categoria:
        conditions.append(f"categoria_actividad = '{categoria}'")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Estadísticas generales
    general_stats = db.execute(f"""
        SELECT 
            COUNT(*) as total_actividades,
            SUM(total_asistentes) as total_asistentes,
            COUNT(DISTINCT grupo_interes) as total_grupos
        FROM {table}
        WHERE {where_clause}
    """).fetchone()

    # Distribución por categoría
    categories = db.execute(f"""
        SELECT 
            categoria_actividad as name,
            COUNT(*) as value
        FROM {table}
        WHERE {where_clause}
        GROUP BY categoria_actividad
        ORDER BY value DESC
    """).fetchall()

    # Distribución temporal
    temporal = db.execute(f"""
        SELECT 
            DATE_TRUNC('month', fecha) as mes,
            COUNT(*) as actividades,
            SUM(total_asistentes) as asistentes
        FROM {table}
        WHERE {where_clause}
        GROUP BY mes
        ORDER BY mes
    """).fetchall()

    # Distribución por grupo de interés
    grupos = db.execute(f"""
        SELECT 
            grupo_interes as name,
            COUNT(*) as value
        FROM {table}
        WHERE {where_clause}
        GROUP BY grupo_interes
        ORDER BY value DESC
    """).fetchall()

    return {
        "total_actividades": general_stats[0],
        "total_asistentes": general_stats[1],
        "total_grupos": general_stats[2],
        "por_categoria": [dict(row) for row in categories],
        "por_mes": [dict(row) for row in temporal],
        "por_grupo": [dict(row) for row in grupos]
    } 