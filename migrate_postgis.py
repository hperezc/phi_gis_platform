#!/usr/bin/env python3
"""
Script de migración especializado para PostGIS
PHI GIS Platform - Migración con soporte geoespacial
"""

import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_postgis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection(db_url):
    """Crear conexión a base de datos desde URL"""
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def get_table_list(conn):
    """Obtener lista de tablas de la base de datos"""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name != 'spatial_ref_sys'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        return tables
    except Exception as e:
        logger.error(f"Error obteniendo lista de tablas: {e}")
        return []

def create_table_postgis(source_conn, dest_conn, table_name):
    """Crear tabla en destino usando DDL adaptado para PostGIS"""
    try:
        source_cur = source_conn.cursor()
        
        # Obtener estructura completa de la tabla
        source_cur.execute(f"""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns_info = source_cur.fetchall()
        source_cur.close()
        
        if not columns_info:
            logger.error(f"No se pudo obtener información de columnas para {table_name}")
            return False
        
        # Construir CREATE TABLE
        dest_cur = dest_conn.cursor()
        
        # Eliminar tabla si existe
        dest_cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        
        create_sql = f"CREATE TABLE {table_name} (\n"
        column_definitions = []
        geometry_columns = []
        
        for col_info in columns_info:
            col_name, data_type, char_max_len, is_nullable, col_default, udt_name = col_info
            
            # Manejar columnas geometry de forma especial
            if udt_name == 'geometry':
                # Por ahora, crear la columna como geometry sin especificar tipo
                col_def = f"    {col_name} geometry"
                geometry_columns.append(col_name)
            else:
                # Construir definición de columna normal
                col_def = f"    {col_name} {data_type}"
                
                if char_max_len and data_type in ['character varying', 'character', 'char', 'varchar']:
                    col_def += f"({char_max_len})"
                
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                
                if col_default and not col_default.startswith('nextval'):
                    col_def += f" DEFAULT {col_default}"
            
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions) + "\n);"
        
        # Ejecutar CREATE TABLE
        logger.info(f"Creando tabla {table_name}...")
        dest_cur.execute(create_sql)
        
        # Obtener información específica de geometría de la tabla original
        if geometry_columns:
            source_cur2 = source_conn.cursor()
            for geom_col in geometry_columns:
                try:
                    # Obtener tipo de geometría, SRID, etc.
                    source_cur2.execute(f"""
                        SELECT 
                            ST_SRID({geom_col}) as srid,
                            ST_GeometryType({geom_col}) as geom_type
                        FROM {table_name} 
                        WHERE {geom_col} IS NOT NULL 
                        LIMIT 1
                    """)
                    
                    geom_info = source_cur2.fetchone()
                    if geom_info:
                        srid, geom_type = geom_info
                        logger.info(f"Columna {geom_col}: tipo={geom_type}, SRID={srid}")
                    
                except Exception as e:
                    logger.warning(f"No se pudo obtener info de geometría para {geom_col}: {e}")
            
            source_cur2.close()
        
        dest_conn.commit()
        dest_cur.close()
        
        logger.info(f"SUCCESS: Tabla {table_name} creada")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error creando tabla {table_name}: {e}")
        try:
            dest_conn.rollback()
        except:
            pass
        return False

def copy_table_data_postgis(source_conn, dest_conn, table_name):
    """Copiar datos de tabla con columnas PostGIS"""
    try:
        logger.info(f"Iniciando migración de datos para tabla: {table_name}")
        
        # Obtener datos usando WKT para geometrías
        source_cur = source_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Primero, obtener info sobre columnas de geometría
        source_cur.execute(f"""
            SELECT column_name, udt_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns_info = source_cur.fetchall()
        
        # Construir SELECT con conversión de geometrías a WKT
        select_parts = []
        column_names = []
        
        for col_name, udt_name in columns_info:
            column_names.append(col_name)
            if udt_name == 'geometry':
                select_parts.append(f"ST_AsEWKT({col_name}) as {col_name}")
            else:
                select_parts.append(col_name)
        
        select_sql = f"SELECT {', '.join(select_parts)} FROM {table_name}"
        
        source_cur.execute(select_sql)
        rows = source_cur.fetchall()
        
        if not rows:
            logger.info(f"Tabla {table_name} esta vacia, saltando...")
            source_cur.close()
            return True
        
        logger.info(f"Encontrados {len(rows)} registros en {table_name}")
        
        # Insertar datos en destino
        dest_cur = dest_conn.cursor()
        
        # Construir INSERT con conversión de WKT a geometría
        insert_parts = []
        placeholders = []
        
        for col_name, udt_name in columns_info:
            insert_parts.append(col_name)
            if udt_name == 'geometry':
                placeholders.append("ST_GeomFromEWKT(%s)")
            else:
                placeholders.append("%s")
        
        insert_sql = f"INSERT INTO {table_name} ({', '.join(insert_parts)}) VALUES ({', '.join(placeholders)})"
        
        # Insertar por lotes
        batch_size = 100  # Reducido para datos geográficos
        total_rows = len(rows)
        successful_inserts = 0
        
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]
            
            try:
                batch_data = [tuple(row) for row in batch]
                dest_cur.executemany(insert_sql, batch_data)
                dest_conn.commit()
                successful_inserts += len(batch)
                logger.info(f"Migrados {min(i + batch_size, total_rows)}/{total_rows} registros de {table_name}")
                
            except Exception as e:
                logger.error(f"Error insertando lote en {table_name}: {e}")
                dest_conn.rollback()
                
                # Intentar insertar uno por uno
                for j, row in enumerate(batch):
                    try:
                        dest_cur.execute(insert_sql, tuple(row))
                        dest_conn.commit()
                        successful_inserts += 1
                    except Exception as row_error:
                        logger.error(f"Error en fila {i+j+1} de {table_name}: {row_error}")
                        dest_conn.rollback()
        
        dest_cur.close()
        source_cur.close()
        
        logger.info(f"SUCCESS: Migración de tabla {table_name} completada: {successful_inserts}/{total_rows} registros")
        return successful_inserts > 0
        
    except Exception as e:
        logger.error(f"ERROR: Error migrando datos de tabla {table_name}: {e}")
        return False

def main():
    """Función principal de migración PostGIS"""
    logger.info("INICIANDO MIGRACION PostGIS de base de datos local a producción")
    
    # Cargar variables de entorno
    load_dotenv('.env.production')
    
    # Configuración de bases de datos
    LOCAL_DB_URL = 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas'
    PRODUCTION_DB_URL = os.getenv('DATABASE_URL')
    
    if not PRODUCTION_DB_URL:
        logger.error("ERROR: No se encontró DATABASE_URL en .env.production")
        sys.exit(1)
    
    logger.info("Conectando a base de datos local...")
    local_conn = get_db_connection(LOCAL_DB_URL)
    if not local_conn:
        logger.error("ERROR: No se pudo conectar a la base de datos local")
        sys.exit(1)
    
    logger.info("Conectando a base de datos de producción...")
    prod_conn = get_db_connection(PRODUCTION_DB_URL)
    if not prod_conn:
        logger.error("ERROR: No se pudo conectar a la base de datos de producción")
        local_conn.close()
        sys.exit(1)
    
    try:
        # Obtener lista de tablas
        logger.info("Obteniendo lista de tablas...")
        tables = get_table_list(local_conn)
        
        if not tables:
            logger.error("ERROR: No se encontraron tablas en la base de datos local")
            return
        
        logger.info(f"Encontradas {len(tables)} tablas: {', '.join(tables)}")
        
        # Migrar cada tabla
        successful_migrations = 0
        failed_migrations = []
        
        for table in tables:
            logger.info(f"Procesando tabla: {table}")
            
            # Crear tabla en destino
            if create_table_postgis(local_conn, prod_conn, table):
                # Migrar datos
                if copy_table_data_postgis(local_conn, prod_conn, table):
                    successful_migrations += 1
                else:
                    failed_migrations.append(table)
            else:
                failed_migrations.append(table)
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("RESUMEN DE MIGRACIÓN POSTGIS")
        logger.info("=" * 60)
        logger.info(f"SUCCESS: Tablas migradas exitosamente: {successful_migrations}")
        logger.info(f"ERROR: Tablas con errores: {len(failed_migrations)}")
        
        if failed_migrations:
            logger.info(f"Tablas fallidas: {', '.join(failed_migrations)}")
        
        if successful_migrations > 0:
            logger.info("MIGRACION POSTGIS COMPLETADA!")
        else:
            logger.error("ERROR: No se pudo migrar ninguna tabla")
            
    except Exception as e:
        logger.error(f"ERROR: Error durante la migración: {e}")
    finally:
        # Cerrar conexiones
        local_conn.close()
        prod_conn.close()
        logger.info("Conexiones cerradas")

if __name__ == "__main__":
    main() 