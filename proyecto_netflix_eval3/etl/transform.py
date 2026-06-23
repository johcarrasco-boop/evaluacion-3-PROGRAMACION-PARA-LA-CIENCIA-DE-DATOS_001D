"""Transformaciones robustas para integrar fuentes y preparar datos analíticos."""
from __future__ import annotations

import pandas as pd
import numpy as np


def build_api_dataframe(api_payload: dict) -> tuple[pd.DataFrame, dict]:
    """Convierte respuesta API en DataFrame de géneros y reglas de riesgo."""
    genre_df = pd.DataFrame(api_payload.get("genre_priority", []))
    risk_rules = api_payload.get("risk_rules", {})
    return genre_df, risk_rules


def add_feature_engineering(df: pd.DataFrame, risk_rules: dict) -> pd.DataFrame:
    """Crea variables de negocio reutilizables para dashboard y modelos."""
    data = df.copy()
    data["churned_binary"] = data["churned"].map({"No": 0, "Yes": 1}).astype(int)

    low_sessions = int(risk_rules.get("low_sessions_threshold", 4))
    high_sessions = int(risk_rules.get("high_sessions_threshold", 12))
    med_days = int(risk_rules.get("inactive_days_medium", 10))
    high_days = int(risk_rules.get("inactive_days_high", 21))

    data["nivel_actividad"] = pd.cut(
        data["watch_sessions_per_week"],
        bins=[-1, low_sessions, high_sessions, np.inf],
        labels=["Baja", "Media", "Alta"]
    ).astype(str)

    data["riesgo_login"] = pd.cut(
        data["days_since_last_login"],
        bins=[-1, med_days, high_days, np.inf],
        labels=["Reciente", "Medio", "Alto"]
    ).astype(str)

    # Score simple para priorizar usuarios: más sesiones, completion y clicks = mejor engagement.
    data["engagement_score"] = (
        data["watch_sessions_per_week"].rank(pct=True) * 0.35 +
        data["completion_rate"].rank(pct=True) * 0.25 +
        data["recommendation_click_rate"].rank(pct=True) * 0.20 +
        data["content_interactions"].rank(pct=True) * 0.20
    ).round(4)

    data["estimated_monthly_revenue"] = data["monthly_fee"] * (1 - data["churned_binary"])
    data["account_value_score"] = (data["account_age_months"] * data["monthly_fee"]).round(2)

    conditions = [
        (data["riesgo_login"].eq("Alto")) | (data["nivel_actividad"].eq("Baja")),
        (data["riesgo_login"].eq("Medio")) | (data["nivel_actividad"].eq("Media")),
    ]
    choices = ["Riesgo alto", "Riesgo medio"]
    data["churn_risk_segment"] = np.select(conditions, choices, default="Riesgo bajo")
    return data


def transform_sources(
    users: pd.DataFrame,
    plans: pd.DataFrame,
    regions: pd.DataFrame,
    api_payload: dict
) -> pd.DataFrame:
    """Integra CSV, SQLite y API en un dataset final."""
    genre_df, risk_rules = build_api_dataframe(api_payload)
    df = users.merge(plans, on="subscription_type", how="left")
    df = df.merge(regions, on="country", how="left")
    df = df.merge(genre_df, on="favorite_genre", how="left")

    df["plan_level"] = df["plan_level"].fillna(0).astype(int)
    df["region"] = df["region"].fillna("Unknown")
    df["market_tier"] = df["market_tier"].fillna("Unknown")
    df["genre_priority_score"] = df["genre_priority_score"].fillna(df["genre_priority_score"].median())
    df["campaign"] = df["campaign"].fillna("Campaña general")

    df = add_feature_engineering(df, risk_rules)
    return df


def build_summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Crea tablas agregadas para dashboards y API."""
    summary = pd.DataFrame([{
        "total_users": len(df),
        "churn_users": int(df["churned_binary"].sum()),
        "no_churn_users": int((df["churned_binary"] == 0).sum()),
        "churn_rate": round(float(df["churned_binary"].mean()), 4),
        "avg_watch_time": round(float(df["avg_watch_time_minutes"].mean()), 2),
        "estimated_active_revenue": round(float(df["estimated_monthly_revenue"].sum()), 2)
    }])

    churn_by_activity = (
        df.groupby(["nivel_actividad", "churned"], observed=False)
        .size().reset_index(name="users")
    )
    churn_by_country = (
        df.groupby(["country", "churned"], observed=False)
        .size().reset_index(name="users")
        .sort_values(["country", "churned"])
    )
    churn_by_plan = (
        df.groupby(["subscription_type", "churned"], observed=False)
        .size().reset_index(name="users")
    )
    risk_segments = (
        df.groupby(["churn_risk_segment", "churned"], observed=False)
        .size().reset_index(name="users")
    )
    return {
        "summary_metrics": summary,
        "churn_by_activity": churn_by_activity,
        "churn_by_country": churn_by_country,
        "churn_by_plan": churn_by_plan,
        "risk_segments": risk_segments,
    }
