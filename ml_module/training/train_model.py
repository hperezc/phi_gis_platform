import sys
import os
from pathlib import Path

# Ajustar el cálculo del directorio raíz
root_dir = Path(__file__).parent.parent  # Solo subimos dos niveles para llegar a ml_module
sys.path.append(str(root_dir))

import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import joblib
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Imports absolutos
from utils.data_loader import DataLoader
from preprocessing.feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.important_features = None
        
    def prepare_features(self, df):
        """Prepara las features para el modelo"""
        try:
            logger.info("Preparando features...")
            
            # Crear dummies para variables categóricas
            categorical_cols = ['departamento', 'zona_geografica', 'categoria_unica']
            df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
            
            # Seleccionar features numéricas relevantes
            numeric_features = [
                'mes', 'dia_semana', 'trimestre',
                'actividades_previas', 'promedio_asistentes_historico',
                'ratio_asistentes_vs_promedio', 'avg_asistentes_departamento_30',
                'tendencia_departamento', 'volatilidad_departamento'
            ]
            
            # Obtener columnas dummy generadas
            dummy_cols = [col for col in df_encoded.columns 
                         if any(x in col for x in categorical_cols)]
            
            # Combinar features
            selected_features = numeric_features + dummy_cols
            
            logger.info(f"Features seleccionadas: {len(selected_features)}")
            logger.info(f"Features numéricas: {len(numeric_features)}")
            logger.info(f"Features categóricas: {len(dummy_cols)}")
            
            # Escalar solo las features numéricas
            X = df_encoded[selected_features].copy()
            X[numeric_features] = self.scaler.fit_transform(X[numeric_features])
            
            # Guardar nombres de features para después
            self.feature_names = selected_features
            
            # Convertir a numpy array
            return X.values, selected_features
            
        except Exception as e:
            logger.error(f"Error en prepare_features: {str(e)}")
            logger.error("Columnas disponibles:", df.columns.tolist())
            raise
    
    def train(self, save_path='models'):
        """Entrena el modelo y guarda los resultados"""
        try:
            save_dir = Path(save_path)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar y preparar datos
            loader = DataLoader()
            df = loader.load_training_data()
            
            # Aplicar feature engineering
            df_features = self.feature_engineer.transform(df)
            
            # Preparar features finales
            X, feature_names = self.prepare_features(df_features)
            y = df_features['total_asistentes'].values
            
            # Split de datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Crear modelo base sin early stopping para cross validation
            base_model = xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.03,
                max_depth=4,
                min_child_weight=3,
                subsample=0.7,
                colsample_bytree=0.7,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42
            )
            
            # Realizar validación cruzada
            cv_scores = cross_val_score(base_model, X, y, cv=5, scoring='neg_root_mean_squared_error')
            
            # Ahora crear y entrenar el modelo final con early stopping
            self.model = xgb.XGBRegressor(
                n_estimators=150,          # Mantener en 150
                learning_rate=0.015,       # Mantener en 0.015
                max_depth=3,               # Mantener en 3
                min_child_weight=6,        # Mantener en 6
                subsample=0.6,             # Mantener en 0.6
                colsample_bytree=0.6,      # Mantener en 0.6
                reg_alpha=0.3,             # Mantener en 0.3
                reg_lambda=2.0,            # Volver a 2.0
                gamma=0.1,                 # Reducir a 0.1
                random_state=42,
                callbacks=[
                    xgb.callback.EarlyStopping(
                        rounds=25,          # Mantener en 25
                        metric_name='rmse',
                        save_best=True
                    )
                ]
            )
            
            # Entrenar modelo final
            eval_set = [(X_train, y_train), (X_test, y_test)]
            self.model.fit(
                X_train, 
                y_train,
                eval_set=eval_set,
                verbose=True
            )
            
            # Evaluar en conjunto de prueba
            y_pred = self.model.predict(X_test)
            
            # Corregir cálculo de MAPE para evitar división por cero
            def safe_mape(y_true, y_pred):
                mask = y_true != 0
                return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            
            metrics = {
                'rmse_train': float(np.sqrt(mean_squared_error(y_train, self.model.predict(X_train)))),
                'rmse_test': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                'mae_train': float(mean_absolute_error(y_train, self.model.predict(X_train))),
                'mae_test': float(mean_absolute_error(y_test, y_pred)),
                'r2_train': float(r2_score(y_train, self.model.predict(X_train))),
                'r2_test': float(r2_score(y_test, y_pred)),
                'cv_rmse_mean': float(-cv_scores.mean()),
                'cv_rmse_std': float(cv_scores.std()),
                'mape_test': float(safe_mape(y_test, y_pred))
            }
            
            # Calcular métricas por rango de manera correcta
            ranges = pd.qcut(y_test, q=5)
            range_metrics = pd.DataFrame({
                'real': y_test,
                'pred': y_pred,
                'error': np.abs(y_test - y_pred),
                'range': ranges
            })
            
            range_stats = range_metrics.groupby('range').agg({
                'error': ['mean', 'std', 'count'],
                'real': ['mean', 'min', 'max']
            }).round(4)
            
            # Convertir las estadísticas por rango a un formato serializable
            range_dict = {}
            for range_label in range_stats.index:
                range_dict[str(range_label)] = {
                    'error_mean': float(range_stats.loc[range_label, ('error', 'mean')]),
                    'error_std': float(range_stats.loc[range_label, ('error', 'std')]),
                    'count': int(range_stats.loc[range_label, ('error', 'count')]),
                    'real_mean': float(range_stats.loc[range_label, ('real', 'mean')]),
                    'real_min': float(range_stats.loc[range_label, ('real', 'min')]),
                    'real_max': float(range_stats.loc[range_label, ('real', 'max')])
                }
            
            metrics['range_metrics'] = range_dict
            
            # Guardar lista de features
            feature_list_path = save_dir / 'feature_list.json'
            with open(feature_list_path, 'w') as f:
                json.dump(feature_names, f)
            
            # Guardar mappings categóricos
            self.save_category_mappings(df_features)
            
            # Guardar importancia de features
            importance = pd.DataFrame({
                'feature': feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # Guardar resultados
            logger.info("Guardando resultados...")
            model_path = save_dir / 'attendance_predictor.joblib'
            metrics_path = save_dir / 'model_metrics.json'
            importance_path = save_dir / 'feature_importance.csv'
            
            joblib.dump(self.model, model_path)
            importance.to_csv(importance_path, index=False)
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            # Visualizar importancia de features
            plt.figure(figsize=(12, 6))
            sns.barplot(data=importance.head(20), x='importance', y='feature')
            plt.title('Top 20 Features más Importantes')
            plt.tight_layout()
            plt.savefig(save_dir / 'feature_importance.png')
            
            # Guardar información adicional
            model_info = {
                'feature_names': feature_names,
                'n_features': len(feature_names),
                'categorical_columns': ['departamento', 'zona_geografica', 'categoria_unica'],
                'numeric_columns': [col for col in feature_names if col not in ['departamento', 'zona_geografica', 'categoria_unica']]
            }
            
            with open(save_dir / 'model_info.json', 'w') as f:
                json.dump(model_info, f, indent=2)
            
            # Realizar validación adicional
            self.validate_predictions(X_test, y_test)
            
            logger.info("Entrenamiento completado exitosamente!")
            logger.info("\nMétricas del modelo:")
            for metric, value in metrics.items():
                # Manejar el caso especial de range_metrics que es un diccionario
                if metric == 'range_metrics':
                    logger.info(f"{metric}: <dict>")
                else:
                    logger.info(f"{metric}: {value:.4f}")
            
            return metrics, importance
            
        except Exception as e:
            logger.error(f"Error en entrenamiento: {str(e)}")
            raise

    def save_category_mappings(self, df):
        """Guarda los mappings de categorías"""
        category_mappings = {}
        for col in ['departamento', 'zona_geografica', 'categoria_unica']:
            le = LabelEncoder()
            le.fit(df[col].unique())
            category_mappings[col] = dict(zip(le.classes_, le.transform(le.classes_)))
        
        joblib.dump(category_mappings, root_dir / 'models' / 'category_mappings.joblib')
        logger.info("Mappings categóricos guardados exitosamente")

    def validate_predictions(self, X_test, y_test):
        """Validación adicional de las predicciones"""
        y_pred = self.model.predict(X_test)
        
        # Análisis por rangos
        ranges = pd.qcut(y_test, q=5)
        errors_by_range = pd.DataFrame({
            'real': y_test,
            'pred': y_pred,
            'error': np.abs(y_test - y_pred),
            'range': ranges
        })
        
        # Calcular error porcentual evitando división por cero
        errors_by_range['error_pct'] = np.where(
            y_test != 0,
            np.abs((y_test - y_pred) / y_test) * 100,
            0  # o algún otro valor por defecto para cuando y_test es 0
        )
        
        # Estadísticas por rango
        range_stats = errors_by_range.groupby('range', observed=True).agg({
            'error': ['mean', 'std', 'count', 'max'],
            'error_pct': ['mean', 'median'],
            'real': ['mean', 'min', 'max']
        })
        
        logger.info("\nEstadísticas detalladas por rango:")
        logger.info(range_stats)
        
        # Análisis de outliers
        z_scores = np.abs((y_pred - y_test.mean()) / y_test.std())
        outliers = (z_scores > 2).sum()
        logger.info(f"\nPredicciones atípicas:")
        logger.info(f"- |z| > 2: {outliers} ({outliers/len(y_test)*100:.1f}%)")
        logger.info(f"- Error máximo: {errors_by_range['error'].max():.2f}")
        logger.info(f"- Error porcentual máximo: {errors_by_range['error_pct'].max():.1f}%")

if __name__ == "__main__":
    trainer = ModelTrainer()
    metrics, importance = trainer.train() 