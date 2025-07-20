#!/usr/bin/env python3
"""
Script para agregar la capa sistema_alarmas al geoportal
Fecha: 2025-07-18
Propósito: Integrar la capa de alarmas al control de capas del geoportal
"""

import os
import json
import shutil
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Hacer backup de un archivo antes de modificarlo"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"✅ Backup creado: {backup_path}")
        return backup_path
    return None

def add_alarmas_layer_to_backend():
    """Agregar endpoint para sistema_alarmas en el backend"""
    backend_file = "geoportal/backend/app/main.py"
    
    if not os.path.exists(backend_file):
        logger.error(f"❌ Archivo no encontrado: {backend_file}")
        return False
    
    backup_file(backend_file)
    
    try:
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la sección donde se definen las capas
        if 'sistema_alarmas' not in content:
            # Agregar la nueva capa después de las existentes
            alarmas_layer_config = '''
    # Capa Sistema de Alarmas
    {
        "id": "sistema_alarmas",
        "name": "Sistema de Alarmas",
        "type": "point",
        "source": "sistema_alarmas",
        "fields": [
            "ID_DEPARTA", "DEPARTAMEN", "ID_MUNICIP", "MUNICIPIO", 
            "COD_SECTOR", "NOMBRE_SEC", "ID_SAT", "NOMBRE_SAT",
            "ALCANCE", "CUBRIMIENT", "ORIENTACIO", "SENTIDO_CO",
            "TIPO_ACTIV", "RESPONSABL", "TIPO_SISTE", "TIPO_TECNO",
            "FUENTE_ENE", "ESTADO", "COOR_NORTE", "COOR_ESTE",
            "LATITUD", "LONGITUD", "affa", "COOR_ESTE_", "FECHA_ACTU"
        ],
        "geometry_field": "geometry",
        "style": {
            "color": "#ff4444",
            "size": 8,
            "symbol": "circle"
        },
        "popup_fields": [
            "NOMBRE_SAT", "DEPARTAMEN", "MUNICIPIO", "ESTADO", 
            "ALCANCE", "TIPO_ACTIV", "RESPONSABL"
        ],
        "filters": ["DEPARTAMEN", "MUNICIPIO", "ESTADO", "TIPO_ACTIV"]
    },'''
            
            # Insertar después de la última capa existente
            if ']' in content:
                # Encontrar el último corchete de cierre de la lista de capas
                last_bracket_pos = content.rfind(']')
                if last_bracket_pos != -1:
                    # Insertar antes del corchete de cierre
                    content = content[:last_bracket_pos] + alarmas_layer_config + '\n    ' + content[last_bracket_pos:]
                    
                    with open(backend_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    logger.info("✅ Capa sistema_alarmas agregada al backend")
                    return True
        
        logger.info("ℹ️ La capa sistema_alarmas ya existe en el backend")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error modificando backend: {e}")
        return False

def add_alarmas_layer_to_frontend():
    """Agregar la capa sistema_alarmas al frontend"""
    frontend_config_file = "geoportal/frontend/src/config/layers.ts"
    
    if not os.path.exists(frontend_config_file):
        logger.warning(f"⚠️ Archivo no encontrado: {frontend_config_file}")
        # Crear el archivo si no existe
        os.makedirs(os.path.dirname(frontend_config_file), exist_ok=True)
    
    backup_file(frontend_config_file)
    
    try:
        # Configuración de la capa sistema_alarmas
        alarmas_config = '''
export const sistemaAlarmasLayer = {
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
            { key: 'RESPONSABL', label: 'Responsable' },
            { key: 'TIPO_SISTE', label: 'Tipo Sistema' },
            { key: 'TIPO_TECNO', label: 'Tipo Tecnología' },
            { key: 'FUENTE_ENE', label: 'Fuente Energía' }
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
        
        # Leer contenido existente o crear nuevo
        if os.path.exists(frontend_config_file):
            with open(frontend_config_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = '// Configuración de capas del geoportal\n'
        
        # Agregar la configuración si no existe
        if 'sistemaAlarmasLayer' not in content:
            content += alarmas_config
            
            with open(frontend_config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ Configuración de capa sistema_alarmas agregada al frontend")
        else:
            logger.info("ℹ️ La configuración de sistema_alarmas ya existe en el frontend")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error modificando frontend: {e}")
        return False

def update_layer_control():
    """Actualizar el control de capas para incluir sistema_alarmas"""
    layer_control_file = "geoportal/frontend/src/components/LayerControl.tsx"
    
    if not os.path.exists(layer_control_file):
        logger.warning(f"⚠️ Archivo no encontrado: {layer_control_file}")
        return False
    
    backup_file(layer_control_file)
    
    try:
        with open(layer_control_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la sección donde se definen las capas en el control
        if 'sistema_alarmas' not in content:
            # Agregar la nueva capa al control
            alarmas_control = '''
        {
            id: 'sistema_alarmas',
            name: 'Sistema de Alarmas',
            icon: '🔴',
            description: 'Sistemas de alarmas de emergencia'
        },'''
            
            # Insertar después de las capas existentes
            if 'layers:' in content:
                # Encontrar la posición después de la última capa
                layers_pos = content.find('layers:')
                if layers_pos != -1:
                    # Buscar el final de la lista de capas
                    end_pos = content.find(']', layers_pos)
                    if end_pos != -1:
                        content = content[:end_pos] + alarmas_control + '\n        ' + content[end_pos:]
                        
                        with open(layer_control_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info("✅ Control de capas actualizado")
                        return True
        
        logger.info("ℹ️ La capa sistema_alarmas ya existe en el control de capas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando control de capas: {e}")
        return False

def create_alarmas_service():
    """Crear servicio para manejar datos de sistema_alarmas"""
    service_file = "geoportal/frontend/src/services/alarmasService.ts"
    
    os.makedirs(os.path.dirname(service_file), exist_ok=True)
    backup_file(service_file)
    
    try:
        service_content = '''
import { apiClient } from './apiClient';

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
            const response = await apiClient.get('/api/sistema_alarmas', { params: filters });
            return response.data;
        } catch (error) {
            console.error('Error obteniendo alarmas:', error);
            return [];
        }
    },

    async getAlarmasByDepartamento(departamento: string): Promise<SistemaAlarma[]> {
        return this.getAlarmas({ departamento });
    },

    async getAlarmasByMunicipio(municipio: string): Promise<SistemaAlarma[]> {
        return this.getAlarmas({ municipio });
    },

    async getAlarmasByEstado(estado: string): Promise<SistemaAlarma[]> {
        return this.getAlarmas({ estado });
    },

    async getFilterOptions(): Promise<any> {
        try {
            const response = await apiClient.get('/api/sistema_alarmas/filters');
            return response.data;
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
        logger.error(f"❌ Error creando servicio de alarmas: {e}")
        return False

def main():
    """Función principal para agregar la capa sistema_alarmas"""
    logger.info("🚀 INICIANDO INTEGRACIÓN DE CAPA SISTEMA_ALARMAS")
    logger.info("=" * 50)
    
    # Lista de funciones a ejecutar
    functions = [
        ("Backend - Agregar endpoint", add_alarmas_layer_to_backend),
        ("Frontend - Configuración de capa", add_alarmas_layer_to_frontend),
        ("Frontend - Control de capas", update_layer_control),
        ("Frontend - Servicio de alarmas", create_alarmas_service)
    ]
    
    success_count = 0
    total_count = len(functions)
    
    for name, func in functions:
        logger.info(f"\n🔧 {name}...")
        try:
            if func():
                success_count += 1
                logger.info(f"✅ {name} completado")
            else:
                logger.warning(f"⚠️ {name} falló")
        except Exception as e:
            logger.error(f"❌ Error en {name}: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 RESUMEN: {success_count}/{total_count} tareas completadas")
    
    if success_count == total_count:
        logger.info("🎉 INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("\n�� PRÓXIMOS PASOS:")
        logger.info("1. Reiniciar servicios Docker")
        logger.info("2. Verificar que la capa aparece en el control")
        logger.info("3. Probar funcionalidades de filtrado")
        logger.info("4. Verificar estilos y popups")
    else:
        logger.warning("⚠️ ALGUNAS TAREAS FALLARON - Revisar logs")
    
    return success_count == total_count

if __name__ == "__main__":
    main()
