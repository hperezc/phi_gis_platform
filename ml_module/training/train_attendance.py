import logging
from ..utils.data_loader import DataLoader
from ..preprocessing.data_cleaner import DataCleaner
from ..models.attendance_predictor import AttendancePredictor
from ..config import ATTENDANCE_FEATURES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_attendance_model():
    """Entrena el modelo de predicción de asistencia"""
    try:
        # Cargar datos
        logger.info("Cargando datos de entrenamiento...")
        data_loader = DataLoader()
        df = data_loader.load_training_data()
        
        # Limpiar y preparar datos
        logger.info("Preparando datos...")
        cleaner = DataCleaner()
        df_cleaned = cleaner.clean_attendance_data(df)
        
        # Preparar features y target
        X = df_cleaned[ATTENDANCE_FEATURES]
        y = df_cleaned['total_asistentes']
        
        # Entrenar modelo
        logger.info("Entrenando modelo...")
        predictor = AttendancePredictor()
        metrics = predictor.train(X, y)
        
        logger.info(f"Métricas del modelo: {metrics}")
        
        # Guardar modelo
        logger.info("Guardando modelo...")
        predictor.save_model()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error en el entrenamiento: {str(e)}")
        raise e

if __name__ == "__main__":
    train_attendance_model() 