import pandas as pd
import numpy as np
from typing import Dict, List
import logging
import streamlit as st

logger = logging.getLogger(__name__)

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def calculate_municipal_metrics(mun_data: pd.Series, dept_data: pd.DataFrame) -> Dict:
    """Calcula métricas específicas para un municipio con cache"""
    try:
        # Pre-calcular métricas departamentales
        dept_stats = {
            'rankings': dept_data['num_actividades'].rank(ascending=False),
            'percentiles': dept_data['num_actividades'].rank(pct=True) * 100,
            'mean': float(dept_data['num_actividades'].mean())
        }
        
        metrics = {
            'general': {
                'total_actividades': int(mun_data['num_actividades']),
                'total_asistentes': int(mun_data['total_asistentes']),
                'promedio_mensual': float(mun_data['intensidad_mensual']),
                'eficiencia': float(mun_data['eficiencia_actividad'])
            },
            'comparacion_departamental': {
                'ranking_actividades': int(dept_stats['rankings'][mun_data.name]),
                'percentil_actividades': float(dept_stats['percentiles'][mun_data.name]),
                'promedio_departamental': dept_stats['mean'],
                'total_municipios_dept': len(dept_data),
                'posicion_relativa': 'Por encima' if mun_data['num_actividades'] > dept_stats['mean'] else 'Por debajo'
            },
            'tendencias': {
                'meses_activos': int(mun_data['meses_activos']),
                'anos_activos': int(mun_data['anos_activos']),
                'tipos_actividad': int(mun_data['tipos_actividad']),
                'grupos_interes': int(mun_data['grupos_interes']),
                'dia_semana_promedio': float(mun_data['dia_semana_promedio'])
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculando métricas municipales: {str(e)}")
        return {}

@st.cache_data(ttl=1800)
def generate_municipal_recommendations(metrics: Dict) -> List[Dict]:
    """Genera recomendaciones específicas con cache"""
    recommendations = []
    
    try:
        # Recomendación basada en actividad vs promedio departamental
        if metrics['comparacion_departamental']['posicion_relativa'] == 'Por debajo':
            gap = metrics['comparacion_departamental']['promedio_departamental'] - metrics['general']['total_actividades']
            recommendations.append({
                'tipo': 'Incremento de Actividades',
                'descripcion': f'Aumentar en {int(gap)} actividades para alcanzar el promedio departamental',
                'prioridad': 'Alta' if gap > metrics['general']['total_actividades'] else 'Media'
            })
        
        # Recomendación basada en eficiencia
        if metrics['general']['eficiencia'] < 20:  # menos de 20 asistentes por actividad
            recommendations.append({
                'tipo': 'Mejora de Convocatoria',
                'descripcion': 'Fortalecer estrategias de convocatoria para aumentar asistencia',
                'prioridad': 'Alta'
            })
        
        # Recomendación basada en diversificación
        if metrics['tendencias']['tipos_actividad'] < 3:
            recommendations.append({
                'tipo': 'Diversificación',
                'descripcion': 'Ampliar la variedad de tipos de actividades',
                'prioridad': 'Media'
            })
        
        # Recomendación basada en regularidad
        meses_esperados = metrics['tendencias']['anos_activos'] * 12
        if metrics['tendencias']['meses_activos'] < (meses_esperados * 0.5):
            recommendations.append({
                'tipo': 'Regularidad',
                'descripcion': 'Aumentar la frecuencia mensual de actividades',
                'prioridad': 'Alta'
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generando recomendaciones: {str(e)}")
        return []

def generate_interest_group_recommendations(data_frame: pd.DataFrame, tipo_actividad: str = None, municipio_seleccionado: str = None, max_actividades_objetivo: int = 200) -> pd.DataFrame:
    """
    Genera recomendaciones de priorización por grupos de interés, por municipio
    Asigna máximo una actividad del mismo tipo por grupo de interés
    Limita las priorizaciones al número objetivo de actividades
    
    Args:
        data_frame: DataFrame con los datos de actividades
        tipo_actividad: Tipo de actividad seleccionada
        municipio_seleccionado: Municipio seleccionado para filtrar
        max_actividades_objetivo: Número máximo de actividades a priorizar
        
    Returns:
        DataFrame con recomendaciones por grupo de interés
    """
    try:
        if data_frame.empty:
            return pd.DataFrame()
            
        # Crear copia del DataFrame para no modificar el original
        df = data_frame.copy()
        
        # Filtrar por municipio si está seleccionado
        if municipio_seleccionado and municipio_seleccionado != "Todos":
            df = df[df['municipio'] == municipio_seleccionado]
            
        if df.empty:
            return pd.DataFrame()
            
        # Asegurarse que tenemos las columnas necesarias
        if 'nombre_grupo_interes' not in df.columns:
            if 'grupo_interes_id' in df.columns:
                df['nombre_grupo_interes'] = 'Grupo ' + df['grupo_interes_id'].astype(str)
            else:
                df['nombre_grupo_interes'] = 'Grupo Desconocido'
                
        # Usar actividades por grupo si está disponible
        if 'actividades_por_grupo' in df.columns:
            activity_col = 'actividades_por_grupo'
        else:
            activity_col = 'num_actividades'
            
        # Usar eficiencia por grupo si está disponible
        if 'eficiencia_actividad_grupo' in df.columns:
            efficiency_col = 'eficiencia_actividad_grupo'
        else:
            efficiency_col = 'eficiencia_actividad'
            
        # Agrupar por municipio y grupo de interés
        grupos_df = df.groupby(['municipio', 'grupo_interes_id', 'nombre_grupo_interes']).agg({
            activity_col: 'mean',  # Promedio de actividades por grupo
            'total_asistentes': 'sum',
            efficiency_col: 'mean',
        }).reset_index()
        
        # Calcular score por grupo de interés
        grupos_df['score_grupo'] = grupos_df[efficiency_col] * 0.7 + \
                                 (grupos_df[activity_col] / grupos_df[activity_col].max() if grupos_df[activity_col].max() > 0 else 0) * 0.3
                                  
        # Asignar prioridades basadas en percentiles del score
        grupos_df['prioridad_grupo'] = pd.qcut(
            grupos_df['score_grupo'], 
            q=3, 
            labels=['Baja', 'Media', 'Alta'],
            duplicates='drop'
        ).astype(str)
        
        # Para cada municipio, calcular el promedio de actividades objetivo
        municipios_df = df.groupby('municipio')[activity_col].mean().reset_index()
        municipios_df['actividades_objetivo'] = municipios_df[activity_col] * 1.2  # 20% más del promedio
        
        # Fusionar con datos de grupos
        grupos_df = grupos_df.merge(municipios_df[['municipio', 'actividades_objetivo']], on='municipio', how='left')
        
        # Calcular diferencia respecto al objetivo
        grupos_df['diferencia_grupo'] = grupos_df[activity_col] - grupos_df['actividades_objetivo']
        grupos_df['diferencia_grupo'] = grupos_df['diferencia_grupo'].round().astype(int)
        
        # Determinar acción a tomar (aumentar o reducir actividades)
        grupos_df['accion_grupo'] = grupos_df['diferencia_grupo'].apply(
            lambda x: 'Incrementar' if x < 0 else 'Reducir'
        )
        
        # Calcular actividades sugeridas por grupo - LÍMITE UNA POR GRUPO DE INTERÉS
        if tipo_actividad:
            grupos_df['actividades_sugeridas_grupo'] = 1  # Máximo una actividad del mismo tipo por grupo
        else:
            # Si no hay tipo de actividad seleccionado, calcular normal pero máximo 1 por grupo
            grupos_df['actividades_sugeridas_grupo'] = grupos_df.apply(
                lambda row: max(
                    1,  # Mínimo 1 actividad
                    min(
                        # No más de 1
                        1,
                        round(row[activity_col] - abs(row['diferencia_grupo'])) if row['accion_grupo'] == 'Reducir' else
                        round(row[activity_col] + abs(row['diferencia_grupo']))
                    )
                ),
                axis=1
            )
        
        # Ordenar por score para priorización (de mayor a menor)
        grupos_df = grupos_df.sort_values('score_grupo', ascending=False)
        
        # Limitar el número total de actividades sugeridas al objetivo
        total_actividades = 0
        grupos_limitados = []
        
        for _, row in grupos_df.iterrows():
            # Si ya alcanzamos el máximo, solo incluir con 0 actividades
            if total_actividades >= max_actividades_objetivo:
                row_copy = row.copy()
                row_copy['actividades_sugeridas_grupo'] = 0
                row_copy['accion_grupo'] = 'No priorizar'
                grupos_limitados.append(row_copy)
            else:
                actividades_a_sugerir = min(
                    row['actividades_sugeridas_grupo'],
                    max_actividades_objetivo - total_actividades
                )
                row_copy = row.copy()
                row_copy['actividades_sugeridas_grupo'] = actividades_a_sugerir
                grupos_limitados.append(row_copy)
                total_actividades += actividades_a_sugerir
                
        # Convertir a DataFrame
        grupos_limitados_df = pd.DataFrame(grupos_limitados)
        
        # Calcular cuántos grupos de interés han sido priorizados (con al menos 1 actividad)
        grupos_priorizados = len(grupos_limitados_df[grupos_limitados_df['actividades_sugeridas_grupo'] > 0])
        
        print(f"Priorizados {grupos_priorizados} grupos de interés con un total de {total_actividades} actividades")
        
        return grupos_limitados_df
        
    except Exception as e:
        logger.error(f"Error generando recomendaciones por grupo de interés: {str(e)}")
        return pd.DataFrame() 