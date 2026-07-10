# Documentación API

La API está implementada con FastAPI en `api/main.py` y consume la base SQLite generada por el ETL y enriquecida por la capa ML.

## Endpoints

- `/health`: valida API, base y artefactos ML.
- `/business-rules`: retorna reglas de negocio tipo API/JSON.
- `/summary`: entrega KPIs generales.
- `/churn-by-activity`: entrega churn por nivel de actividad.
- `/churn-by-country`: entrega churn por país.
- `/users`: lista usuarios procesados.
- `/model-metrics`: retorna métricas de clasificación, regresión y clustering.
- `/confusion-matrix`: retorna matriz de confusión del mejor modelo.
- `/predict-churn/{user_id}`: predice churn para un usuario existente.
- `/predict-watch-time/{user_id}`: predice tiempo promedio de visualización para un usuario existente.
