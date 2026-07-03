# Documentación de la carpeta Gradient Boosting

## Introducción
La carpeta [Models/Gradient_Boosting](../) reúne el desarrollo completo de un sistema de clasificación para predecir el incumplimiento de pago de clientes de tarjeta de crédito. El proyecto integra análisis exploratorio, extracción de datos desde SQL Server, preparación de variables, entrenamiento de un modelo XGBoost y almacenamiento de artefactos para su reutilización posterior.

## Estructura del proyecto

- [__init__.py](../__init__.py): define el directorio como paquete de Python.
- [data_processing.py](../data_processing.py): realiza la conexión con SQL Server, consulta la vista `vw_ml_dataset`, limpia variables y prepara los datos.
- [train.py](../train.py): ejecuta el entrenamiento con XGBoost mediante GridSearchCV y guarda los artefactos del modelo.
- [Notebook/gradient_boosting.ipynb](gradient_boosting.ipynb): notebook principal donde se documenta la exploración de datos y la ejecución del pipeline.
- Artefactos generados en la ejecución: `xgb_model.pkl`, `scaler.pkl`, `medians.pkl`, `columns.pkl`.

## Objetivo del proyecto
El objetivo del proyecto es identificar si un cliente caerá en default el siguiente mes utilizando variables financieras y demográficas. Se trata de un problema real de clasificación binaria con desbalance de clases.

## Desarrollo del notebook

### 1. Importación de librerías
El notebook carga librerías para:
- manipulación de datos: `pandas`, `numpy`,
- visualización: `matplotlib`, `seaborn`,
- modelado y evaluación: `train_test_split`, `GridSearchCV`, `StandardScaler` y métricas de clasificación,
- aprendizaje por boosting: `xgboost` y `lightgbm`.

### 2. Carga del dataset original
Se carga el dataset **Default of Credit Card Clients** desde la fuente pública de UCI.

Resultado observado:
- **30,000 filas**
- **25 columnas**

El conjunto de datos incluye:
- variables de perfil del cliente,
- historial de pagos,
- montos facturados,
- montos pagados,
- y la variable objetivo `default payment next month`.

### 3. Exploración inicial
Se revisan los elementos básicos del dataset:
- estructura general con `df.info()`,
- estadísticos con `df.describe()`,
- valores nulos con `df.isnull().sum()`,
- distribución de la variable objetivo.

## Resultados del análisis exploratorio

### Distribución de la variable objetivo
La variable objetivo es `default payment next month`.

Resultados visibles:
- default: **22.12%**
- no default: **77.88%**

Estos valores confirman un problema de clasificación **desbalanceado**, por lo que resulta apropiado considerar métricas robustas como ROC-AUC y el ajuste de pesos de clase.

### Estadísticas descriptivas relevantes
Algunos valores representativos del dataset:
- `LIMIT_BAL` promedio: **167,484.32**
- edad promedio: **35.49 años**
- media de la variable objetivo: **0.2212**

### Análisis visual
El notebook genera tres bloques de gráficos:
- distribución del target,
- comportamiento del default por `SEX`, `EDUCATION`, `MARRIAGE` y `AGE`,
- matriz de correlación.

#### Interpretación de la matriz de correlación
La figura muestra que:
- las variables de pago `PAY_0` a `PAY_6` están fuertemente correlacionadas entre sí,
- los montos facturados `BILL_AMT1` a `BILL_AMT6` también presentan alta correlación temporal,
- el target parece relacionarse más con el historial reciente de pago que con variables demográficas aisladas.

## Pipeline de producción con SQL Server
Tras el análisis exploratorio, el notebook ejecuta un flujo orientado a reutilización y posible despliegue.

### 4. Preparación de rutas
Se agrega el directorio padre al `sys.path` para permitir la importación de módulos locales sin errores.

### 5. Extracción desde SQL Server
El módulo [data_processing.py](../data_processing.py) se conecta con SQL Server mediante `pyodbc` y consulta la vista `vw_ml_dataset`.

Transformaciones realizadas:
- selección de variables relevantes,
- renombrado de columnas para alinearlas con el modelo,
- codificación y limpieza de `EDUCATION` y `MARRIAGE`,
- separación entre `X` e `y`.

Resultados observados en la ejecución:
- **30,000 registros** cargados desde SQL Server,
- `X` con forma **(30000, 23)**,
- `y` con forma **(30000, )**.

### 6. Preparación para entrenamiento
La función `prepare_for_training` realiza:
- división en entrenamiento y prueba con `train_test_split`,
- escalado con `StandardScaler`,
- cálculo de medianas para reutilización posterior,
- cálculo de `scale_pos_weight` para compensar el desbalance.

### 7. Entrenamiento del modelo
El módulo [train.py](../train.py) entrena `XGBClassifier` mediante `GridSearchCV`.

Parámetros explorados:
- `n_estimators`: 100, 150
- `max_depth`: 4, 6
- `learning_rate`: 0.05, 0.1

La búsqueda evalúa **8 combinaciones** de hiperparámetros con **validación cruzada de 3 folds**, lo que da un total de **24 entrenamientos**.

### 8. Guardado de artefactos
Al finalizar el proceso, se guardan:
- `xgb_model.pkl`: modelo entrenado,
- `medians.pkl`: medianas de las variables,
- `columns.pkl`: orden de columnas usado en entrenamiento,
- `scaler.pkl`: escalador ajustado.

## Resultado final visible
La ejecución mostrada en el notebook confirma que:
- la carga desde SQL Server funciona,
- la preparación de datos se completa correctamente,
- el entrenamiento de XGBoost finaliza con GridSearchCV,
- los artefactos quedan guardados en el directorio de trabajo.

## Observación importante
En el notebook no aparecen métricas finales de evaluación sobre test, como:
- accuracy,
- precision,
- recall,
- F1-score,
- ROC-AUC.

Por ello, este documento describe adecuadamente el entrenamiento y la preparación de datos, pero no expone de forma explícita el rendimiento final del modelo.

## Conclusión
La carpeta implementa un flujo completo para clasificación de default con Gradient Boosting:
1. exploración del dataset,
2. extracción y limpieza desde SQL Server,
3. preparación de variables,
4. entrenamiento con XGBoost,
5. guardado de artefactos para inferencia o integración con Streamlit.

Como mejora futura, sería recomendable añadir métricas finales del modelo o un diagrama del pipeline para complementar la documentación.
