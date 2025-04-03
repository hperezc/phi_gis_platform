from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
from ..models.attendance_predictor import AttendancePredictor
from ..preprocessing.data_cleaner import DataCleaner
from ..config import ATTENDANCE_FEATURES
from ..utils.data_loader import DataLoader
from sqlalchemy import text

router = APIRouter(prefix="/ml", tags=["machine-learning"])

# Modelos de datos
class PredictionRequest(BaseModel):
    departamento: str
    municipio: str
    zona_geografica: str
    categoria_actividad: str
    grupo_interes: str
    fecha: datetime

class PredictionResponse(BaseModel):
    predicted_attendance: int
    confidence_score: float
    features_importance: dict

# 1. Endpoints de datos geográficos (en orden de selección)
@router.get("/zonas-geograficas")
async def get_zonas_geograficas():
    """Obtiene lista de zonas geográficas disponibles"""
    try:
        data_loader = DataLoader()
        zonas = data_loader.get_zonas_geograficas()
        
        return {
            "status": "success",
            "data": {
                "zonas_geograficas": zonas,
                "total": len(zonas)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo zonas geográficas: {str(e)}"
        )

@router.get("/departamentos")
async def get_departamentos(zona_geografica: str = Query(None)):
    """Obtiene departamentos, opcionalmente filtrados por zona geográfica"""
    try:
        data_loader = DataLoader()
        if zona_geografica:
            departamentos = data_loader.get_departamentos_por_zona(zona_geografica)
        else:
            query = """
                SELECT DISTINCT departamento 
                FROM actividades 
                WHERE departamento IS NOT NULL 
                ORDER BY departamento
            """
            with data_loader.engine.connect() as conn:
                result = conn.execute(text(query))
                departamentos = [row[0] for row in result]
        
        return {
            "status": "success",
            "data": {
                "zona_geografica": zona_geografica,
                "departamentos": departamentos,
                "total": len(departamentos)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo departamentos: {str(e)}"
        )

@router.get("/municipios")
async def get_municipios(
    departamento: str = Query(None),
    zona_geografica: str = Query(None)
):
    """Obtiene municipios filtrados por departamento y/o zona geográfica"""
    try:
        data_loader = DataLoader()
        municipios = data_loader.get_municipios(departamento, zona_geografica)
        
        return {
            "status": "success",
            "data": {
                "municipios": municipios,
                "total": len(municipios),
                "filtros": {
                    "departamento": departamento,
                    "zona_geografica": zona_geografica
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo municipios: {str(e)}"
        )

@router.get("/municipios/{municipio}/stats")
async def get_municipio_stats(municipio: str):
    """Obtiene estadísticas para un municipio específico"""
    try:
        predictor = AttendancePredictor()
        stats = predictor.get_municipio_stats(municipio)
        
        if stats is None:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron datos para el municipio {municipio}"
            )
            
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

# 2. Endpoints de predicción y métricas
@router.post("/predict-attendance", response_model=PredictionResponse)
async def predict_attendance(request: PredictionRequest):
    """Realiza predicción de asistentes"""
    try:
        data = {
            'departamento': [request.departamento],
            'municipio': [request.municipio],
            'zona_geografica': [request.zona_geografica],
            'categoria_actividad': [request.categoria_actividad],
            'grupo_interes': [request.grupo_interes],
            'fecha': [request.fecha]
        }
        
        df = pd.DataFrame(data)
        cleaner = DataCleaner()
        df_cleaned = cleaner.clean_attendance_data(df)
        
        predictor = AttendancePredictor()
        predictor.load_model()
        
        X = df_cleaned[ATTENDANCE_FEATURES]
        prediction = predictor.predict(X)[0]
        
        feature_importance = dict(zip(
            ATTENDANCE_FEATURES,
            predictor.model.feature_importances_
        ))
        
        return {
            "predicted_attendance": int(max(0, round(prediction))),
            "confidence_score": float(predictor.model.best_score),
            "features_importance": feature_importance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-metrics")
async def get_model_metrics():
    """Obtiene métricas del modelo"""
    try:
        predictor = AttendancePredictor()
        predictor.load_model()
        
        return {
            "model_version": "1.0",
            "last_training": datetime.now().isoformat(),
            "metrics": {
                "rmse": float(predictor.model.best_score),
                "feature_importance": dict(zip(
                    ATTENDANCE_FEATURES,
                    predictor.model.feature_importances_
                ))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 