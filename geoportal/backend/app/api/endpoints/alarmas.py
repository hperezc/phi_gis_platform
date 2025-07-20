from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...models.sistema_alarmas import SistemaAlarmas
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/alarmas', tags=['alarmas'])

@router.get('/sistema_alarmas')
async def get_sistema_alarmas(limit: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        query = db.query(SistemaAlarmas)
        if limit:
            query = query.limit(limit)
        results = query.all()
        data = []
        for result in results:
            data.append({
                'ID_DEPARTA': result.ID_DEPARTA,
                'DEPARTAMEN': result.DEPARTAMEN,
                'MUNICIPIO': result.MUNICIPIO,
                'NOMBRE_SAT': result.NOMBRE_SAT,
                'ESTADO': result.ESTADO
            })
        return data
    except Exception as e:
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
