import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import pmdarima as pm
from prophet import Prophet
import joblib
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemporalTrainer:
    def __init__(self):
        self.data_loader = DataLoader()
        self.models = {}
        self.metrics = {}
        
    def prepare_temporal_data(self):
        """Prepara los datos temporales para el entrenamiento"""
        try:
            query = """
                WITH date_range AS (
                    SELECT generate_series(
                        date_trunc('month', min(fecha)),
                        date_trunc('month', max(fecha)),
                        '1 month'::interval
                    ) as fecha
                    FROM actividades
                ),
                base_data AS (
                    SELECT 
                        date_trunc('month', fecha) as fecha,
                        departamento,
                        municipio,
                        zona_geografica,
                        categoria_unica,
                        COUNT(*) as total_actividades,
                        SUM(total_asistentes) as total_asistentes,
                        COUNT(DISTINCT EXTRACT(DAY FROM fecha)) as dias_con_actividades
                    FROM actividades
                    WHERE fecha IS NOT NULL
                        AND fecha >= '2014-01-01'
                        AND fecha <= CURRENT_DATE
                    GROUP BY 
                        date_trunc('month', fecha),
                        departamento,
                        municipio,
                        zona_geografica,
                        categoria_unica
                ),
                filled_data AS (
                    SELECT 
                        dr.fecha,
                        bd.departamento,
                        bd.municipio,
                        bd.zona_geografica,
                        bd.categoria_unica,
                        COALESCE(bd.total_actividades, 0) as total_actividades,
                        COALESCE(bd.total_asistentes, 0) as total_asistentes,
                        COALESCE(bd.dias_con_actividades, 0) as dias_con_actividades,
                        -- Agregar promedio móvil para suavizar series con pocos datos
                        AVG(bd.total_actividades) OVER (
                            ORDER BY dr.fecha 
                            ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING
                        ) as actividades_suavizadas
                    FROM date_range dr
                    CROSS JOIN (
                        SELECT DISTINCT 
                            departamento, municipio, zona_geografica, categoria_unica 
                        FROM base_data
                    ) cats
                    LEFT JOIN base_data bd 
                        ON dr.fecha = bd.fecha
                        AND cats.departamento = bd.departamento
                        AND cats.municipio = bd.municipio
                        AND cats.zona_geografica = bd.zona_geografica
                        AND cats.categoria_unica = bd.categoria_unica
                )
                SELECT 
                    fecha,
                    departamento,
                    municipio,
                    zona_geografica,
                    categoria_unica,
                    total_actividades,
                    total_asistentes,
                    dias_con_actividades,
                    actividades_suavizadas,
                    COUNT(*) OVER (
                        PARTITION BY departamento, municipio
                    ) as registros_municipio,
                    COUNT(*) OVER (
                        PARTITION BY departamento
                    ) as registros_departamento,
                    AVG(total_actividades) OVER (
                        PARTITION BY departamento, municipio
                        ORDER BY fecha
                        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
                    ) as promedio_movil_actividades
                FROM filled_data
                ORDER BY fecha, departamento, municipio
            """
            
            df = pd.read_sql(query, self.data_loader.engine)
            logger.info(f"Total de registros en la base: {len(df)}")
            
            # Convertir fecha a datetime y crear features temporales
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['año'] = df['fecha'].dt.year
            df['mes'] = df['fecha'].dt.month
            df['trimestre'] = df['fecha'].dt.quarter
            df['dia_semana'] = df['fecha'].dt.dayofweek
            
            # Agregar features adicionales
            df['es_temporada_alta'] = df['mes'].isin([3,4,9,10]).astype(int)  # Meses típicamente con más actividad
            df['dias_actividad_ratio'] = df['dias_con_actividades'] / 30  # Ratio de días con actividades
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparando datos temporales: {str(e)}")
            raise

    def train_sarima_models(self, df):
        """Entrena modelos SARIMA con parámetros optimizados"""
        try:
            aggregation_levels = [
                ['departamento'],
                ['departamento', 'municipio'],
                ['zona_geografica'],
                ['categoria_unica']
            ]
            
            for level in aggregation_levels:
                logger.info(f"Entrenando modelos SARIMA para nivel: {level}")
                
                grouped = df.groupby(level + ['fecha'])['total_actividades'].sum().reset_index()
                
                for name, group in grouped.groupby(level):
                    ts = group.set_index('fecha')['total_actividades']
                    ts = ts.resample('ME').sum()
                    
                    # Verificar suficientes datos y variabilidad
                    if len(ts) < 24 or ts.std() < 0.1:
                        logger.warning(f"Serie insuficiente o sin variabilidad para {name}")
                        continue
                    
                    try:
                        # Aplicar transformación para estabilizar varianza
                        ts_transformed = np.sqrt(ts + 1)  # Transformación raíz cuadrada
                        
                        # Entrenar modelo con parámetros más robustos
                        model = pm.auto_arima(
                            ts_transformed,
                            start_p=1,
                            start_q=1,
                            max_p=3,
                            max_q=3,
                            m=12,  # Mantener estacionalidad anual
                            seasonal=True,
                            d=1,
                            D=1,
                            stepwise=True,
                            suppress_warnings=True,
                            error_action="ignore",
                            max_order=5,
                            information_criterion='aic',
                            random_state=42
                        )
                        
                        # Validación cruzada temporal
                        cv_scores = self._temporal_cross_validation(ts_transformed, model)
                        
                        if cv_scores['rmse_mean'] < np.inf:
                            key = '_'.join(level + [str(n) for n in name if n is not None])
                            self.models[f'sarima_{key}'] = model
                            self.metrics[f'sarima_{key}'] = cv_scores
                        
                    except Exception as e:
                        logger.warning(f"Error en modelo SARIMA para {name}: {str(e)}")
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelos SARIMA: {str(e)}")
            raise

    def train_prophet_models(self, df):
        """Entrena modelos Prophet con configuración optimizada y simplificada"""
        try:
            aggregation_levels = [
                ['departamento'],
                ['departamento', 'municipio'],
                ['zona_geografica'],
                ['categoria_unica']
            ]
            
            for level in aggregation_levels:
                logger.info(f"Entrenando modelos Prophet para nivel: {level}")
                
                # Agregar datos por nivel y fecha
                grouped = df.groupby(level + ['fecha'])[['total_actividades', 'total_asistentes']].agg({
                    'total_actividades': 'sum',
                    'total_asistentes': 'sum'
                }).reset_index()
                
                for name, group in grouped.groupby(level):
                    # Preparar datos para Prophet y eliminar timezone
                    prophet_df = pd.DataFrame({
                        'ds': group['fecha'].dt.tz_localize(None),  # Eliminar timezone
                        'y': group['total_actividades'],
                        'asistentes': group['total_asistentes']
                    })
                    
                    # Requerir al menos 6 meses de datos
                    if len(prophet_df) < 6:
                        logger.warning(f"Serie insuficiente para {name}: {len(prophet_df)} meses")
                        continue
                    
                    try:
                        # Configuración simplificada de Prophet
                        model = Prophet(
                            yearly_seasonality=True,
                            weekly_seasonality=False,
                            daily_seasonality=False,
                            seasonality_mode='multiplicative',
                            changepoint_prior_scale=0.05,
                            seasonality_prior_scale=10.0,
                            interval_width=0.95
                        )
                        
                        # Agregar estacionalidad mensual
                        model.add_seasonality(
                            name='monthly',
                            period=30.5,
                            fourier_order=5
                        )
                        
                        # Agregar regresores si hay suficientes datos
                        if len(prophet_df) >= 12:
                            prophet_df['asistentes_ratio'] = prophet_df['asistentes'] / prophet_df['y'].mean()
                            model.add_regressor('asistentes_ratio', standardize=True)
                        
                        # Entrenar modelo
                        model.fit(prophet_df)
                        
                        # Realizar validación cruzada
                        cv_metrics = self._prophet_cross_validation(
                            model, 
                            prophet_df,
                            horizon='60 days',
                            parallel='processes'
                        )
                        
                        # Guardar solo si las métricas son razonables
                        if cv_metrics['rmse'] < np.inf and cv_metrics['mae'] < np.inf:
                            key = '_'.join(level + [str(n) for n in name if n is not None])
                            self.models[f'prophet_{key}'] = model
                            self.metrics[f'prophet_{key}'] = cv_metrics
                            
                            logger.info(f"Modelo Prophet exitoso para {name} - RMSE: {cv_metrics['rmse']:.2f}")
                        
                    except Exception as e:
                        logger.warning(f"Error en modelo Prophet para {name}: {str(e)}")
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelos Prophet: {str(e)}")
            raise

    def _temporal_cross_validation(self, ts, model, n_splits=3):
        """Realiza validación cruzada temporal"""
        errors = []
        n = len(ts)
        fold_size = n // n_splits
        
        for i in range(n_splits):
            start_idx = i * fold_size
            end_idx = start_idx + fold_size
            
            if end_idx > n:
                break
            
            train = ts[:end_idx]
            test = ts[end_idx:end_idx + fold_size]
            
            if len(test) == 0:
                continue
            
            try:
                # Reentrenar modelo en datos de entrenamiento
                model_fold = model.fit(train)
                
                # Predecir y calcular error
                pred = model_fold.predict(n_periods=len(test))
                mse = np.mean((test - pred) ** 2)
                rmse = np.sqrt(mse)
                mae = np.mean(np.abs(test - pred))
                
                errors.append({
                    'mse': mse,
                    'rmse': rmse,
                    'mae': mae
                })
                
            except Exception as e:
                logger.warning(f"Error en fold {i}: {str(e)}")
                continue
        
        if not errors:
            return {
                'mse_mean': np.inf,
                'rmse_mean': np.inf,
                'mae_mean': np.inf,
                'n_observations': len(ts)
            }
        
        return {
            'mse_mean': np.mean([e['mse'] for e in errors]),
            'rmse_mean': np.mean([e['rmse'] for e in errors]),
            'mae_mean': np.mean([e['mae'] for e in errors]),
            'n_observations': len(ts)
        }

    def _prophet_cross_validation(self, model, df, horizon='60 days', parallel='processes'):
        """Realiza validación cruzada para Prophet con manejo de errores mejorado"""
        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            
            # Parámetros de validación cruzada
            initial = '180 days'
            period = '30 days'
            
            # Realizar validación cruzada con manejo de errores
            try:
                cv_results = cross_validation(
                    model,
                    initial=initial,
                    period=period,
                    horizon=horizon,
                    parallel=parallel
                )
                
                # Calcular métricas
                metrics = performance_metrics(cv_results)
                
                return {
                    'mse': float(metrics['mse'].mean()),
                    'rmse': float(np.sqrt(metrics['mse'].mean())),
                    'mae': float(metrics['mae'].mean()),
                    'coverage': float(metrics['coverage'].mean()),
                    'n_forecasts': len(cv_results)
                }
                
            except Exception as e:
                logger.warning(f"Error en validación cruzada: {str(e)}")
                # Realizar validación manual si la automática falla
                return self._manual_prophet_validation(model, df)
                
        except Exception as e:
            logger.warning(f"Error en _prophet_cross_validation: {str(e)}")
            return {
                'mse': np.inf,
                'rmse': np.inf,
                'mae': np.inf,
                'coverage': 0.0,
                'n_forecasts': 0
            }

    def _manual_prophet_validation(self, model, df):
        """Realiza validación manual cuando la validación cruzada automática falla"""
        try:
            # Usar últimos 60 días como conjunto de prueba
            train_df = df[:-2].copy()
            test_df = df[-2:].copy()
            
            # Reentrenar modelo en datos de entrenamiento
            model_cv = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='multiplicative'
            )
            
            model_cv.fit(train_df)
            
            # Predecir en conjunto de prueba
            future = model_cv.make_future_dataframe(periods=2, freq='M')
            forecast = model_cv.predict(future)
            
            # Calcular métricas
            y_true = test_df['y'].values
            y_pred = forecast['yhat'].tail(2).values
            
            mse = np.mean((y_true - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_true - y_pred))
            
            return {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'coverage': 0.95,  # Valor por defecto
                'n_forecasts': 2
            }
            
        except Exception as e:
            logger.warning(f"Error en validación manual: {str(e)}")
            return {
                'mse': np.inf,
                'rmse': np.inf,
                'mae': np.inf,
                'coverage': 0.0,
                'n_forecasts': 0
            }

    def save_models(self, save_path='models/temporal_models'):
        """Guarda los modelos entrenados y sus métricas"""
        try:
            save_dir = Path(root_dir) / save_path
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar modelos
            for name, model in self.models.items():
                try:
                    model_path = save_dir / f'{name}.joblib'
                    joblib.dump(model, model_path)
                    logger.info(f"Modelo guardado: {name}")
                except Exception as e:
                    logger.error(f"Error guardando modelo {name}: {str(e)}")
            
            # Guardar métricas
            metrics_path = save_dir / 'model_metrics.json'
            with open(metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            logger.info(f"Modelos y métricas guardados en {save_dir}")
            
        except Exception as e:
            logger.error(f"Error guardando modelos: {str(e)}")
            raise

    def train(self):
        """Proceso principal de entrenamiento"""
        try:
            logger.info("Iniciando entrenamiento de modelos temporales...")
            
            # Preparar datos
            df = self.prepare_temporal_data()
            logger.info(f"Datos preparados: {len(df)} registros")
            
            # Entrenar modelos SARIMA
            logger.info("Entrenando modelos SARIMA...")
            self.train_sarima_models(df)
            
            # Entrenar modelos Prophet
            logger.info("Entrenando modelos Prophet...")
            self.train_prophet_models(df)
            
            # Guardar modelos
            logger.info("Guardando modelos...")
            self.save_models()
            
            logger.info("Entrenamiento completado exitosamente!")
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error en entrenamiento: {str(e)}")
            raise

if __name__ == "__main__":
    trainer = TemporalTrainer()
    metrics = trainer.train()
    print("Métricas de entrenamiento:", metrics) 