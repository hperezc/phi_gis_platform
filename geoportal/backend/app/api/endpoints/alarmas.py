from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ...core.database import get_db
from ...models.sistema_alarmas import SistemaAlarmas
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/alarmas', tags=['alarmas'])

def parse_dms_to_decimal(dms_string):
    """Convierte coordenadas de grados, minutos, segundos a decimales"""
    if not dms_string or dms_string == "No aplica":
        return None
    
    # Patrón para grados, minutos, segundos
    pattern = r"(\d+)°\s*(\d+)'\s*(\d+\.?\d*)\"*\s*([NSWE])"
    match = re.match(pattern, dms_string)
    
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4)
        
        decimal = degrees + minutes/60 + seconds/3600
        
        if direction in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    
    return None

@router.get('/sistema_alarmas')
async def get_sistema_alarmas(limit: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        # Query para extraer coordenadas de la geometría
        # Primero verificar el SRID de la geometría
        query = db.query(
            SistemaAlarmas.ID_DEPARTA,
            SistemaAlarmas.DEPARTAMEN,
            SistemaAlarmas.MUNICIPIO,
            SistemaAlarmas.NOMBRE_SAT,
            SistemaAlarmas.ESTADO,
            SistemaAlarmas.ALCANCE,
            SistemaAlarmas.TIPO_ACTIV,
            SistemaAlarmas.RESPONSABL,
            SistemaAlarmas.LATITUD,
            SistemaAlarmas.LONGITUD,
            SistemaAlarmas.COOR_NORTE,
            SistemaAlarmas.COOR_ESTE,
            # Verificar el SRID de la geometría
            func.ST_SRID(SistemaAlarmas.geometry).label('srid'),
            # Extraer lat/lng de la geometría transformando a WGS84
            func.ST_Y(func.ST_Transform(SistemaAlarmas.geometry, 4326)).label('lat'),
            func.ST_X(func.ST_Transform(SistemaAlarmas.geometry, 4326)).label('lng')
        )
        
        if limit:
            query = query.limit(limit)
        
        results = query.all()
        data = []
        
        for result in results:
            # Convertir coordenadas originales de DMS a decimales
            original_lat = parse_dms_to_decimal(result.LATITUD)
            original_lng = parse_dms_to_decimal(result.LONGITUD)
            
            # Verificar que las coordenadas de la geometría estén en el rango correcto para Colombia
            lat = float(result.lat) if result.lat else None
            lng = float(result.lng) if result.lng else None
            
            # Si las coordenadas de la geometría son válidas, usarlas
            if lat and lng and 0 <= lat <= 15 and -85 <= lng <= -65:
                data.append({
                    'ID_DEPARTA': result.ID_DEPARTA,
                    'DEPARTAMEN': result.DEPARTAMEN,
                    'MUNICIPIO': result.MUNICIPIO,
                    'NOMBRE_SAT': result.NOMBRE_SAT,
                    'ESTADO': result.ESTADO,
                    'ALCANCE': result.ALCANCE,
                    'TIPO_ACTIV': result.TIPO_ACTIV,
                    'RESPONSABL': result.RESPONSABL,
                    'LATITUD': result.LATITUD,
                    'LONGITUD': result.LONGITUD,
                    'COOR_NORTE': result.COOR_NORTE,
                    'COOR_ESTE': result.COOR_ESTE,
                    'lat': lat,
                    'lng': lng,
                    'srid': result.srid
                })
            # Si las coordenadas originales son válidas, usarlas
            elif original_lat and original_lng and 0 <= original_lat <= 15 and -85 <= original_lng <= -65:
                data.append({
                    'ID_DEPARTA': result.ID_DEPARTA,
                    'DEPARTAMEN': result.DEPARTAMEN,
                    'MUNICIPIO': result.MUNICIPIO,
                    'NOMBRE_SAT': result.NOMBRE_SAT,
                    'ESTADO': result.ESTADO,
                    'ALCANCE': result.ALCANCE,
                    'TIPO_ACTIV': result.TIPO_ACTIV,
                    'RESPONSABL': result.RESPONSABL,
                    'LATITUD': result.LATITUD,
                    'LONGITUD': result.LONGITUD,
                    'COOR_NORTE': result.COOR_NORTE,
                    'COOR_ESTE': result.COOR_ESTE,
                    'lat': original_lat,
                    'lng': original_lng,
                    'srid': result.srid
                })
            else:
                logger.warning(f"No se encontraron coordenadas válidas para {result.NOMBRE_SAT}. SRID: {result.srid}, Lat: {lat}, Lng: {lng}, Original Lat: {original_lat}, Original Lng: {original_lng}")
        
        return data
    except Exception as e:
        logger.error(f"Error getting sistema alarmas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/sistema_alarmas/filters')
async def get_sistema_alarmas_filters(db: Session = Depends(get_db)):
    try:
        departamentos = db.query(SistemaAlarmas.DEPARTAMEN).distinct().all()
        municipios = db.query(SistemaAlarmas.MUNICIPIO).distinct().all()
        estados = db.query(SistemaAlarmas.ESTADO).distinct().all()
        tipos_activ = db.query(SistemaAlarmas.TIPO_ACTIV).distinct().all()
        return {
            'departamentos': [d[0] for d in departamentos if d[0]],
            'municipios': [m[0] for m in municipios if m[0]],
            'estados': [e[0] for e in estados if e[0]],
            'tipos_activacion': [t[0] for t in tipos_activ if t[0]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/sistema_alarmas/count')
async def get_sistema_alarmas_count(db: Session = Depends(get_db)):
    try:
        count = db.query(SistemaAlarmas).count()
        return {'total': count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
