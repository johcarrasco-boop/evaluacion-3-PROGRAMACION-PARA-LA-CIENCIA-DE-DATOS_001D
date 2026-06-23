"""Pruebas automatizadas del pipeline ETL."""
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "etl"))

from extract import read_csv_source, read_sql_sources, read_api_source
from transform import transform_sources
from validation import validate_processed_schema, validate_raw_schema


def test_raw_csv_schema():
    df = read_csv_source(PROJECT_ROOT / "data/raw/netflix_user_behavior_dataset.csv")
    validate_raw_schema(df)
    assert df.shape[0] == 50000
    assert "churned" in df.columns


def test_transform_outputs_required_columns():
    users = read_csv_source(PROJECT_ROOT / "data/raw/netflix_user_behavior_dataset.csv").head(100)
    plans, regions = read_sql_sources(PROJECT_ROOT / "data/sources/netflix_reference.db")
    api_payload = read_api_source(None, PROJECT_ROOT / "data/sources/api_business_rules.json")
    processed = transform_sources(users, plans, regions, api_payload)
    validate_processed_schema(processed)
    assert set(processed["churned_binary"].unique()).issubset({0, 1})
    assert "engagement_score" in processed.columns
