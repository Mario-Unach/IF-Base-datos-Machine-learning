import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, recall_score, f1_score, roc_auc_score

# Importamos la función desde nuestro nuevo archivo
from Processing_RF import load_and_preprocess_data

def main():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = CURRENT_DIR
    
    print("Iniciando procesamiento de datos...")
    # Llamamos a la función y desempaquetamos todo lo que nos devuelve
    X_train, X_test, y_train, y_test, scaler, feature_names = load_and_preprocess_data()
    print("Datos limpios y escalados exitosamente.")
    
    print("\nEntrenando el modelo Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=100, 
        random_state=42, 
        class_weight='balanced', 
        n_jobs=-1 
    )
    rf_model.fit(X_train, y_train)
    
    # Predicciones
    y_pred = rf_model.predict(X_test)
    y_prob = rf_model.predict_proba(X_test)[:, 1] 
    
    print("\n=== MÉTRICAS DEL MODELO ===")
    print(f"Recall (Sensibilidad) : {recall_score(y_test, y_pred):.4f} <- ¡Métrica crítica!")
    print(f"F1-Score              : {f1_score(y_test, y_pred):.4f}")
    print(f"AUC-ROC               : {roc_auc_score(y_test, y_prob):.4f}")
    print("\n--- Reporte de Clasificación ---")
    print(classification_report(y_test, y_pred))
    
    # Guardar los artefactos con Joblib
    print("\nGuardando artefactos del modelo...")
    joblib.dump(rf_model, os.path.join(MODEL_DIR, 'random_forest_model.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
    joblib.dump(feature_names, os.path.join(MODEL_DIR, 'feature_names.pkl'))
    
    print("¡Listo! Los archivos .pkl han sido generados en la carpeta Random_Forest.")

# Esto asegura que el código solo se ejecute si corres este script directamente
if __name__ == "__main__":
    main()