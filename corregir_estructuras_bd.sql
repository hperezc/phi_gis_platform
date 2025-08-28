-- Script para corregir estructuras de defaultdb_new para que sean idénticas a defaultdb
-- Ejecutar en defaultdb_new

-- 1. CORREGIR actividades_municipios (eliminar columna extra)
ALTER TABLE actividades_municipios DROP COLUMN IF EXISTS fecha_actualizacion;

-- 2. CORREGIR actividades_departamentos (eliminar columna extra)  
ALTER TABLE actividades_departamentos DROP COLUMN IF EXISTS fecha_actualizacion;

-- 3. CORREGIR rutas_evacuacion (falta id, nombres incorrectos, tipos incorrectos)
-- 3a. Agregar columna id como clave primaria
ALTER TABLE rutas_evacuacion ADD COLUMN id SERIAL PRIMARY KEY;

-- 3b. Renombrar columnas para que coincidan con defaultdb
ALTER TABLE rutas_evacuacion RENAME COLUMN longitud_r TO longitud_rut;
ALTER TABLE rutas_evacuacion RENAME COLUMN descrip_ru TO descrip_rut;
ALTER TABLE rutas_evacuacion RENAME COLUMN orden_geo_ TO orden_geo_re;
ALTER TABLE rutas_evacuacion RENAME COLUMN shape_leng TO shape_length;

-- 3c. Cambiar tipos de datos para que coincidan
ALTER TABLE rutas_evacuacion ALTER COLUMN id_presa TYPE integer USING id_presa::integer;
ALTER TABLE rutas_evacuacion ALTER COLUMN cod_ruta TYPE integer USING cod_ruta::integer;
ALTER TABLE rutas_evacuacion ALTER COLUMN codigo_pe TYPE integer USING codigo_pe::integer;
ALTER TABLE rutas_evacuacion ALTER COLUMN longitud_rut TYPE numeric USING longitud_rut::numeric;
ALTER TABLE rutas_evacuacion ALTER COLUMN tiempo_rut TYPE numeric USING tiempo_rut::numeric;
ALTER TABLE rutas_evacuacion ALTER COLUMN shape_length TYPE numeric USING shape_length::numeric;

-- 4. CORREGIR senales_evacuacion (falta id, nombres incorrectos, tipos incorrectos, columnas extras)
-- 4a. Agregar columna id como clave primaria
ALTER TABLE senales_evacuacion ADD COLUMN id SERIAL PRIMARY KEY;

-- 4b. Renombrar columnas para que coincidan con defaultdb
ALTER TABLE senales_evacuacion RENAME COLUMN tipo_seÑa TO tipo_señal;
ALTER TABLE senales_evacuacion RENAME COLUMN cod_seÑal TO cod_señal;
ALTER TABLE senales_evacuacion RENAME COLUMN id_municip TO id_municipio;
ALTER TABLE senales_evacuacion RENAME COLUMN jurisdicci TO jurisdiccion;
ALTER TABLE senales_evacuacion RENAME COLUMN coor_nor_1 TO coor_norte_ctm12;
ALTER TABLE senales_evacuacion RENAME COLUMN coor_este_ TO coor_este_ctm12;
ALTER TABLE senales_evacuacion RENAME COLUMN mantenimie TO mantenimiento;

-- 4c. Eliminar columnas extras que no existen en defaultdb
ALTER TABLE senales_evacuacion DROP COLUMN IF EXISTS coord_geog;
ALTER TABLE senales_evacuacion DROP COLUMN IF EXISTS coord_ge_1;

-- 4d. Cambiar tipos de datos para que coincidan
ALTER TABLE senales_evacuacion ALTER COLUMN coor_norte TYPE numeric USING coor_norte::numeric;
ALTER TABLE senales_evacuacion ALTER COLUMN coor_este TYPE numeric USING coor_este::numeric;
ALTER TABLE senales_evacuacion ALTER COLUMN id_presa TYPE integer USING id_presa::integer;
ALTER TABLE senales_evacuacion ALTER COLUMN id_vereda TYPE integer USING id_vereda::integer;
ALTER TABLE senales_evacuacion ALTER COLUMN cod_señal TYPE integer USING cod_señal::integer;
ALTER TABLE senales_evacuacion ALTER COLUMN cod_pe TYPE integer USING cod_pe::integer;
ALTER TABLE senales_evacuacion ALTER COLUMN coor_norte_ctm12 TYPE numeric USING coor_norte_ctm12::numeric;
ALTER TABLE senales_evacuacion ALTER COLUMN coor_este_ctm12 TYPE numeric USING coor_este_ctm12::numeric;

-- 5. CORREGIR sistema_alarmas (nombres en mayúsculas, tipo fecha_actu, eliminar coor_nor_)
-- 5a. Renombrar todas las columnas a MAYÚSCULAS para que coincidan con defaultdb
ALTER TABLE sistema_alarmas RENAME COLUMN id_departa TO "ID_DEPARTA";
ALTER TABLE sistema_alarmas RENAME COLUMN departamen TO "DEPARTAMEN";
ALTER TABLE sistema_alarmas RENAME COLUMN id_municip TO "ID_MUNICIP";
ALTER TABLE sistema_alarmas RENAME COLUMN municipio TO "MUNICIPIO";
ALTER TABLE sistema_alarmas RENAME COLUMN cod_sector TO "COD_SECTOR";
ALTER TABLE sistema_alarmas RENAME COLUMN nombre_sec TO "NOMBRE_SEC";
ALTER TABLE sistema_alarmas RENAME COLUMN id_sat TO "ID_SAT";
ALTER TABLE sistema_alarmas RENAME COLUMN nombre_sat TO "NOMBRE_SAT";
ALTER TABLE sistema_alarmas RENAME COLUMN alcance TO "ALCANCE";
ALTER TABLE sistema_alarmas RENAME COLUMN cubrimient TO "CUBRIMIENT";
ALTER TABLE sistema_alarmas RENAME COLUMN orientacio TO "ORIENTACIO";
ALTER TABLE sistema_alarmas RENAME COLUMN sentido_co TO "SENTIDO_CO";
ALTER TABLE sistema_alarmas RENAME COLUMN tipo_activ TO "TIPO_ACTIV";
ALTER TABLE sistema_alarmas RENAME COLUMN responsabl TO "RESPONSABL";
ALTER TABLE sistema_alarmas RENAME COLUMN tipo_siste TO "TIPO_SISTE";
ALTER TABLE sistema_alarmas RENAME COLUMN tipo_tecno TO "TIPO_TECNO";
ALTER TABLE sistema_alarmas RENAME COLUMN fuente_ene TO "FUENTE_ENE";
ALTER TABLE sistema_alarmas RENAME COLUMN estado TO "ESTADO";
ALTER TABLE sistema_alarmas RENAME COLUMN coor_norte TO "COOR_NORTE";
ALTER TABLE sistema_alarmas RENAME COLUMN coor_este TO "COOR_ESTE";
ALTER TABLE sistema_alarmas RENAME COLUMN latitud TO "LATITUD";
ALTER TABLE sistema_alarmas RENAME COLUMN longitud TO "LONGITUD";
ALTER TABLE sistema_alarmas RENAME COLUMN coor_este_ TO "COOR_ESTE_";
ALTER TABLE sistema_alarmas RENAME COLUMN fecha_actu TO "FECHA_ACTU";

-- 5b. Eliminar columna extra que no existe en defaultdb
ALTER TABLE sistema_alarmas DROP COLUMN IF EXISTS coor_nor_;

-- 5c. Cambiar tipo de FECHA_ACTU de timestamp a text
ALTER TABLE sistema_alarmas ALTER COLUMN "FECHA_ACTU" TYPE text USING "FECHA_ACTU"::text;

-- Verificar resultados
SELECT 'Corrección completada!' as mensaje;
