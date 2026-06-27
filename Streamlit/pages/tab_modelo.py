import streamlit as st
import joblib
import pandas as pd
from Streamlit.db_connections import get_mongo_db
from datetime import datetime

def show_modelo_tab(ROOT_DIR):
    st.header("Modelo de Machine Learning: XGBoost (Gradient Boosting)")
    
    MODEL_DIR = ROOT_DIR / "Models" / "Gradient_Boosting"
    try:
        model = joblib.load(MODEL_DIR / "xgb_model.pkl")
        scaler = joblib.load(MODEL_DIR / "scaler.pkl") # Asegúrate de guardarlo en el notebook
        medians = joblib.load(MODEL_DIR / "medians.pkl")
        columns = joblib.load(MODEL_DIR / "columns.pkl")
        st.success("✅ Modelo y artefactos cargados exitosamente.")
    except Exception as e:
        st.error(f"Error al cargar artefactos: {e}. Ejecuta primero el notebook de entrenamiento.")
        st.stop()

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Hiperparámetros Óptimos")
        params = model.get_params()
        for k in ['n_estimators', 'max_depth', 'learning_rate']:
            st.metric(label=k, value=params.get(k, "N/A"))
                
    with col2:
        st.subheader("🔮 Formulario Simplificado de Predicción")
        st.markdown("Para usabilidad, solo solicitamos las variables de mayor impacto. *El resto se imputa con la mediana del dataset.*")
        
        with st.form("pred_form"):
            limit_bal = st.slider("Límite de Crédito (LIMIT_BAL)", 10000, 1000000, 50000, step=10000)
            pay_0 = st.selectbox("Estado de Pago Reciente (PAY_0)", [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8], help="-1 = Pago a tiempo, 1+ = Meses de retraso")
            bill_amt1 = st.number_input("Monto de Factura Reciente (BILL_AMT1)", 0, 1000000, 5000)
            pay_amt1 = st.number_input("Monto Pagado Reciente (PAY_AMT1)", 0, 1000000, 1000)
            age = st.slider("Edad (AGE)", 21, 79, 30)
            
            submit = st.form_submit_button("Calcular Probabilidad de Impago")
            
            if submit:
                # Imputación inteligente con medianas
                input_dict = medians.to_dict()
                
                # 🔍 Mapeo dinámico: Busca el nombre real de la columna en el modelo entrenado
                limit_key = next((c for c in columns if 'LIMIT' in c or 'CREDITO' in c), 'LIMIT_BAL')
                pay_key = next((c for c in columns if c in ['PAY_0', 'PAGO_MES_ACTUAL']), 'PAY_0')
                bill_key = next((c for c in columns if 'BILL_AMT1' in c or 'FACTURA_MES_1' in c), 'BILL_AMT1')
                pay_amt_key = next((c for c in columns if 'PAY_AMT1' in c or 'PAGO_REALIZADO_MES_1' in c), 'PAY_AMT1')
                age_key = next((c for c in columns if c in ['AGE', 'EDAD']), 'AGE')

                # Asignamos los valores del formulario a las claves correctas
                input_dict[limit_key] = limit_bal
                input_dict[pay_key] = pay_0
                input_dict[bill_key] = bill_amt1
                input_dict[pay_amt_key] = pay_amt1
                input_dict[age_key] = age
                
                # Aseguramos el orden exacto de las columnas para el modelo
                input_df = pd.DataFrame([input_dict])[columns]
                input_scaled = scaler.transform(input_df)
                
                prob = model.predict_proba(input_scaled)[0][1]
                pred = model.predict(input_scaled)[0]
                
                st.markdown("### 📊 Resultado de la Inferencia")
                if pred == 1:
                    st.error(f"⚠️ **ALERTA DE IMPAGO** | Probabilidad: {prob*100:.2f}%")
                else:
                    st.success(f"✅ **CLIENTE CONFIABLE** | Probabilidad: {prob*100:.2f}%")
                    
                # Guardar en MongoDB (Arquitectura Híbrida)
                db = get_mongo_db()
                if db is not None:
                    record = {
                        "timestamp": datetime.now(),
                        "model": "XGBoost_GradientBoosting",
                        "input_data": {k: float(v) if isinstance(v, (int, float)) else v for k, v in input_dict.items()},
                        "probability": float(prob),
                        "prediction": int(pred)
                    }
                    db["predictions"].insert_one(record)
                    st.info("💾 Predicción registrada en MongoDB (Colección: `predictions`).")