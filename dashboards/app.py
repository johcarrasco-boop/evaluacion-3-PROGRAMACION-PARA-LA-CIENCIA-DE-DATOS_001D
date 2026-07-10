"""Dashboard interactivo Streamlit para Netflix Churn Analytics + Machine Learning."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", PROJECT_ROOT / "data" / "processed" / "netflix_analytics.db"))

st.set_page_config(page_title="Netflix Churn Dashboard", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Carga datos procesados, tablas de dashboard y resultados ML."""
    if not DB_PATH.exists():
        st.error("No existe la base procesada. Ejecute primero: python etl/run_etl.py")
        st.stop()
    with sqlite3.connect(DB_PATH) as con:
        users = pd.read_sql_query("SELECT * FROM clean_users", con)
        tables = {
            "summary": pd.read_sql_query("SELECT * FROM summary_metrics", con),
            "activity": pd.read_sql_query("SELECT * FROM churn_by_activity", con),
            "country": pd.read_sql_query("SELECT * FROM churn_by_country", con),
            "plan": pd.read_sql_query("SELECT * FROM churn_by_plan", con),
            "risk": pd.read_sql_query("SELECT * FROM risk_segments", con),
        }
        for name, sql in {
            "classification_metrics": "SELECT * FROM model_metrics_classification",
            "regression_metrics": "SELECT * FROM model_metrics_regression",
            "confusion_matrix": "SELECT * FROM confusion_matrix_best_model",
            "cluster_summary": "SELECT * FROM cluster_summary",
        }.items():
            try:
                tables[name] = pd.read_sql_query(sql, con)
            except Exception:
                tables[name] = pd.DataFrame()
    return users, tables


users, tables = load_data()
summary = tables["summary"].iloc[0]

st.title("Netflix User Behavior — Churn Analytics + ML")
st.caption("Dashboard interactivo para audiencias ejecutiva, técnica y operativa, con resultados de Machine Learning.")

with st.sidebar:
    st.header("Filtros")
    countries = sorted(users["country"].dropna().unique())
    plans = sorted(users["subscription_type"].dropna().unique())
    country_filter = st.multiselect("País", countries, default=countries)
    plan_filter = st.multiselect("Tipo de suscripción", plans, default=plans)
    churn_filter = st.multiselect("Churn", ["No", "Yes"], default=["No", "Yes"])

filtered = users[
    users["country"].isin(country_filter)
    & users["subscription_type"].isin(plan_filter)
    & users["churned"].isin(churn_filter)
]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Usuarios", f"{len(filtered):,}")
k2.metric("Churn rate", f"{filtered['churned_binary'].mean()*100:.2f}%")
k3.metric("Tiempo promedio", f"{filtered['avg_watch_time_minutes'].mean():.1f} min")
k4.metric("Ingreso activo estimado", f"US$ {filtered['estimated_monthly_revenue'].sum():,.0f}")

tab_exec, tab_tech, tab_ops, tab_ml = st.tabs([
    "Audiencia ejecutiva",
    "Audiencia técnica",
    "Audiencia operativa",
    "Modelos ML",
])

with tab_exec:
    st.subheader("Vista ejecutiva: comportamiento y riesgo de abandono")
    c1, c2 = st.columns(2)
    churn_counts = filtered.groupby("churned", as_index=False).size().rename(columns={"size": "usuarios"})
    c1.plotly_chart(px.pie(churn_counts, names="churned", values="usuarios", title="Distribución churn"), use_container_width=True)
    activity = filtered.groupby(["nivel_actividad", "churned"], as_index=False).size().rename(columns={"size": "usuarios"})
    c2.plotly_chart(px.bar(activity, x="nivel_actividad", y="usuarios", color="churned", barmode="group", title="Churn por nivel de actividad"), use_container_width=True)

with tab_tech:
    st.subheader("Vista técnica: variables y comportamiento")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.box(filtered, x="churned", y="avg_watch_time_minutes", title="Tiempo de visualización por churn"), use_container_width=True)
    sample = filtered.sample(min(5000, len(filtered)), random_state=42) if len(filtered) else filtered
    c2.plotly_chart(px.scatter(sample, x="watch_sessions_per_week", y="completion_rate", color="churned", hover_data=["user_id", "country"], title="Sesiones vs completion rate"), use_container_width=True)
    st.dataframe(filtered.head(100), use_container_width=True)

with tab_ops:
    st.subheader("Vista operativa: segmentos para campañas")
    c1, c2 = st.columns(2)
    risk = filtered.groupby(["churn_risk_segment", "churned"], as_index=False).size().rename(columns={"size": "usuarios"})
    c1.plotly_chart(px.bar(risk, x="churn_risk_segment", y="usuarios", color="churned", barmode="group", title="Segmentos de riesgo"), use_container_width=True)
    campaigns = filtered.groupby(["campaign", "churned"], as_index=False).size().rename(columns={"size": "usuarios"})
    c2.plotly_chart(px.bar(campaigns, x="campaign", y="usuarios", color="churned", title="Usuarios por campaña sugerida"), use_container_width=True)

with tab_ml:
    st.subheader("Resultados de Machine Learning")
    clf = tables.get("classification_metrics", pd.DataFrame())
    reg = tables.get("regression_metrics", pd.DataFrame())
    cm = tables.get("confusion_matrix", pd.DataFrame())
    clusters = tables.get("cluster_summary", pd.DataFrame())
    if clf.empty or reg.empty:
        st.warning("No hay métricas ML. Ejecute: python models/train_models.py")
    else:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.bar(clf, x="modelo", y=["accuracy", "precision", "recall", "f1_score", "roc_auc"], barmode="group", title="Comparación de modelos de clasificación"), use_container_width=True)
        c2.plotly_chart(px.bar(reg, x="modelo", y=["mae", "rmse", "r2"], barmode="group", title="Comparación de modelos de regresión"), use_container_width=True)
        st.markdown("**Matriz de confusión del mejor clasificador**")
        if not cm.empty:
            pivot_cm = cm.pivot(index="real", columns="predicho", values="usuarios")
            st.plotly_chart(px.imshow(pivot_cm, text_auto=True, title="Matriz de confusión"), use_container_width=True)
        st.markdown("**Segmentación no supervisada con KMeans**")
        if not clusters.empty:
            st.dataframe(clusters, use_container_width=True)
            st.plotly_chart(px.bar(clusters, x="cluster_ml", y="churn_rate", title="Churn rate por cluster ML"), use_container_width=True)
        st.dataframe(clf, use_container_width=True)
