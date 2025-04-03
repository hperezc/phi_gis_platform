import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import joblib
import json
import logging
import folium
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
from kneed import KneeLocator
from sqlalchemy import text

# Ajustar el path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import DataLoader

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GeographicTrainer:
    def __init__(self):
        self.data_loader = DataLoader()
        self.models = {}
        self.metrics = {}
        self.scaler = StandardScaler()
        self.kmeans_model = None
        self.dbscan_model = None
        self.feature_weights = None
        self.type_specific_weights = {}
        
    def prepare_geographic_data(self):
        """Prepara los datos geográficos para el clustering"""
        try:
            query = """
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
                categorias_municipio AS (
                    SELECT 
                        municipio,
                        departamento,
                        categoria_unica::integer as categoria_unica,
                        COUNT(*) as conteo
                    FROM actividades
                    WHERE categoria_unica IS NOT NULL
                    AND categoria_unica ~ '^[0-9]+$'  -- Asegurar que es numérico
                    GROUP BY municipio, departamento, categoria_unica
                ),
                categoria_principal AS (
                    SELECT DISTINCT ON (municipio, departamento)
                        municipio,
                        departamento,
                        categoria_unica
                    FROM categorias_municipio
                    ORDER BY municipio, departamento, conteo DESC
                ),
                activity_stats AS (
                    SELECT 
                        m.municipio,
                        m.departamento,
                        m.zona_geografica,
                        ST_X(ST_Centroid(m.geometry::geometry)) as longitud,
                        ST_Y(ST_Centroid(m.geometry::geometry)) as latitud,
                        COUNT(a.*) as num_actividades,
                        SUM(COALESCE(a.total_asistentes, 0)) as total_asistentes,
                        COUNT(DISTINCT EXTRACT(MONTH FROM a.fecha)) as meses_activos,
                        COALESCE(cp.categoria_unica, 0) as categoria_unica,
                        COUNT(*) as actividades_tipo
                    FROM municipios_base m
                    LEFT JOIN actividades a ON 
                        m.municipio = a.municipio AND 
                        m.departamento = a.departamento AND
                        a.fecha >= '2014-01-01'
                    LEFT JOIN categoria_principal cp ON
                        m.municipio = cp.municipio AND
                        m.departamento = cp.departamento
                    GROUP BY 
                        m.municipio, 
                        m.departamento, 
                        m.zona_geografica,
                        m.geometry,
                        cp.categoria_unica
                )
                SELECT 
                    municipio,
                    departamento,
                    zona_geografica,
                    longitud,
                    latitud,
                    num_actividades,
                    total_asistentes,
                    meses_activos,
                    categoria_unica,
                    actividades_tipo,
                    CASE 
                        WHEN num_actividades > 0 THEN total_asistentes::float / num_actividades 
                        ELSE 0 
                    END as promedio_asistentes,
                    CASE 
                        WHEN meses_activos > 0 THEN num_actividades::float / meses_activos 
                        ELSE 0 
                    END as intensidad_mensual,
                    CASE 
                        WHEN num_actividades > 0 THEN total_asistentes::float / num_actividades 
                        ELSE 0 
                    END as eficiencia_actividad
                FROM activity_stats
                WHERE longitud IS NOT NULL AND latitud IS NOT NULL
            """
            
            df = pd.read_sql(query, self.data_loader.engine)
            logger.info(f"Datos geográficos cargados: {len(df)} municipios")
            
            # Validar que tenemos coordenadas válidas
            df = df.dropna(subset=['latitud', 'longitud'])
            df = df[
                (df['latitud'] != 0) & 
                (df['longitud'] != 0) &
                (df['latitud'].between(-4.5, 13.5)) &  # Rango aproximado para Colombia
                (df['longitud'].between(-82, -66))  # Rango aproximado para Colombia
            ]
            
            # Asegurar que categoria_unica es numérica
            df['categoria_unica'] = pd.to_numeric(df['categoria_unica'], errors='coerce')
            df['categoria_unica'] = df['categoria_unica'].fillna(0).astype(int)
            
            logger.info(f"Municipios con coordenadas válidas: {len(df)}")
            
            # Mostrar resumen de actividades por departamento
            dept_summary = df.groupby('departamento').agg({
                'municipio': 'count',
                'num_actividades': 'sum'
            }).rename(columns={'municipio': 'num_municipios'})
            
            logger.info("\nResumen por departamento:")
            for dept, row in dept_summary.iterrows():
                logger.info(f"{dept}: {row['num_municipios']} municipios, {row['num_actividades']} actividades")
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparando datos geográficos: {str(e)}")
            raise

    def find_optimal_clusters(self, data, max_clusters=10):
        """Encuentra el número óptimo de clusters usando el método del codo"""
        try:
            inertias = []
            silhouette_scores = []
            
            # Calcular inertia y silhouette score para diferentes números de clusters
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42)
                kmeans.fit(data)
                inertias.append(kmeans.inertia_)
                silhouette_scores.append(silhouette_score(data, kmeans.labels_))
            
            # Usar KneeLocator para encontrar el punto de inflexión
            kl = KneeLocator(
                range(2, max_clusters + 1), 
                inertias,
                curve='convex', 
                direction='decreasing'
            )
            
            optimal_clusters = kl.elbow
            
            # Guardar gráfico del método del codo
            plt.figure(figsize=(10, 6))
            plt.plot(range(2, max_clusters + 1), inertias, 'bx-')
            plt.xlabel('k')
            plt.ylabel('Inertia')
            plt.title('Método del Codo para Número Óptimo de Clusters')
            plt.axvline(x=optimal_clusters, color='r', linestyle='--')
            plt.savefig(root_dir / 'models/geographic_models/elbow_plot.png')
            plt.close()
            
            return optimal_clusters if optimal_clusters else 4  # Default a 4 si no se encuentra un punto claro
            
        except Exception as e:
            logger.error(f"Error encontrando clusters óptimos: {str(e)}")
            return 4  # Valor por defecto

    def train_kmeans_model(self, df):
        """Entrena modelo K-means para clustering geográfico"""
        try:
            # Preparar features para clustering
            features = [
                'latitud', 'longitud', 'num_actividades',
                'total_asistentes', 'intensidad_mensual',
                'tipos_actividad', 'eficiencia_actividad'
            ]
            
            X = df[features].copy()
            
            # Escalar datos
            X_scaled = self.scaler.fit_transform(X)
            
            # Encontrar número óptimo de clusters
            n_clusters = self.find_optimal_clusters(X_scaled)
            logger.info(f"Número óptimo de clusters: {n_clusters}")
            
            # Entrenar modelo K-means
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            
            kmeans.fit(X_scaled)
            
            # Calcular métricas
            silhouette_avg = silhouette_score(X_scaled, kmeans.labels_)
            
            # Guardar modelo y métricas
            self.models['kmeans'] = {
                'model': kmeans,
                'scaler': self.scaler,
                'features': features
            }
            
            self.metrics['kmeans'] = {
                'silhouette_score': float(silhouette_avg),
                'inertia': float(kmeans.inertia_),
                'n_clusters': n_clusters
            }
            
            # Agregar clusters al DataFrame
            df['cluster'] = kmeans.labels_
            
            # Calcular características de cada cluster
            cluster_profiles = self._calculate_cluster_profiles(df)
            self.metrics['kmeans']['cluster_profiles'] = cluster_profiles
            
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelo K-means: {str(e)}")
            raise

    def train_dbscan_model(self, df):
        """Entrena modelo DBSCAN para detección de zonas de densidad"""
        try:
            # Preparar features para clustering
            features = ['latitud', 'longitud', 'num_actividades']
            X = df[features].copy()
            
            # Escalar datos
            X_scaled = StandardScaler().fit_transform(X)
            
            # Encontrar eps óptimo usando NearestNeighbors
            neighbors = NearestNeighbors(n_neighbors=2)
            neighbors_fit = neighbors.fit(X_scaled)
            distances, indices = neighbors_fit.kneighbors(X_scaled)
            distances = np.sort(distances, axis=0)
            distances = distances[:,1]
            
            # Usar el "punto de codo" como eps
            knee = KneeLocator(
                range(len(distances)), 
                distances,
                curve='convex', 
                direction='increasing'
            )
            eps = distances[knee.knee] if knee.knee else 0.5
            
            # Entrenar DBSCAN
            dbscan = DBSCAN(
                eps=eps,
                min_samples=3,
                metric='euclidean'
            )
            
            dbscan.fit(X_scaled)
            
            # Guardar modelo y métricas
            self.models['dbscan'] = {
                'model': dbscan,
                'scaler': StandardScaler(),
                'features': features
            }
            
            # Calcular métricas
            n_clusters = len(set(dbscan.labels_)) - (1 if -1 in dbscan.labels_ else 0)
            n_noise = list(dbscan.labels_).count(-1)
            
            self.metrics['dbscan'] = {
                'n_clusters': n_clusters,
                'n_noise_points': n_noise,
                'eps_value': float(eps)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelo DBSCAN: {str(e)}")
            raise

    def _calculate_cluster_profiles(self, df):
        """Calcula perfiles detallados de cada cluster"""
        profiles = {}
        
        for cluster in df['cluster'].unique():
            cluster_data = df[df['cluster'] == cluster]
            
            profile = {
                'size': len(cluster_data),
                'municipios': cluster_data['municipio'].tolist(),
                'actividades_promedio': float(cluster_data['num_actividades'].mean()),
                'asistentes_promedio': float(cluster_data['total_asistentes'].mean()),
                'eficiencia_promedio': float(cluster_data['eficiencia_actividad'].mean()),
                'intensidad_mensual_promedio': float(cluster_data['intensidad_mensual'].mean()),
                'tipos_actividad_promedio': float(cluster_data['tipos_actividad'].mean()),
                'centroide': {
                    'lat': float(cluster_data['latitud'].mean()),
                    'lon': float(cluster_data['longitud'].mean())
                }
            }
            
            profiles[int(cluster)] = profile
        
        return profiles

    def save_models(self, save_path='models/geographic_models'):
        """Guarda los modelos entrenados y sus métricas"""
        try:
            save_dir = Path(root_dir) / save_path
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar modelos y scaler
            models_to_save = {
                'kmeans': self.kmeans_model,
                'dbscan': self.dbscan_model,
                'scaler': self.scaler,
                'feature_weights': self.feature_weights,
                'type_specific_weights': {
                    str(k.split('_')[-1]): v  # Convertir 'type_2' a '2'
                    for k, v in self.type_specific_weights.items()
                }
            }
            
            for name, model in models_to_save.items():
                if model is not None:
                    model_path = save_dir / f'{name}_model.joblib'
                    joblib.dump(model, model_path)
                    logger.info(f"Guardado {name} en {model_path}")
            
            # Convertir métricas a tipos nativos de Python
            metrics_json = {}
            for model_name, metrics in self.metrics.items():
                metrics_json[model_name] = {}
                for key, value in metrics.items():
                    if isinstance(value, dict):
                        # Para diccionarios anidados (como cluster_profiles)
                        metrics_json[model_name][key] = {}
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, dict):
                                # Para perfiles de cluster
                                metrics_json[model_name][key][int(subkey)] = {
                                    k: float(v) if isinstance(v, (np.float32, np.float64, np.int32, np.int64))
                                    else [str(x) if isinstance(x, np.int32) else x for x in v] if isinstance(v, list)
                                    else v
                                    for k, v in subvalue.items()
                                }
                            else:
                                metrics_json[model_name][key][int(subkey) if isinstance(subkey, np.int32) else subkey] = (
                                    float(subvalue) if isinstance(subvalue, (np.float32, np.float64, np.int32, np.int64))
                                    else subvalue
                                )
                    else:
                        # Para métricas simples
                        metrics_json[model_name][key] = (
                            float(value) if isinstance(value, (np.float32, np.float64, np.int32, np.int64))
                            else value
                        )
            
            # Guardar métricas
            metrics_path = save_dir / 'model_metrics.json'
            with open(metrics_path, 'w') as f:
                json.dump(metrics_json, f, indent=2)
            
            logger.info(f"Modelos y métricas guardados en {save_dir}")
            
        except Exception as e:
            logger.error(f"Error guardando modelos: {str(e)}")
            raise

    def train(self, data: pd.DataFrame) -> dict:
        """Entrena los modelos y calcula pesos"""
        try:
            # Preparar features
            features = self._prepare_features(data)
            
            # Entrenar K-means
            self.kmeans_model = self._train_kmeans(features)
            
            # Entrenar DBSCAN
            self.dbscan_model = self._train_dbscan(features)
            
            # Debug: Imprimir distribución de categorías
            logger.info("\nDistribución de categorías:")
            logger.info(data['categoria_unica'].value_counts())
            
            # Calcular pesos específicos por tipo
            for tipo in range(1, 8):
                tipo_key = str(tipo)
                # Filtrar datos para este tipo
                tipo_data = data[data['categoria_unica'] == tipo]
                
                logger.info(f"\nDatos para tipo {tipo_key}:")
                logger.info(f"Número de registros: {len(tipo_data)}")
                
                if not tipo_data.empty:
                    # Calcular correlaciones específicas
                    correlations = abs(tipo_data[[
                        'num_actividades',
                        'total_asistentes',
                        'eficiencia_actividad'
                    ]].corr()['eficiencia_actividad'])
                    
                    # Normalizar correlaciones
                    total_corr = correlations.sum()
                    self.type_specific_weights[tipo_key] = {
                        'actividades': float(correlations['num_actividades'] / total_corr),
                        'asistentes': float(correlations['total_asistentes'] / total_corr),
                        'eficiencia': float(correlations['eficiencia_actividad'] / total_corr)
                    }
                    logger.info(f"Calculados pesos para tipo {tipo_key}: {self.type_specific_weights[tipo_key]}")
                else:
                    # Si no hay datos para este tipo, usar pesos generales
                    self.type_specific_weights[tipo_key] = {
                        'actividades': 0.33,
                        'asistentes': 0.33,
                        'eficiencia': 0.34
                    }
                    logger.info(f"No hay datos para tipo {tipo_key}, usando pesos generales")
            
            # Guardar modelos y pesos
            self.save_models()
            
            return {
                'kmeans_model': self.kmeans_model,
                'dbscan_model': self.dbscan_model,
                'feature_weights': self.feature_weights,
                'type_specific_weights': self.type_specific_weights
            }
            
        except Exception as e:
            logger.error(f"Error en entrenamiento: {str(e)}")
            return {}
    
    def _calculate_feature_weights(self, data: pd.DataFrame) -> dict:
        """Calcula pesos óptimos basados en correlaciones con eficiencia"""
        try:
            # Calcular correlaciones con eficiencia_actividad
            correlations = abs(data[[
                'num_actividades',
                'total_asistentes',
                'eficiencia_actividad'
            ]].corr()['eficiencia_actividad'])
            
            # Normalizar correlaciones como pesos
            total_corr = correlations.sum()
            weights = {
                'actividades': correlations['num_actividades'] / total_corr,
                'asistentes': correlations['total_asistentes'] / total_corr,
                'eficiencia': correlations['eficiencia_actividad'] / total_corr
            }
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculando pesos: {str(e)}")
            return {
                'actividades': 0.3,
                'asistentes': 0.3,
                'eficiencia': 0.4
            }
    
    def _calculate_type_specific_weights(self, data: pd.DataFrame) -> dict:
        """Calcula pesos específicos para cada tipo de actividad"""
        try:
            type_weights = {}
            
            for tipo in data['tipos_actividad'].unique():
                # Filtrar datos para este tipo
                df_tipo = data[data['tipos_actividad'] == tipo]
                
                if not df_tipo.empty:
                    # Calcular correlaciones específicas
                    correlations = abs(df_tipo[[
                        'num_actividades',
                        'total_asistentes',
                        'eficiencia_actividad'
                    ]].corr()['eficiencia_actividad'])
                    
                    # Normalizar correlaciones
                    total_corr = correlations.sum()
                    type_weights[f'type_{tipo}'] = {
                        'actividades': correlations['num_actividades'] / total_corr,
                        'asistentes': correlations['total_asistentes'] / total_corr,
                        'eficiencia': correlations['eficiencia_actividad'] / total_corr
                    }
            
            return type_weights
            
        except Exception as e:
            logger.error(f"Error calculando pesos por tipo: {str(e)}")
            return {}

    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepara y normaliza features para clustering"""
        try:
            features = data[[
                'num_actividades',
                'total_asistentes',
                'meses_activos',
                'eficiencia_actividad',
                'intensidad_mensual'
            ]].copy()
            
            # Normalizar features
            features_scaled = self.scaler.fit_transform(features)
            return pd.DataFrame(features_scaled, columns=features.columns)
        except Exception as e:
            logger.error(f"Error preparando features: {str(e)}")
            return pd.DataFrame()

    def _train_kmeans(self, features: pd.DataFrame) -> KMeans:
        """Entrena modelo K-means"""
        try:
            kmeans = KMeans(n_clusters=5, random_state=42)
            kmeans.fit(features)
            return kmeans
        except Exception as e:
            logger.error(f"Error entrenando K-means: {str(e)}")
            return None

    def _train_dbscan(self, features: pd.DataFrame) -> DBSCAN:
        """Entrena modelo DBSCAN"""
        try:
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            dbscan.fit(features)
            return dbscan
        except Exception as e:
            logger.error(f"Error entrenando DBSCAN: {str(e)}")
            return None

    def validate_models(self, data: pd.DataFrame) -> dict:
        """Valida los modelos entrenados"""
        try:
            validation_metrics = {}
            
            # Validar K-means
            if self.kmeans_model:
                inertia = self.kmeans_model.inertia_
                validation_metrics['kmeans'] = {
                    'inertia': inertia,
                    'n_clusters': len(set(self.kmeans_model.labels_))
                }
            
            # Validar pesos
            if self.feature_weights:
                validation_metrics['weights'] = {
                    'correlation_score': self._calculate_weight_correlation(data)
                }
            
            return validation_metrics
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            return {}

    def calculate_priority_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula scores de priorización para cada municipio"""
        try:
            scores = pd.DataFrame()
            scores['general_score'] = (
                data['num_actividades'] * self.feature_weights['actividades'] +
                data['total_asistentes'] * self.feature_weights['asistentes'] +
                data['eficiencia_actividad'] * self.feature_weights['eficiencia']
            )
            
            # Calcular scores específicos por tipo
            for tipo, weights in self.type_specific_weights.items():
                scores[f'{tipo}_score'] = (
                    data['num_actividades'] * weights['actividades'] +
                    data['total_asistentes'] * weights['asistentes'] +
                    data['eficiencia_actividad'] * weights['eficiencia']
                )
            
            return scores
        except Exception as e:
            logger.error(f"Error calculando scores: {str(e)}")
            return pd.DataFrame()

    def _calculate_weight_correlation(self, data: pd.DataFrame) -> float:
        """Calcula la correlación entre los pesos y la eficiencia"""
        try:
            weighted_score = (
                data['num_actividades'] * self.feature_weights['actividades'] +
                data['total_asistentes'] * self.feature_weights['asistentes'] +
                data['eficiencia_actividad'] * self.feature_weights['eficiencia']
            )
            return abs(weighted_score.corr(data['eficiencia_actividad']))
        except Exception as e:
            logger.error(f"Error calculando correlación de pesos: {str(e)}")
            return 0.0

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida que los datos cumplan los requisitos mínimos"""
        try:
            # Verificar número mínimo de registros
            if len(data) < 10:
                logger.error("Insuficientes datos para entrenar")
                return False
            
            # Verificar que no hay valores negativos en métricas clave
            for col in ['num_actividades', 'total_asistentes', 'eficiencia_actividad']:
                if (data[col] < 0).any():
                    logger.error(f"Valores negativos encontrados en {col}")
                    return False
                
            return True
        
        except Exception as e:
            logger.error(f"Error validando datos: {str(e)}")
            return False

if __name__ == "__main__":
    trainer = GeographicTrainer()
    
    try:
        # Primero obtener los datos geográficos preparados
        data = trainer.prepare_geographic_data()
        logger.info(f"Datos cargados: {len(data)} registros")
        
        # Verificar columnas requeridas
        required_columns = [
            'num_actividades',
            'total_asistentes',
            'meses_activos',
            'eficiencia_actividad',
            'intensidad_mensual'
        ]
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"Faltan columnas requeridas: {missing_columns}")
            raise ValueError(f"Faltan columnas requeridas: {missing_columns}")
        
        # Entrenar modelos
        metrics = trainer.train(data)
        
        if metrics:
            logger.info("Entrenamiento exitoso")
            logger.info(f"Métricas de entrenamiento: {metrics}")
            
            # Guardar modelos
            trainer.save_models()
        else:
            logger.error("Error en el entrenamiento")
            
    except Exception as e:
        logger.error(f"Error en el proceso de entrenamiento: {str(e)}") 