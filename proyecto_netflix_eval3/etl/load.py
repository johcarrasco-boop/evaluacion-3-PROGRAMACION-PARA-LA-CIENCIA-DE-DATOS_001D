"""Carga de resultados procesados en CSV y SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def save_processed(df: pd.DataFrame, tables: dict[str, pd.DataFrame], output_dir: str | Path) -> dict[str, str]:
    """Guarda dataset procesado, agregados y base analítica SQLite."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "netflix_users_processed.csv"
    db_path = output_dir / "netflix_analytics.db"
    df.to_csv(csv_path, index=False)

    with sqlite3.connect(db_path) as con:
        df.to_sql("clean_users", con, if_exists="replace", index=False)
        for name, table in tables.items():
            table.to_sql(name, con, if_exists="replace", index=False)

    return {"processed_csv": str(csv_path), "analytics_db": str(db_path)}
