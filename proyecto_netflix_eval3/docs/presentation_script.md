# Guion breve para defensa individual Evaluación 3

## Introducción
Este proyecto desarrolla una solución end-to-end para analizar el comportamiento de usuarios de Netflix y apoyar la detección de churn. Integra tres fuentes de datos, ejecuta un pipeline ETL, expone métricas mediante API, presenta resultados en dashboard y se despliega con Docker.

## Pipeline ETL
El pipeline integra el CSV principal, una base SQLite de referencia y una fuente tipo API con reglas de negocio. Luego valida esquema, nulos, duplicados y rangos, para finalmente generar variables como `churned_binary`, `nivel_actividad`, `riesgo_login` y segmentos de riesgo.

## Dashboard
El dashboard está hecho en Streamlit y tiene vistas para audiencia ejecutiva, técnica y operativa. La vista ejecutiva muestra indicadores de negocio; la técnica revisa variables y comportamiento; la operativa permite priorizar segmentos y campañas.

## API y Docker
La API en FastAPI expone métricas como resumen general, churn por actividad y usuarios filtrados. Docker permite ejecutar la solución de forma reproducible mediante servicios separados para API, dashboard y ETL.

## Cierre
La principal fortaleza del proyecto es que transforma el análisis anterior en una solución profesional reproducible, documentada y lista para demo técnica.
