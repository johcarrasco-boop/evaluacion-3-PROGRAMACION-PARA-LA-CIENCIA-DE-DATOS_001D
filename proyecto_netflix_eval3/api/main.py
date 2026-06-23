"""API RESTful para exponer métricas del proyecto Netflix."""
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
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", DEFAULT_DB))

app = FastAPI(title="Netflix Churn Analytics API", version="1.0")


def read_table(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base analítica no encontrada. Ejecutar ETL primero.")
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(f"SELECT * FROM {table}", con)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "database_exists": DB_PATH.exists()}


@app.get("/business-rules")
def business_rules() -> dict:
    with open(DEFAULT_RULES, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/summary")
def summary() -> dict:
    df = read_table("summary_metrics")
    return df.iloc[0].to_dict()


@app.get("/churn-by-activity")
def churn_by_activity() -> list[dict]:
    return read_table("churn_by_activity").to_dict(orient="records")


@app.get("/churn-by-country")
def churn_by_country() -> list[dict]:
    return read_table("churn_by_country").to_dict(orient="records")


@app.get("/users")
def users(limit: int = Query(default=20, ge=1, le=500), churned: str | None = None) -> list[dict]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base analítica no encontrada. Ejecutar ETL primero.")
    query = "SELECT user_id, age, country, subscription_type, favorite_genre, nivel_actividad, riesgo_login, churned, engagement_score FROM clean_users"
    params = []
    if churned:
        query += " WHERE churned = ?"
        params.append(churned)
    query += " LIMIT ?"
    params.append(limit)
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)
    return df.to_dict(orient="records")
