#!/usr/bin/env python3
"""
Script de migración de base de datos local a producción (Versión Simple)
PHI GIS Platform - Migración a Digital Ocean
"""

import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configurar logging sin emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
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
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        return tables
    except Exception as e:
        logger.error(f"Error obteniendo lista de tablas: {e}")
        return []

def copy_table_data(source_conn, dest_conn, table_name):
    """Copiar datos de una tabla desde origen a destino"""
    try:
        logger.info(f"Iniciando migración de tabla: {table_name}")
        
        # Obtener datos de la tabla origen
        source_cur = source_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        source_cur.execute(f"SELECT * FROM {table_name}")
        rows = source_cur.fetchall()
        
        if not rows:
            logger.info(f"Tabla {table_name} esta vacia, saltando...")
            source_cur.close()
            return True
        
        # Obtener nombres de columnas
        columns = [desc[0] for desc in source_cur.description]
        source_cur.close()
        
        # Insertar datos en la tabla destino
        dest_cur = dest_conn.cursor()
        
        # Crear placeholders para INSERT
        placeholders = ','.join(['%s'] * len(columns))
        columns_str = ','.join(columns)
        
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insertar datos por lotes
        batch_size = 1000
        total_rows = len(rows)
        
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]
            batch_data = [tuple(row) for row in batch]
            
            try:
                dest_cur.executemany(insert_query, batch_data)
                dest_conn.commit()
                logger.info(f"Migrados {min(i + batch_size, total_rows)}/{total_rows} registros de {table_name}")
            except Exception as e:
                logger.error(f"Error insertando lote en {table_name}: {e}")
                dest_conn.rollback()
                # Intentar insertar uno por uno para identificar problemas
                for row in batch:
                    try:
                        dest_cur.execute(insert_query, tuple(row))
                        dest_conn.commit()
                    except Exception as row_error:
                        logger.error(f"Error en fila específica de {table_name}: {row_error}")
                        dest_conn.rollback()
        
        dest_cur.close()
        logger.info(f"SUCCESS: Migración de tabla {table_name} completada: {total_rows} registros")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error migrando tabla {table_name}: {e}")
        return False

def create_table_if_not_exists(source_conn, dest_conn, table_name):
    """Crear tabla en destino si no existe"""
    try:
        # Obtener DDL de la tabla desde el origen
        source_cur = source_conn.cursor()
        
        # Obtener estructura de la tabla
        source_cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
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
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        column_definitions = []
        
        for col_info in columns_info:
            col_name, data_type, char_max_len, is_nullable, col_default = col_info
            
            # Construir definición de columna
            col_def = f"    {col_name} {data_type}"
            
            if char_max_len:
                col_def += f"({char_max_len})"
            
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            
            if col_default:
                col_def += f" DEFAULT {col_default}"
            
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions) + "\n);"
        
        # Ejecutar CREATE TABLE en destino
        dest_cur = dest_conn.cursor()
        dest_cur.execute(create_sql)
        dest_conn.commit()
        dest_cur.close()
        
        logger.info(f"SUCCESS: Tabla {table_name} creada/verificada en destino")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error creando tabla {table_name}: {e}")
        return False

def main():
    """Función principal de migración"""
    logger.info("INICIANDO MIGRACION de base de datos local a producción")
    
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
            
            # Crear tabla en destino si no existe
            if create_table_if_not_exists(local_conn, prod_conn, table):
                # Migrar datos
                if copy_table_data(local_conn, prod_conn, table):
                    successful_migrations += 1
                else:
                    failed_migrations.append(table)
            else:
                failed_migrations.append(table)
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("RESUMEN DE MIGRACIÓN")
        logger.info("=" * 60)
        logger.info(f"SUCCESS: Tablas migradas exitosamente: {successful_migrations}")
        logger.info(f"ERROR: Tablas con errores: {len(failed_migrations)}")
        
        if failed_migrations:
            logger.info(f"Tablas fallidas: {', '.join(failed_migrations)}")
        
        if successful_migrations > 0:
            logger.info("MIGRACION COMPLETADA!")
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
    # Verificar dependencias
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 no está instalado")
        print("Instala con: pip install psycopg2-binary")
        sys.exit(1)
    
    # Ejecutar migración
    main() 