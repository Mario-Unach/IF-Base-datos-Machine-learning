##GRID SEARCH
import joblib
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, recall_score, f1_score, roc_auc_score, confusion_matrix

# Importamos tu función de limpieza de datos
from Processing_RF import load_and_preprocess_data

def main():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = CURRENT_DIR
    
    print("1. Cargando y procesando datos...")
    X_train, X_test, y_train, y_test, scaler, feature_names = load_and_preprocess_data()
    
    # ==========================================
    # FASE 1: AJUSTE DE HIPERPARÁMETROS (Grid Search)
    # ==========================================
    print("\n2. Configurando Grid Search...")
    
    # Definimos el modelo base
    rf_base = RandomForestClassifier(random_state=42, class_weight='balanced')
    
    # Definimos la cuadrícula de parámetros a explorar
    # Limitamos un poco las opciones para que no tarde horas en compilar
    param_grid = {
        'n_estimators': [100, 200],       # Número de árboles
        'max_depth': [10, 15, None],      # Profundidad máxima (evita sobreajuste)
        'min_samples_split': [5, 10],     # Muestras mínimas para dividir un nodo
        'min_samples_leaf': [2, 5]        # Muestras mínimas en cada hoja final
    }
    
    # scoring='recall' es la clave: le decimos que solo le importe detectar morosos
    grid_search = GridSearchCV(
        estimator=rf_base, 
        param_grid=param_grid, 
        cv=3,                 # Validación cruzada de 3 pliegues
        scoring='recall',     # ¡Optimizamos específicamente el Recall!
        n_jobs=-1,            # Usar todos los núcleos del procesador
        verbose=2             # Mostrar el progreso en la terminal
    )
    
    print("Iniciando entrenamiento exhaustivo (esto puede tomar un par de minutos)...")
    grid_search.fit(X_train, y_train)
    
    # Extraemos el mejor modelo encontrado
    best_rf = grid_search.best_estimator_
    print(f"\n¡Mejores parámetros encontrados!\n{grid_search.best_params_}")
    
    # ==========================================
    # FASE 2: MOVER EL UMBRAL DE DECISIÓN
    # ==========================================
    print("\n3. Aplicando ajuste de Umbral (Threshold Moving)...")
    
    # Obtenemos las PROBABILIDADES de que sea clase 1 (Impago), no la predicción final
    y_prob = best_rf.predict_proba(X_test)[:, 1]
    
    # Definimos nuestro nuevo umbral más estricto
    NUEVO_UMBRAL = 0.35
    
    # Si la probabilidad es mayor o igual a 0.35, lo marcamos como 1, si no, como 0.
    y_pred_custom = (y_prob >= NUEVO_UMBRAL).astype(int)
    
    # ==========================================
    # EVALUACIÓN DEL MODELO OPTIMIZADO
    # ==========================================
    print(f"\n=== MÉTRICAS DEL MODELO OPTIMIZADO (Umbral {NUEVO_UMBRAL}) ===")
    print(f"Recall (Sensibilidad) : {recall_score(y_test, y_pred_custom):.4f} <- ¡Mira cómo subió!")
    print(f"F1-Score              : {f1_score(y_test, y_pred_custom):.4f}")
    print(f"AUC-ROC               : {roc_auc_score(y_test, y_prob):.4f}")
    print("\n--- Nuevo Reporte de Clasificación ---")
    print(classification_report(y_test, y_pred_custom))
    
    # Matriz de confusión para ver exactamente a cuántos detectamos ahora
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_custom).ravel()
    print("\n--- Impacto de Negocio ---")
    print(f"Morosos detectados correctamente (Verdaderos Positivos): {tp} de {tp+fn}")
    print(f"Morosos que se escaparon (Falsos Negativos): {fn}")
    
    # Guardar el NUEVO modelo optimizado
    print("\nGuardando el modelo optimizado...")
    joblib.dump(best_rf, os.path.join(MODEL_DIR, 'random_forest_optimizado.pkl'))
    
    print("¡Proceso completado exitosamente!")

if __name__ == "__main__":
    main()