from sqlalchemy import Column, String, Integer, Float, DateTime
from geoalchemy2 import Geometry
from ..core.database import Base

class SistemaAlarmas(Base):
    __tablename__ = "sistema_alarmas"
    
    # Campos principales
    ID_DEPARTA = Column(String, primary_key=True)
    DEPARTAMEN = Column(String)
    ID_MUNICIP = Column(String)
    MUNICIPIO = Column(String)
    COD_SECTOR = Column(String)
    NOMBRE_SEC = Column(String)
    ID_SAT = Column(String)
    NOMBRE_SAT = Column(String)
    ALCANCE = Column(Float)
    CUBRIMIENT = Column(String)
    ORIENTACIO = Column(String)
    SENTIDO_CO = Column(String)
    TIPO_ACTIV = Column(String)
    RESPONSABL = Column(String)
    TIPO_SISTE = Column(String)
    TIPO_TECNO = Column(String)
    FUENTE_ENE = Column(String)
    ESTADO = Column(String)
    COOR_NORTE = Column(Float)
    COOR_ESTE = Column(Float)
    LATITUD = Column(String)
    LONGITUD = Column(String)
    affa = Column(Float)
    COOR_ESTE_ = Column(Float)
    FECHA_ACTU = Column(String)
    geometry = Column(Geometry('POINT', srid=3116))
