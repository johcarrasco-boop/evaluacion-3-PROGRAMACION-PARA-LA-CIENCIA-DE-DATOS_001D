"""Entrenamiento de modelos ML para el Examen Final Transversal.

Este script toma la base analítica generada por el ETL, entrena modelos de
clasificación para churn, modelos de regresión para tiempo de visualización y
un modelo no supervisado de segmentación. Los resultados quedan persistidos en
CSV, SQLite y archivos .pkl para ser consumidos por la API y el dashboard.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

RANDOM_STATE = 42
logger = logging.getLogger("netflix_ml")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def build_preprocessor(x: pd.DataFrame) -> ColumnTransformer:
    """Construye un preprocesador con imputación, escalado y OneHotEncoding."""
    numeric_features = x.select_dtypes(include=["int64", "float64", "int32", "float32"]).columns.tolist()
    categorical_features = x.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    numeric_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(transformers=[
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ])


def safe_roc_auc(y_true: pd.Series, proba: np.ndarray | None) -> float:
    """Calcula ROC-AUC controlando modelos sin predict_proba."""
    if proba is None:
        return float("nan")
    try:
        return float(roc_auc_score(y_true, proba))
    except ValueError:
        return float("nan")


def train_classification(df: pd.DataFrame, artifacts_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Entrena varios clasificadores para predecir churn."""
    target = "churned_binary"
    drop_cols = ["user_id", "churned", target, "estimated_monthly_revenue"]
    x = df.drop(columns=[c for c in drop_cols if c in df.columns])
    if target not in df.columns:
        if "churned" in df.columns:
            df[target] = (
                df["churned"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({
                    "yes": 1,
                    "no": 0,
                    "true": 1,
                    "false": 0,
                    "1": 1,
                    "0": 0,
                    "si": 1,
                    "sí": 1
                })
            )

            if df[target].isna().any():
                df[target] = df["churned"].astype(int)
        else:
            raise KeyError("No existe la columna churned_binary ni churned para entrenar el modelo.")

    y = df[target].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    preprocessor = build_preprocessor(x_train)

    models = {
        "Regresión logística": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        "Árbol de decisión": DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=25, max_depth=8, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1),
    }

    rows: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        proba = pipe.predict_proba(x_test)[:, 1] if hasattr(pipe.named_steps["model"], "predict_proba") else None
        rows.append({
            "modelo": name,
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, pred, zero_division=0)), 4),
            "roc_auc": round(safe_roc_auc(y_test, proba), 4),
        })
        fitted[name] = pipe

    # Optimización liviana para evidenciar tuning y validación cruzada.
    tuned_pipe = Pipeline(steps=[
        ("preprocess", build_preprocessor(x_train)),
        ("model", DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE)),
    ])
    param_dist = {
        "model__max_depth": [4, 6, 8, 10, None],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2, 4],
    }
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        tuned_pipe,
        param_distributions=param_dist,
        n_iter=3,
        scoring="f1",
        cv=cv,
        random_state=RANDOM_STATE,
        n_jobs=1,
        verbose=0,
    )
    search.fit(x_train, y_train)
    tuned = search.best_estimator_
    pred = tuned.predict(x_test)
    proba = tuned.predict_proba(x_test)[:, 1]
    rows.append({
        "modelo": "Árbol de decisión optimizado",
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
    })
    fitted["Árbol de decisión optimizado"] = tuned

    metrics = pd.DataFrame(rows).sort_values(["f1_score", "roc_auc"], ascending=False).reset_index(drop=True)
    best_name = metrics.iloc[0]["modelo"]
    best_model = fitted[str(best_name)]
    best_pred = best_model.predict(x_test)
    cm = confusion_matrix(y_test, best_pred)
    cm_df = pd.DataFrame([
        {"real": "No churn", "predicho": "No churn", "usuarios": int(cm[0, 0])},
        {"real": "No churn", "predicho": "Churn", "usuarios": int(cm[0, 1])},
        {"real": "Churn", "predicho": "No churn", "usuarios": int(cm[1, 0])},
        {"real": "Churn", "predicho": "Churn", "usuarios": int(cm[1, 1])},
    ])

    artifact = {"model": best_model, "feature_columns": x.columns.tolist(), "best_model_name": str(best_name)}
    joblib.dump(artifact, artifacts_dir / "churn_classifier.pkl")
    (artifacts_dir / "classification_best_params.json").write_text(
        json.dumps({"best_model": str(best_name), "random_search_best_params": search.best_params_}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metrics, cm_df, artifact


def train_regression(df: pd.DataFrame, artifacts_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Entrena modelos de regresión para predecir tiempo promedio de visualización."""
    target = "avg_watch_time_minutes"
    drop_cols = ["user_id", target]
    x = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df[target].astype(float)
    if "churned" in x.columns:
        # Mantener churned como variable explicativa operacional; churned_binary queda como dato histórico procesado.
        pass

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=RANDOM_STATE)
    preprocessor = build_preprocessor(x_train)
    models = {
        "Regresión lineal": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=25, max_depth=8, random_state=RANDOM_STATE, n_jobs=1),
    }
    rows: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        rows.append({
            "modelo": name,
            "mae": round(float(mean_absolute_error(y_test, pred)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
            "r2": round(float(r2_score(y_test, pred)), 4),
        })
        fitted[name] = pipe

    metrics = pd.DataFrame(rows).sort_values("r2", ascending=False).reset_index(drop=True)
    best_name = str(metrics.iloc[0]["modelo"])
    artifact = {"model": fitted[best_name], "feature_columns": x.columns.tolist(), "best_model_name": best_name}
    joblib.dump(artifact, artifacts_dir / "watch_time_regressor.pkl")
    return metrics, artifact


def train_clustering(df: pd.DataFrame, artifacts_dir: Path) -> pd.DataFrame:
    """Entrena KMeans para segmentar usuarios por engagement y riesgo operativo."""
    features = [
        "watch_sessions_per_week",
        "completion_rate",
        "days_since_last_login",
        "recommendation_click_rate",
        "content_interactions",
        "engagement_score",
        "monthly_fee",
    ]
    x = df[features].copy()
    pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", KMeans(n_clusters=3, random_state=RANDOM_STATE, n_init=10)),
    ])
    clusters = pipe.fit_predict(x)
    clustered = df.copy()
    clustered["cluster_ml"] = clusters
    summary = (
        clustered.groupby("cluster_ml")
        .agg(
            usuarios=("user_id", "count"),
            churn_rate=("churned_binary", "mean"),
            avg_engagement=("engagement_score", "mean"),
            avg_watch_time=("avg_watch_time_minutes", "mean"),
            avg_days_since_login=("days_since_last_login", "mean"),
        )
        .reset_index()
    )
    for col in ["churn_rate", "avg_engagement", "avg_watch_time", "avg_days_since_login"]:
        summary[col] = summary[col].round(4)
    joblib.dump({"model": pipe, "feature_columns": features}, artifacts_dir / "user_segmenter.pkl")
    return summary


def persist_results(project_root: Path, metrics_clf: pd.DataFrame, cm_df: pd.DataFrame, metrics_reg: pd.DataFrame, cluster_summary: pd.DataFrame) -> None:
    """Guarda resultados ML en CSV y en la base analítica SQLite."""
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    db_path = processed_dir / "netflix_analytics.db"
    metrics_clf.to_csv(processed_dir / "model_metrics_classification.csv", index=False)
    metrics_reg.to_csv(processed_dir / "model_metrics_regression.csv", index=False)
    cm_df.to_csv(processed_dir / "confusion_matrix_best_model.csv", index=False)
    cluster_summary.to_csv(processed_dir / "cluster_summary.csv", index=False)
    with sqlite3.connect(db_path) as con:
        metrics_clf.to_sql("model_metrics_classification", con, if_exists="replace", index=False)
        metrics_reg.to_sql("model_metrics_regression", con, if_exists="replace", index=False)
        cm_df.to_sql("confusion_matrix_best_model", con, if_exists="replace", index=False)
        cluster_summary.to_sql("cluster_summary", con, if_exists="replace", index=False)


def run_training(project_root: Path) -> dict[str, str]:
    """Ejecuta el entrenamiento completo y retorna rutas de artefactos."""
    db_path = Path(os.getenv("ANALYTICS_DB_PATH", project_root / "data" / "processed" / "netflix_analytics.db"))
    if not db_path.exists():
        raise FileNotFoundError("No existe netflix_analytics.db. Ejecute primero python etl/run_etl.py")
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql_query("SELECT * FROM clean_users", con)
    # Entrenar sobre muestra estratificada mejora el tiempo de ejecución en equipos de laboratorio.
    if len(df) > 5000:
        df = (
            df.groupby("churned_binary", group_keys=False)
            .apply(lambda x: x.sample(frac=5000 / len(df), random_state=RANDOM_STATE))
            .reset_index(drop=True)
        )
    artifacts_dir = project_root / "models" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    metrics_clf, cm_df, _ = train_classification(df, artifacts_dir)
    metrics_reg, _ = train_regression(df, artifacts_dir)
    cluster_summary = train_clustering(df, artifacts_dir)
    persist_results(project_root, metrics_clf, cm_df, metrics_reg, cluster_summary)
    logger.info("Entrenamiento ML finalizado. Mejor clasificador: %s", metrics_clf.iloc[0].to_dict())
    return {
        "classifier": str(artifacts_dir / "churn_classifier.pkl"),
        "regressor": str(artifacts_dir / "watch_time_regressor.pkl"),
        "segmenter": str(artifacts_dir / "user_segmenter.pkl"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrena modelos ML para la EFT")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    run_training(Path(args.project_root))
