# Documentación de la carpeta Random Forest

## Introducción
La carpeta [Models/Random_Forest](.) reúne la implementación de un modelo de clasificación basado en Random Forest para predecir el incumplimiento de pago de clientes de tarjeta de crédito. El desarrollo incluye la carga y limpieza del dataset, el escalado de variables, el entrenamiento del modelo base, una versión optimizada con ajuste de hiperparámetros y umbral de decisión, y el guardado de los artefactos generados.

## Estructura del proyecto

- [Processing_RF.py](Processing_RF.py): carga el dataset, limpia los datos, separa variables predictoras y objetivo, divide en entrenamiento y prueba, y aplica escalado.
- [train_RF.py](train_RF.py): entrena un modelo Random Forest base, evalúa métricas y guarda el modelo junto con el escalador y los nombres de variables.
- [RF_optimizado.py](RF_optimizado.py): entrena una versión mejorada con GridSearchCV, optimiza el recall y aplica ajuste del umbral de decisión.
- [random_forest_model.pkl](random_forest_model.pkl): modelo base entrenado.
- [random_forest_optimizado.pkl](random_forest_optimizado.pkl): modelo optimizado generado por el flujo mejorado.
- [scaler.pkl](scaler.pkl): escalador ajustado sobre los datos de entrenamiento.
- [feature_names.pkl](feature_names.pkl): nombres de las variables utilizadas en el entrenamiento.

## Objetivo del proyecto
El objetivo es detectar clientes con riesgo de impago utilizando variables demográficas y financieras del dataset de tarjetas de crédito. Se trata de un problema de clasificación binaria con clases desbalanceadas, por lo que el enfoque prioriza la detección de la clase minoritaria.

## Flujo general de procesamiento

### 1. Carga y limpieza de datos
El archivo [Processing_RF.py](Processing_RF.py) centraliza la preparación del dataset:
- carga el archivo CSV desde la carpeta [Dataset](../../Dataset),
- elimina la primera fila, que contiene texto no numérico,
- convierte todas las columnas a formato numérico,
- elimina valores nulos,
- separa las variables predictoras `X` y la variable objetivo `Y`.

### 2. Separación de variables
Si existe la columna `ID`, se elimina junto con `Y` para construir `X`. Luego se guarda la lista de nombres de variables en `feature_names` para reutilización posterior.

### 3. División y escalado
Los datos se dividen en entrenamiento y prueba con un esquema estratificado:
- `test_size = 0.2`
- `random_state = 42`

Después se aplica `StandardScaler` para normalizar las variables.

## Modelo base de Random Forest
El script [train_RF.py](train_RF.py) implementa la primera versión del modelo.

### Configuración del modelo
Se utiliza `RandomForestClassifier` con:
- `n_estimators = 100`
- `random_state = 42`
- `class_weight = 'balanced'`
- `n_jobs = -1`

### Evaluación del modelo
Tras el entrenamiento, el script calcula:
- `Recall`
- `F1-Score`
- `AUC-ROC`
- `classification_report`

Este enfoque es apropiado para el problema, ya que el recall es una métrica crítica cuando se desea detectar la mayor cantidad posible de casos de impago.

### Artefactos generados
El script guarda:
- el modelo entrenado en `random_forest_model.pkl`,
- el escalador en `scaler.pkl`,
- los nombres de las variables en `feature_names.pkl`.

## Versión optimizada
El archivo [RF_optimizado.py](RF_optimizado.py) implementa una versión más robusta del flujo.

### Grid Search
Se realiza una búsqueda de hiperparámetros con `GridSearchCV` sobre:
- `n_estimators`: 100, 200
- `max_depth`: 10, 15, None
- `min_samples_split`: 5, 10
- `min_samples_leaf`: 2, 5

La validación cruzada usa `cv = 3` y optimiza específicamente `scoring = 'recall'`.

### Ajuste del umbral de decisión
Después de entrenar el mejor estimador, el script calcula probabilidades sobre el conjunto de prueba y aplica un nuevo umbral:
- umbral original de decisión de clase,
- umbral personalizado de **0.35** para clasificar como impago.

Esto busca aumentar la sensibilidad del modelo y reducir falsos negativos.

### Métricas evaluadas
La versión optimizada reporta:
- `Recall`
- `F1-Score`
- `AUC-ROC`
- `classification_report`
- matriz de confusión

Además, imprime el impacto de negocio en términos de:
- morosos detectados correctamente,
- morosos que no fueron detectados.

### Artefacto generado
El modelo optimizado se guarda en:
- `random_forest_optimizado.pkl`

## Resultados funcionales de la carpeta
La carpeta deja implementados dos flujos claros:
1. una versión base de Random Forest con entrenamiento y evaluación estándar,
2. una versión optimizada enfocada en mejorar la detección de la clase minoritaria mediante GridSearch y ajuste del umbral.

## Observaciones importantes
- El proyecto trabaja con un dataset desbalanceado, por eso se usa `class_weight='balanced'` y se prioriza el recall.
- La limpieza inicial del archivo CSV es necesaria porque la primera fila contiene texto y no datos numéricos válidos.
- Los artefactos guardados permiten reutilizar el modelo en otros componentes del proyecto, por ejemplo en una aplicación de consulta o despliegue.

## Conclusión
La carpeta [Models/Random_Forest](.) contiene una implementación completa y funcional para clasificación de default con Random Forest. El código incluye preparación de datos, entrenamiento base, optimización de hiperparámetros, ajuste de umbral y persistencia de artefactos, por lo que sirve como una alternativa sólida al enfoque de Gradient Boosting dentro del mismo proyecto.