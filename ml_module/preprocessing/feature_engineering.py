import pandas as pd
import numpy as np
from datetime import datetime
import logging
from sklearn.preprocessing import LabelEncoder
from config import ATTENDANCE_FEATURES

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        self.label_encoders = {}
        self.historical_stats = {}
        
    def create_temporal_features(self, df):
        """Crea características basadas en tiempo"""
        df = df.copy()
        
        # Asegurar que fecha es datetime
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Features básicos de tiempo
        df['mes'] = df['fecha'].dt.month
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['dia_mes'] = df['fecha'].dt.day
        df['trimestre'] = df['fecha'].dt.quarter
        df['es_fin_semana'] = df['fecha'].dt.dayofweek.isin([5, 6]).astype(int)
        
        # Temporada del año
        df['temporada'] = pd.cut(
            df['fecha'].dt.month,
            bins=[0, 3, 6, 9, 12],
            labels=['Invierno', 'Primavera', 'Verano', 'Otoño']
        )
        
        # Días desde inicio del año
        df['dias_desde_inicio_ano'] = df['fecha'].dt.dayofyear
        
        return df
    
    def create_geographical_features(self, df):
        """Crea características basadas en ubicación"""
        df = df.copy()
        
        # Agrupar por departamento y municipio
        geo_stats = df.groupby(['departamento', 'municipio']).agg({
            'total_asistentes': ['mean', 'std', 'count'],
            'grupo_interes': 'nunique'
        }).reset_index()
        
        # Renombrar columnas
        geo_stats.columns = [
            'departamento', 'municipio', 
            'promedio_asistentes_local', 
            'std_asistentes_local',
            'total_actividades_local',
            'grupos_unicos_local'
        ]
        
        # Merge con el DataFrame original
        df = df.merge(
            geo_stats, 
            on=['departamento', 'municipio'], 
            how='left'
        )
        
        # Calcular ratios
        df['ratio_asistentes_vs_promedio'] = (
            df['total_asistentes'] / df['promedio_asistentes_local']
        )
        
        return df
    
    def create_categorical_features(self, df):
        """Procesa y codifica variables categóricas"""
        df = df.copy()
        
        # Encoding para variables categóricas
        categorical_cols = [
            'departamento', 'municipio', 'zona_geografica',
            'categoria_actividad', 'categoria_unica', 
            'grupo_interes', 'grupo_intervencion'
        ]
        
        for col in categorical_cols:
            if col in df.columns:
                # Crear label encoder si no existe
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    # Fit con todos los valores posibles
                    self.label_encoders[col].fit(df[col].fillna('DESCONOCIDO'))
                
                # Transform
                df[f'{col}_encoded'] = self.label_encoders[col].transform(
                    df[col].fillna('DESCONOCIDO')
                )
                
                # Crear features de conteo
                value_counts = df[col].value_counts()
                df[f'{col}_frequency'] = df[col].map(value_counts)
        
        return df
    
    def create_historical_features(self, df):
        """Crea características basadas en históricos"""
        df = df.copy()
        
        # Eliminar duplicados si existen
        duplicate_cols = df.columns[df.columns.duplicated()]
        df = df.loc[:, ~df.columns.duplicated()]
        
        if len(duplicate_cols) > 0:
            logger.warning(f"Se eliminaron columnas duplicadas: {duplicate_cols}")
        
        df = df.sort_values('fecha')
        
        # Calcular promedios móviles usando ventanas numéricas en lugar de fechas
        for group in ['departamento', 'municipio', 'categoria_unica']:
            # Promedio móvil de asistentes (últimos 30 registros)
            df[f'avg_asistentes_{group}_30'] = df.groupby(group)['total_asistentes'].transform(
                lambda x: x.rolling(window=30, min_periods=1).mean()
            )
            
            # Tendencia de asistentes (diferencia entre promedios)
            df[f'tendencia_{group}'] = df.groupby(group)['total_asistentes'].transform(
                lambda x: x.rolling(window=90, min_periods=1).mean() - 
                         x.rolling(window=30, min_periods=1).mean()
            )
            
            # Volatilidad de asistentes
            df[f'volatilidad_{group}'] = df.groupby(group)['total_asistentes'].transform(
                lambda x: x.rolling(window=30, min_periods=1).std()
            )
            
            # Agregar conteos acumulados
            df[f'actividades_acumuladas_{group}'] = df.groupby(group).cumcount() + 1
            
            # Calcular estadísticas acumuladas usando cummax y cummin
            df[f'max_asistentes_{group}'] = df.groupby(group)['total_asistentes'].transform('cummax')
            df[f'min_asistentes_{group}'] = df.groupby(group)['total_asistentes'].transform('cummin')
            
            # Agregar más estadísticas históricas
            df[f'total_actividades_{group}'] = df.groupby(group)['id'].transform('count')
            df[f'promedio_historico_{group}'] = df.groupby(group)['total_asistentes'].transform('mean')
            df[f'mediana_historica_{group}'] = df.groupby(group)['total_asistentes'].transform('median')
            
            # Calcular rankings
            df[f'ranking_asistentes_{group}'] = df.groupby(group)['total_asistentes'].transform(
                lambda x: x.rank(method='dense', ascending=False)
            )
            
            # Calcular percentiles
            df[f'percentil_asistentes_{group}'] = df.groupby(group)['total_asistentes'].transform(
                lambda x: x.rank(pct=True)
            )
        
        return df
    
    def create_interaction_features(self, df):
        """Crea características de interacción entre variables"""
        df = df.copy()
        
        # Interacciones entre características numéricas
        df['asistentes_por_actividad'] = (
            df['total_asistentes'] / df.groupby('categoria_unica')['total_asistentes'].transform('count')
        )
        
        # Ratio de asistentes por grupo de interés
        df['ratio_asistentes_grupo'] = (
            df['total_asistentes'] / df.groupby('grupo_interes')['total_asistentes'].transform('mean')
        )
        
        return df
    
    def transform(self, df):
        """Aplica todas las transformaciones de features"""
        logger.info("Iniciando feature engineering...")
        
        try:
            # Aplicar transformaciones en orden
            logger.info("Creando features temporales...")
            df = self.create_temporal_features(df)
            logger.info("Features temporales creados exitosamente")
            
            logger.info("Creando features geográficos...")
            df = self.create_geographical_features(df)
            logger.info("Features geográficos creados exitosamente")
            
            logger.info("Creando features categóricos...")
            df = self.create_categorical_features(df)
            logger.info("Features categóricos creados exitosamente")
            
            logger.info("Creando features históricos...")
            df = self.create_historical_features(df)
            logger.info("Features históricos creados exitosamente")
            
            logger.info("Creando features de interacción...")
            df = self.create_interaction_features(df)
            logger.info("Features de interacción creados exitosamente")
            
            logger.info("Limpiando valores nulos...")
            
            # Manejar valores nulos según el tipo de columna
            for column in df.columns:
                if pd.api.types.is_categorical_dtype(df[column]):
                    # Para columnas categóricas, primero agregar 'DESCONOCIDO' a las categorías
                    categories = df[column].cat.categories.tolist()
                    if 'DESCONOCIDO' not in categories:
                        df[column] = df[column].cat.add_categories('DESCONOCIDO')
                    df[column] = df[column].fillna('DESCONOCIDO')
                elif df[column].dtype == 'object':
                    # Para columnas de tipo objeto
                    df[column] = df[column].fillna('DESCONOCIDO')
                elif pd.api.types.is_numeric_dtype(df[column]):
                    # Para columnas numéricas
                    df[column] = df[column].fillna(0)
                elif pd.api.types.is_datetime64_any_dtype(df[column]):
                    # Para fechas
                    df[column] = df[column].fillna(df[column].min())
            
            logger.info(f"Feature engineering completado. Total de features generados: {len(df.columns)}")
            
            # Mostrar información sobre las features generadas
            numeric_features = df.select_dtypes(include=['int64', 'float64']).columns
            categorical_features = df.select_dtypes(include=['object', 'category']).columns
            
            logger.info(f"\nResumen de features:")
            logger.info(f"- Features numéricas: {len(numeric_features)}")
            logger.info(f"- Features categóricas: {len(categorical_features)}")
            logger.info(f"- Total features: {len(df.columns)}")
            
            # Mostrar algunas estadísticas básicas
            logger.info("\nEstadísticas de features numéricas:")
            stats = df[numeric_features].describe()
            logger.info(f"\n{stats}")
            
            # Mostrar distribución de categorías
            logger.info("\nDistribución de categorías en features categóricas:")
            for col in categorical_features[:5]:  # Mostrar solo las primeras 5 para no saturar el log
                value_counts = df[col].value_counts()
                logger.info(f"\n{col}:\n{value_counts.head()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error en feature engineering: {str(e)}")
            logger.error("Stack trace:", exc_info=True)
            raise 