# Documentación de Machine Learning

## Problemas abordados

- Clasificación: predecir si un usuario presenta churn (`churned_binary`).
- Regresión: estimar el tiempo promedio de visualización (`avg_watch_time_minutes`).
- Segmentación: agrupar usuarios mediante KMeans para identificar perfiles de riesgo y engagement.

## Algoritmos utilizados

Clasificación:

- Regresión logística
- Árbol de decisión
- Random Forest
- Gradient Boosting
- Random Forest optimizado con RandomizedSearchCV

Regresión:

- Regresión lineal
- Random Forest Regressor

No supervisado:

- KMeans con 3 clusters

## Métricas

Clasificación: accuracy, precision, recall, F1-score, ROC-AUC y matriz de confusión.

Regresión: MAE, RMSE y R2.

## Justificación

Se implementan varios algoritmos para comparar modelos simples, interpretables y modelos de ensamble. El F1-score se considera especialmente importante en churn porque el objetivo de negocio es detectar usuarios con riesgo de abandono, no solo maximizar accuracy.
