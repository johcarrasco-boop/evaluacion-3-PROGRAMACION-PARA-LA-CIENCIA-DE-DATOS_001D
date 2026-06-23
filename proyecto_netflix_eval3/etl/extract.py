"""Extracción de fuentes para Evaluación Parcial 3.

Fuentes integradas:
1. CSV principal de usuarios Netflix.
2. Base de datos SQLite con información de planes y regiones.
3. API REST / JSON de reglas de negocio para enriquecer géneros y riesgo.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def read_csv_source(path: str | Path) -> pd.DataFrame:
    """Lee el CSV principal y valida que exista."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el CSV principal: {path}")
    df = pd.read_csv(path)
    logger.info("CSV cargado con forma %s", df.shape)
    return df


def read_sql_sources(db_path: str | Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Lee tablas de referencia desde SQLite."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"No se encontró la base SQLite: {db_path}")
    with sqlite3.connect(db_path) as con:
        plans = pd.read_sql_query("SELECT * FROM subscription_plans", con)
        regions = pd.read_sql_query("SELECT * FROM country_regions", con)
    logger.info("SQL cargado: plans=%s, regions=%s", plans.shape, regions.shape)
    return plans, regions


def read_api_source(api_url: str | None, fallback_json: str | Path) -> Dict:
    """Obtiene reglas desde una API REST; si falla, usa JSON local.

    Esto permite demo end-to-end con API y ejecución reproducible sin internet.
    """
    fallback_json = Path(fallback_json)
    if api_url:
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            logger.info("API REST cargada correctamente desde %s", api_url)
            return response.json()
        except Exception as exc:
            logger.warning("No fue posible leer API %s. Se usará fallback JSON. Error: %s", api_url, exc)

    if not fallback_json.exists():
        raise FileNotFoundError(f"No se encontró fallback de API: {fallback_json}")
    with open(fallback_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Fuente API fallback cargada desde %s", fallback_json)
    return data
