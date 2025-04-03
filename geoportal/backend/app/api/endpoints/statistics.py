from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.statistics import StatisticsService
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/{level}/{geometry_id}")
async def get_statistics(
    level: str,
    geometry_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas para una geometría específica
    """
    try:
        logger.info(f"Recibida solicitud de estadísticas para {level}/{geometry_id}")
        
        # Validar nivel
        if level not in ['departamentos', 'municipios', 'veredas', 'cabeceras']:
            raise HTTPException(
                status_code=400,
                detail="Nivel no válido"
            )

        service = StatisticsService(db)
        result = await service.get_activity_statistics(
            level=level,
            geometry_id=geometry_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Estadísticas generadas exitosamente para {level}/{geometry_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_statistics():
    """
    Endpoint de prueba para verificar que el router está funcionando
    """
    return {"message": "Statistics endpoint is working"} 