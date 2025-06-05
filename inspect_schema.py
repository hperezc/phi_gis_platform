#!/usr/bin/env python3
"""
Script para inspeccionar el esquema de la base de datos en DigitalOcean
"""

import os
import sys
import psycopg2
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de la base de datos de DigitalOcean
DB_CONFIG = {
    'host': 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com',
    'port': 25060,
    'database': 'defaultdb',
    'user': 'doadmin',
    'password': 'AVNS_nAsg-fcAlH1dOF3pzB_',
    'sslmode': 'require'
}

def inspect_table_structure():
    """Inspecciona la estructura de las tablas principales"""
    try:
        logger.info("🔍 Inspeccionando estructura de tablas...")
        
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        logger.info(f"📋 Tablas encontradas: {len(tables)}")
        
        # Inspeccionar cada tabla importante
        important_tables = ['actividades', 'actividades_departamentos', 'actividades_municipios']
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            if table_name in important_tables:
                logger.info(f"\n🔍 Estructura de tabla: {table_name}")
                
                # Obtener columnas
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                for col in columns:
                    logger.info(f"   📊 {col[0]}: {col[1]} ({'NULL' if col[2]=='YES' else 'NOT NULL'})")
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                logger.info(f"   📈 Registros: {count}")
                
                # Buscar columnas geométricas
                cursor.execute("""
                    SELECT column_name, udt_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND (data_type = 'USER-DEFINED' OR column_name LIKE '%%geom%%' OR column_name LIKE '%%geo%%');
                """, (table_name,))
                
                geom_cols = cursor.fetchall()
                if geom_cols:
                    logger.info(f"   🗺️ Columnas geométricas: {geom_cols}")
                
                # Obtener muestra de una fila
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                sample = cursor.fetchone()
                if sample:
                    # Obtener nombres de columnas
                    colnames = [desc[0] for desc in cursor.description]
                    logger.info(f"   📋 Columnas: {colnames[:10]}...")  # Mostrar solo primeras 10
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inspeccionando esquema: {e}")
        return False

def check_geometry_columns():
    """Verifica las columnas de geometría usando PostGIS"""
    try:
        logger.info("🗺️ Verificando columnas geométricas con PostGIS...")
        
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Consultar geometry_columns
        cursor.execute("""
            SELECT f_table_name, f_geometry_column, type, srid 
            FROM geometry_columns 
            WHERE f_table_schema = 'public'
            ORDER BY f_table_name;
        """)
        
        geom_info = cursor.fetchall()
        
        logger.info(f"📊 Columnas geométricas registradas:")
        for info in geom_info:
            logger.info(f"   🗺️ Tabla: {info[0]}, Columna: {info[1]}, Tipo: {info[2]}, SRID: {info[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando geometrías: {e}")
        return False

def test_sample_queries():
    """Prueba consultas con los nombres reales de columnas"""
    try:
        logger.info("🔍 Probando consultas con estructura real...")
        
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Obtener nombres de columnas de la tabla actividades
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'actividades'
            ORDER BY ordinal_position;
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Columnas de 'actividades': {columns}")
        
        # Buscar columna geométrica
        geom_column = None
        for col in columns:
            if 'geom' in col.lower() or 'geo' in col.lower():
                geom_column = col
                break
        
        if geom_column:
            logger.info(f"🗺️ Columna geométrica encontrada: {geom_column}")
            
            # Contar registros con geometría
            cursor.execute(f"SELECT COUNT(*) FROM actividades WHERE {geom_column} IS NOT NULL;")
            count_with_geom = cursor.fetchone()[0]
            logger.info(f"📍 Actividades con geometría: {count_with_geom}")
        else:
            logger.warning("⚠️ No se encontró columna geométrica evidente")
        
        # Obtener muestra de datos
        cursor.execute("SELECT * FROM actividades LIMIT 3;")
        sample_data = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        
        logger.info("📋 Muestra de datos:")
        for i, row in enumerate(sample_data):
            logger.info(f"   Registro {i+1}:")
            for j, col in enumerate(colnames[:8]):  # Mostrar solo primeras 8 columnas
                value = str(row[j])[:50] if row[j] else 'NULL'
                logger.info(f"     {col}: {value}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando consultas: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando inspección del esquema de base de datos...")
    
    # Inspeccionar estructura
    if not inspect_table_structure():
        logger.error("❌ Fallo inspeccionando estructura")
        return False
    
    # Verificar columnas geométricas
    if not check_geometry_columns():
        logger.error("❌ Fallo verificando geometrías")
        return False
    
    # Probar consultas
    if not test_sample_queries():
        logger.error("❌ Fallo probando consultas")
        return False
    
    logger.info("🎉 ¡Inspección completada exitosamente!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 