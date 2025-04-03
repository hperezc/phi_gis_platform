import logging
import json
import os
from data_loader import DataLoader
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Crear directorio para resultados si no existe
        os.makedirs('results', exist_ok=True)
        
        logger.info("Iniciando verificación de datos...")
        loader = DataLoader()
        results = loader.verify_tables()
        
        # Guardar resultados en un archivo JSON
        output_file = os.path.join('results', 'data_verification_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Verificación completada. Resultados guardados en '{output_file}'")
        
        # Mostrar resumen detallado
        logger.info("\n=== RESUMEN DE DATOS ===")
        logger.info(f"\nTabla actividades:")
        logger.info(f"- Total registros: {results['actividades']['total']}")
        logger.info(f"- Columnas disponibles: {', '.join(results['actividades']['columnas'])}")
        
        logger.info(f"\nTabla actividades_municipios:")
        logger.info(f"- Total registros: {results['actividades_municipios']['total']}")
        logger.info(f"- Columnas disponibles: {', '.join(results['actividades_municipios']['columnas'])}")
        
        logger.info(f"\nTabla actividades_departamentos:")
        logger.info(f"- Total registros: {results['actividades_departamentos']['total']}")
        logger.info(f"- Columnas disponibles: {', '.join(results['actividades_departamentos']['columnas'])}")
        
        logger.info("\n=== VERIFICACIÓN COMPLETA ===")
        
    except Exception as e:
        logger.error(f"Error durante la verificación: {str(e)}")
        raise

if __name__ == "__main__":
    main() 