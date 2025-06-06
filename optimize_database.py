#!/usr/bin/env python3
"""
Script para optimizar la base de datos de DigitalOcean
Crea índices específicos para mejorar el rendimiento de las consultas del dashboard
"""

import os
import sys
import psycopg2
from psycopg2 import sql
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

def create_connection():
    """Crear conexión a la base de datos"""
    try:
        conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}"
        conn = psycopg2.connect(conn_string)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def create_indexes(conn):
    """Crear índices para optimizar consultas del dashboard"""
    cursor = conn.cursor()
    
    indexes = [
        # Índices para filtros más comunes
        ("idx_actividades_fecha", "CREATE INDEX IF NOT EXISTS idx_actividades_fecha ON actividades(fecha);"),
        ("idx_actividades_ano", "CREATE INDEX IF NOT EXISTS idx_actividades_ano ON actividades(ano);"),
        ("idx_actividades_departamento", "CREATE INDEX IF NOT EXISTS idx_actividades_departamento ON actividades(departamento);"),
        ("idx_actividades_municipio", "CREATE INDEX IF NOT EXISTS idx_actividades_municipio ON actividades(municipio);"),
        ("idx_actividades_zona", "CREATE INDEX IF NOT EXISTS idx_actividades_zona ON actividades(zona_geografica);"),
        ("idx_actividades_categoria", "CREATE INDEX IF NOT EXISTS idx_actividades_categoria ON actividades(categoria_unica);"),
        ("idx_actividades_grupo", "CREATE INDEX IF NOT EXISTS idx_actividades_grupo ON actividades(grupo_interes);"),
        
        # Índices compuestos para consultas frecuentes
        ("idx_actividades_depto_municipio", "CREATE INDEX IF NOT EXISTS idx_actividades_depto_municipio ON actividades(departamento, municipio);"),
        ("idx_actividades_fecha_departamento", "CREATE INDEX IF NOT EXISTS idx_actividades_fecha_departamento ON actividades(fecha, departamento);"),
        ("idx_actividades_ano_zona", "CREATE INDEX IF NOT EXISTS idx_actividades_ano_zona ON actividades(ano, zona_geografica);"),
        
        # Índices para geometrías (optimizar mapas)
        ("idx_actividades_geometry", "CREATE INDEX IF NOT EXISTS idx_actividades_geometry ON actividades USING GIST(geometry);"),
        ("idx_actividades_tipo_geometry", "CREATE INDEX IF NOT EXISTS idx_actividades_tipo_geometry ON actividades(tipo_geometria) WHERE geometry IS NOT NULL;"),
        
        # Índices para consultas de KPIs (operaciones agregadas)
        ("idx_actividades_asistentes", "CREATE INDEX IF NOT EXISTS idx_actividades_asistentes ON actividades(total_asistentes) WHERE total_asistentes > 0;"),
        ("idx_actividades_contrato", "CREATE INDEX IF NOT EXISTS idx_actividades_contrato ON actividades(contrato);"),
        
        # Índice parcial para fechas válidas
        ("idx_actividades_fecha_valida", "CREATE INDEX IF NOT EXISTS idx_actividades_fecha_valida ON actividades(fecha) WHERE fecha IS NOT NULL;"),
    ]
    
    success_count = 0
    for index_name, query in indexes:
        try:
            logger.info(f"Creando índice: {index_name}")
            cursor.execute(query)
            conn.commit()
            success_count += 1
            logger.info(f"✅ Índice {index_name} creado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error creando índice {index_name}: {e}")
            conn.rollback()
    
    cursor.close()
    logger.info(f"✅ Creados {success_count}/{len(indexes)} índices exitosamente")
    return success_count

def optimize_database_settings(conn):
    """Aplicar configuraciones de optimización a la base de datos"""
    cursor = conn.cursor()
    
    optimizations = [
        # Configuraciones para mejorar rendimiento de consultas
        ("VACUUM ANALYZE actividades;", "Actualizar estadísticas de la tabla actividades"),
        
        # Configurar cache para mejores consultas geométricas
        ("SET work_mem = '256MB';", "Incrementar memoria de trabajo"),
        ("SET random_page_cost = 1.1;", "Optimizar para SSD"),
        
        # Configurar para consultas complejas
        ("SET effective_cache_size = '3GB';", "Configurar cache efectivo"),
        ("SET shared_buffers = '512MB';", "Configurar buffers compartidos"),
    ]
    
    success_count = 0
    for query, description in optimizations:
        try:
            logger.info(f"Aplicando: {description}")
            cursor.execute(query)
            conn.commit()
            success_count += 1
            logger.info(f"✅ {description} aplicado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error aplicando {description}: {e}")
            conn.rollback()
    
    cursor.close()
    logger.info(f"✅ Aplicadas {success_count}/{len(optimizations)} optimizaciones")
    return success_count

def analyze_table_stats(conn):
    """Analizar estadísticas de la tabla para verificar mejoras"""
    cursor = conn.cursor()
    
    try:
        # Obtener estadísticas básicas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT departamento) as total_departamentos,
                COUNT(DISTINCT municipio) as total_municipios,
                MIN(fecha) as fecha_min,
                MAX(fecha) as fecha_max,
                COUNT(*) FILTER (WHERE geometry IS NOT NULL) as registros_con_geometria
            FROM actividades;
        """)
        stats = cursor.fetchone()
        
        logger.info("📊 ESTADÍSTICAS DE LA BASE DE DATOS:")
        logger.info(f"   Total registros: {stats[0]:,}")
        logger.info(f"   Departamentos: {stats[1]}")
        logger.info(f"   Municipios: {stats[2]}")
        logger.info(f"   Rango fechas: {stats[3]} - {stats[4]}")
        logger.info(f"   Registros con geometría: {stats[5]:,}")
        
        # Verificar índices existentes
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE tablename = 'actividades' 
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        
        logger.info(f"📈 ÍNDICES EXISTENTES ({len(indexes)}):")
        for index_name, table_name in indexes:
            logger.info(f"   - {index_name}")
            
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
    
    cursor.close()

def main():
    """Función principal para optimizar la base de datos"""
    logger.info("🚀 INICIANDO OPTIMIZACIÓN DE BASE DE DATOS PHI GIS")
    logger.info("=" * 60)
    
    # Conectar a la base de datos
    conn = create_connection()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        # Analizar estado actual
        logger.info("📊 Analizando estado actual...")
        analyze_table_stats(conn)
        
        # Crear índices
        logger.info("\n🔧 Creando índices de optimización...")
        indexes_created = create_indexes(conn)
        
        # Aplicar optimizaciones
        logger.info("\n⚡ Aplicando optimizaciones de configuración...")
        optimizations_applied = optimize_database_settings(conn)
        
        # Analizar estado final
        logger.info("\n📊 Analizando estado final...")
        analyze_table_stats(conn)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ OPTIMIZACIÓN COMPLETADA")
        logger.info(f"📈 Índices creados: {indexes_created}")
        logger.info(f"⚡ Optimizaciones aplicadas: {optimizations_applied}")
        logger.info("🚀 La base de datos debería funcionar más rápido ahora")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error durante la optimización: {e}")
    finally:
        conn.close()
        logger.info("🔐 Conexión cerrada")

if __name__ == "__main__":
    main() 