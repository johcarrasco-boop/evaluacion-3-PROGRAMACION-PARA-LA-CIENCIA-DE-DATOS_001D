"""Pipeline ETL end-to-end para el proyecto Netflix Eval 3."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from extract import read_api_source, read_csv_source, read_sql_sources
from load import save_processed
from transform import build_summary_tables, transform_sources
from validation import validate_numeric_ranges, validate_processed_schema, validate_raw_schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("netflix_etl")


def run_pipeline(project_root: Path, api_url: str | None = None) -> dict[str, str]:
    """Ejecuta extracción, validación, transformación y carga."""
    raw_csv = project_root / "data" / "raw" / "netflix_user_behavior_dataset.csv"
    reference_db = project_root / "data" / "sources" / "netflix_reference.db"
    fallback_api = project_root / "data" / "sources" / "api_business_rules.json"
    output_dir = project_root / "data" / "processed"

    logger.info("Inicio pipeline ETL")
    users = read_csv_source(raw_csv)
    plans, regions = read_sql_sources(reference_db)
    api_payload = read_api_source(api_url, fallback_api)

    validate_raw_schema(users)
    validate_numeric_ranges(users)

    processed = transform_sources(users, plans, regions, api_payload)
    validate_processed_schema(processed)

    tables = build_summary_tables(processed)
    saved = save_processed(processed, tables, output_dir)
    logger.info("ETL finalizado correctamente: %s", saved)
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecuta pipeline ETL Netflix Eval 3")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--api-url", default=os.getenv("BUSINESS_RULES_API_URL"))
    args = parser.parse_args()
    run_pipeline(Path(args.project_root), args.api_url)
