from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.spatial_analysis import SpatialService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/geometries",
    tags=["geometries"]
)

@router.get("/{level}")
async def get_geometries(
    level: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene las geometrías para un nivel específico (departamentos o municipios)
    """
    try:
        if level not in ["departamentos", "municipios"]:
            raise HTTPException(
                status_code=400,
                detail="Nivel no válido. Use 'departamentos' o 'municipios'"
            )

        service = SpatialService(db)
        if level == "departamentos":
            return await service.get_department_geometries()
        else:
            return await service.get_municipal_geometries()

    except Exception as e:
        logger.error(f"Error obteniendo geometrías: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 