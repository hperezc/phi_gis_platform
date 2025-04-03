import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ml_module.utils.data_loader import DataLoader
from ml_module.preprocessing.feature_engineering import FeatureEngineer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_features():
    try:
        # Crear directorio para resultados
        results_dir = Path('results/feature_analysis')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar datos
        logger.info("Cargando datos...")
        loader = DataLoader()
        df = loader.load_training_data()
        
        # Mostrar información inicial
        logger.info(f"\nInformación del dataset original:")
        logger.info(f"Registros: {len(df)}")
        logger.info(f"Columnas: {df.columns.tolist()}")
        
        # Aplicar feature engineering
        logger.info("\nAplicando feature engineering...")
        engineer = FeatureEngineer()
        df_features = engineer.transform(df)
        
        # Análisis de características
        logger.info("\nAnalizando características generadas...")
        
        # 1. Resumen de características
        feature_summary = pd.DataFrame({
            'tipo': df_features.dtypes,
            'no_nulos': df_features.count(),
            'nulos': df_features.isnull().sum(),
            'nunicos': df_features.nunique(),
            'media': df_features.mean(numeric_only=True),
            'std': df_features.std(numeric_only=True)
        })
        
        # Guardar resumen
        summary_file = results_dir / 'feature_summary.csv'
        feature_summary.to_csv(summary_file)
        logger.info(f"\nResumen de características guardado en: {summary_file}")
        
        # 2. Correlaciones con target
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns
        correlations = df_features[numeric_cols].corr()['total_asistentes'].sort_values(ascending=False)
        
        # Guardar correlaciones
        corr_file = results_dir / 'target_correlations.csv'
        correlations.to_csv(corr_file)
        logger.info(f"Correlaciones guardadas en: {corr_file}")
        
        # 3. Visualizaciones
        logger.info("\nGenerando visualizaciones...")
        
        # Matriz de correlación
        plt.figure(figsize=(15, 10))
        sns.heatmap(df_features[numeric_cols].corr(), cmap='RdBu', center=0, annot=True, fmt='.2f')
        plt.title('Matriz de Correlación de Features')
        plt.tight_layout()
        plt.savefig(results_dir / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Análisis temporal
        plt.figure(figsize=(18, 6))
        temporal_features = ['mes', 'dia_semana', 'trimestre']
        for i, col in enumerate(temporal_features, 1):
            plt.subplot(1, 3, i)
            avg_attendance = df_features.groupby(col)['total_asistentes'].mean()
            avg_attendance.plot(kind='bar')
            plt.title(f'Asistentes promedio por {col}')
            plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(results_dir / 'temporal_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Análisis geográfico
        plt.figure(figsize=(15, 8))
        df_features.groupby('departamento')['total_asistentes'].mean().sort_values(ascending=False).plot(kind='bar')
        plt.title('Asistentes promedio por Departamento')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(results_dir / 'geographical_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizaciones guardadas en: {results_dir}")
        
        # Generar resumen final
        results = {
            'total_features': len(df_features.columns),
            'numeric_features': len(numeric_cols),
            'categorical_features': len(df_features.select_dtypes(include=['object']).columns),
            'temporal_features': len([col for col in df_features.columns if 'dia' in col or 'mes' in col or 'ano' in col]),
            'top_correlations': correlations.head().to_dict()
        }
        
        # Guardar resumen en formato JSON
        import json
        with open(results_dir / 'analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("\nAnálisis completado exitosamente!")
        return results
        
    except Exception as e:
        logger.error(f"Error en análisis de features: {str(e)}")
        raise

if __name__ == "__main__":
    print("\n=== Iniciando Análisis de Features ===\n")
    results = analyze_features()
    print("\n=== Resumen de Features ===")
    for key, value in results.items():
        if key != 'top_correlations':
            print(f"{key}: {value}")
    print("\nTop 5 correlaciones con total_asistentes:")
    for feature, corr in results['top_correlations'].items():
        print(f"{feature}: {corr:.3f}") 