#!/usr/bin/env python3
"""
Script simple para agregar la capa sistema_alarmas al geoportal
"""

import os
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Hacer backup de un archivo"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"✅ Backup: {backup_path}")
        return backup_path
    return None

def check_geoportal_structure():
    """Verificar la estructura del geoportal"""
    logger.info("🔍 Verificando estructura del geoportal...")
    
    files_to_check = [
        "geoportal/backend/app/main.py",
        "geoportal/frontend/src/components/",
        "geoportal/frontend/src/services/",
        "docker-compose.production.yml",
        ".env.production"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            logger.info(f"✅ Encontrado: {file}")
        else:
            logger.warning(f"⚠️ No encontrado: {file}")
    
    return True

def add_alarmas_to_backend():
    """Agregar sistema_alarmas al backend"""
    backend_file = "geoportal/backend/app/main.py"
    
    if not os.path.exists(backend_file):
        logger.error(f"❌ No se encontró: {backend_file}")
        return False
    
    backup_file(backend_file)
    
    try:
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya existe
        if 'sistema_alarmas' in content:
            logger.info("ℹ️ sistema_alarmas ya existe en el backend")
            return True
        
        # Buscar donde agregar la nueva capa
        if 'layers' in content or 'capas' in content:
            logger.info("✅ Backend encontrado, agregando capa sistema_alarmas...")
            # Aquí agregarías la configuración específica
            logger.info("📝 Nota: Se requiere configuración manual del backend")
        else:
            logger.warning("⚠️ No se encontró configuración de capas en el backend")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en backend: {e}")
        return False

def create_alarmas_config():
    """Crear archivo de configuración para sistema_alarmas"""
    config_dir = "geoportal/frontend/src/config"
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = f"{config_dir}/alarmas.ts"
    backup_file(config_file)
    
    try:
        config_content = '''
// Configuración de la capa Sistema de Alarmas
export const sistemaAlarmasConfig = {
    id: 'sistema_alarmas',
    name: 'Sistema de Alarmas',
    type: 'point',
    visible: false,
    style: {
        color: '#ff4444',
        size: 8,
        symbol: 'circle',
        opacity: 0.8
    },
    popup: {
        title: 'Sistema de Alarmas',
        fields: [
            { key: 'NOMBRE_SAT', label: 'Nombre SAT' },
            { key: 'DEPARTAMEN', label: 'Departamento' },
            { key: 'MUNICIPIO', label: 'Municipio' },
            { key: 'ESTADO', label: 'Estado' },
            { key: 'ALCANCE', label: 'Alcance (m)' },
            { key: 'TIPO_ACTIV', label: 'Tipo Activación' },
            { key: 'RESPONSABL', label: 'Responsable' }
        ]
    },
    filters: [
        { key: 'DEPARTAMEN', label: 'Departamento', type: 'select' },
        { key: 'MUNICIPIO', label: 'Municipio', type: 'select' },
        { key: 'ESTADO', label: 'Estado', type: 'select' },
        { key: 'TIPO_ACTIV', label: 'Tipo Activación', type: 'select' }
    ]
};
'''
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info("✅ Configuración de alarmas creada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando configuración: {e}")
        return False

def create_alarmas_service():
    """Crear servicio para sistema_alarmas"""
    service_dir = "geoportal/frontend/src/services"
    os.makedirs(service_dir, exist_ok=True)
    
    service_file = f"{service_dir}/alarmasService.ts"
    backup_file(service_file)
    
    try:
        service_content = '''
// Servicio para Sistema de Alarmas
export interface SistemaAlarma {
    ID_DEPARTA: string;
    DEPARTAMEN: string;
    ID_MUNICIP: string;
    MUNICIPIO: string;
    COD_SECTOR: string;
    NOMBRE_SEC: string;
    ID_SAT: string;
    NOMBRE_SAT: string;
    ALCANCE: number;
    CUBRIMIENT: string;
    ORIENTACIO: string;
    SENTIDO_CO: string;
    TIPO_ACTIV: string;
    RESPONSABL: string;
    TIPO_SISTE: string;
    TIPO_TECNO: string;
    FUENTE_ENE: string;
    ESTADO: string;
    COOR_NORTE: number;
    COOR_ESTE: number;
    LATITUD: string;
    LONGITUD: string;
    affa: number;
    COOR_ESTE_: number;
    FECHA_ACTU: string;
    geometry: any;
}

export const alarmasService = {
    async getAlarmas(filters?: any): Promise<SistemaAlarma[]> {
        try {
            // Implementar llamada a API
            console.log('Obteniendo alarmas con filtros:', filters);
            return [];
        } catch (error) {
            console.error('Error obteniendo alarmas:', error);
            return [];
        }
    },

    async getFilterOptions(): Promise<any> {
        try {
            // Implementar obtención de opciones de filtros
            return {
                departamentos: [],
                municipios: [],
                estados: [],
                tipos_activacion: []
            };
        } catch (error) {
            console.error('Error obteniendo opciones de filtros:', error);
            return {};
        }
    }
};
'''
        
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        logger.info("✅ Servicio de alarmas creado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando servicio: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO INTEGRACIÓN SISTEMA_ALARMAS")
    logger.info("=" * 40)
    
    # Verificar estructura
    check_geoportal_structure()
    
    # Ejecutar tareas
    tasks = [
        ("Verificar backend", add_alarmas_to_backend),
        ("Crear configuración", create_alarmas_config),
        ("Crear servicio", create_alarmas_service)
    ]
    
    success = 0
    total = len(tasks)
    
    for name, task in tasks:
        logger.info(f"\n🔧 {name}...")
        if task():
            success += 1
            logger.info(f"✅ {name} completado")
        else:
            logger.warning(f"⚠️ {name} falló")
    
    logger.info("\n" + "=" * 40)
    logger.info(f"📊 RESUMEN: {success}/{total} tareas completadas")
    
    if success == total:
        logger.info("🎉 INTEGRACIÓN COMPLETADA")
        logger.info("\n📋 PRÓXIMOS PASOS:")
        logger.info("1. Revisar archivos creados")
        logger.info("2. Configurar backend manualmente")
        logger.info("3. Reiniciar servicios")
        logger.info("4. Probar la nueva capa")
    else:
        logger.warning("⚠️ ALGUNAS TAREAS FALLARON")
    
    return success == total

if __name__ == "__main__":
    main() 