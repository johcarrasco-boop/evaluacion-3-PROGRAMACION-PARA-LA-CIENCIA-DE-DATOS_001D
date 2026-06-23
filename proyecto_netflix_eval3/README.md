# Netflix User Behavior — Evaluación Parcial 3 SCY1101

Proyecto end-to-end de análisis de datos para detectar patrones de abandono de usuarios de Netflix (*churn*).

## Objetivo
Construir una solución profesional que integre múltiples fuentes de datos, ejecute un pipeline ETL, exponga resultados mediante API REST, visualice información en un dashboard interactivo y pueda desplegarse con Docker.

## Fuentes integradas
1. `data/raw/netflix_user_behavior_dataset.csv`: dataset principal de comportamiento de usuarios.
2. `data/sources/netflix_reference.db`: base SQLite con planes y regiones.
3. `data/sources/api_business_rules.json` o endpoint `/business-rules`: fuente tipo API REST con reglas de negocio para campañas y riesgo.

## Estructura
```text
etl/          Pipeline ETL: extracción, validación, transformación y carga
api/          API RESTful con FastAPI
dashboards/   Dashboard interactivo Streamlit
data/         Datos originales, fuentes auxiliares y datos procesados
docs/         Arquitectura, guía de usuario, API y despliegue
docker/       Dockerfiles
tests/        Pruebas automatizadas
notebooks/    Notebook base del proyecto
```

## Ejecución local
```bash
pip install -r requirements.txt
python etl/run_etl.py
uvicorn api.main:app --reload
streamlit run dashboards/app.py
```

## Ejecución con Docker
```bash
docker compose up --build
```

Servicios:
- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Testing
```bash
pytest tests/
```

## Métricas principales del dataset
- Registros: 50.000
- Columnas originales: 20
- Nulos: 0
- Duplicados: 0
- Churn aproximado: 19,93%

## Valor de negocio
La solución permite revisar abandono de usuarios, segmentos de riesgo, actividad de visualización y posibles campañas de retención para apoyar decisiones ejecutivas, técnicas y operativas.
