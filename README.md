# Netflix User Behavior — Evaluación Final Transversal SCY1101

Proyecto end-to-end de análisis de datos para detectar patrones de abandono de usuarios de Netflix (*churn*) e incorporar una capa de Machine Learning para apoyar decisiones de retención.

## Objetivo

Construir una solución profesional que integre múltiples fuentes de datos, ejecute un pipeline ETL, entrene modelos de clasificación y regresión, exponga resultados mediante API REST, visualice información en un dashboard interactivo y evidencie automatización con CI/CD.

## Fuentes integradas

1. `data/raw/netflix_user_behavior_dataset.csv`: dataset principal de comportamiento de usuarios.
2. `data/sources/netflix_reference.db`: base SQLite de referencia con planes y regiones.
3. `data/sources/api_business_rules.json` o endpoint `/business-rules`: fuente tipo API REST con reglas de negocio para campañas y riesgo.

## Estructura

```text
etl/          Pipeline ETL: extracción, validación, transformación y carga
models/       Entrenamiento ML, predicción y artefactos serializados
api/          API RESTful con FastAPI
dashboards/   Dashboard interactivo Streamlit
data/         Datos originales, fuentes auxiliares y datos procesados
docker/       Dockerfiles
.github/      Workflow CI/CD con GitHub Actions
docs/         Arquitectura, guía de usuario, API y despliegue
tests/        Pruebas automatizadas
notebooks/    Notebook base del proyecto
repo/         Evidencias de Git
```

## Instalación local

```bash
python -m pip install -r requirements.txt
```

## Ejecución local

1. Ejecutar ETL:

```bash
python etl/run_etl.py
```

2. Entrenar modelos ML:

```bash
python models/train_models.py
```

3. Iniciar API:

```bash
python -m uvicorn api.main:app --reload
```

API disponible en:

```text
http://localhost:8000/docs
```

4. Iniciar dashboard:

```bash
python -m streamlit run dashboards/app.py
```

Dashboard disponible en:

```text
http://localhost:8501
```

## Ejecución con Docker

```bash
docker compose up --build
```

Servicios:

- API: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

## Machine Learning

La carpeta `models/` entrena:

- Modelos de clasificación para predecir `churned_binary`.
- Modelos de regresión para predecir `avg_watch_time_minutes`.
- Segmentación no supervisada con KMeans.

Resultados principales guardados en:

```text
data/processed/model_metrics_classification.csv
data/processed/model_metrics_regression.csv
data/processed/confusion_matrix_best_model.csv
data/processed/cluster_summary.csv
models/artifacts/churn_classifier.pkl
models/artifacts/watch_time_regressor.pkl
models/artifacts/user_segmenter.pkl
```

## Endpoints principales

- `GET /health`
- `GET /summary`
- `GET /churn-by-activity`
- `GET /churn-by-country`
- `GET /model-metrics`
- `GET /confusion-matrix`
- `GET /predict-churn/{user_id}`
- `GET /predict-watch-time/{user_id}`

## CI/CD

El repositorio incluye `.github/workflows/python-ci.yml`, que automatiza instalación de dependencias, ejecución del ETL, entrenamiento de modelos y pruebas con `pytest`.

## Integrantes

- Johann Carrasco — Product Owner / documentación y defensa de negocio.
- Pablo Daza — Data Engineer / ETL, datos y despliegue.
- Ricardo Ruiz — Data Analyst / API, dashboard y visualización.

## Video de exposición

Link del video: PENDIENTE_DE_AGREGAR
