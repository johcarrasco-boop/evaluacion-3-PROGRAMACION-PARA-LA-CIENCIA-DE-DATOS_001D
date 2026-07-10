from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "etl"))
sys.path.append(str(PROJECT_ROOT))

from transform import add_feature_engineering, build_summary_tables


def test_add_feature_engineering_creates_churn_binary():
    df = pd.DataFrame({
        "churned": ["No", "Yes"],
        "watch_sessions_per_week": [2, 15],
        "days_since_last_login": [5, 30],
        "completion_rate": [0.5, 0.9],
        "recommendation_click_rate": [0.1, 0.8],
        "content_interactions": [3, 20],
        "monthly_fee": [9.99, 15.99],
        "account_age_months": [10, 30],
    })
    out = add_feature_engineering(df, {"low_sessions_threshold": 4, "high_sessions_threshold": 12})
    assert "churned_binary" in out.columns
    assert out["churned_binary"].tolist() == [0, 1]
    assert "engagement_score" in out.columns


def test_summary_tables_has_expected_tables():
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "churned": ["No", "Yes", "No"],
        "churned_binary": [0, 1, 0],
        "nivel_actividad": ["Alta", "Baja", "Media"],
        "country": ["Chile", "Chile", "Brazil"],
        "subscription_type": ["Basic", "Premium", "Basic"],
        "churn_risk_segment": ["Riesgo bajo", "Riesgo alto", "Riesgo medio"],
        "avg_watch_time_minutes": [100, 50, 120],
        "estimated_monthly_revenue": [9.99, 0, 9.99],
    })
    tables = build_summary_tables(df)
    assert "summary_metrics" in tables
    assert tables["summary_metrics"].iloc[0]["total_users"] == 3
