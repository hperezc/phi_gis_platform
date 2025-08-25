#!/usr/bin/env python3
"""
Script para implementar carga condicional en el dashboard PHI
Evita la carga masiva de datos al iniciar la aplicación
"""
import os
import datetime
import re

def backup_file(filepath):
    """Crear respaldo adicional del archivo"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}_backup_{timestamp}"
    os.system(f"cp {filepath} {backup_path}")
    print(f"✅ Respaldo creado: {backup_path}")
    return backup_path

def modify_callbacks():
    """Modifica callbacks.py para implementar carga condicional"""
    filepath = "dashboard/components/callbacks.py"
    
    # Crear respaldo
    backup_path = backup_file(filepath)
    
    try:
        # Leer archivo actual
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la función update_all_components
        pattern = r'(def update_all_components\([^}]+?\):.*?"""Actualiza todos los componentes según los filtros seleccionados""")'
        
        # Código de validación para insertar
        validation_code = '''
        
        # ===== VALIDACIÓN DE FILTROS PARA EVITAR SOBRECARGA DE MEMORIA =====
        # Solo cargar datos si hay al menos un filtro específico aplicado
        has_specific_filter = any([
            depto is not None,
            municipio is not None, 
            categoria is not None,
            grupo is not None,
            zona is not None,
            contrato is not None,
            ano is not None,
            (start_date is not None and end_date is not None)
        ])
        
        # Si no hay filtros específicos, retornar valores vacíos
        if not has_specific_filter:
            print("⚠️  SEGURIDAD: No se cargan datos sin filtros específicos para evitar sobrecarga de memoria")
            
            # Crear figura vacía con mensaje informativo
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="🔍 Seleccione filtros para cargar datos",
                title_x=0.5,
                title_font_size=18,
                annotations=[{
                    'text': "Para optimizar el rendimiento del servidor,<br>" +
                           "seleccione al menos uno de estos filtros:<br><br>" +
                           "• 🏛️ Departamento<br>" +
                           "• 🏘️ Municipio<br>" +
                           "• 📋 Categoría<br>" +
                           "• 👥 Grupo de Interés<br>" +
                           "• 🌍 Zona Geográfica<br>" +
                           "• 📄 Contrato<br>" +
                           "• 📅 Año<br>" +
                           "• 📆 Rango de fechas<br><br>" +
                           "<i>Esto evita la carga de ~5000 registros simultáneamente</i>",
                    'showarrow': False,
                    'x': 0.5,
                    'y': 0.5,
                    'font': {'size': 14, 'color': '#2c3e50'},
                    'align': 'center'
                }],
                height=600,
                paper_bgcolor='#f8f9fa',
                plot_bgcolor='white'
            )
            
            # Retornar estructura completa con valores seguros
            return (
                # KPIs vacíos (8 elementos)
                ["Sin filtro"] * 8 +
                # Todas las figuras vacías (14 elementos)
                [empty_fig] * 14 +
                # Datos de tabla vacíos (2 elementos)
                [[], []]
            )
        
        # Si hay filtros, continuar con la carga normal
        print(f"✅ Filtros aplicados - procediendo con carga de datos")'''
        
        # Insertar el código después de la docstring
        if '"""Actualiza todos los componentes según los filtros seleccionados"""' in content:
            content = content.replace(
                '"""Actualiza todos los componentes según los filtros seleccionados"""',
                '"""Actualiza todos los componentes según los filtros seleccionados"""' + validation_code
            )
            
            # Escribir archivo modificado
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Archivo {filepath} modificado exitosamente")
            print(f"✅ Validación de filtros implementada")
            return True
        else:
            print(f"❌ No se encontró el patrón de función en {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error modificando {filepath}: {str(e)}")
        # Restaurar desde respaldo
        os.system(f"cp {backup_path} {filepath}")
        print(f"🔄 Archivo restaurado desde respaldo")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando optimización de memoria del Dashboard PHI")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("dashboard/components/callbacks.py"):
        print("❌ Error: No se encuentra el archivo callbacks.py")
        print("   Asegúrese de estar en el directorio Dashboard_BD_PHI")
        return False
    
    # Aplicar modificaciones
    success = modify_callbacks()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ OPTIMIZACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ El dashboard ahora requiere filtros específicos antes de cargar datos")
        print("✅ Esto evitará problemas de memoria con ~5000 registros")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Reiniciar el servicio: systemctl restart phi-dashboard.service")
        print("   2. Verificar funcionamiento en: http://45.55.212.201:8050")
        print("   3. Probar con filtros específicos")
    else:
        print("\n❌ Error en la optimización - archivos restaurados")
    
    return success

if __name__ == "__main__":
    main()
