from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración base
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "trained_models"
DATA_DIR = BASE_DIR / "data"

# Asegurar que los directorios existen
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas')

# Features expandidas para el modelo de predicción de asistencia
ATTENDANCE_FEATURES = [
    # Features básicas
    'departamento',
    'municipio',
    'zona_geografica',
    'categoria_actividad',
    'categoria_unica',
    'grupo_interes',
    'grupo_intervencion',
    
    # Features temporales
    'mes_numero',
    'dia_semana',
    'year',
    
    # Features estadísticas
    'actividades_previas',
    'promedio_asistentes_historico',
    
    # Features derivadas (se agregarán en el feature engineering)
    'dias_desde_ultima_actividad',
    'actividades_ultimo_mes',
    'ratio_asistencia_historica'
]

# Configuración expandida del modelo
MODEL_CONFIG = {
    'attendance_predictor': {
        'model_type': 'xgboost',
        'params': {
            'n_estimators': 200,
            'max_depth': 8,
            'learning_rate': 0.05,
            'objective': 'reg:squarederror',
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1
        },
        'cv_folds': 5,
        'early_stopping_rounds': 20
    }
}

# Configuración de evaluación
EVALUATION_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'metrics': ['rmse', 'mae', 'r2']
} 