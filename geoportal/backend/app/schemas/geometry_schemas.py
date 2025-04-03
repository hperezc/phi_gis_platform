from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class GeometryBase(BaseModel):
    type: str
    coordinates: List

class Feature(BaseModel):
    type: str = "Feature"
    geometry: GeometryBase
    properties: Dict

class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]

class ActivityFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    zona: Optional[str] = None
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    categoria: Optional[str] = None
    grupo_interes: Optional[str] = None 