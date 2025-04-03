import pandas as pd
class FeatureEngineer:
    def __init__(self):
        self.feature_columns = [
            # Features temporales
            'mes_del_año',
            'dia_semana',
            'semana_del_mes',
            'es_fin_semana',
            'es_festivo',
            
            # Features históricas
            'promedio_categoria',
            'mediana_categoria',
            'desviacion_categoria',
            'total_actividades_categoria',
            'promedio_mismo_mes',
            'promedio_mismo_dia',
            'promedio_movil_30',
            
            # Features de ratios
            'ratio_mes_actual',
            'ratio_dia_actual',
            'ratio_vs_promedio_dept',
            
            # Features categóricas (encoded)
            'departamento_encoded',
            'zona_geografica_encoded',
            'categoria_encoded'
        ]

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Crea features consistentes para entrenamiento y predicción"""
        df = data.copy()
        
        # Features temporales
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mes_del_año'] = df['fecha'].dt.month
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['semana_del_mes'] = df['fecha'].dt.day // 7
        df['es_fin_semana'] = df['fecha'].dt.dayofweek.isin([5, 6]).astype(int)
        
        # Calcular festivos (usando tu lógica actual de festivos)
        df['es_festivo'] = self._calcular_festivos(df['fecha'])
        
        # Features de ratios
        df['ratio_mes_actual'] = df['promedio_mismo_mes'] / df['promedio_categoria']
        df['ratio_dia_actual'] = df['promedio_mismo_dia'] / df['promedio_categoria']
        df['ratio_vs_promedio_dept'] = df['promedio_categoria'] / df['promedio_departamento']
        
        # Encoding de variables categóricas
        df = self._encode_categorical_features(df)
        
        return df[self.feature_columns]

    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encoding consistente de variables categóricas"""
        # Usar el mismo encoding en training y predicción
        categorical_mappings = {
            'departamento': self._get_departamento_mapping(),
            'zona_geografica': self._get_zona_mapping(),
            'categoria_unica': self._get_categoria_mapping()
        }
        
        for col, mapping in categorical_mappings.items():
            df[f'{col}_encoded'] = df[col].map(mapping)
        
        return df 