from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ...core.database import get_db
from ...models.sistema_alarmas import SistemaAlarmas
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/alarmas', tags=['alarmas'])

@router.get('/sistema_alarmas')
async def get_sistema_alarmas(limit: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        # Query para extraer coordenadas de la geometría
        # Primero detectar el SRID de la geometría y luego transformar a WGS84
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
            # Extraer lat/lng de la geometría con SRID correcto
            func.ST_Y(func.ST_Transform(SistemaAlarmas.geometry, 4326)).label('lat'),
            func.ST_X(func.ST_Transform(SistemaAlarmas.geometry, 4326)).label('lng')
        )
        
        if limit:
            query = query.limit(limit)
        
        results = query.all()
        data = []
        
        for result in results:
            # Verificar que las coordenadas estén en el rango correcto para Colombia
            lat = float(result.lat) if result.lat else None
            lng = float(result.lng) if result.lng else None
            
            # Validar que las coordenadas estén en el rango de Colombia
            if lat and lng and -5 <= lat <= 15 and -85 <= lng <= -65:
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
                    'lng': lng
                })
            else:
                # Si las coordenadas no son válidas, usar las coordenadas UTM convertidas
                if result.COOR_NORTE and result.COOR_ESTE:
                    # Convertir coordenadas UTM a WGS84 (aproximación)
                    # Esto es una conversión básica, puede necesitar ajustes
                    utm_lat = result.COOR_NORTE / 100000  # Aproximación
                    utm_lng = result.COOR_ESTE / 100000 - 75  # Aproximación para Colombia
                    
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
                        'lat': utm_lat,
                        'lng': utm_lng
                    })
        
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
