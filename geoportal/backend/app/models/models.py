from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class Activity(Base):
    __tablename__ = 'actividades'

    id = Column(Integer, primary_key=True)
    contrato = Column(String)
    ano = Column(Integer)
    mes = Column(Integer)
    fecha = Column(DateTime)
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
    geometry = Column(Geometry('GEOMETRY', srid=4326))

    class Config:
        orm_mode = True

class MunicipalActivity(Base):
    __tablename__ = 'actividades_municipios'

    id = Column(Integer, primary_key=True)
    municipio = Column(String)
    departamento = Column(String)
    geometry = Column(Geometry('GEOMETRY', srid=4326))
    total_actividades = Column(Integer)

class DepartmentalActivity(Base):
    __tablename__ = 'actividades_departamentos'

    id = Column(Integer, primary_key=True)
    departamento = Column(String)
    geometry = Column(Geometry('GEOMETRY', srid=4326))
    total_actividades = Column(Integer)

class PuntoEncuentro(Base):
    __tablename__ = 'puntos_encuentro'

    id = Column(Integer, primary_key=True)
    orde_geo_p = Column(String)
    nombre_mun = Column(String)
    cod_sector = Column(String)
    codigo_pe = Column(String)
    nombre_pe = Column(String)
    ruta_de_evacuacion = Column(String)
    tiempo_de_llegada = Column(String)
    recorrido_maximo = Column(String)
    cod_lider = Column(String)
    id_presa = Column(String)
    coor_norte = Column(Float)
    coor_este = Column(Float)
    latitud = Column(Float)
    longitud = Column(Float)
    coor_norte_ctm12 = Column(Float)
    coor_este_ctm12 = Column(Float)
    field = Column(String)
    geometry = Column(Geometry('POINT', srid=4326))

    def to_dict(self):
        return {
            'id': self.id,
            'orde_geo_p': self.orde_geo_p,
            'nombre_mun': self.nombre_mun,
            'cod_sector': self.cod_sector,
            'codigo_pe': self.codigo_pe,
            'nombre_pe': self.nombre_pe,
            'ruta_de_evacuacion': self.ruta_de_evacuacion,
            'tiempo_de_llegada': self.tiempo_de_llegada,
            'recorrido_maximo': self.recorrido_maximo,
            'cod_lider': self.cod_lider,
            'id_presa': self.id_presa,
            'coor_norte': self.coor_norte,
            'coor_este': self.coor_este,
            'latitud': self.latitud,
            'longitud': self.longitud
        }

    class Config:
        orm_mode = True

class SenalEvacuacion(Base):
    __tablename__ = 'senales_evacuacion'

    id = Column(Integer, primary_key=True)
    tipo_señal = Column(String)
    cod_señal = Column(String)
    nombre_mun = Column(String)
    nombre_sec = Column(String)
    estado = Column(String)
    mantenimiento = Column(String)
    cod_sector = Column(String)
    jurisdiccion = Column(String)
    geometry = Column(Geometry('POINT', srid=4326))

class RutaEvacuacion(Base):
    __tablename__ = 'rutas_evacuacion'

    id = Column(Integer, primary_key=True)
    estado_rut = Column(String)
    nombre_rut = Column(String)
    id_presa = Column(String)
    nombre_mun = Column(String)
    nombre_sec = Column(String)
    cod_ruta = Column(String)
    longitud_rut = Column(Float)
    tiempo_rut = Column(String)
    codigo_pe = Column(String)
    descrip_rut = Column(String)
    orden_geo_re = Column(String)
    cod_sector = Column(String)
    shape_length = Column(Float)
    geometry = Column(Geometry('LINESTRING', srid=4326))

class RiosPrincipales(Base):
    __tablename__ = 'rios_principales'

    id = Column(Integer, primary_key=True)
    nombre_geografico = Column(String)
    geometry = Column(Geometry('MULTILINESTRING', srid=4326))

class Vias(Base):
    __tablename__ = 'vias'

    id = Column(Integer, primary_key=True)
    tipo_via = Column(String)
    geometry = Column(Geometry('MULTILINESTRING', srid=4326)) 