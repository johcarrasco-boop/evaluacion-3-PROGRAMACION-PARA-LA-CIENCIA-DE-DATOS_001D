# Manual de usuario del dashboard

## Acceso
Ejecutar:
```bash
streamlit run dashboards/app.py
```
Abrir: `http://localhost:8501`

## Vistas del dashboard

### Audiencia ejecutiva
Muestra indicadores generales, churn rate y comportamiento por nivel de actividad. Sirve para decisiones de negocio y retención.

### Audiencia técnica
Muestra distribución de variables y datos filtrados. Sirve para revisar calidad y relaciones entre variables.

### Audiencia operativa
Muestra segmentos de riesgo y campañas sugeridas. Sirve para priorizar acciones concretas sobre usuarios.

## Filtros
- País
- Tipo de suscripción
- Estado churn

## Interpretación rápida
Un aumento en usuarios con baja actividad o riesgo de login alto puede indicar grupos prioritarios para campañas de retención.
