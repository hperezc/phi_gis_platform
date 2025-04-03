import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import numpy as np
from ..config import MODEL_CONFIG, MODELS_DIR

class AttendancePredictor:
    def __init__(self):
        self.model = None
        self.config = MODEL_CONFIG['attendance_predictor']
        
    def train(self, X, y):
        """Entrena el modelo de predicción de asistencia"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model = xgb.XGBRegressor(**self.config['params'])
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=10,
            verbose=True
        )
        
        # Evaluar el modelo
        y_pred = self.model.predict(X_test)
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred)
        }
        
        return metrics
    
    def predict(self, X):
        """Realiza predicciones de asistencia"""
        if self.model is None:
            raise ValueError("El modelo debe ser entrenado primero")
        
        return self.model.predict(X)
    
    def save_model(self, filename='attendance_predictor.joblib'):
        """Guarda el modelo entrenado"""
        if self.model is None:
            raise ValueError("No hay modelo para guardar")
            
        path = MODELS_DIR / filename
        joblib.dump(self.model, path)
        
    def load_model(self, filename='attendance_predictor.joblib'):
        """Carga un modelo guardado"""
        path = MODELS_DIR / filename
        self.model = joblib.load(path) 