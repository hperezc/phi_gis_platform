from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class SistemaAlarmasResponse(BaseModel):
    ID_DEPARTA: str
    DEPARTAMEN: str
    ID_MUNICIP: str
    MUNICIPIO: str
    COD_SECTOR: str
    NOMBRE_SEC: str
    ID_SAT: str
    NOMBRE_SAT: str
    ALCANCE: Optional[float]
    CUBRIMIENT: str
    ORIENTACIO: str
    SENTIDO_CO: str
    TIPO_ACTIV: str
    RESPONSABL: str
    TIPO_SISTE: str
    TIPO_TECNO: str
    FUENTE_ENE: str
    ESTADO: str
    COOR_NORTE: Optional[float]
    COOR_ESTE: Optional[float]
    LATITUD: str
    LONGITUD: str
    affa: Optional[float]
    COOR_ESTE_: Optional[float]
    FECHA_ACTU: str
    geometry: Optional[Any]

    class Config:
        from_attributes = True
