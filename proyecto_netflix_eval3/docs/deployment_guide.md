# Guía de instalación y despliegue

## Instalación local
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
python etl/run_etl.py
uvicorn api.main:app --reload
streamlit run dashboards/app.py
```

## Docker Compose
```bash
docker compose up --build
```

## Variables de entorno
Copiar `.env.example` y ajustar rutas si es necesario.

```bash
ANALYTICS_DB_PATH=data/processed/netflix_analytics.db
BUSINESS_RULES_API_URL=http://api:8000/business-rules
```

## Validación
```bash
pytest tests/
```

## Posibles errores
- Si el dashboard no abre, verificar que la base procesada exista.
- Si la API no encuentra datos, ejecutar primero el ETL.
- Si Docker no monta datos, revisar los volúmenes definidos en `docker-compose.yml`.
