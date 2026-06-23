# Documentación API REST

Base local: `http://localhost:8000`

## Endpoints

### GET `/health`
Verifica estado del servicio y existencia de base analítica.

### GET `/business-rules`
Entrega reglas de negocio usadas como fuente tipo API REST.

### GET `/summary`
Retorna métricas generales: total de usuarios, churn, churn rate, tiempo promedio e ingreso activo estimado.

### GET `/churn-by-activity`
Entrega cantidad de usuarios por nivel de actividad y estado churn.

### GET `/churn-by-country`
Entrega cantidad de usuarios por país y estado churn.

### GET `/users?limit=20&churned=Yes`
Retorna muestra de usuarios filtrable por churn.

## Ejemplo
```bash
curl http://localhost:8000/summary
```
