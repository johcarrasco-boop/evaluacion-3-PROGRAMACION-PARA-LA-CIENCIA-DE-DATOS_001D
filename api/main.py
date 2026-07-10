"""API RESTful para exponer métricas, datos y predicciones del proyecto Netflix."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "processed" / "netflix_analytics.db"
DEFAULT_RULES = PROJECT_ROOT / "data" / "sources" / "api_business_rules.json"
CLASSIFIER_PATH = PROJECT_ROOT / "models" / "artifacts" / "churn_classifier.pkl"
REGRESSOR_PATH = PROJECT_ROOT / "models" / "artifacts" / "watch_time_regressor.pkl"
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", DEFAULT_DB))

app = FastAPI(title="Netflix Churn Analytics API", version="2.0")


def read_table(table: str) -> pd.DataFrame:
    """Lee una tabla desde SQLite y controla errores de existencia."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base analítica no encontrada. Ejecutar ETL primero.")
    with sqlite3.connect(DB_PATH) as con:
        try:
            return pd.read_sql_query(f"SELECT * FROM {table}", con)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Tabla no encontrada: {table}") from exc


def read_user(user_id: int) -> pd.DataFrame:
    """Obtiene un usuario puntual desde la tabla clean_users."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base analítica no encontrada. Ejecutar ETL primero.")
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query("SELECT * FROM clean_users WHERE user_id = ?", con, params=[user_id])
    if df.empty:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return df


@app.get("/health")
def health() -> dict:
    """Comprueba estado general de API, base y artefactos ML."""
    return {
        "status": "ok",
        "database_exists": DB_PATH.exists(),
        "classifier_exists": CLASSIFIER_PATH.exists(),
        "regressor_exists": REGRESSOR_PATH.exists(),
    }


@app.get("/business-rules")
def business_rules() -> dict:
    """Entrega reglas de negocio usadas por el ETL."""
    with open(DEFAULT_RULES, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/summary")
def summary() -> dict:
    """Entrega KPIs globales del proyecto."""
    df = read_table("summary_metrics")
    return df.iloc[0].to_dict()


@app.get("/churn-by-activity")
def churn_by_activity() -> list[dict]:
    """Usuarios por nivel de actividad y churn."""
    return read_table("churn_by_activity").to_dict(orient="records")


@app.get("/churn-by-country")
def churn_by_country() -> list[dict]:
    """Usuarios por país y churn."""
    return read_table("churn_by_country").to_dict(orient="records")


@app.get("/users")
def users(limit: int = Query(default=20, ge=1, le=500), churned: str | None = None) -> list[dict]:
    """Lista usuarios procesados con filtro opcional de churn."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base analítica no encontrada. Ejecutar ETL primero.")
    query = "SELECT user_id, age, country, subscription_type, favorite_genre, nivel_actividad, riesgo_login, churned, engagement_score FROM clean_users"
    params: list[object] = []
    if churned:
        query += " WHERE churned = ?"
        params.append(churned)
    query += " LIMIT ?"
    params.append(limit)
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)
    return df.to_dict(orient="records")


@app.get("/model-metrics")
def model_metrics() -> dict:
    """Entrega métricas de clasificación, regresión y segmentación."""
    return {
        "classification": read_table("model_metrics_classification").to_dict(orient="records"),
        "regression": read_table("model_metrics_regression").to_dict(orient="records"),
        "clusters": read_table("cluster_summary").to_dict(orient="records"),
    }


@app.get("/confusion-matrix")
def confusion_matrix_best_model() -> list[dict]:
    """Matriz de confusión del mejor clasificador."""
    return read_table("confusion_matrix_best_model").to_dict(orient="records")


@app.get("/predict-churn/{user_id}")
def predict_churn_endpoint(user_id: int) -> dict:
    """Predice riesgo de churn para un usuario existente."""
    try:
        from models.predict import load_artifact, predict_churn
        artifact = load_artifact(CLASSIFIER_PATH)
        row = read_user(user_id)
        result = predict_churn(row, artifact)
        return {"user_id": user_id, **result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Modelo de clasificación no encontrado. Ejecutar models/train_models.py") from exc


@app.get("/predict-watch-time/{user_id}")
def predict_watch_time_endpoint(user_id: int) -> dict:
    """Predice tiempo promedio de visualización para un usuario existente."""
    try:
        from models.predict import load_artifact, predict_watch_time
        artifact = load_artifact(REGRESSOR_PATH)
        row = read_user(user_id)
        result = predict_watch_time(row, artifact)
        return {"user_id": user_id, **result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Modelo de regresión no encontrado. Ejecutar models/train_models.py") from exc
