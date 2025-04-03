import pandas as pd
from sklearn.preprocessing import LabelEncoder
import numpy as np
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.label_encoders = {}
        
    def clean_attendance_data(self, df):
        """Limpia y prepara los datos para el modelo de predicción de asistencia"""
        df = df.copy()
        
        # Convertir fecha a datetime si no lo está
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Extraer características temporales
        df['mes'] = df['fecha'].dt.month
        df['dia_semana'] = df['fecha'].dt.dayofweek
        
        # Manejar valores nulos
        df['total_asistentes'] = df['total_asistentes'].fillna(0)
        
        # Codificar variables categóricas
        categorical_columns = [
            'departamento', 'municipio', 'zona_geografica',
            'categoria_actividad', 'grupo_interes'
        ]
        
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].fillna('DESCONOCIDO')
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
        
        return df
    
    def inverse_transform_predictions(self, X, y_pred):
        """Convierte las predicciones y features de nuevo a su forma original"""
        results = []
        
        for i, pred in enumerate(y_pred):
            row = {}
            for col in X.columns:
                if col in self.label_encoders:
                    original_value = self.label_encoders[col].inverse_transform([X[col].iloc[i]])[0]
                    row[col] = original_value
                else:
                    row[col] = X[col].iloc[i]
            row['predicted_attendance'] = int(max(0, round(pred)))
            results.append(row)
            
        return pd.DataFrame(results) 