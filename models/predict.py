"""Funciones reutilizables de predicción para la API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def load_artifact(path: str | Path) -> dict[str, Any]:
    """Carga un artefacto joblib guardado por models/train_models.py."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el artefacto ML: {path}")
    return joblib.load(path)


def predict_churn(row: pd.DataFrame, artifact: dict[str, Any]) -> dict[str, Any]:
    """Predice clase y probabilidad de churn para un usuario."""
    x = row[artifact["feature_columns"]]
    model = artifact["model"]
    predicted_class = int(model.predict(x)[0])
    probability = float(model.predict_proba(x)[0, 1]) if hasattr(model, "predict_proba") else None
    return {
        "modelo": artifact.get("best_model_name", "clasificador"),
        "prediccion_churn": "Yes" if predicted_class == 1 else "No",
        "probabilidad_churn": None if probability is None else round(probability, 4),
    }


def predict_watch_time(row: pd.DataFrame, artifact: dict[str, Any]) -> dict[str, Any]:
    """Predice tiempo promedio de visualización para un usuario."""
    x = row[artifact["feature_columns"]]
    model = artifact["model"]
    value = float(model.predict(x)[0])
    return {
        "modelo": artifact.get("best_model_name", "regresor"),
        "avg_watch_time_minutes_predicho": round(value, 2),
    }
