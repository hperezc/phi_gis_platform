import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import json
import logging
import folium
from folium import plugins
from branca.colormap import LinearColormap
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from functools import lru_cache
import streamlit as st

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import DataLoader
from ml_module.geographic_analysis.analysis_utils import calculate_municipal_metrics, generate_municipal_recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeographicPredictor:
    # Variable de clase para almacenar los modelos
    _instance = None
    _models = None
    _metrics = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GeographicPredictor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        self.data_loader = DataLoader()
        self.models = self._load_models()
        # Mapeo de tipos de actividad a IDs
        self.tipo_mapping = {
            'Talleres': '1',
            'Simulacros': '2', 
            'Divulgaciones': '3',
            'Apoyo a simulacro': '4',
            'Kits': '5',
            'Planes comunitarios': '6',
            'Asesoría especializada': '7',
            'Simulaciones': '8'
        }
        self.current_weights = None
        self._initialize_weights()
        
    def _initialize_weights(self):
        """Inicializa los pesos por defecto y específicos"""
        try:
            # Cargar pesos específicos por tipo
            type_weights = self.models.get('type_specific_weights', {})
            
            # Almacenar pesos en un diccionario de clase
            self.weights = {
                'default': {
                    'actividades': 0.33,
                    'asistentes': 0.33,
                    'eficiencia': 0.34
                }
            }
            
            # Agregar pesos específicos por tipo
            for tipo_id, weights in type_weights.items():
                self.weights[tipo_id] = weights
                
            logger.info(f"Pesos inicializados: {self.weights}")
            
        except Exception as e:
            logger.error(f"Error inicializando pesos: {str(e)}")
            self.weights = {'default': {'actividades': 0.33, 'asistentes': 0.33, 'eficiencia': 0.34}}

    @staticmethod
    def get_weights(tipo_actividad: str = None, weights_dict: dict = None) -> dict:
        """Obtiene los pesos para un tipo de actividad específico"""
        try:
            if weights_dict is None:
                weights_dict = {
                    'default': {'actividades': 0.33, 'asistentes': 0.33, 'eficiencia': 0.34},
                    '1': {'actividades': 0.2323, 'asistentes': 0.173, 'eficiencia': 0.5946},
                    '2': {'actividades': 0.1808, 'asistentes': 0.2213, 'eficiencia': 0.5979},
                    '3': {'actividades': 0.02037124848656075, 'asistentes': 0.18426415172205035, 'eficiencia': 0.7953645997913888},
                    '4': {'actividades': 0.0284, 'asistentes': 0.2533, 'eficiencia': 0.7183},
                    '5': {'actividades': 0.133, 'asistentes': 0.3646, 'eficiencia': 0.5024},
                    '6': {'actividades': 0.02037124848656075, 'asistentes': 0.18426415172205035, 'eficiencia': 0.7953645997913888},
                    '7': {'actividades': 0.042, 'asistentes': 0.0111, 'eficiencia': 0.9469}
                }
            
            tipo_mapping = {
                'Talleres': '1',
                'Simulacros': '2', 
                'Divulgaciones': '3',
                'Apoyo a simulacro': '4',
                'Kits': '5',
                'Planes comunitarios': '6',
                'Asesoría especializada': '7',
                'Simulaciones': '8'
            }
            
            if tipo_actividad:
                tipo_id = tipo_mapping.get(tipo_actividad)
                if tipo_id and tipo_id in weights_dict:
                    logger.info(f"Usando pesos específicos para {tipo_actividad} (ID: {tipo_id})")
                    return weights_dict[tipo_id]
            
            logger.info("Usando pesos por defecto")
            return weights_dict['default']
            
        except Exception as e:
            logger.error(f"Error obteniendo pesos: {str(e)}")
            return {'actividades': 0.33, 'asistentes': 0.33, 'eficiencia': 0.34}

    def _load_models(self):
        """Carga los modelos entrenados y sus pesos"""
        try:
            models_dir = Path(root_dir) / 'models/geographic_models'
            
            models = {
                'kmeans': joblib.load(models_dir / 'kmeans_model.joblib'),
                'dbscan': joblib.load(models_dir / 'dbscan_model.joblib'),
                'scaler': joblib.load(models_dir / 'scaler_model.joblib'),
                'feature_weights': joblib.load(models_dir / 'feature_weights_model.joblib'),
                'type_specific_weights': joblib.load(models_dir / 'type_specific_weights_model.joblib')
            }
            
            # Cargar métricas
            with open(models_dir / 'model_metrics.json', 'r') as f:
                models['metrics'] = json.load(f)
                
            return models
            
        except Exception as e:
            logger.error(f"Error cargando modelos: {str(e)}")
            return {}

    def predict(self, input_data: dict) -> dict:
        """Realiza predicciones usando los modelos entrenados"""
        try:
            # Obtener datos
            data = self._get_data(input_data)
            if data.empty:
                return {'error': 'No hay datos disponibles'}
            
            # Crear una copia persistente de los datos
            data = data.copy()
            
            # Aplicar clustering usando K-means
            kmeans_results = self._apply_kmeans(data)
            
            # Obtener tipo de actividad
            tipo_actividad = input_data.get('tipo_actividad')
            
            # Obtener y almacenar los pesos apropiados usando el método estático
            self.current_weights = self.get_weights(tipo_actividad)
            
            # Calcular scores de priorización con los pesos almacenados
            priority_scores = self._calculate_priority_scores(data)
            
            # Asegurar que los resultados son serializables
            results = {
                'data': data,
                'kmeans_results': {
                    'clusters': kmeans_results['clusters'],
                    'cluster_profiles': kmeans_results['cluster_profiles'],
                    'n_clusters': kmeans_results['n_clusters']
                },
                'predicted_score': priority_scores,
                'model_weights': self.current_weights,
                'tipo_actividad': tipo_actividad,
                'weights_source': 'specific' if tipo_actividad else 'general'
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            return {'error': str(e)}

    def _calculate_priority_scores(self, data: pd.DataFrame) -> dict:
        """Calcula scores de priorización usando los pesos almacenados"""
        try:
            scores = {}
            
            # Usar los pesos almacenados en la instancia
            weights = self.current_weights
            logger.info(f"Calculando scores con pesos almacenados: {weights}")
            
            scores['general_score'] = (
                data['num_actividades'] * weights['actividades'] +
                data['total_asistentes'] * weights['asistentes'] +
                data['eficiencia_actividad'] * weights['eficiencia']
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculando scores: {str(e)}")
            return {'general_score': data['eficiencia_actividad']}

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def _cached_get_geographic_data(input_data_tuple: tuple) -> pd.DataFrame:
        """Versión cacheada de get_geographic_data"""
        # Convertir tuple a dict
        input_data = {
            'zona_geografica': input_data_tuple[0],
            'departamento': input_data_tuple[1],
            'municipio': input_data_tuple[2],
            'fecha_inicio': input_data_tuple[3],
            'fecha_fin': input_data_tuple[4],
            'tipo_actividad': input_data_tuple[5]
        }
        
        try:
            # Crear una nueva conexión para evitar problemas con el cache
            data_loader = DataLoader()
            
            # Mapeo de tipos de actividad a IDs
            tipo_mapping = {
                'Talleres': '1',
                'Simulacros': '2', 
                'Divulgaciones': '3',
                'Apoyo a simulacro': '4',
                'Kits': '5',
                'Planes comunitarios': '6',
                'Asesoría especializada': '7',
                'Simulaciones': '8'
            }
            
            # Construir query
            filters = []
            params = {}
            
            if input_data.get('departamento'):
                filters.append("a.departamento = %(departamento)s")
                params['departamento'] = input_data['departamento']
            
            if input_data.get('municipio') and input_data['municipio'] != "Todos":
                filters.append("a.municipio = %(municipio)s")
                params['municipio'] = input_data['municipio']
            
            if input_data.get('zona_geografica') and input_data['zona_geografica'] != "Todas":
                filters.append("a.zona_geografica = %(zona)s")
                params['zona'] = input_data['zona_geografica']
            
            if input_data.get('fecha_inicio'):
                filters.append("a.fecha >= %(fecha_inicio)s")
                params['fecha_inicio'] = input_data['fecha_inicio']
            
            if input_data.get('fecha_fin'):
                filters.append("a.fecha <= %(fecha_fin)s")
                params['fecha_fin'] = input_data['fecha_fin']
                
            # Agregar filtro para tipo_actividad usando el texto directamente
            if input_data.get('tipo_actividad'):
                filters.append("a.categoria_unica = %(tipo_actividad)s")
                params['tipo_actividad'] = input_data['tipo_actividad']
                logger.info(f"Filtrando por tipo de actividad: {input_data['tipo_actividad']}")
            
            # Construir where_clause
            where_clause = " AND ".join(filters) if filters else "TRUE"
            logger.info(f"Where clause: {where_clause}")
            logger.info(f"Parámetros: {params}")
            
            query = f"""
                WITH municipios_base AS (
                    SELECT DISTINCT 
                        m.municipio,
                        m.departamento,
                        m.geometry,
                        COALESCE(a.zona_geografica, 'No definida') as zona_geografica
                    FROM actividades_municipios m
                    LEFT JOIN actividades a ON 
                        m.municipio = a.municipio AND 
                        m.departamento = a.departamento
                    WHERE m.geometry IS NOT NULL
                ),
                activity_stats AS (
                    SELECT 
                        m.municipio,
                        m.departamento,
                        m.zona_geografica,
                        ST_X(ST_Centroid(m.geometry::geometry)) as longitud,
                        ST_Y(ST_Centroid(m.geometry::geometry)) as latitud,
                        COUNT(DISTINCT CASE WHEN {where_clause} THEN a.grupo_interes ELSE NULL END) as num_grupos_interes,
                        COUNT(DISTINCT CASE WHEN {where_clause} THEN a.id ELSE NULL END) as num_actividades,
                        SUM(CASE WHEN {where_clause} THEN COALESCE(a.total_asistentes, 0) ELSE 0 END) as total_asistentes,
                        COUNT(DISTINCT CASE WHEN {where_clause} THEN EXTRACT(MONTH FROM a.fecha) ELSE NULL END) as meses_activos,
                        MAX(CASE WHEN {where_clause} THEN a.categoria_unica ELSE NULL END) as categoria_unica,
                        COUNT(DISTINCT CASE WHEN {where_clause} THEN EXTRACT(YEAR FROM a.fecha) ELSE NULL END) as anos_activos,
                        string_agg(DISTINCT CAST(a.grupo_interes AS TEXT), ',') as grupos_interes_list,
                        AVG(CASE WHEN {where_clause} THEN EXTRACT(DOW FROM a.fecha) ELSE NULL END) as dia_semana_promedio
                    FROM municipios_base m
                    LEFT JOIN actividades a ON 
                        m.municipio = a.municipio AND 
                        m.departamento = a.departamento
                    GROUP BY 
                        m.municipio, 
                        m.departamento,
                        m.zona_geografica,
                        m.geometry
                    HAVING COUNT(DISTINCT CASE WHEN {where_clause} THEN a.id ELSE NULL END) > 0
                ),
                grupos_stats AS (
                    SELECT 
                        a.municipio,
                        a.departamento,
                        a.grupo_interes,
                        CONCAT('Grupo ', a.grupo_interes) as nombre_grupo_interes,
                        COUNT(DISTINCT CASE WHEN {where_clause} THEN a.id ELSE NULL END) as actividades_por_grupo,
                        SUM(CASE WHEN {where_clause} THEN COALESCE(a.total_asistentes, 0) ELSE 0 END) as asistentes_por_grupo
                    FROM actividades a
                    WHERE {where_clause}
                    GROUP BY 
                        a.municipio, 
                        a.departamento,
                        a.grupo_interes
                )
                SELECT 
                    m.*,
                    g.grupo_interes as grupo_interes_id,
                    g.nombre_grupo_interes,
                    g.actividades_por_grupo,
                    g.asistentes_por_grupo,
                    CASE 
                        WHEN m.num_actividades > 0 THEN m.total_asistentes::float / m.num_actividades 
                        ELSE 0 
                    END as promedio_asistentes,
                    CASE 
                        WHEN m.meses_activos > 0 THEN m.num_actividades::float / m.meses_activos 
                        ELSE 0 
                    END as intensidad_mensual,
                    CASE 
                        WHEN m.num_actividades > 0 THEN m.total_asistentes::float / m.num_actividades 
                        ELSE 0 
                    END as eficiencia_actividad,
                    CASE 
                        WHEN g.actividades_por_grupo > 0 THEN g.asistentes_por_grupo::float / g.actividades_por_grupo 
                        ELSE 0 
                    END as eficiencia_actividad_grupo
                FROM activity_stats m
                LEFT JOIN grupos_stats g ON
                    m.municipio = g.municipio AND
                    m.departamento = g.departamento
                WHERE m.longitud IS NOT NULL AND m.latitud IS NOT NULL
            """
            
            df = pd.read_sql(query, data_loader.engine, params=params)
            logger.info(f"Datos geográficos obtenidos: {len(df)} municipios")
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos geográficos: {str(e)}")
            return pd.DataFrame()

    def _get_data(self, input_data: dict) -> pd.DataFrame:
        """Obtiene y prepara los datos para predicción"""
        try:
            # Convertir input_data a tuple para el cache
            input_tuple = (
                input_data.get('zona_geografica'),
                input_data.get('departamento'),
                input_data.get('municipio'),
                input_data.get('fecha_inicio'),
                input_data.get('fecha_fin'),
                input_data.get('tipo_actividad')  # Agregar tipo_actividad al cache key
            )
            
            # Usar la versión cacheada
            df = self._cached_get_geographic_data(input_tuple)
            
            if df.empty:
                logger.warning("No se encontraron datos")
                return pd.DataFrame()
            
            # Asegurar que tenemos las columnas necesarias
            required_columns = [
                'num_actividades',
                'total_asistentes',
                'meses_activos',
                'intensidad_mensual'
            ]
            
            # Verificar si tenemos eficiencia_actividad o eficiencia_actividad_grupo
            if 'eficiencia_actividad' not in df.columns:
                if 'eficiencia_actividad_grupo' in df.columns:
                    # Usar eficiencia_actividad_grupo como alternativa
                    df['eficiencia_actividad'] = df['eficiencia_actividad_grupo']
                    logger.info("Usando eficiencia_actividad_grupo como eficiencia_actividad")
                else:
                    # Agregar a la lista de columnas faltantes
                    required_columns.append('eficiencia_actividad')
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Faltan columnas requeridas: {missing_columns}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def _cached_apply_kmeans(data_records: tuple, features: tuple, model_name: str, model_path: Path) -> dict:
        """Versión cacheada de apply_kmeans"""
        try:
            # Cargar el modelo específicamente para esta ejecución
            model_dict = joblib.load(model_path / f'{model_name}_model.joblib')
            
            # Convertir los records a DataFrame
            df = pd.DataFrame.from_records(data_records)
            
            kmeans = model_dict['model']
            scaler = model_dict['scaler']
            
            # Preparar datos
            X = df[list(features)].copy()
            X_scaled = scaler.transform(X)
            
            # Predecir clusters
            clusters = kmeans.predict(X_scaled)
            
            return {
                'clusters': clusters.tolist(),
                'n_clusters': len(set(clusters))
            }
            
        except Exception as e:
            logger.error(f"Error aplicando K-means: {str(e)}")
            return {
                'clusters': [0] * len(data_records),
                'n_clusters': 1
            }

    def _apply_kmeans(self, df: pd.DataFrame) -> dict:
        """Aplica clustering K-means a los datos"""
        try:
            if 'kmeans' not in self.models:
                raise ValueError("Modelo K-means no encontrado")
            
            kmeans = self.models['kmeans']
            scaler = self.models.get('scaler')
            
            # Preparar datos con nombres de features
            features = pd.DataFrame({
                'num_actividades': df['num_actividades'],
                'total_asistentes': df['total_asistentes'],
                'meses_activos': df['meses_activos'],
                'eficiencia_actividad': df['eficiencia_actividad'],
                'intensidad_mensual': df['intensidad_mensual']
            })
            
            if scaler:
                features_scaled = pd.DataFrame(
                    scaler.transform(features),
                    columns=features.columns,
                    index=features.index
                )
            else:
                features_scaled = features
            
            # Predecir clusters
            clusters = kmeans.predict(features_scaled)
            
            # Calcular perfiles de cluster
            df['cluster'] = clusters
            cluster_profiles = self._calculate_cluster_profiles(df)
            
            return {
                'clusters': clusters.tolist(),
                'cluster_profiles': cluster_profiles,
                'n_clusters': len(set(clusters))
            }
            
        except Exception as e:
            logger.error(f"Error en _apply_kmeans: {str(e)}")
            return {
                'clusters': [0] * len(df),
                'cluster_profiles': {0: {'size': len(df), 'municipios': df['municipio'].tolist()}}
            }

    def _calculate_cluster_profiles(self, df: pd.DataFrame) -> dict:
        """Calcula perfiles de cluster"""
        try:
            # Eliminar la decoración @lru_cache ya que causa el error de unhashable
            profiles = {}
            
            for cluster in df['cluster'].unique():
                cluster_data = df[df['cluster'] == cluster]
                
                profile = {
                    'size': len(cluster_data),
                    'municipios': cluster_data['municipio'].tolist(),
                    'actividades_promedio': float(cluster_data['num_actividades'].mean()),
                    'asistentes_promedio': float(cluster_data['total_asistentes'].mean()),
                    'eficiencia_promedio': float(cluster_data['eficiencia_actividad'].mean()),
                    'intensidad_mensual_promedio': float(cluster_data['intensidad_mensual'].mean())
                }
                
                profiles[int(cluster)] = profile
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error calculando perfiles de cluster: {str(e)}")
            return {0: {
                    'size': len(df),
                    'municipios': df['municipio'].tolist(),
                'actividades_promedio': 0.0,
                'asistentes_promedio': 0.0,
                'eficiencia_promedio': 0.0,
                'intensidad_mensual_promedio': 0.0
            }}

    def _apply_dbscan(self, df: pd.DataFrame) -> dict:
        """Aplica DBSCAN para análisis de densidad"""
        try:
            if 'dbscan' not in GeographicPredictor._models:
                raise ValueError("Modelo DBSCAN no encontrado")
            
            model_dict = GeographicPredictor._models['dbscan']
            dbscan = model_dict['model']
            features = model_dict['features']
            
            # Preparar datos
            X = df[features].copy()
            
            # Crear y ajustar un nuevo scaler para estos datos
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Predecir clusters
            clusters = dbscan.fit_predict(X_scaled)
            
            # Calcular estadísticas
            n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
            n_noise = list(clusters).count(-1)
            
            return {
                'clusters': clusters.tolist(),
                'n_clusters': n_clusters,
                'n_noise_points': n_noise
            }
            
        except Exception as e:
            logger.error(f"Error aplicando DBSCAN: {str(e)}")
            return {
                'clusters': [0] * len(df),
                'n_clusters': 1,
                'n_noise_points': 0
            }

    def _create_maps(self, df: pd.DataFrame, kmeans_results: dict, dbscan_results: dict) -> dict:
        """Crea visualizaciones de mapas"""
        try:
            # Crear mapa base
            center_lat = df['latitud'].mean()
            center_lon = df['longitud'].mean()
            
            # Mapa de clusters K-means
            kmeans_map = self._create_cluster_map(
                df, 
                kmeans_results['clusters'],
                'K-means Clusters'
            )
            
            # Mapa de densidad DBSCAN
            dbscan_map = self._create_density_map(
                df,
                dbscan_results['clusters'],
                'Análisis de Densidad'
            )
            
            # Mapa de calor de actividades
            heatmap = self._create_heatmap(df)
            
            return {
                'kmeans_map': kmeans_map,
                'dbscan_map': dbscan_map,
                'heatmap': heatmap
            }
            
        except Exception as e:
            logger.error(f"Error creando mapas: {str(e)}")
            return {}

    def _create_cluster_map(self, df: pd.DataFrame, clusters: list, title: str) -> folium.Map:
        """Crea mapa de clusters"""
        try:
            # Crear mapa base
            m = folium.Map(
                location=[df['latitud'].mean(), df['longitud'].mean()],
                zoom_start=7
            )
            
            # Crear colormap para clusters
            n_clusters = len(set(clusters))
            colors = px.colors.qualitative.Set3[:n_clusters]
            
            # Agregar marcadores por cluster
            for idx, row in df.iterrows():
                cluster = clusters[idx]
                color = colors[cluster]
                
                folium.CircleMarker(
                    location=[row['latitud'], row['longitud']],
                    radius=8,
                    popup=f"""
                        <b>{row['municipio']}</b><br>
                        Cluster: {cluster}<br>
                        Actividades: {row['num_actividades']}<br>
                        Asistentes: {row['total_asistentes']}
                    """,
                    color=color,
                    fill=True,
                    fill_color=color
                ).add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creando mapa de clusters: {str(e)}")
            return folium.Map()

    def _create_density_map(self, df: pd.DataFrame, clusters: list, title: str) -> folium.Map:
        """Crea mapa de densidad"""
        try:
            m = folium.Map(
                location=[df['latitud'].mean(), df['longitud'].mean()],
                zoom_start=7
            )
            
            # Crear heatmap de densidad
            heat_data = [[row['latitud'], row['longitud'], row['num_actividades']] 
                        for idx, row in df.iterrows()]
            
            plugins.HeatMap(heat_data).add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creando mapa de densidad: {str(e)}")
            return folium.Map()

    def _create_heatmap(self, df: pd.DataFrame) -> folium.Map:
        """Crea mapa de calor de actividades"""
        try:
            m = folium.Map(
                location=[df['latitud'].mean(), df['longitud'].mean()],
                zoom_start=7
            )
            
            # Normalizar valores para el heatmap
            max_activities = df['num_actividades'].max()
            heat_data = [[row['latitud'], row['longitud'], row['num_actividades']/max_activities] 
                        for idx, row in df.iterrows()]
            
            plugins.HeatMap(
                heat_data,
                min_opacity=0.5,
                max_val=1.0,
                radius=15,
                blur=10,
                gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
            ).add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creando mapa de calor: {str(e)}")
            return folium.Map()

    def _calculate_statistics(self, df: pd.DataFrame, kmeans_results: dict, dbscan_results: dict) -> dict:
        """Calcula estadísticas detalladas del análisis"""
        try:
            stats = {
                'general': {
                    'total_municipios': len(df),
                    'total_actividades': int(df['num_actividades'].sum()),
                    'total_asistentes': int(df['total_asistentes'].sum()),
                    'promedio_actividades': float(df['num_actividades'].mean()),
                    'promedio_asistentes': float(df['total_asistentes'].mean())
                },
                'clusters': self._calculate_cluster_statistics(df),
                'density': {
                    'high_density_areas': len([x for x in dbscan_results['clusters'] if x != -1]),
                    'isolated_points': dbscan_results['n_noise_points']
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            return {}

    def _calculate_cluster_statistics(self, df: pd.DataFrame) -> dict:
        """Calcula estadísticas por cluster"""
        try:
            stats = {}
            
            for cluster in df['cluster'].unique():
                cluster_data = df[df['cluster'] == cluster]
                
                stats[int(cluster)] = {
                    'size': len(cluster_data),
                    'total_actividades': int(cluster_data['num_actividades'].sum()),
                    'promedio_actividades': float(cluster_data['num_actividades'].mean()),
                    'total_asistentes': int(cluster_data['total_asistentes'].sum()),
                    'promedio_asistentes': float(cluster_data['total_asistentes'].mean()),
                    'municipios': cluster_data['municipio'].tolist()
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas de clusters: {str(e)}")
            return {}

    def _generate_recommendations(self, df: pd.DataFrame, kmeans_results: dict, dbscan_results: dict, input_data: dict) -> dict:
        """Genera recomendaciones basadas en el análisis"""
        try:
            recommendations = {
                'zonas_prioritarias': [],
                'oportunidades_expansion': [],
                'optimizacion_recursos': []
            }
            
            # Identificar zonas prioritarias
            low_activity_clusters = []
            for cluster, stats in kmeans_results.get('cluster_stats', {}).items():
                if stats['promedio_actividades'] < df['num_actividades'].mean() * 0.5:
                    low_activity_clusters.append({
                        'cluster': cluster,
                        'municipios': stats['municipios'],
                        'promedio_actual': stats['promedio_actividades']
                    })
            
            recommendations['zonas_prioritarias'] = low_activity_clusters
            
            # Identificar oportunidades de expansión
            high_density_areas = [
                i for i, c in enumerate(dbscan_results['clusters']) 
                if c != -1
            ]
            
            if high_density_areas:
                recommendations['oportunidades_expansion'] = [
                    {
                        'zona': i,
                        'municipios': df.iloc[i]['municipio'],
                        'potencial': 'Alto'
                    }
                    for i in high_density_areas[:3]
                ]
            
            # Recomendaciones de optimización
            recommendations['optimizacion_recursos'] = [
                {
                    'tipo': 'Redistribución',
                    'descripcion': 'Balancear actividades entre clusters',
                    'impacto_estimado': 'Medio'
                },
                {
                    'tipo': 'Focalización',
                    'descripcion': 'Concentrar recursos en zonas de alta densidad',
                    'impacto_estimado': 'Alto'
                }
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {}

    def _handle_empty_data(self) -> dict:
        """Maneja el caso de datos vacíos"""
        return {
            'data': pd.DataFrame(),
            'kmeans_results': {},
            'dbscan_results': {},
            'maps': {},
            'statistics': {},
            'recommendations': {},
            'error': 'No hay datos disponibles para los filtros seleccionados'
        }

    def _handle_prediction_error(self, error_message: str) -> dict:
        """Maneja errores en la predicción"""
        return {
            'data': pd.DataFrame(),
            'kmeans_results': {},
            'dbscan_results': {},
            'maps': {},
            'statistics': {},
            'recommendations': {},
            'error': f'Error en la predicción: {error_message}'
        }

    def predict_expansion_zones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predice zonas potenciales para expansión de actividades"""
        try:
            # Crear copia del DataFrame para no modificar el original
            df_expansion = df.copy()
            
            # Calcular métricas de potencial
            df_expansion['potencial_expansion'] = (
                (df_expansion['num_actividades'].max() - df_expansion['num_actividades']) / 
                df_expansion['num_actividades'].max()
            ) * 100
            
            # Calcular actividades sugeridas
            df_expansion['actividades_sugeridas'] = df_expansion.apply(
                lambda x: max(
                    int(x['num_actividades'] * 1.5),  # Mínimo 50% más que actual
                    int(df_expansion['num_actividades'].mean())  # O el promedio general
                ),
                axis=1
            )
            
            # Calcular score de prioridad
            df_expansion['prioridad_score'] = (
                df_expansion['potencial_expansion'] * 0.4 +  # Peso del potencial
                (df_expansion['eficiencia_actividad'] / df_expansion['eficiencia_actividad'].max()) * 0.3 +  # Peso de la eficiencia
                (df_expansion['intensidad_mensual'] / df_expansion['intensidad_mensual'].max()) * 0.3  # Peso de la intensidad
            )
            
            # Asignar categorías manualmente basado en percentiles
            percentiles = df_expansion['prioridad_score'].quantile([0.33, 0.66])
            df_expansion['categoria_expansion'] = 'Media Prioridad'
            df_expansion.loc[df_expansion['prioridad_score'] <= percentiles[0.33], 'categoria_expansion'] = 'Baja Prioridad'
            df_expansion.loc[df_expansion['prioridad_score'] > percentiles[0.66], 'categoria_expansion'] = 'Alta Prioridad'
            
            # Asegurar que todas las columnas necesarias estén presentes
            required_columns = [
                'municipio', 'departamento', 'num_actividades', 
                'potencial_expansion', 'actividades_sugeridas',
                'prioridad_score', 'categoria_expansion'
            ]
            
            for col in required_columns:
                if col not in df_expansion.columns:
                    logger.error(f"Columna faltante: {col}")
                    return pd.DataFrame()
            
            return df_expansion.sort_values('prioridad_score', ascending=False)
            
        except Exception as e:
            logger.error(f"Error en predicción de expansión: {str(e)}")
            return pd.DataFrame()

    def create_expansion_map(self, df: pd.DataFrame) -> folium.Map:
        """Crea mapa con predicciones de expansión"""
        try:
            m = folium.Map(
                location=[df['latitud'].mean(), df['longitud'].mean()],
                zoom_start=7,
                tiles='cartodbpositron'
            )
            
            # Normalizar los valores de potencial para mejor visualización
            max_potencial = df['potencial_expansion'].max()
            min_potencial = df['potencial_expansion'].min()
            
            # Agregar círculos con radio proporcional al potencial
            for _, row in df.iterrows():
                # Calcular el color basado en el potencial de expansión
                if row['potencial_expansion'] > 70:
                    color = '#ff4444'  # Rojo para alto potencial
                elif row['potencial_expansion'] > 40:
                    color = '#ffbb33'  # Naranja para potencial medio
                else:
                    color = '#00C851'  # Verde para bajo potencial
                
                # Crear popup detallado
                popup_html = f"""
                    <div style="font-family: Arial; width: 200px;">
                        <h4 style="margin-bottom: 10px;">{row['municipio']}</h4>
                        <b>Potencial:</b> {row['potencial_expansion']:.1f}%<br>
                        <b>Actividades actuales:</b> {int(row['num_actividades'])}<br>
                        <b>Actividades sugeridas:</b> {int(row['actividades_sugeridas'])}<br>
                        <b>Prioridad:</b> {row.get('categoria_expansion', 'No definida')}<br>
                        <b>Score:</b> {row.get('prioridad_score', 0):.2f}
                    </div>
                """
                
                # Ajustar el tamaño del círculo según el potencial
                radius = 8 + (row['potencial_expansion'] / 10)
                
                # Si hay un municipio seleccionado
                if 'municipio_seleccionado' in df.columns:
                    if row['municipio'] == df['municipio_seleccionado'].iloc[0]:
                        # Municipio seleccionado: resaltado y más grande
                        folium.CircleMarker(
                            location=[row['latitud'], row['longitud']],
                            radius=radius * 1.5,  # 50% más grande
                            popup=folium.Popup(popup_html, max_width=300),
                            color='white',
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.9,
                            weight=3
                        ).add_to(m)
                    else:
                        # Otros municipios: más tenues pero manteniendo su color
                        folium.CircleMarker(
                            location=[row['latitud'], row['longitud']],
                            radius=radius * 0.8,  # 20% más pequeño
                            popup=folium.Popup(popup_html, max_width=300),
                            color=color,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.4,  # Más transparente
                            weight=1
                        ).add_to(m)
                else:
                    # Visualización normal cuando no hay municipio seleccionado
                    folium.CircleMarker(
                        location=[row['latitud'], row['longitud']],
                        radius=radius,
                        popup=folium.Popup(popup_html, max_width=300),
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.7,
                        weight=1
                    ).add_to(m)
            
            # Agregar leyenda
            legend_html = """
            <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; 
                 background: white; padding: 10px; border-radius: 5px;">
                <h4 style="margin-bottom: 10px;">Potencial de Expansión</h4>
                <div style="display: flex; flex-direction: column; gap: 5px;">
                    <p><span style="color: #ff4444;">●</span> Alto (>70%)</p>
                    <p><span style="color: #ffbb33;">●</span> Medio (40-70%)</p>
                    <p><span style="color: #00C851;">●</span> Bajo (<40%)</p>
                </div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            return m
            
        except Exception as e:
            logger.error(f"Error creando mapa de expansión: {str(e)}")
            return None 

    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepara características para clustering"""
        try:
            feature_cols = [
                'num_actividades',
                'total_asistentes',
                'meses_activos',
                'eficiencia_actividad',
                'intensidad_mensual'
            ]
            features = data[feature_cols].copy()
            
            # Usar el scaler del modelo entrenado
            scaler = self.models.get('scaler')
            if scaler:
                features_scaled = scaler.transform(features)
                return pd.DataFrame(features_scaled, columns=feature_cols)
            else:
                logger.warning("Scaler no encontrado, usando datos sin normalizar")
                return features
            
        except Exception as e:
            logger.error(f"Error preparando features: {str(e)}")
            return pd.DataFrame() 