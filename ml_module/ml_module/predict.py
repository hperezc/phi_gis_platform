import sys
from pathlib import Path
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Ajustar el cálculo del directorio raíz
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import joblib
import pandas as pd
import numpy as np
from feature_engineering import FeatureEngineer
import logging
from scipy.stats import norm
from utils.data_loader import DataLoader
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttendancePredictor:
    def __init__(self, model_path=None):
        """Inicializa el predictor cargando el modelo y los recursos necesarios"""
        try:
            if model_path is None:
                model_path = root_dir / 'models' / 'attendance_predictor.joblib'
            
            # Cargar modelo y recursos
            self.model = joblib.load(model_path)
            self.feature_engineer = FeatureEngineer()
            
            # Cargar información del modelo
            with open(root_dir / 'models' / 'model_info.json', 'r') as f:
                self.model_info = json.load(f)
            
            # Cargar lista de features
            with open(root_dir / 'models' / 'feature_list.json', 'r') as f:
                self.expected_features = json.load(f)
            
            # Cargar mappings categóricos
            self.category_mappings = joblib.load(root_dir / 'models' / 'category_mappings.joblib')
            
            # Cargar y verificar feature importance
            self.feature_importance = pd.read_csv(root_dir / 'models' / 'feature_importance.csv')
            logger.info("Feature importance cargada:")
            logger.info(self.feature_importance.head())
            
            # Verificar estructura del DataFrame
            if 'feature' not in self.feature_importance.columns or 'importance' not in self.feature_importance.columns:
                logger.error("Estructura incorrecta en feature_importance.csv")
                logger.error(f"Columnas encontradas: {self.feature_importance.columns.tolist()}")
            
            # Renombrar columnas de historical_stats si es necesario
            if len(self.model_info['categorical_columns']) == 6:
                self.model_info['categorical_columns'] = [
                    'categoria_unica', 'departamento', 
                    'total_asistentes_mean', 'total_asistentes_median',
                    'total_asistentes_std', 'total_asistentes_count'
                ]
            
            # Agregar DataLoader
            self.data_loader = DataLoader()
            
            logger.info("Modelo cargado exitosamente")
            logger.info(f"Número de features esperadas: {len(self.expected_features)}")
            
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {str(e)}")
            raise

    def _get_historical_data(self, departamento: str, categoria_unica: str, fecha: str, municipio: str = None) -> dict:
        try:
            logger.info(f"Intentando obtener datos históricos para:")
            logger.info(f"- Departamento: {departamento}")
            logger.info(f"- Municipio: {municipio}")
            logger.info(f"- Categoría: {categoria_unica}")
            logger.info(f"- Fecha: {fecha}")
            
            fecha_dt = pd.to_datetime(fecha)
            params = {
                'departamento': departamento,
                'categoria_unica': categoria_unica,
                'fecha': fecha,
                'mes': fecha_dt.month,
                'dia_semana': fecha_dt.weekday()
            }
            
            # Agregar consulta para promedios por día
            promedios_query = """
                WITH promedios_dia AS (
                    SELECT 
                        EXTRACT(DOW FROM fecha) as dia_semana,
                        AVG(total_asistentes) as promedio_asistentes,
                        COUNT(*) as total_actividades
                    FROM actividades 
                    WHERE departamento = %(departamento)s 
                    AND categoria_unica = %(categoria_unica)s 
                    {where_municipio}
                    GROUP BY EXTRACT(DOW FROM fecha)
                )
                SELECT 
                    dia_semana,
                    promedio_asistentes,
                    total_actividades
                FROM promedios_dia
                ORDER BY promedio_asistentes DESC
            """
            
            result_dict = None
            
            # Primero intentar con datos del municipio
            if municipio:
                params['municipio'] = municipio
                query = self._build_historical_query("AND municipio = %(municipio)s")
                promedios_municipio_query = promedios_query.format(
                    where_municipio="AND municipio = %(municipio)s"
                )
                
                result = pd.read_sql_query(query, self.data_loader.engine, params=params)
                promedios_result = pd.read_sql_query(
                    promedios_municipio_query, 
                    self.data_loader.engine, 
                    params=params
                )
                
                if not result.empty:
                    result_dict = result.iloc[0].to_dict()
                    # Agregar promedios por día
                    result_dict['promedios_por_dia'] = {
                        str(row['dia_semana']): float(row['promedio_asistentes'])
                        for _, row in promedios_result.iterrows()
                    }
                    
                    # Verificar que realmente hay actividades
                    if result_dict.get('total_actividades_categoria', 0) > 0:
                        logger.info(f"Usando datos del municipio {municipio}")
                        logger.info(f"Total actividades encontradas: {result_dict['total_actividades_categoria']}")
                        return result_dict
                    else:
                        logger.info(f"No se encontraron actividades para el municipio {municipio}")
            
            # Si no hay datos del municipio, usar datos del departamento
            logger.info(f"Intentando obtener datos del departamento {departamento}")
            query = self._build_historical_query("")
            promedios_dept_query = promedios_query.format(where_municipio="")
            
            result = pd.read_sql_query(query, self.data_loader.engine, params=params)
            promedios_result = pd.read_sql_query(
                promedios_dept_query, 
                self.data_loader.engine, 
                params=params
            )
            
            if not result.empty:
                result_dict = result.iloc[0].to_dict()
                # Agregar promedios por día
                result_dict['promedios_por_dia'] = {
                    str(row['dia_semana']): float(row['promedio_asistentes'])
                    for _, row in promedios_result.iterrows()
                }
                
                # Verificar que hay actividades a nivel departamental
                if result_dict.get('total_actividades_categoria', 0) > 0:
                    logger.info(f"Usando datos del departamento {departamento}")
                    logger.info(f"Total actividades encontradas: {result_dict['total_actividades_categoria']}")
                    return result_dict
                else:
                    logger.warning(f"No se encontraron actividades para el departamento {departamento}")
            
            logger.warning(f"No se encontraron datos históricos en ningún nivel")
            return self._get_default_stats()
            
        except Exception as e:
            logger.error(f"Error en _get_historical_data: {str(e)}")
            logger.error(f"Parámetros de entrada: dept={departamento}, mun={municipio}, cat={categoria_unica}")
            return self._get_default_stats()

    def _build_historical_query(self, where_municipio: str) -> str:
        """Construye la consulta SQL para datos históricos"""
        return """
            WITH datos_encoding AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY departamento) as departamento_encoded,
                    ROW_NUMBER() OVER (ORDER BY zona_geografica) as zona_geografica_encoded,
                    departamento,
                    zona_geografica
                FROM (
                    SELECT DISTINCT departamento, zona_geografica 
                    FROM actividades
                ) t
            ),
            datos_recientes AS (
                SELECT 
                    total_asistentes,
                    fecha
                FROM actividades 
                WHERE departamento = %(departamento)s 
                {where_municipio}
                AND fecha < %(fecha)s
                AND total_asistentes >= 0
                ORDER BY fecha DESC
                LIMIT 30
            ),
            datos_categoria AS (
                SELECT 
                    COUNT(*) as total_actividades_categoria,
                    AVG(total_asistentes) as promedio_categoria,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_asistentes) as mediana_categoria,
                    STDDEV(total_asistentes) as desviacion_categoria,
                    MAX(total_asistentes) as max_categoria,
                    MIN(CASE WHEN total_asistentes > 0 THEN total_asistentes END) as min_categoria,
                    COALESCE(
                        REGR_SLOPE(total_asistentes, EXTRACT(EPOCH FROM fecha)::float),
                        0
                    ) as tendencia_categoria
                FROM actividades
                WHERE departamento = %(departamento)s
                AND categoria_unica = %(categoria_unica)s
                AND fecha < %(fecha)s
                AND total_asistentes >= 0
            ),
            datos_departamento AS (
                SELECT 
                    COUNT(*) as total_actividades_departamento,
                    AVG(total_asistentes) as promedio_departamento,
                    STDDEV(total_asistentes) as desviacion_departamento,
                    MAX(total_asistentes) as max_departamento,
                    MIN(total_asistentes) as min_departamento
                FROM actividades
                WHERE departamento = %(departamento)s
                AND fecha < %(fecha)s
            ),
            datos_mes AS (
                SELECT AVG(total_asistentes) as promedio_mes
                FROM actividades
                WHERE departamento = %(departamento)s 
                {where_municipio}
                AND categoria_unica = %(categoria_unica)s
                AND EXTRACT(MONTH FROM fecha) = %(mes)s
                AND fecha < %(fecha)s
            ),
            datos_dia AS (
                SELECT AVG(total_asistentes) as promedio_dia
                FROM actividades
                WHERE departamento = %(departamento)s 
                {where_municipio}
                AND categoria_unica = %(categoria_unica)s
                AND EXTRACT(DOW FROM fecha) = %(dia_semana)s
                AND fecha < %(fecha)s
            ),
            datos_filtrados AS (
                SELECT dr.* 
                FROM datos_recientes dr 
                WHERE dr.total_asistentes > 0
            )
            SELECT 
                e.departamento_encoded,
                e.zona_geografica_encoded,
                d.total_actividades_departamento,
                d.promedio_departamento,
                d.desviacion_departamento,
                d.max_departamento,
                d.min_departamento,
                c.total_actividades_categoria,
                c.promedio_categoria,
                c.mediana_categoria,
                c.desviacion_categoria,
                c.max_categoria,
                c.min_categoria,
                c.tendencia_categoria,
                COALESCE(m.promedio_mes, c.promedio_categoria) as promedio_mismo_mes_cat,
                COALESCE(dia.promedio_dia, c.promedio_categoria) as promedio_mismo_dia_semana_cat,
                COALESCE(
                    ARRAY_AGG(df.total_asistentes ORDER BY df.fecha DESC),
                    ARRAY[]::integer[]
                ) as asistentes_previos,
                COALESCE(AVG(df.total_asistentes), 0) as promedio_movil_30,
                EXTRACT(DOW FROM %(fecha)s::date) as dia_semana_mas_comun,
                EXTRACT(MONTH FROM %(fecha)s::date) as mes_mas_comun,
                EXTRACT(QUARTER FROM %(fecha)s::date) as trimestre_mas_comun,
                CASE 
                    WHEN d.promedio_departamento > 0 
                    THEN c.promedio_categoria / d.promedio_departamento 
                    ELSE 1 
                END as ratio_asistentes_vs_promedio,
                PERCENT_RANK() OVER (ORDER BY c.promedio_categoria) as percentil_asistentes_categoria
            FROM datos_encoding e
            CROSS JOIN datos_departamento d
            CROSS JOIN datos_categoria c
            LEFT JOIN datos_filtrados df ON true
            LEFT JOIN datos_mes m ON true
            LEFT JOIN datos_dia dia ON true
            GROUP BY 
                e.departamento_encoded,
                e.zona_geografica_encoded,
                d.total_actividades_departamento,
                d.promedio_departamento,
                d.desviacion_departamento,
                d.max_departamento,
                d.min_departamento,
                c.total_actividades_categoria,
                c.promedio_categoria,
                c.mediana_categoria,
                c.desviacion_categoria,
                c.max_categoria,
                c.min_categoria,
                c.tendencia_categoria,
                m.promedio_mes,
                dia.promedio_dia
        """.format(where_municipio=where_municipio)

    def _get_default_stats(self):
        """Retorna estadísticas por defecto cuando no hay datos"""
        return {
            'asistentes_previos': [],
            'promedio_movil_30': 0,
            'actividades_departamento': 0,
            'promedio_departamento': 0,
            'mediana_departamento': 0,
            'desviacion_departamento': 0,
            'max_departamento': 0,
            'min_departamento': 0,
            'actividades_categoria': 0,
            'promedio_categoria': 0,
            'mediana_categoria': 0,
            'desviacion_categoria': 0,
            'max_categoria': 0,
            'min_categoria': 0,
            'tendencia_departamento': 0,
            'tendencia_categoria': 0,
            'promedio_mismo_mes_cat': 0,
            'promedio_mismo_dia_semana_cat': 0,
            'dia_semana_mas_comun': 0,
            'mes_mas_comun': 0,
            'trimestre_mas_comun': 0,
            'percentil_asistentes_categoria': 0.5
        }

    def _ensure_scalar(self, value):
        """Asegura que un valor sea escalar"""
        if isinstance(value, (pd.Series, np.ndarray)):
            if len(value) > 0:
                return float(value.iloc[0] if isinstance(value, pd.Series) else value[0])
            return 0.0
        try:
            return float(value)
        except:
            return 0.0

    def prepare_input_features(self, input_data: dict) -> pd.DataFrame:
        try:
            # Convertir fecha a datetime
            fecha_dt = pd.to_datetime(input_data['fecha'])
            
            # Obtener datos históricos
            historical_data = self._get_historical_data(
                input_data['departamento'],
                input_data['categoria_unica'],
                input_data['fecha'],
                input_data.get('municipio')
            )
            
            # Asegurar que los valores no sean None
            promedio_movil = historical_data.get('promedio_movil_30', 0) or 0
            promedio_mismo_mes = historical_data.get('promedio_mismo_mes_cat', 0) or 0
            promedio_mismo_dia = historical_data.get('promedio_mismo_dia_semana_cat', 0) or 0
            dia_semana_comun = historical_data.get('dia_semana_mas_comun', 0) or 0
            mes_comun = historical_data.get('mes_mas_comun', 0) or 0
            
            # Manejar asistentes_previos cuando es None
            asistentes_previos = historical_data.get('asistentes_previos', [])
            if asistentes_previos is None:
                asistentes_previos = []
            
            # Características temporales y principales
            features_dict = {
                # Features temporales
                'mes': fecha_dt.month,
                'dia_semana': fecha_dt.weekday(),
                'trimestre': (fecha_dt.month - 1) // 3 + 1,
                'es_fin_semana': 1 if fecha_dt.weekday() >= 5 else 0,
                'es_mismo_mes_que_historico': 1 if fecha_dt.month == mes_comun else 0,
                'es_mismo_dia_semana_que_historico': 1 if fecha_dt.weekday() == dia_semana_comun else 0,
                
                # Features de actividad
                'actividades_previas': len(asistentes_previos),
                'actividades_acumuladas_departamento': historical_data.get('actividades_departamento', 0) or 0,
                'actividades_acumuladas_categoria_unica': historical_data.get('actividades_categoria', 0) or 0,
                
                # Features de promedios y medianas
                'promedio_historico_categoria_unica': historical_data.get('promedio_categoria', 0) or 0,
                'mediana_historica_categoria_unica': historical_data.get('mediana_categoria', 0) or 0,
                'promedio_historico_departamento': historical_data.get('promedio_departamento', 0) or 0,
                'mediana_historica_departamento': historical_data.get('mediana_departamento', 0) or 0,
                
                # Features de volatilidad
                'volatilidad_departamento': historical_data.get('desviacion_departamento', 0) or 0,
                'volatilidad_categoria_unica': historical_data.get('desviacion_categoria', 0) or 0,
                
                # Features de tendencia
                'tendencia_departamento': historical_data.get('tendencia_departamento', 0) or 0,
                'tendencia_categoria_unica': historical_data.get('tendencia_categoria', 0) or 0,
                
                # Features de máximos y mínimos
                'max_asistentes_departamento': historical_data.get('max_departamento', 0) or 0,
                'min_asistentes_departamento': historical_data.get('min_departamento', 0) or 0,
                'max_asistentes_categoria_unica': historical_data.get('max_categoria', 0) or 0,
                'min_asistentes_categoria_unica': historical_data.get('min_categoria', 0) or 0,
                
                # Promedios móviles
                'avg_asistentes_departamento_30': historical_data.get('promedio_movil_30', 0) or 0,
                'avg_asistentes_categoria_unica_30': historical_data.get('promedio_movil_30', 0) or 0,
                
                # Features de frecuencia
                'categoria_unica_frequency': (
                    historical_data.get('actividades_categoria', 0) / historical_data.get('actividades_departamento', 0)
                    if historical_data.get('actividades_departamento', 0) > 0 else 0
                ),
                'departamento_frequency': (
                    historical_data.get('actividades_departamento', 0) / 3704  # Total de actividades en la base
                ),
                'zona_geografica_frequency': (
                    historical_data.get('actividades_departamento', 0) / 3704  # Total de actividades en la base
                ),
                'promedio_mismo_mes_dept': historical_data.get('promedio_mismo_mes_dept', 0) or 0,
                'promedio_mismo_mes_cat': promedio_mismo_mes,
                'promedio_mismo_dia_semana_cat': promedio_mismo_dia,
                'dia_semana_mas_comun': dia_semana_comun,
                'mes_mas_comun': mes_comun,
                'trimestre_mas_comun': historical_data.get('trimestre_mas_comun', 0) or 0,
                'percentil_asistentes_categoria': historical_data.get('percentil_asistentes_categoria', 0.5)
            }
            
            # Calcular rankings y percentiles
            features_dict.update({
                'ranking_asistentes_departamento': self._calculate_ranking(
                    historical_data.get('promedio_departamento', 0),
                    historical_data.get('total_actividades_departamento', 1)
                ),
                'percentil_asistentes_departamento': self._calculate_percentile(
                    historical_data.get('promedio_departamento', 0),
                    historical_data.get('promedio_categoria', 0),
                    historical_data.get('desviacion_categoria', 1)
                ),
                'ratio_asistentes_vs_promedio': (
                    historical_data.get('promedio_categoria', 0) / 
                    historical_data.get('promedio_departamento', 1)
                    if historical_data.get('promedio_departamento', 0) > 0 else 1.0
                )
            })
            
            # Agregar encodings
            features_dict.update({
                'departamento_encoded': self._get_encoding(input_data['departamento'], 'departamento'),
                'categoria_unica_encoded': self._get_encoding(input_data['categoria_unica'], 'categoria_unica'),
                'zona_geografica_encoded': self._get_encoding(input_data['zona_geografica'], 'zona_geografica')
            })
            
            # Asegurar que los valores sean escalares y no Series
            for key in features_dict:
                if isinstance(features_dict[key], (pd.Series, np.ndarray)):
                    features_dict[key] = features_dict[key].iloc[0] if isinstance(features_dict[key], pd.Series) else features_dict[key][0]
            
            # Crear DataFrame y asegurar tipos
            df_final = pd.DataFrame([features_dict])
            
            # Convertir todas las columnas a float64
            for col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0.0).astype('float64')
            
            # Asegurar que tenemos todas las features necesarias
            missing_features = set(self.expected_features) - set(df_final.columns)
            if missing_features:
                for feat in missing_features:
                    df_final[feat] = 0.0
            
            # Eliminar features extra
            extra_features = set(df_final.columns) - set(self.expected_features)
            if extra_features:
                df_final = df_final.drop(columns=list(extra_features))
            
            # Asegurar orden exacto de columnas
            df_final = df_final.reindex(columns=self.expected_features)
            
            return df_final
            
        except Exception as e:
            logger.error(f"Error al preparar features: {str(e)}")
            logger.error(f"Input data: {input_data}")
            logger.error("Features esperadas vs generadas:")
            logger.error(f"Esperadas ({len(self.expected_features)}): {self.expected_features}")
            if 'df_final' in locals():
                logger.error(f"Generadas ({len(df_final.columns)}): {df_final.columns.tolist()}")
                logger.error("Tipos de datos:")
                logger.error(df_final.dtypes)
                logger.error("Valores de ejemplo:")
                logger.error(df_final.iloc[0])
            raise

    def _ensure_float64(self, df: pd.DataFrame) -> pd.DataFrame:
        """Asegura que todas las columnas sean float64"""
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
            except Exception as e:
                logger.warning(f"Error convirtiendo columna {col} a float64: {str(e)}")
                logger.warning(f"Valores únicos en {col}: {df[col].unique()}")
        return df

    def predict(self, input_data: dict) -> dict:
        """Realiza la predicción y retorna resultados con métricas"""
        try:
            # Validar datos de entrada
            required_fields = ['departamento', 'municipio', 'categoria_unica', 'fecha']
            for field in required_fields:
                if field not in input_data:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Obtener datos históricos
            historical_data = self._get_historical_data(
                input_data['departamento'],
                input_data['categoria_unica'],
                input_data['fecha'],
                input_data['municipio']
            )
            
            # Limpiar datos históricos (modificar esta parte)
            if historical_data.get('total_actividades_categoria', 0) > 0:
                historical_data = self._clean_historical_data(historical_data)
            
            # Validar que haya datos históricos suficientes (modificar el criterio)
            total_actividades = historical_data.get('total_actividades_categoria', 0)
            if total_actividades < 1:
                logger.warning(f"Datos históricos insuficientes. Total actividades: {total_actividades}")
                # En lugar de lanzar error, usar datos del departamento
                historical_data = self._get_historical_data(
                    input_data['departamento'],
                    input_data['categoria_unica'],
                    input_data['fecha'],
                    None  # Sin municipio para obtener datos departamentales
                )
                total_actividades = historical_data.get('total_actividades_categoria', 0)
            
            logger.info(f"Procesando predicción con {total_actividades} actividades históricas")
            
            # Preparar features
            df = self.prepare_input_features(input_data)
            
            # Verificar que tenemos todas las features necesarias
            if df.shape[1] != len(self.expected_features):
                missing_features = set(self.expected_features) - set(df.columns)
                logger.warning(f"Faltan features: {missing_features}")
            
            # Realizar predicción
            prediction_base = self.model.predict(df.values)[0]
            logger.info(f"Predicción base: {prediction_base}")
            
            # Obtener datos históricos
            historical_data = self._get_historical_data(
                input_data['departamento'],
                input_data['categoria_unica'],
                input_data['fecha'],
                input_data.get('municipio')
            )
            
            # Asegurar valores no nulos
            promedio_categoria = historical_data.get('promedio_categoria', 0)
            promedio_movil = historical_data.get('promedio_movil_30', 0) or 0
            max_categoria = historical_data.get('max_categoria', 0) or 0
            promedio_mismo_mes = historical_data.get('promedio_mismo_mes_cat', 0) or 0
            promedio_mismo_dia = historical_data.get('promedio_mismo_dia_semana_cat', 0) or 0
            
            # Ajustar predicción según promedios históricos
            prediction_adjusted = prediction_base * (
                0.5 +  # Reducir peso de predicción base
                0.25 * (promedio_mismo_mes / promedio_categoria if promedio_categoria > 0 else 1.0) +
                0.25 * (promedio_mismo_dia / promedio_categoria if promedio_categoria > 0 else 1.0)
            )
            
            # Establecer límites más estrictos
            min_prediction = max(
                promedio_categoria * 0.4,  # No menor al 40% del promedio
                promedio_movil * 0.5 if promedio_movil > 0 else 5
            )
            
            max_prediction = min(
                max_categoria * 1.1,  # Solo 10% más que máximo histórico
                promedio_categoria * 1.5  # Máximo 50% sobre el promedio
            )
            
            # Validar predicción
            if not self._validate_prediction(prediction_adjusted, historical_data):
                # Si la predicción es atípica, ajustar hacia el promedio
                prediction_adjusted = (prediction_adjusted + promedio_categoria) / 2
            
            prediction_final = np.clip(prediction_adjusted, min_prediction, max_prediction)
            
            # Validación final de realismo
            if prediction_final > promedio_categoria * 2:
                logger.warning("Predicción muy alta, ajustando...")
                prediction_final = promedio_categoria * 1.5
            
            # Calcular nivel de confianza basado en la variación temporal
            desviacion = historical_data.get('desviacion_categoria', 1) or 1
            variacion_temporal = abs(prediction_final - promedio_mismo_mes) / desviacion
            std_distances = min(
                abs(prediction_final - promedio_movil) / desviacion,
                variacion_temporal
            )
            confidence = 'Alta' if std_distances < 1 else 'Media' if std_distances < 2 else 'Baja'
            
            # Calcular importancia de variables de forma dinámica
            feature_importance = {
                'Histórico': 0,
                'Categoría': 0,
                'Municipio': 0,
                'Día Semana': 0,
                'Mes': 0
            }
            
            # Obtener datos específicos
            total_actividades = historical_data.get('total_actividades', 0)
            datos_historicos = len(historical_data.get('asistentes_previos', []))
            
            logger.info(f"Calculando importancias para {total_actividades} actividades totales y {datos_historicos} datos históricos")
            
            # Calcular importancias solo si hay datos suficientes (3 o más actividades)
            if datos_historicos >= 3:
                # Importancia histórica (10% - 40%)
                peso_historico = 0.1 + (0.3 * min(datos_historicos / 100, 1))
                feature_importance['Histórico'] = peso_historico
                
                # Importancia de categoría (15% - 35%)
                actividades_categoria = historical_data.get('actividades_categoria', 0)
                peso_categoria = 0.15 + (0.2 * min(actividades_categoria / 50, 1))
                feature_importance['Categoría'] = peso_categoria
                
                # Importancia del municipio (10% - 30%)
                actividades_municipio = historical_data.get('actividades_departamento', 0)
                peso_municipio = 0.1 + (0.2 * min(actividades_municipio / 30, 1))
                feature_importance['Municipio'] = peso_municipio
                
                # Importancia temporal (5% - 15% cada uno)
                promedio_dia = historical_data.get('promedio_mismo_dia_semana_cat', 0)
                promedio_mes = historical_data.get('promedio_mismo_mes_cat', 0)
                promedio_general = historical_data.get('promedio_categoria', 1)
                
                if promedio_general > 0:
                    variacion_dia = abs(promedio_dia - promedio_general) / promedio_general
                    variacion_mes = abs(promedio_mes - promedio_general) / promedio_general
                    
                    feature_importance['Día Semana'] = 0.05 + (0.1 * min(variacion_dia, 1))
                    feature_importance['Mes'] = 0.05 + (0.1 * min(variacion_mes, 1))
                
                logger.info("Pesos calculados antes de normalización:")
                for k, v in feature_importance.items():
                    logger.info(f"- {k}: {v:.2%}")
            else:
                logger.warning(f"Usando valores por defecto (solo {datos_historicos} datos históricos)")
                feature_importance = {
                    'Histórico': 0.3,
                    'Categoría': 0.25,
                    'Municipio': 0.2,
                    'Día Semana': 0.15,
                    'Mes': 0.1
                }
            
            # Normalizar para que sumen 1
            total = sum(feature_importance.values())
            feature_importance = {k: v/total for k, v in feature_importance.items()}
            
            logger.info(f"Importancias finales para {input_data['municipio']} - {input_data['categoria_unica']}:")
            for k, v in feature_importance.items():
                logger.info(f"- {k}: {v:.2%}")
            
            # Obtener estadísticas históricas completas
            historical_stats = {
                'min_historico': historical_data.get('min_categoria', 0),
                'max_historico': historical_data.get('max_categoria', 0),
                'promedio_historico': promedio_categoria,
                'mediana_historica': historical_data.get('mediana_categoria', 0),
                'desviacion_estandar': historical_data.get('desviacion_categoria', 0),
                'total_actividades': total_actividades
            }
            
            # Calcular insights dinámicos
            mejor_dia = self._calcular_mejor_dia(historical_data)
            tendencia = self._calcular_tendencia(historical_data)
            confianza = self._calcular_confianza(input_data, prediction_final)
            
            # Calcular recomendaciones dinámicas
            recomendaciones = self._generar_recomendaciones(
                historical_data,
                input_data,
                prediction_final,
                feature_importance
            )
            
            # Agregar al resultado
            result = {
                'prediccion_asistentes': round(prediction_final, 0),
                'importancia_variables': feature_importance,
                'mejor_dia': mejor_dia,
                'tendencia_mensual': tendencia,
                'confianza_prediccion': confianza,
                'recomendaciones': recomendaciones,
                'historical_data': historical_data,
                # Agregar todas las estadísticas históricas
                **historical_stats
            }
            
            # Agregar logs para debug con manejo de lista vacía
            asistentes = historical_data.get('asistentes_previos', [])
            if asistentes:
                logger.info(f"Datos históricos limpios: {len(asistentes)} registros")
                logger.info(f"Rango de valores: {min(asistentes)} - {max(asistentes)}")
            else:
                logger.warning("No hay datos históricos para mostrar rango de valores")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            raise

    def _calcular_mejor_dia(self, historical_data):
        """Calcula el mejor día basado en datos históricos"""
        try:
            promedios_por_dia = historical_data.get('promedios_por_dia', {})
            if not promedios_por_dia:
                return {'dia': 'No disponible', 'incremento': 0}
            
            # Mapeo de números de día a nombres
            dias = {
                '0': 'Lunes',
                '1': 'Martes',
                '2': 'Miércoles',
                '3': 'Jueves',
                '4': 'Viernes',
                '5': 'Sábado',
                '6': 'Domingo'
            }
            
            # Convertir valores a float y manejar posibles errores de formato
            promedios_numericos = {}
            for dia, promedio in promedios_por_dia.items():
                try:
                    # Asegurar que el día sea string y el promedio sea float
                    dia_str = str(int(float(dia)))  # Convertir a float primero por si viene como '5.0'
                    promedio_float = float(promedio)
                    promedios_numericos[dia_str] = promedio_float
                except (ValueError, TypeError):
                    logger.warning(f"Valor inválido en promedios_por_dia: dia={dia}, promedio={promedio}")
                    continue
            
            if not promedios_numericos:
                return {'dia': 'No disponible', 'incremento': 0}
            
            # Encontrar el mejor día
            mejor_dia_num = max(promedios_numericos.items(), key=lambda x: x[1])[0]
            mejor_promedio = promedios_numericos[mejor_dia_num]
            promedio_general = historical_data.get('promedio_categoria', 1)
            
            # Calcular incremento
            incremento = ((mejor_promedio / promedio_general) - 1) if promedio_general > 0 else 0
            
            # Obtener el nombre del día
            nombre_dia = dias.get(mejor_dia_num, 'No disponible')
            
            logger.info(f"Mejor día calculado: {nombre_dia} con incremento de {incremento:.2%}")
            
            return {
                'dia': nombre_dia,
                'incremento': incremento
            }
            
        except Exception as e:
            logger.error(f"Error calculando mejor día: {str(e)}")
            logger.error(f"Promedios por día: {promedios_por_dia}")
            return {'dia': 'No disponible', 'incremento': 0}

    def _calcular_tendencia(self, historical_data):
        """Calcula la tendencia mensual"""
        try:
            asistentes_recientes = historical_data.get('asistentes_previos', [])[-30:]
            if len(asistentes_recientes) < 2:
                return 0
            
            tendencia = np.polyfit(range(len(asistentes_recientes)), asistentes_recientes, 1)[0]
            promedio = np.mean(asistentes_recientes)
            
            return tendencia / promedio if promedio > 0 else 0
        except Exception as e:
            logger.error(f"Error calculando tendencia: {str(e)}")
            return 0

    def _generar_recomendaciones(self, historical_data, input_data, prediccion, importancias):
        """Genera recomendaciones basadas en datos históricos y predicción"""
        try:
            # Identificar factores clave (top 2 más importantes)
            factores_clave = sorted(importancias.items(), key=lambda x: x[1], reverse=True)[:2]
            
            # Calcular mejor mes
            query_mejor_mes = """
                SELECT 
                    EXTRACT(MONTH FROM fecha) as mes,
                    AVG(total_asistentes) as promedio_asistentes,
                    COUNT(*) as total_actividades
                FROM actividades 
                WHERE departamento = %(departamento)s 
                AND categoria_unica = %(categoria_unica)s 
                {where_municipio}
                GROUP BY EXTRACT(MONTH FROM fecha)
                ORDER BY promedio_asistentes DESC
                LIMIT 1
            """
            
            where_municipio = "AND municipio = %(municipio)s" if input_data.get('municipio') else ""
            query_final = query_mejor_mes.format(where_municipio=where_municipio)
            
            try:
                mejor_mes_df = pd.read_sql_query(
                    query_final,
                    self.data_loader.engine,
                    params={
                        'departamento': input_data['departamento'],
                        'categoria_unica': input_data['categoria_unica'],
                        'municipio': input_data.get('municipio')
                    }
                )
                
                meses = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }
                
                mejor_mes = 'No disponible'
                if not mejor_mes_df.empty:
                    mes_num = int(mejor_mes_df.iloc[0]['mes'])
                    mejor_mes = meses.get(mes_num, 'No disponible')
            except Exception as e:
                logger.error(f"Error obteniendo mejor mes: {str(e)}")
                mejor_mes = 'No disponible'
            
            # Calcular potencial de mejora más realista
            asistentes_previos = historical_data.get('asistentes_previos', [])
            percentil_75 = np.percentile(asistentes_previos, 75) if asistentes_previos else prediccion
            potencial_mejora = ((percentil_75 - prediccion) / prediccion * 100) if prediccion > 0 else 20
            potencial_mejora = min(max(potencial_mejora, 0), 100)  # Limitar entre 0% y 100%
            
            return {
                'mejor_mes': mejor_mes,
                'potencial_mejora': potencial_mejora,
                'factores_clave': [factor[0] for factor in factores_clave]
            }
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {
                'mejor_mes': 'No disponible',
                'potencial_mejora': 20,
                'factores_clave': ['Histórico', 'Categoría']
            }

    def _calcular_confianza(self, input_data, prediction):
        """Calcula el nivel de confianza de la predicción"""
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data(
                input_data['departamento'],
                input_data['categoria_unica'],
                input_data['fecha'],
                input_data['municipio']
            )
            
            # Factor 1: Cantidad de datos históricos (0-0.4)
            datos_historicos = len(historical_data.get('asistentes_previos', []))
            peso_datos = min(0.4, datos_historicos / 100)
            
            # Factor 2: Consistencia de datos (0-0.3)
            desviacion = historical_data.get('desviacion_categoria', 0)
            promedio = historical_data.get('promedio_categoria', 1)
            coef_variacion = desviacion / promedio if promedio > 0 else 1
            peso_consistencia = 0.3 * (1 - min(coef_variacion, 1))
            
            # Factor 3: Proximidad al promedio (0-0.3)
            distancia_promedio = abs(prediction - promedio) / promedio if promedio > 0 else 1
            peso_proximidad = 0.3 * (1 - min(distancia_promedio, 1))
            
            # Calcular confianza total
            confianza = peso_datos + peso_consistencia + peso_proximidad
            
            # Normalizar entre 0 y 1
            return min(max(confianza, 0), 1)
        except Exception as e:
            logger.error(f"Error calculando confianza: {str(e)}")
            return 0.5  # Valor por defecto si hay error

    def debug_features(self, df):
        """Función auxiliar para debuggear features"""
        logger.info("\n=== Debug de Features ===")
        logger.info(f"Shape del DataFrame: {df.shape}")
        
        # Verificar valores nulos
        null_cols = df.columns[df.isnull().any()].tolist()
        if null_cols:
            logger.warning(f"Columnas con valores nulos: {null_cols}")
        
        # Verificar valores infinitos
        inf_cols = df.columns[np.isinf(df.values).any(axis=0)].tolist()
        if inf_cols:
            logger.warning(f"Columnas con valores infinitos: {inf_cols}")

    def _safe_float_conversion(self, value):
        """Convierte un valor a float de manera segura"""
        try:
            if pd.isna(value):
                return 0.0
            if isinstance(value, bool):
                return float(value)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value.replace(',', ''))
            return float(value)
        except:
            return 0.0

    def _calculate_percentile(self, value: float, mean: float, std: float) -> float:
        """Calcula el percentil basado en la distribución normal"""
        try:
            value = float(value)
            mean = float(mean)
            std = float(std)
            
            if std == 0:
                return 0.5
            
            return float(norm.cdf((value - mean) / std))
        except Exception as e:
            logger.warning(f"Error en _calculate_percentile: {str(e)}")
            logger.warning(f"Valores: value={value}, mean={mean}, std={std}")
            return 0.5

    def _calculate_ranking(self, value, total_activities):
        """Calcula el ranking normalizado"""
        if total_activities == 0:
            return 0.5
        return value / total_activities

    def get_municipio_stats(self, municipio: str) -> dict:
        """Obtiene estadísticas generales para un municipio"""
        try:
            query = """
                WITH stats AS (
                    SELECT 
                        categoria_unica,
                        COUNT(*) as total_actividades,
                        AVG(total_asistentes) as promedio_asistentes,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_asistentes) as mediana_asistentes,
                        STDDEV(total_asistentes) as desviacion_asistentes,
                        MAX(total_asistentes) as max_asistentes,
                        MIN(total_asistentes) as min_asistentes
                    FROM actividades
                    WHERE municipio = %(municipio)s
                    GROUP BY categoria_unica
                )
                SELECT 
                    categoria_unica,
                    total_actividades,
                    ROUND(promedio_asistentes::numeric, 2) as promedio,
                    ROUND(mediana_asistentes::numeric, 2) as mediana,
                    ROUND(desviacion_asistentes::numeric, 2) as desviacion,
                    max_asistentes,
                    min_asistentes
                FROM stats
                ORDER BY total_actividades DESC
            """
            
            df = pd.read_sql(query, self.data_loader.engine, params={'municipio': municipio})
            
            return {
                'municipio': municipio,
                'total_actividades': df['total_actividades'].sum(),
                'categorias': df.to_dict('records'),
                'ultima_actualizacion': pd.Timestamp.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del municipio: {str(e)}")
            return None

    def _get_encoding(self, value: str, column: str) -> float:
        """Obtiene el encoding para un valor categórico"""
        try:
            return float(self.category_mappings[column].get(value, 0))
        except Exception as e:
            logger.warning(f"Error obteniendo encoding para {value} en {column}: {str(e)}")
            return 0.0

    def _validate_prediction(self, prediction: float, historical_data: dict) -> bool:
        """Valida si una predicción parece realista"""
        promedio = historical_data.get('promedio_categoria', 0)
        desviacion = historical_data.get('desviacion_categoria', 1)
        max_hist = historical_data.get('max_categoria', 0)
        
        if promedio > 0:
            # Validar usando z-score
            z_score = abs(prediction - promedio) / desviacion
            if z_score > 2.5:  # Más conservador: 2.5 desviaciones estándar
                logger.warning(f"Predicción atípica detectada: {prediction} (z-score: {z_score})")
                return False
            
            # Validar contra máximo histórico
            if prediction > max_hist * 1.2:
                logger.warning(f"Predicción excede máximo histórico por más del 20%")
                return False
            
            # Validar contra promedio
            if prediction > promedio * 2:
                logger.warning(f"Predicción excede el doble del promedio histórico")
                return False
        
        return True

    def _clean_historical_data(self, historical_data: dict) -> dict:
        """Limpia y prepara los datos históricos para visualización"""
        try:
            # Obtener y limpiar asistentes previos
            asistentes = historical_data.get('asistentes_previos', [])
            if not asistentes:
                # Si no hay datos, usar valores por defecto
                historical_data['asistentes_previos'] = [0]
                return historical_data
            
            # Convertir a numpy array y eliminar valores nulos o 0
            asistentes = np.array([
                float(x) for x in asistentes 
                if x is not None and float(x) >= 0
            ])
            
            if len(asistentes) == 0:
                # Si después de limpiar no quedan datos, usar valores por defecto
                historical_data['asistentes_previos'] = [0]
                return historical_data
            
            # Ordenar los valores para mejor visualización
            asistentes = np.sort(asistentes)
            
            # Actualizar los datos históricos
            historical_data['asistentes_previos'] = asistentes.tolist()
            
            # Recalcular estadísticas básicas solo si hay cambios significativos
            promedio_actual = historical_data.get('promedio_categoria', 0)
            promedio_nuevo = float(np.mean(asistentes))
            
            # Solo actualizar si hay una diferencia significativa
            if abs(promedio_actual - promedio_nuevo) > 0.1:
                historical_data.update({
                    'promedio_categoria': promedio_nuevo,
                    'mediana_categoria': float(np.median(asistentes)),
                    'desviacion_categoria': float(np.std(asistentes)) if len(asistentes) > 1 else 0,
                    'min_categoria': float(np.min(asistentes)),
                    'max_categoria': float(np.max(asistentes))
                })
            
            return historical_data
        except Exception as e:
            logger.error(f"Error limpiando datos históricos: {str(e)}")
            # Retornar datos históricos con valores por defecto
            historical_data['asistentes_previos'] = [0]
            return historical_data

    def get_feature_importances(self) -> dict:
        """Retorna los pesos reales de las características del modelo"""
        return {
            'Contextuales': 55,    # Promedios históricos y ratios
                                  # - promedio_historico_categoria_unica (13.6%)
                                  # - ratio_asistentes_vs_promedio (9.2%)
                                  # - mediana_historica_categoria_unica (6.1%)
                                  # - percentil_asistentes_categoria_unica (5.7%)
                                  # - avg_asistentes_categoria_unica_30 (3.0%)
                                  # - min_asistentes_categoria_unica (2.4%)
            
            'Actividad': 41,       # Características de la actividad
                                  # - total_actividades_categoria_unica (14.8%)
                                  # - categoria_unica_frequency (8.1%)
                                  # - ranking_asistentes_categoria_unica (6.0%)
                                  # - categoria_unica_encoded (2.2%)
            
            'Geográficos': 4      # Factores de ubicación
                                  # - departamento_frequency (1.6%)
                                  # - departamento_encoded (0.8%)
                                  # - zona_geografica_frequency (0.3%)
        }

def create_historical_trend(historical_data, fecha_seleccionada, prediccion=None):
    """Crea gráfico de tendencia histórica"""
    asistentes = historical_data.get('asistentes_previos', [])
    
    if not asistentes:
        return go.Figure().add_annotation(
            text="No hay datos históricos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Usar la fecha seleccionada como punto final
    fecha_fin = pd.to_datetime(fecha_seleccionada)
    fecha_inicio = fecha_fin - pd.Timedelta(days=30)
    
    # Crear fechas correspondientes
    fechas = pd.date_range(
        start=fecha_inicio,
        end=fecha_fin,
        freq='D'
    )
    
    # Tomar solo los últimos 30 registros antes de la fecha seleccionada
    asistentes = asistentes[-30:] if len(asistentes) > 30 else asistentes
    
    df = pd.DataFrame({
        'Fecha': fechas[-len(asistentes):],
        'Asistentes': asistentes
    })
    
    fig = go.Figure()
    
    # Agregar línea de tendencia
    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Asistentes'],
        mode='lines+markers',
        name='Asistentes históricos',
        line=dict(color='#2196F3')
    ))
    
    # Agregar la predicción como punto destacado si existe
    if prediccion is not None:
        fig.add_trace(go.Scatter(
            x=[fecha_fin],
            y=[prediccion],
            mode='markers',
            name='Predicción',
            marker=dict(
                color='red',
                size=12,
                symbol='star'
            )
        ))
    
    # Agregar línea de promedio
    promedio = historical_data.get('promedio_categoria', 0)
    fig.add_hline(
        y=promedio,
        line_dash="dash",
        line_color="red",
        annotation_text="Promedio histórico"
    )
    
    # Actualizar layout
    fig.update_layout(
        title='Tendencia de Asistentes (Últimos 30 días)',
        template='plotly_white',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white'),
        xaxis=dict(
            title='Fecha',
            gridcolor='#2C2C2C',
            showgrid=True
        ),
        yaxis=dict(
            title='Asistentes',
            gridcolor='#2C2C2C',
            showgrid=True
        )
    )
    
    return fig

def create_comparison_chart(result):
    """Crea gráfico comparativo de predicción vs históricos"""
    fig = go.Figure()
    
    # Datos para el gráfico
    categories = ['Mínimo', 'Promedio', 'Predicción', 'Máximo']
    values = [
        result.get('min_historico', 0),
        result.get('promedio_historico', 0),
        result.get('prediccion_asistentes', 0),
        result.get('max_historico', 0)
    ]
    
    # Agregar barras
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=['#90CAF9', '#4CAF50', '#FFA726', '#EF5350']
    ))
    
    fig.update_layout(
        title='Comparación de Predicción vs Datos Históricos',
        template='plotly_white',
        showlegend=False
    )
    return fig

def create_distribution_plot(historical_data, prediction):
    """Crea gráfico de distribución con la predicción"""
    fig = go.Figure()
    
    # Datos históricos
    hist_values = historical_data.get('asistentes_previos', [])
    
    # Agregar histograma
    fig.add_trace(go.Histogram(
        x=hist_values,
        name='Distribución histórica',
        nbinsx=20,
        opacity=0.7
    ))
    
    # Agregar línea vertical de predicción
    fig.add_vline(x=prediction,
                  line_dash="dash",
                  line_color="red",
                  annotation_text="Predicción")
    
    fig.update_layout(
        title='Distribución de Asistentes y Predicción',
        xaxis_title='Número de Asistentes',
        yaxis_title='Frecuencia',
        template='plotly_white'
    )
    return fig

def show_prediction_details(result, input_data):
    """Muestra detalles de la predicción con gráficos"""
    
    # Métricas principales en columnas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predicción", f"{result['prediccion_asistentes']:.1f}")
    with col2:
        st.metric("Promedio Histórico", f"{result.get('promedio_historico', 0):.1f}")
    with col3:
        st.metric("Confianza", f"{result.get('confianza_prediccion', 0):.1%}")
    
    # Tabs para diferentes visualizaciones
    tab1, tab2, tab3 = st.tabs(["Comparación", "Tendencia", "Distribución"])
    
    with tab1:
        st.plotly_chart(create_comparison_chart(result), use_container_width=True)
        
    with tab2:
        historical_data = result.get('historical_data', {})
        st.plotly_chart(create_historical_trend(historical_data, input_data['fecha'], result['prediccion_asistentes']), use_container_width=True)
        
    with tab3:
        st.plotly_chart(
            create_distribution_plot(
                historical_data,
                result['prediccion_asistentes']
            ),
            use_container_width=True
        )
    
    # Información adicional en expander
    with st.expander("Detalles Estadísticos"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("Estadísticas Históricas")
            st.write(f"- Mediana: {result.get('mediana_historica', 0):.1f}")
            st.write(f"- Desviación: {result.get('desviacion_estandar', 0):.1f}")
            st.write(f"- Total actividades: {result.get('total_actividades', 0)}")
        with col2:
            st.write("Contexto Temporal")
            st.write(f"- Promedio mismo mes: {result.get('promedio_mismo_mes', 0):.1f}")
            st.write(f"- Promedio mismo día: {result.get('promedio_mismo_dia', 0):.1f}")
            st.write(f"- Tendencia: {result.get('tendencia_departamento', 0):.2%}")

def test_predictions():
    """Función para probar diferentes escenarios de predicción"""
    predictor = AttendancePredictor()
    
    st.title("Predictor de Asistentes")
    
    # Input form - cambiamos la key del formulario
    with st.form("prediction_form_test"):  # <- Cambiado aquí
        col1, col2 = st.columns(2)
        with col1:
            departamento = st.selectbox("Departamento", ["Antioquia", "Sucre", "Bolívar"])
            municipio = st.selectbox("Municipio", ["Valdivia", "Caucasia", "Majagual"])
        with col2:
            categoria = st.selectbox("Categoría", ["Socialización", "Reunión", "Capacitación"])
            fecha = st.date_input("Fecha")
        
        submitted = st.form_submit_button("Predecir")
    
    if submitted:
        input_data = {
            'departamento': departamento,
            'zona_geografica': departamento,
            'municipio': municipio,
            'categoria_unica': categoria,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'mes': fecha.month,
            'dia_semana': fecha.weekday(),
            'trimestre': (fecha.month - 1) // 3 + 1
        }
        
        with st.spinner('Calculando predicción...'):
            result = predictor.predict(input_data)
            show_prediction_details(result, input_data)

if __name__ == "__main__":
    test_predictions() 