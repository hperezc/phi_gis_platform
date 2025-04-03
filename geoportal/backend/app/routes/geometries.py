from fastapi import APIRouter, HTTPException
from ..database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/geometries/{level}")
async def get_geometries(level: str):
    db = get_db()
    try:
        # Seleccionar la tabla según el nivel
        if level == "departamentos":
            table = "actividades_departamentos"
            group_by = "departamento"
        elif level == "municipios":
            table = "actividades_municipios"
            group_by = "municipio"
        else:
            table = "actividades"
            group_by = "ubicacion"

        # Consulta SQL para obtener las geometrías únicas
        query = text(f"""
            SELECT DISTINCT ON ({group_by})
                id,
                departamento,
                municipio,
                ubicacion,
                zona_geografica,
                ST_AsGeoJSON(geometry)::json as geometry
            FROM {table}
            WHERE geometry IS NOT NULL
            ORDER BY {group_by}, fecha DESC
        """)

        result = db.execute(query)
        features = []
        
        for row in result:
            feature = {
                "type": "Feature",
                "geometry": row.geometry,
                "properties": {
                    "id": row.id,
                    "departamento": row.departamento,
                    "municipio": row.municipio,
                    "ubicacion": row.ubicacion,
                    "zona_geografica": row.zona_geografica
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        print(f"Error obteniendo geometrías: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 