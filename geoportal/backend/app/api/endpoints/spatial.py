from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional
from datetime import datetime
from ...services.spatial_analysis import SpatialAnalysisService
from ...schemas.geometry_schemas import ActivityFilter, FeatureCollection
import logging
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.sql import text
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/geometries/{level}")
async def get_geometries(
    level: str = Path(..., description="Nivel de geometría: departamentos, municipios, veredas, etc"),
    departamento: Optional[str] = Query(None),
    municipio: Optional[str] = Query(None)
):
    """Obtiene las geometrías filtradas por nivel y filtros opcionales"""
    try:
        logger.info(f"Recibida petición para nivel: {level}")
        
        spatial_service = SpatialAnalysisService()
        filters = {
            "departamento": departamento,
            "municipio": municipio
        }
        
        geojson = await spatial_service.get_geometries(level, filters)
        
        # Añadir logs detallados para puntos de encuentro
        if level == 'puntos_encuentro':
            logger.info(f"Total de features: {len(geojson['features'])}")
            if geojson['features']:
                logger.info(f"Ejemplo de feature: {geojson['features'][0]}")
        
        return JSONResponse(content=jsonable_encoder(geojson))
        
    except Exception as e:
        logger.error(f"Error en get_geometries endpoint: {str(e)}")
        logger.exception(e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/statistics/{level}")
async def get_statistics(
    level: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    zona: Optional[str] = None,
):
    """
    Obtiene estadísticas agregadas por nivel
    """
    return {
        "total_actividades": 100,
        "total_asistentes": 1500,
        "por_categoria": [
            {"categoria": "Educación", "total": 30},
            {"categoria": "Salud", "total": 40},
            {"categoria": "Otros", "total": 30}
        ]
    }

@router.get("/test/puntos-encuentro")
async def test_puntos_encuentro():
    """Endpoint de prueba para verificar la estructura de datos de puntos de encuentro"""
    try:
        spatial_service = SpatialAnalysisService()
        geojson = await spatial_service.get_geometries('puntos_encuentro')
        
        if not geojson or not geojson.get("features"):
            return JSONResponse(
                content={"error": "No se encontraron datos"},
                status_code=404
            )
        
        # Tomar una muestra de los datos
        sample = {
            "total_features": len(geojson["features"]),
            "sample_feature": geojson["features"][0] if geojson["features"] else None,
            "properties_example": geojson["features"][0]["properties"] if geojson["features"] else None
        }
        
        logger.info(f"Muestra de datos generada: {sample}")
        return JSONResponse(content=jsonable_encoder(sample))
        
    except Exception as e:
        logger.error(f"Error en test_puntos_encuentro: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/test/punto/{id}")
async def test_punto(id: int):
    """Endpoint de prueba para verificar un punto específico"""
    try:
        spatial_service = SpatialAnalysisService()
        with spatial_service.engine.connect() as connection:
            query = text("""
                SELECT 
                    id, nombre_pe, codigo_pe, nombre_mun,
                    ruta_de_evacuacion, tiempo_de_llegada,
                    ST_AsGeoJSON(geometry)::json as geom
                FROM puntos_encuentro
                WHERE id = :id
            """)
            result = connection.execute(query, {"id": id}).first()
            
            if result:
                return JSONResponse(content=jsonable_encoder(dict(result)))
            return JSONResponse(
                content={"error": "Punto no encontrado"},
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error en test_punto: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/test/puntos-raw")
async def test_puntos_raw():
    """Endpoint para verificar los datos crudos de puntos de encuentro"""
    try:
        spatial_service = SpatialAnalysisService()
        with spatial_service.engine.connect() as connection:
            query = text("""
                SELECT 
                    id,
                    nombre_pe,
                    codigo_pe,
                    nombre_mun,
                    ruta_de_evacuacion,
                    tiempo_de_llegada,
                    ST_AsText(geometry) as geom_text
                FROM puntos_encuentro
                LIMIT 5;
            """)
            result = connection.execute(query)
            rows = result.fetchall()
            
            data = [dict(row._mapping) for row in rows]
            return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        logger.error(f"Error en test_puntos_raw: {str(e)}")
        logger.exception(e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/filter/{layer}")
async def filter_features(
    layer: str,
    field: str = Query(...),
    value: str = Query(...)
):
    """Filtra features por capa, campo y valor"""
    try:
        logger.info(f"Recibida petición de filtro: layer={layer}, field={field}, value={value}")
        spatial_service = SpatialAnalysisService()
        
        # Obtener el nombre real de la tabla
        table_name = spatial_service.table_mappings.get(layer)
        if not table_name:
            raise HTTPException(
                status_code=404,
                detail=f"Capa no encontrada: {layer}"
            )
        
        # Consulta simplificada
        query = f"""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    (
                        SELECT json_agg(
                            json_build_object(
                                'type', 'Feature',
                                'id', id,
                                'geometry', ST_AsGeoJSON(geometry)::json,
                                'properties', json_build_object(
                                    '{field}', {field},
                                    'id', id
                                )
                            )
                        )
                        FROM {table_name}
                        WHERE {field}::text ILIKE :value
                        AND geometry IS NOT NULL
                    ),
                    '[]'
                )
            )::text AS geojson
        """
        
        logger.info(f"Ejecutando consulta: {query}")
        logger.info(f"Con parámetros: value={value}")
        
        with spatial_service.engine.connect() as connection:
            try:
                result = connection.execute(
                    text(query),
                    {"value": f"%{value}%"}
                )
                row = result.fetchone()
                
                if not row or not row.geojson:
                    return JSONResponse(content={
                        "type": "FeatureCollection",
                        "features": []
                    })
                
                # Convertir el texto JSON a diccionario
                try:
                    geojson_dict = json.loads(row.geojson)
                    logger.info(f"Resultado filtrado: {len(geojson_dict.get('features', []))} elementos encontrados")
                    return JSONResponse(content=geojson_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando JSON: {e}")
                    logger.error(f"JSON recibido: {row.geojson}")
                    raise HTTPException(
                        status_code=500,
                        detail="Error procesando resultados"
                    )
                
            except Exception as e:
                logger.error(f"Error ejecutando consulta: {str(e)}")
                logger.error(f"Query: {query}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al ejecutar la consulta: {str(e)}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en filter_features: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error al filtrar: {str(e)}"
        )

@router.get("/fields/{table_name}")
async def get_table_fields(table_name: str):
    """Obtiene los campos disponibles de una tabla"""
    try:
        logger.info(f"Solicitando campos para tabla: {table_name}")
        spatial_service = SpatialAnalysisService()
        fields = await spatial_service.get_table_fields(table_name)
        return fields
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo campos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo campos: {str(e)}"
        )

@router.get("/values/{table_name}/{field_name}")
async def get_field_values(table_name: str, field_name: str):
    """Obtiene los valores únicos de un campo"""
    try:
        spatial_service = SpatialAnalysisService()
        values = await spatial_service.get_field_values(table_name, field_name)
        return values
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/filter/{layer}/{field}/{value}")
async def test_filter(layer: str, field: str, value: str):
    """Endpoint de prueba para verificar el filtrado"""
    try:
        spatial_service = SpatialAnalysisService()
        table_name = spatial_service.table_mappings.get(layer)
        
        # Consulta simple para verificar los datos
        query = f"""
            SELECT 
                id,
                {field},
                ST_AsText(geometry) as geom_wkt
            FROM {table_name}
            WHERE LOWER({field}::text) LIKE LOWER(:value)
            LIMIT 5;
        """
        
        with spatial_service.engine.connect() as connection:
            result = connection.execute(
                text(query),
                {"value": f"%{value}%"}
            )
            rows = result.fetchall()
            
            return JSONResponse(content={
                "count": len(rows),
                "sample": [dict(row._mapping) for row in rows]
            })
            
    except Exception as e:
        logger.error(f"Error en test_filter: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/test/filter-format/{layer}/{field}/{value}")
async def test_filter_format(layer: str, field: str, value: str):
    """Endpoint de prueba para verificar el formato del filtro"""
    try:
        spatial_service = SpatialAnalysisService()
        table_name = spatial_service.table_mappings.get(layer)
        
        # Consulta simple para verificar el formato
        query = f"""
            SELECT 
                jsonb_pretty(
                    jsonb_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(geometry)::jsonb,
                        'properties', to_jsonb(row_to_json(t)) - 'geometry'
                    )
                ) as feature
            FROM (
                SELECT *
                FROM {table_name}
                WHERE LOWER({field}::text) LIKE LOWER(:value)
                AND geometry IS NOT NULL
                LIMIT 1
            ) t;
        """
        
        with spatial_service.engine.connect() as connection:
            result = connection.execute(
                text(query),
                {"value": f"%{value}%"}
            )
            row = result.fetchone()
            
            return JSONResponse(content={
                "query": query,
                "sample": row.feature if row else None
            })
            
    except Exception as e:
        logger.error(f"Error en test_filter_format: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/test/filter-raw/{layer}/{field}/{value}")
async def test_filter_raw(layer: str, field: str, value: str):
    """Endpoint de prueba para verificar el filtrado raw"""
    try:
        spatial_service = SpatialAnalysisService()
        table_name = spatial_service.table_mappings.get(layer)
        
        # Consulta simple para verificar los datos
        query = f"""
            SELECT 
                id,
                {field}::text as field_value,
                ST_AsText(geometry) as geom_wkt
            FROM {table_name}
            WHERE {field}::text ILIKE :value
            AND geometry IS NOT NULL
            LIMIT 5;
        """
        
        with spatial_service.engine.connect() as connection:
            result = connection.execute(
                text(query),
                {"value": f"%{value}%"}
            )
            rows = result.fetchall()
            
            return JSONResponse(content={
                "query": query,
                "params": {"value": f"%{value}%"},
                "count": len(rows),
                "sample": [
                    {
                        "id": row.id,
                        "field_value": row.field_value,
                        "geom_wkt": row.geom_wkt
                    }
                    for row in rows
                ]
            })
            
    except Exception as e:
        logger.error(f"Error en test_filter_raw: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/test/filter-json/{layer}/{field}/{value}")
async def test_filter_json(layer: str, field: str, value: str):
    """Endpoint de prueba para verificar el formato JSON"""
    try:
        spatial_service = SpatialAnalysisService()
        table_name = spatial_service.table_mappings.get(layer)
        
        # Consulta de prueba
        query = f"""
            SELECT 
                id,
                {field}::text as field_value,
                ST_AsGeoJSON(geometry) as geom_json,
                json_build_object(
                    'type', 'Feature',
                    'id', id,
                    'geometry', ST_AsGeoJSON(geometry)::json,
                    'properties', json_build_object(
                        'id', id,
                        '{field}', {field}
                    )
                )::text as feature_json
            FROM {table_name}
            WHERE {field}::text ILIKE :value
            AND geometry IS NOT NULL
            LIMIT 1;
        """
        
        with spatial_service.engine.connect() as connection:
            result = connection.execute(
                text(query),
                {"value": f"%{value}%"}
            )
            row = result.fetchone()
            
            if row:
                return JSONResponse(content={
                    "raw_values": {
                        "id": row.id,
                        "field_value": row.field_value,
                        "geom_json": row.geom_json
                    },
                    "feature_json": row.feature_json,
                    "parsed_feature": json.loads(row.feature_json) if row.feature_json else None
                })
            return JSONResponse(content={"message": "No se encontraron resultados"})
            
    except Exception as e:
        logger.error(f"Error en test_filter_json: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 