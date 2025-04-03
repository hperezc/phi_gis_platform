from sqlalchemy import Column, Integer, String, Date, Float
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from ..core.database import Base

class Activity(Base):
    __tablename__ = "actividades"

    id = Column(Integer, primary_key=True, index=True)
    contrato = Column(String)
    ano = Column(Integer)
    mes = Column(String)
    fecha = Column(Date)
    zona_geografica = Column(String)
    departamento = Column(String)
    municipio = Column(String)
    grupo_interes = Column(String)
    ubicacion = Column(String)
    grupo_intervencion = Column(String)
    descripcion_actividad = Column(String)
    categoria_actividad = Column(String)
    categoria_unica = Column(String)
    total_asistentes = Column(Integer)
    pais = Column(String)
    tipo_geometria = Column(String)
    geometry = Column(Geometry('GEOMETRY')) 