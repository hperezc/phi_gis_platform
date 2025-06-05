import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy import stats

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemporalPredictor:
    def __init__(self, models_path='models/temporal_models'):
        """Inicializa el predictor cargando los modelos entrenados"""
        self.data_loader = DataLoader()
        self.models_path = Path(root_dir) / models_path
        self.models = {}
        self.metrics = {}
        self.load_models()
        
    def load_models(self):
        """Carga los modelos guardados y sus métricas"""
        try:
            # Cargar modelos
            for model_path in self.models_path.glob('*.joblib'):
                if model_path.stem != 'category_mappings' and model_path.stem != 'model_metrics':
                    try:
                        model = joblib.load(model_path)
                        if hasattr(model, 'predict'):  # Verificar que sea un modelo válido
                            self.models[model_path.stem] = model
                            logger.info(f"Modelo cargado: {model_path.stem}")
                        else:
                            logger.warning(f"Archivo no es un modelo válido: {model_path.stem}")
                    except Exception as e:
                        logger.error(f"Error cargando modelo {model_path.stem}: {str(e)}")
            
            # Cargar métricas
            metrics_path = self.models_path / 'model_metrics.json'
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    self.metrics = json.load(f)
            
            logger.info(f"Modelos cargados exitosamente: {len(self.models)}")
            logger.info(f"Modelos disponibles: {list(self.models.keys())}")
            
        except Exception as e:
            logger.error(f"Error cargando modelos: {str(e)}")
            logger.exception("Traceback completo:")
            raise

    def predict(self, input_data: dict) -> dict:
        """Realiza predicciones usando los modelos más apropiados"""
        try:
            logger.info(f"Iniciando predicción con datos: {input_data}")
            
            # Obtener datos históricos
            historical_data = self._get_historical_data(input_data)
            logger.info(f"Datos históricos obtenidos: {len(historical_data.get('dates', []))} registros")
            
            if historical_data.get('empty', True):
                logger.warning("No hay datos históricos disponibles")
                return {
                    'predicciones': None,
                    'grafico': self._create_empty_plot(input_data),
                    'metricas': {
                        'Estado': 'Sin datos históricos',
                        'Mensaje': 'No hay suficientes datos para realizar predicciones'
                    },
                    'historical_data': historical_data
                }
            
            # Seleccionar el mejor modelo disponible
            model_key = self._get_best_model_key(input_data)
            logger.info(f"Modelo seleccionado: {model_key}")
            
            if not model_key:
                raise ValueError("No se encontró un modelo adecuado para la predicción")
            
            # Calcular meses adicionales necesarios para llegar a la fecha actual
            last_historical_date = pd.to_datetime(historical_data['dates'][-1])
            # Obtener el primer día del mes actual de manera más robusta
            now = datetime.now()
            current_date = pd.Timestamp(year=now.year, month=now.month, day=1)
            
            months_to_current = max(0, ((current_date.year - last_historical_date.year) * 12 + 
                                      current_date.month - last_historical_date.month))
                       
            # Ajustar el período de predicción para incluir la fecha actual + período solicitado
            adjusted_period = months_to_current + input_data['periodo']
            logger.info(f"Período ajustado: {adjusted_period} meses (incluyendo {months_to_current} meses hasta fecha actual)")
            
            # Realizar predicción según el tipo de modelo
            if 'sarima' in model_key:
                predictions = self._predict_sarima(model_key, adjusted_period)
            else:  # prophet
                predictions = self._predict_prophet(model_key, adjusted_period)
            
            logger.info(f"Predicciones generadas: {len(predictions.get('values', []))} valores")
            
            # Guardar información sobre la predicción para usarla en visualización
            predictions['months_to_current'] = months_to_current
            
            # Calcular métricas adicionales
            stats = self._calculate_enhanced_statistics(historical_data, predictions)
            
            # Crear visualización mejorada
            fig = self._create_enhanced_forecast_plot(historical_data, predictions, input_data)
            
            # Agregar nuevos análisis
            pattern_analysis = self._create_pattern_analysis_plot(historical_data)
            performance_metrics = self._calculate_performance_metrics(historical_data)
            
            return {
                'predicciones': predictions,
                'grafico': fig,
                'grafico_patrones': pattern_analysis,
                'metricas': stats,
                'metricas_desempeno': performance_metrics,
                'historical_data': historical_data
            }
            
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            logger.exception("Traceback completo:")
            return self._handle_prediction_error(str(e))

    def _get_best_model_key(self, input_data: dict) -> str:
        """Selecciona el mejor modelo con validación mejorada"""
        try:
            errors = {}
            for model_key in self.models:
                if self._is_applicable_model(model_key, input_data):
                    try:
                        # Obtener predicciones de prueba
                        error_metrics = self._calculate_model_error(model_key, input_data)
                        predictions = self._predict_sarima(model_key, 6) if 'sarima' in model_key else self._predict_prophet(model_key, 6)
                        
                        # Validar coherencia de las predicciones
                        historical_data = self._get_historical_data(input_data)
                        if self._validate_predictions(predictions, historical_data):
                            errors[model_key] = error_metrics['rmse']
                    except Exception as e:
                        logger.warning(f"Error evaluando modelo {model_key}: {str(e)}")
                        continue
            
            if errors:
                return min(errors.items(), key=lambda x: x[1])[0]
            
            return self._get_fallback_model(input_data)
            
        except Exception as e:
            logger.error(f"Error seleccionando modelo: {str(e)}")
            return None

    def _get_historical_data(self, input_data: dict):
        """Obtiene datos históricos con filtros mejorados"""
        try:
            # Construir filtros dinámicamente
            filters = {'departamento': input_data['departamento']}
            municipio_filter = ""
            categoria_filter = ""
            
            if input_data.get('municipio'):
                municipio_filter = "AND municipio = :municipio"
                filters['municipio'] = input_data['municipio']
                
            if input_data.get('categoria'):
                categoria_filter = "AND categoria_unica = :categoria"
                filters['categoria'] = input_data['categoria']

            # Construir la consulta con los filtros
            query = f"""
                WITH monthly_data AS (
                    SELECT
                        date_trunc('month', fecha)::date as fecha,
                        COUNT(*) as total_actividades,
                        SUM(total_asistentes) as total_asistentes,
                        COUNT(DISTINCT EXTRACT(DAY FROM fecha)) as dias_actividad
                    FROM actividades
                    WHERE fecha IS NOT NULL
                    AND departamento = :departamento
                    {municipio_filter}
                    {categoria_filter}
                    GROUP BY date_trunc('month', fecha)::date
                )
                SELECT
                    fecha as ds,
                    total_actividades as y,
                    total_asistentes,
                    dias_actividad,
                    total_asistentes::float / NULLIF(total_actividades, 0) as asistentes_ratio
                FROM monthly_data
                ORDER BY fecha
            """
            
            logger.info(f"Ejecutando consulta: {query}")
            logger.info(f"Parámetros: {filters}")
            
            with self.data_loader.engine.connect() as conn:
                from sqlalchemy import text
                
                result = conn.execute(text(query), filters)
                df = pd.DataFrame(result.fetchall(), columns=['fecha', 'total_actividades', 'total_asistentes', 'dias_actividad', 'asistentes_ratio'])
                
                if df.empty:
                    logger.warning("No se encontraron datos históricos")
                    return {'dates': [], 'activities': [], 'empty': True}
                
                # Convertir explícitamente la columna fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])
                
                logger.info(f"Datos obtenidos: {len(df)} registros")
                logger.info(f"Rango de fechas: {df['fecha'].min()} - {df['fecha'].max()}")
                logger.info(f"Total actividades: {df['total_actividades'].sum()}")
                
                return {
                    'dates': df['fecha'].tolist(),
                    'activities': df['total_actividades'].tolist(),
                    'empty': False,
                    'asistentes': df['total_asistentes'].tolist(),
                    'dias_actividad': df['dias_actividad'].tolist(),
                    'asistentes_ratio': df['asistentes_ratio'].tolist()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {str(e)}")
            logger.exception("Traceback completo:")
            return {'dates': [], 'activities': [], 'empty': True}

    def _predict_sarima(self, model_key: str, periods: int) -> dict:
        """Realiza predicción con modelo SARIMA"""
        try:
            if model_key not in self.models:
                raise ValueError(f"Modelo no encontrado: {model_key}")
            
            model = self.models[model_key]
            if not hasattr(model, 'predict'):
                raise ValueError(f"Modelo inválido para {model_key}: no tiene método predict")
            
            # Realizar predicción
            forecast, conf_int = model.predict(n_periods=periods, return_conf_int=True)
            
            # Ajustar intervalos según la distribución de errores históricos
            residuals = model.resid()
            error_std = np.std(residuals)
            
            logger.info(f"Predicción SARIMA exitosa para {model_key}")
            logger.info(f"Valores predichos: {forecast.tolist()}")
            
            return {
                'values': forecast.tolist(),
                'lower': (forecast - 1.96 * error_std).tolist(),
                'upper': (forecast + 1.96 * error_std).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error en predicción SARIMA para {model_key}: {str(e)}")
            logger.exception("Traceback completo:")
            raise

    def _predict_prophet(self, model_key: str, periods: int) -> dict:
        """Realiza predicción usando modelo Prophet con todas las variables requeridas"""
        try:
            future = self.models[model_key].make_future_dataframe(
                periods=periods, 
                freq='ME'  # Cambiar 'M' a 'ME' para evitar el warning
            )
            
            # Agregar todas las variables requeridas
            future['asistentes_ratio'] = future['ds'].map(lambda x: 30)
            future['intensidad_actividad'] = future['ds'].map(lambda x: 1)
            future['es_temporada_alta'] = future['ds'].map(
                lambda x: 1 if x.month in [3,4,9,10] else 0
            )
            
            forecast = self.models[model_key].predict(future)
            
            # Aplicar transformaciones inversas si es necesario
            predictions = forecast['yhat'][-periods:].clip(0)  # No permitir valores negativos
            
            return {
                'values': predictions.tolist(),
                'lower': forecast['yhat_lower'][-periods:].clip(0).tolist(),
                'upper': forecast['yhat_upper'][-periods:].tolist()
            }
        except Exception as e:
            logger.error(f"Error en predicción Prophet: {str(e)}")
            raise

    def _create_forecast_plot(self, historical_data: dict, predictions: dict, input_data: dict) -> go.Figure:
        """Crea visualización de predicciones"""
        try:
            fig = go.Figure()
            
            # Convertir fechas históricas a datetime
            historical_dates = pd.to_datetime(historical_data['dates'])
            
            # Datos históricos
            fig.add_trace(go.Scatter(
                x=historical_dates,
                y=historical_data['activities'],
                name='Histórico',
                line=dict(color='blue')
            ))
            
            if predictions and 'values' in predictions:
                # Predicciones
                future_dates = pd.date_range(
                    start=historical_dates[-1],
                    periods=len(predictions['values']) + 1,
                    freq='M'
                )[1:]
                
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=predictions['values'],
                    name='Predicción',
                    line=dict(color='red', dash='dash')
                ))
                
                # Intervalo de confianza
                if 'lower' in predictions and 'upper' in predictions:
                    fig.add_trace(go.Scatter(
                        x=future_dates.tolist() + future_dates.tolist()[::-1],
                        y=predictions['lower'] + predictions['upper'][::-1],
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        line=dict(color='rgba(255,0,0,0)'),
                        name='Intervalo de Confianza'
                    ))
            
            # Actualizar layout
            fig.update_layout(
                title=f"Pronóstico de Actividades - {input_data['departamento']}, {input_data.get('municipio', 'Todos los municipios')}",
                xaxis_title='Fecha',
                yaxis_title='Número de Actividades',
                template='plotly_dark',
                height=500,
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creando gráfico: {str(e)}")
            logger.exception("Traceback completo:")
            return self._create_error_plot(str(e))

    def _calculate_statistics(self, historical_data: dict, predictions: dict) -> dict:
        """Calcula estadísticas y métricas de la predicción"""
        try:
            historical_values = np.array(historical_data['activities'])
            predicted_values = np.array(predictions['values'])
            
            stats = {
                'Promedio histórico': np.mean(historical_values),
                'Máximo histórico': np.max(historical_values),
                'Mínimo histórico': np.min(historical_values),
                'Tendencia': np.polyfit(range(len(historical_values)), historical_values, 1)[0],
                'Predicción promedio': np.mean(predicted_values),
                'Predicción máxima': np.max(predicted_values),
                'Predicción mínima': np.min(predicted_values),
                'Intervalo de confianza': f"{np.mean(predictions['lower']):.1f} - {np.mean(predictions['upper']):.1f}"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            raise

    def _create_empty_plot(self, input_data: dict) -> go.Figure:
        """Crea un gráfico vacío con mensaje informativo"""
        fig = go.Figure()
        
        fig.add_annotation(
            text="No hay datos históricos disponibles para los filtros seleccionados",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        fig.update_layout(
            title=f"Sin datos - {input_data['departamento']}, {input_data.get('municipio', 'Todos los municipios')}",
            xaxis_title='Fecha',
            yaxis_title='Número de Actividades',
            template='plotly_dark',
            height=500
        )
        
        return fig

    def _create_error_plot(self, error_message: str) -> go.Figure:
        """Crea un gráfico de error"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=f"Error: {error_message}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color='red')
        )
        
        fig.update_layout(
            title="Error en la predicción",
            template='plotly_dark',
            height=500
        )
        
        return fig

    def _calculate_enhanced_statistics(self, historical_data: dict, predictions: dict) -> dict:
        """Calcula estadísticas mejoradas de la predicción"""
        try:
            historical_values = np.array(historical_data['activities'])
            
            # Usar solo predicciones futuras
            months_to_current = predictions.get('months_to_current', 0)
            if months_to_current < len(predictions['values']):
                predicted_values = np.array(predictions['values'][months_to_current:])
                lower_values = np.array(predictions['lower'][months_to_current:]) if 'lower' in predictions else None
                upper_values = np.array(predictions['upper'][months_to_current:]) if 'upper' in predictions else None
            else:
                # No hay predicciones futuras
                predicted_values = np.array([])
                lower_values = upper_values = None
            
            # Calcular tendencia
            x = np.arange(len(historical_values))
            z = np.polyfit(x, historical_values, 1)
            tendencia = z[0]
            
            # Calcular estacionalidad solo si hay suficientes datos
            if len(historical_values) >= 24:
                try:
                    seasonal = seasonal_decompose(historical_values, period=12)
                    estacionalidad = seasonal.seasonal.std()
                    estacionalidad_desc = f"{'Alta' if estacionalidad > 1 else 'Baja'} ({estacionalidad:.2f})"
                except Exception:
                    estacionalidad_desc = "No calculable (se requieren 24 meses)"
            else:
                estacionalidad_desc = "No calculable (datos insuficientes)"
            
            # Calcular variabilidad mensual
            variabilidad = np.std(historical_values) / np.mean(historical_values) if len(historical_values) > 0 else 0
            
            # Información sobre las predicciones futuras
            if len(predicted_values) > 0:
                prediccion_promedio = f"{float(np.mean(predicted_values)):.2f} actividades/mes"
                confiabilidad = f"{min(95, 100 * (1 - np.std(predicted_values)/np.mean(predicted_values))):.1f}%" if np.mean(predicted_values) > 0 else "N/A"
                
                if lower_values is not None and upper_values is not None:
                    rango_prediccion = f"{np.min(lower_values):.1f} - {np.max(upper_values):.1f}"
                else:
                    rango_prediccion = "No disponible"
            else:
                prediccion_promedio = "No hay predicciones futuras"
                confiabilidad = "N/A"
                rango_prediccion = "N/A"
            
            stats = {
                'Promedio histórico': f"{float(np.mean(historical_values)):.2f} actividades/mes",
                'Tendencia': f"{'Creciente' if tendencia > 0 else 'Decreciente'} ({abs(tendencia):.2f}/mes)",
                'Estacionalidad': estacionalidad_desc,
                'Variabilidad mensual': f"{variabilidad * 100:.1f}%",
                'Predicción promedio': prediccion_promedio,
                'Confiabilidad': confiabilidad,
                'Rango de predicción': rango_prediccion
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            return {
                'Estado': 'Error en cálculos',
                'Mensaje': 'No se pudieron calcular todas las estadísticas',
                'Promedio histórico': f"{float(np.mean(historical_values)):.2f} actividades/mes" if len(historical_values) > 0 else "N/A",
                'Predicción promedio': f"{float(np.mean(predicted_values)):.2f} actividades/mes" if len(predicted_values) > 0 else "N/A"
            }

    def _create_enhanced_forecast_plot(self, historical_data: dict, predictions: dict, input_data: dict) -> go.Figure:
        """Crea una visualización mejorada de las predicciones"""
        try:
            if historical_data.get('empty', True):
                return self._create_error_plot("No hay datos históricos disponibles")
            
            # Crear figura base
            fig = go.Figure()
            
            # Datos históricos
            historical_dates = historical_data['dates']
            historical_values = historical_data['activities']
            
            fig.add_trace(go.Scatter(
                x=historical_dates,
                y=historical_values,
                name='Datos Históricos',
                mode='lines+markers',
                line=dict(color='blue'),
                marker=dict(size=6)
            ))
            
            # Predicciones
            if predictions and 'values' in predictions:
                # Calcular fechas futuras desde la fecha actual en lugar del último dato histórico
                last_historical_date = pd.to_datetime(historical_dates[-1])
                # Obtener el primer día del mes actual de manera más robusta
                now = datetime.now()
                current_date = pd.Timestamp(year=now.year, month=now.month, day=1)
                
                # Si el último dato histórico es más reciente que la fecha actual, usarlo como inicio
                start_date = max(last_historical_date + pd.DateOffset(months=1), current_date)
                
                # Calcular las fechas futuras desde la fecha de inicio determinada
                total_periods = len(predictions['values'])
                all_future_dates = pd.date_range(
                    start=last_historical_date + pd.DateOffset(months=1),
                    periods=total_periods,
                    freq='MS'  # Usar 'MS' en lugar de 'ME'
                )
                
                # Determinar cuáles predicciones son realmente futuras (a partir de la fecha actual)
                months_to_current = predictions.get('months_to_current', 0)
                
                # Usar solo las predicciones futuras (a partir del índice months_to_current)
                future_dates = all_future_dates[months_to_current:]
                future_values = predictions['values'][months_to_current:] if months_to_current < total_periods else []
                
                if len(future_values) > 0:
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=future_values,
                        name='Predicción',
                        line=dict(color='red', dash='dash')
                    ))
                    
                    # Intervalo de confianza si está disponible
                    if 'lower' in predictions and 'upper' in predictions:
                        lower_values = predictions['lower'][months_to_current:] if months_to_current < total_periods else []
                        upper_values = predictions['upper'][months_to_current:] if months_to_current < total_periods else []
                        
                        if len(lower_values) > 0 and len(upper_values) > 0:
                            fig.add_trace(go.Scatter(
                                x=future_dates.tolist() + future_dates.tolist()[::-1],
                                y=lower_values + upper_values[::-1],
                                fill='toself',
                                fillcolor='rgba(255,0,0,0.2)',
                                line=dict(color='rgba(255,0,0,0)'),
                                name='Intervalo de Confianza'
                            ))
                else:
                    # Añadir anotación si no hay predicciones futuras (solo históricas)
                    fig.add_annotation(
                        text="Todos los períodos solicitados son pasados. Aumente el período de predicción.",
                        xref="paper", yref="paper",
                        x=0.5, y=0.9,
                        showarrow=False,
                        font=dict(color="yellow", size=14)
                    )
            
            # Mejorar el layout
            titulo = f"Pronóstico de Actividades - {input_data['departamento']}"
            if input_data.get('municipio'):
                titulo += f", {input_data['municipio']}"
            if input_data.get('categoria'):
                titulo += f" - {input_data['categoria']}"
            
            # Agregar período de predicción al título
            now = datetime.now()
            current_month_name = now.strftime('%B')
            current_year = now.year
            titulo += f"\n(Predicción a partir de {current_month_name} {current_year})"
            
            fig.update_layout(
                title=titulo,
                xaxis_title='Fecha',
                yaxis_title='Número de Actividades',
                template='plotly_dark',
                height=500,
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creando gráfico: {str(e)}")
            return self._create_error_plot(str(e))

    def _handle_prediction_error(self, error_message: str) -> dict:
        """Maneja el error de predicción y devuelve un resultado adecuado"""
        return {
            'predicciones': None,
            'grafico': self._create_error_plot(error_message),
            'metricas': {
                'Estado': 'Error',
                'Mensaje': error_message
            },
            'historical_data': {'dates': [], 'activities': [], 'empty': True}
        }

    def _is_applicable_model(self, model_key: str, input_data: dict) -> bool:
        """Determina si un modelo es aplicable para los datos de entrada"""
        try:
            # Verificar si el modelo coincide con el departamento y municipio
            if input_data.get('municipio'):
                if f"_{input_data['departamento']}_{input_data['municipio']}" in model_key:
                    return True
            
            # Verificar si el modelo coincide con el departamento
            if f"_{input_data['departamento']}" in model_key:
                return True
            
            # Verificar si el modelo coincide con la categoría
            if input_data.get('categoria') and f"_categoria_unica_{input_data['categoria']}" in model_key:
                return True
            
            # Verificar si es un modelo de zona geográfica
            if 'zona_geografica' in model_key:
                zona = self.data_loader.get_zona_from_departamento(input_data['departamento'])
                if f"_zona_geografica_{zona}" in model_key:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando aplicabilidad del modelo {model_key}: {str(e)}")
            return False

    def _get_fallback_model(self, input_data: dict) -> str:
        """Obtiene un modelo alternativo cuando no hay métricas disponibles"""
        try:
            # Intentar modelo municipal
            if input_data.get('municipio'):
                key = f"sarima_departamento_municipio_{input_data['departamento']}_{input_data['municipio']}"
                if key in self.models:
                    return key
                
                key = f"prophet_departamento_municipio_{input_data['departamento']}_{input_data['municipio']}"
                if key in self.models:
                    return key
            
            # Intentar modelo departamental
            key = f"sarima_departamento_{input_data['departamento']}"
            if key in self.models:
                return key
            
            key = f"prophet_departamento_{input_data['departamento']}"
            if key in self.models:
                return key
            
            # Usar modelo de zona geográfica como última opción
            zona = self.data_loader.get_zona_from_departamento(input_data['departamento'])
            key = f"prophet_zona_geografica_{zona}"
            if key in self.models:
                return key
            
            key = f"sarima_zona_geografica_{zona}"
            if key in self.models:
                return key
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo modelo fallback: {str(e)}")
            return None

    def _calculate_model_error(self, model_key: str, input_data: dict) -> dict:
        """Calcula métricas de error para un modelo específico"""
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data(input_data)
            if historical_data.get('empty', True):
                return {'rmse': np.inf}
            
            # Obtener últimos N valores para validación
            n_validation = 6  # últimos 6 meses
            actual_values = np.array(historical_data['activities'][-n_validation:])
            
            # Realizar predicción
            if 'sarima' in model_key:
                predictions = self._predict_sarima(model_key, n_validation)
            else:
                predictions = self._predict_prophet(model_key, n_validation)
            
            predicted_values = np.array(predictions['values'])
            
            # Calcular RMSE
            rmse = np.sqrt(np.mean((actual_values - predicted_values) ** 2))
            
            return {'rmse': rmse}
            
        except Exception as e:
            logger.error(f"Error calculando error del modelo {model_key}: {str(e)}")
            return {'rmse': np.inf}

    def _validate_predictions(self, predictions: dict, historical_data: dict) -> bool:
        """Valida que las predicciones sean coherentes con ajustes por contexto"""
        hist_mean = np.mean(historical_data['activities'])
        pred_mean = np.mean(predictions['values'])
        
        # Ajustar umbrales según el volumen de actividades
        if hist_mean < 2:  # Pocas actividades
            lower_threshold = 0
            upper_threshold = hist_mean * 3
        elif hist_mean < 5:  # Actividades moderadas
            lower_threshold = hist_mean * 0.3
            upper_threshold = hist_mean * 2
        else:  # Muchas actividades
            lower_threshold = hist_mean * 0.5
            upper_threshold = hist_mean * 1.5
        
        if pred_mean < lower_threshold or pred_mean > upper_threshold:
            logger.warning(f"Predicción fuera de rango: histórico={hist_mean:.2f}, predicción={pred_mean:.2f}")
            return False
        return True

    def _create_pattern_analysis_plot(self, historical_data: dict) -> go.Figure:
        """Crea visualización de patrones temporales"""
        try:
            df = pd.DataFrame({
                'fecha': pd.to_datetime(historical_data['dates']),
                'actividades': historical_data['activities']
            })
            
            if len(df) < 6:  # Si hay muy pocos datos
                return self._create_error_plot("Se requieren al menos 6 meses de datos para el análisis de patrones")
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Actividades por Mes del Año', 
                    'Actividades por Día de Semana',
                    'Evolución Temporal',
                    'Distribución de Frecuencias'
                )
            )
            
            # 1. Patrón Mensual (más simple)
            monthly_avg = df.groupby(df['fecha'].dt.month).agg({
                'actividades': ['mean', 'count']
            })['actividades']
            
            fig.add_trace(
                go.Bar(
                    x=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
                    y=monthly_avg['mean'],
                    name='Promedio Mensual',
                    text=monthly_avg['count'],
                    textposition='auto',
                    hovertemplate='Promedio: %{y:.1f}<br>Meses con datos: %{text}'
                ),
                row=1, col=1
            )
            
            # 2. Patrón Semanal
            daily_avg = df.groupby(df['fecha'].dt.dayofweek).agg({
                'actividades': ['mean', 'count']
            })['actividades']
            
            fig.add_trace(
                go.Bar(
                    x=['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                    y=daily_avg['mean'],
                    name='Promedio Diario',
                    text=daily_avg['count'],
                    textposition='auto',
                    hovertemplate='Promedio: %{y:.1f}<br>Días con datos: %{text}'
                ),
                row=1, col=2
            )
            
            # 3. Evolución Temporal
            fig.add_trace(
                go.Scatter(
                    x=df['fecha'],
                    y=df['actividades'],
                    mode='lines+markers',
                    name='Actividades',
                    line=dict(color='blue'),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
            
            # Agregar línea de tendencia
            z = np.polyfit(range(len(df)), df['actividades'], 1)
            p = np.poly1d(z)
            
            fig.add_trace(
                go.Scatter(
                    x=df['fecha'],
                    y=p(range(len(df))),
                    name='Tendencia',
                    line=dict(color='red', dash='dash')
                ),
                row=2, col=1
            )
            
            # 4. Distribución de Frecuencias
            fig.add_trace(
                go.Histogram(
                    x=df['actividades'],
                    name='Frecuencia',
                    nbinsx=max(10, len(df) // 4),
                    histnorm='probability density'
                ),
                row=2, col=2
            )
            
            # Mejorar layout
            fig.update_layout(
                height=800,
                showlegend=True,
                template='plotly_dark',
                title={
                    'text': 'Análisis de Patrones de Actividades',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                }
            )
            
            # Actualizar ejes
            fig.update_xaxes(title_text="Mes", row=1, col=1)
            fig.update_xaxes(title_text="Día", row=1, col=2)
            fig.update_xaxes(title_text="Fecha", row=2, col=1)
            fig.update_xaxes(title_text="Cantidad de Actividades", row=2, col=2)
            
            fig.update_yaxes(title_text="Promedio", row=1, col=1)
            fig.update_yaxes(title_text="Promedio", row=1, col=2)
            fig.update_yaxes(title_text="Actividades", row=2, col=1)
            fig.update_yaxes(title_text="Densidad", row=2, col=2)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error en análisis de patrones: {str(e)}")
            return self._create_error_plot(str(e))

    def _calculate_performance_metrics(self, historical_data: dict) -> dict:
        """Calcula métricas de desempeño adicionales"""
        try:
            values = np.array(historical_data['activities'])
            dates = pd.to_datetime(historical_data['dates'])
            
            # Calcular métricas
            metrics = {
                'Actividades totales': int(np.sum(values)),
                'Promedio mensual': f"{np.mean(values):.2f}",
                'Máximo mensual': f"{np.max(values):.0f}",
                'Mínimo mensual': f"{np.min(values):.0f}",
                'Meses sin actividad': int(np.sum(values == 0)),
                'Meses más activos': self._get_top_months(dates, values),
                'Crecimiento anual': f"{self._calculate_yearly_growth(dates, values):.1f}%",
                'Estabilidad': self._calculate_stability(values)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {str(e)}")
            return {}

    def _get_top_months(self, dates, values, top_n=3):
        """Obtiene los meses con más actividades"""
        df = pd.DataFrame({'fecha': dates, 'valor': values})
        top_months = df.nlargest(top_n, 'valor')
        return [f"{d.strftime('%B %Y')}: {v:.0f}" for d, v in zip(top_months['fecha'], top_months['valor'])]

    def _calculate_yearly_growth(self, dates, values):
        """Calcula el crecimiento anual promedio"""
        df = pd.DataFrame({'fecha': dates, 'valor': values})
        yearly_avg = df.groupby(df['fecha'].dt.year)['valor'].mean()
        if len(yearly_avg) > 1:
            return ((yearly_avg.iloc[-1] / yearly_avg.iloc[0]) ** (1/(len(yearly_avg)-1)) - 1) * 100
        return 0

    def _calculate_stability(self, values):
        """Calcula la estabilidad de las actividades"""
        cv = np.std(values) / np.mean(values)
        if cv < 0.3:
            return "Alta"
        elif cv < 0.6:
            return "Media"
        else:
            return "Baja" 