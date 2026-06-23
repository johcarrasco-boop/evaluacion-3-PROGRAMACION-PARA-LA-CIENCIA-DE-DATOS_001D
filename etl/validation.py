"""Validaciones de esquema y calidad para el pipeline ETL."""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "user_id", "age", "gender", "country", "account_age_months", "subscription_type",
    "monthly_fee", "payment_method", "primary_device", "devices_used", "favorite_genre",
    "avg_watch_time_minutes", "watch_sessions_per_week", "binge_watch_sessions",
    "completion_rate", "rating_given", "content_interactions",
    "recommendation_click_rate", "days_since_last_login", "churned"
}

NUMERIC_COLUMNS = [
    "age", "account_age_months", "monthly_fee", "devices_used", "avg_watch_time_minutes",
    "watch_sessions_per_week", "binge_watch_sessions", "completion_rate", "rating_given",
    "content_interactions", "recommendation_click_rate", "days_since_last_login"
]


def validate_raw_schema(df: pd.DataFrame) -> None:
    """Valida columnas mínimas, nulos críticos y duplicados."""
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")
    if df["user_id"].duplicated().any():
        raise ValueError("Existen user_id duplicados en la fuente principal")
    nulls = df[list(REQUIRED_COLUMNS)].isna().sum()
    bad_nulls = nulls[nulls > 0]
    if not bad_nulls.empty:
        raise ValueError(f"Existen valores nulos críticos: {bad_nulls.to_dict()}")
    invalid_churn = set(df["churned"].unique()).difference({"Yes", "No"})
    if invalid_churn:
        raise ValueError(f"Valores inválidos en churned: {invalid_churn}")


def validate_numeric_ranges(df: pd.DataFrame) -> None:
    """Valida rangos básicos de variables numéricas."""
    checks = {
        "age": (13, 100),
        "account_age_months": (0, 240),
        "monthly_fee": (0, 100),
        "avg_watch_time_minutes": (0, 1000),
        "watch_sessions_per_week": (0, 100),
        "completion_rate": (0, 100),
        "rating_given": (0, 5),
        "recommendation_click_rate": (0, 100),
        "days_since_last_login": (0, 365),
    }
    for col, (lo, hi) in checks.items():
        if col in df.columns and not df[col].between(lo, hi).all():
            raise ValueError(f"Valores fuera de rango en {col}")


def validate_processed_schema(df: pd.DataFrame) -> None:
    """Valida columnas generadas por la transformación."""
    required = {"churned_binary", "nivel_actividad", "riesgo_login", "engagement_score", "churn_risk_segment"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas procesadas: {sorted(missing)}")
    if df["churned_binary"].isin([0, 1]).all() is False:
        raise ValueError("churned_binary debe contener solo 0 y 1")
