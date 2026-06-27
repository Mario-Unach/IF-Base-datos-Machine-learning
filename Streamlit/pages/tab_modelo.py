import streamlit as st
import joblib
import pandas as pd
import numpy as np
from Streamlit.db_connections import get_mongo_db
from datetime import datetime

def show_modelo_tab(ROOT_DIR):
    # Header con estilo
    st.markdown("""
    <style>
    .prediction-success {
        background-color: #d4edda;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 20px 0;
    }
    .prediction-warning {
        background-color: #fff3cd;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 20px 0;
    }
    .feature-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("🤖 Modelo Predictivo XGBoost")
    st.markdown("### Gradient Boosting para Detección de Impagos")
    
    # Cargar modelo y artefactos
    MODEL_DIR = ROOT_DIR / "Models" / "Gradient_Boosting"
    try:
        model = joblib.load(MODEL_DIR / "xgb_model.pkl")
        scaler = joblib.load(MODEL_DIR / "scaler.pkl")
        medians = joblib.load(MODEL_DIR / "medians.pkl")
        columns = joblib.load(MODEL_DIR / "columns.pkl")
        
        # Mostrar badges de estado
        col_badge1, col_badge2, col_badge3 = st.columns(3)
        with col_badge1:
            st.success("✅ Modelo Cargado")
        with col_badge2:
            st.success("✅ Scaler Listo")
        with col_badge3:
            st.success("✅ Datos Validados")
            
    except Exception as e:
        st.error(f"❌ Error crítico al cargar artefactos: {e}")
        st.info("💡 Ejecuta primero el notebook de entrenamiento para generar los archivos del modelo.")
        st.stop()

    # Layout principal en dos columnas
    col_form, col_info = st.columns([1.2, 0.8])
    
    with col_form:
        # Crear contenedor con borde
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Configuración de Entrada")
        st.markdown("*Ingresa los datos del cliente para obtener una predicción en tiempo real*")
        
        # Formulario estilizado
        with st.form("pred_form", clear_on_submit=False):
            # Sección 1: Información Crediticia Principal
            st.markdown("**💰 Variables Crediticias**")
            col1, col2 = st.columns(2)
            with col1:
                limit_bal = st.slider(
                    "Límite de Crédito (NT$)", 
                    min_value=10000, 
                    max_value=1000000, 
                    value=50000, 
                    step=10000,
                    help="Monto máximo de crédito disponible"
                )
            with col2:
                age = st.slider(
                    "Edad del Cliente", 
                    min_value=21, 
                    max_value=79, 
                    value=30,
                    help="Edad en años"
                )
            
            st.divider()
            
            # Sección 2: Comportamiento de Pago Reciente
            st.markdown("**📅 Comportamiento de Pago**")
            col3, col4 = st.columns(2)
            with col3:
                pay_0 = st.selectbox(
                    "Estado de Pago (Mes Actual)", 
                    options=[-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8],
                    index=1,
                    help="-2/-1: Pago anticipado/a tiempo | 0: Sin retraso | 1+: Meses de retraso"
                )
                pay_status_help = {
                    -2: "Pago anticipado",
                    -1: "Pago a tiempo",
                    0: "Sin retraso",
                    1: "1 mes de retraso",
                    2: "2 meses de retraso",
                    3: "3 meses de retraso",
                    4: "4+ meses de retraso"
                }
                if pay_0 in pay_status_help:
                    st.caption(f"ℹ️ {pay_status_help[pay_0]}")
            
            with col4:
                bill_amt1 = st.number_input(
                    "Monto Factura (Mes 1)", 
                    min_value=0, 
                    max_value=1000000, 
                    value=5000,
                    step=100,
                    help="Monto total de la factura del mes actual"
                )
            
            st.divider()
            
            # Sección 3: Pagos Realizados
            st.markdown("**💳 Historial de Pagos**")
            pay_amt1 = st.number_input(
                "Monto Pagado (Mes 1)", 
                min_value=0, 
                max_value=1000000, 
                value=1000,
                step=100,
                help="Cantidad pagada en el último mes"
            )
            
            st.divider()
            
            # Botón de predicción
            submit = st.form_submit_button(
                "🔮 Calcular Predicción", 
                use_container_width=True,
                type="primary"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resultados de la predicción
        if submit:
            # Imputación inteligente con medianas
            input_dict = medians.to_dict()
            
            # Mapeo dinámico de columnas
            limit_key = next((c for c in columns if 'LIMIT' in c or 'CREDITO' in c), 'LIMIT_BAL')
            pay_key = next((c for c in columns if c in ['PAY_0', 'PAGO_MES_ACTUAL']), 'PAY_0')
            bill_key = next((c for c in columns if 'BILL_AMT1' in c or 'FACTURA_MES_1' in c), 'BILL_AMT1')
            pay_amt_key = next((c for c in columns if 'PAY_AMT1' in c or 'PAGO_REALIZADO_MES_1' in c), 'PAY_AMT1')
            age_key = next((c for c in columns if c in ['AGE', 'EDAD']), 'AGE')

            # Asignar valores
            input_dict[limit_key] = limit_bal
            input_dict[pay_key] = pay_0
            input_dict[bill_key] = bill_amt1
            input_dict[pay_amt_key] = pay_amt1
            input_dict[age_key] = age
            
            # Preparar DataFrame en orden correcto
            input_df = pd.DataFrame([input_dict])[columns]
            input_scaled = scaler.transform(input_df)
            
            # Obtener predicción
            prob = model.predict_proba(input_scaled)[0][1]
            pred = model.predict(input_scaled)[0]
            
            # Mostrar resultados con diseño mejorado
            st.divider()
            st.subheader("📊 Resultado de la Inferencia")
            
            # Métricas en columnas
            col_prob, col_pred, col_threshold = st.columns(3)
            with col_prob:
                st.metric(
                    label="Probabilidad de Impago",
                    value=f"{prob*100:.2f}%",
                    delta=f"{prob*100:.1f}% vs threshold"
                )
            with col_pred:
                prediction_text = "IMPAGO" if pred == 1 else "CONFIALE"
                st.metric(
                    label="Predicción",
                    value=prediction_text,
                    delta="Alto Riesgo" if pred == 1 else "Bajo Riesgo"
                )
            with col_threshold:
                st.metric(
                    label="Threshold",
                    value="50%",
                    delta="Estándar"
                )
            
            # Alerta visual según resultado
            if pred == 1:
                st.markdown(f"""
                <div class="prediction-warning">
                    <h3>⚠️ ALERTA DE IMPAGO DETECTADA</h3>
                    <p><strong>Probabilidad:</strong> {prob*100:.2f}%</p>
                    <p><strong>Recomendación:</strong> Se sugiere revisar línea de crédito y solicitar garantías adicionales.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="prediction-success">
                    <h3>✅ CLIENTE CONFIABLE</h3>
                    <p><strong>Probabilidad de impago:</strong> {prob*100:.2f}%</p>
                    <p><strong>Recomendación:</strong> Perfil de riesgo aceptable. Aprobar operaciones normales.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Guardar en MongoDB
            db = get_mongo_db()
            if db is not None:
                record = {
                    "timestamp": datetime.now(),
                    "model": "XGBoost_GradientBoosting",
                    "input_data": {
                        "LIMIT_BAL": float(limit_bal),
                        "PAY_0": int(pay_0),
                        "BILL_AMT1": float(bill_amt1),
                        "PAY_AMT1": float(pay_amt1),
                        "AGE": int(age)
                    },
                    "probability": float(prob),
                    "prediction": int(pred),
                    "risk_level": "HIGH" if pred == 1 else "LOW"
                }
                db["predictions"].insert_one(record)
                st.caption("💾 Predicción registrada en MongoDB (Colección: `predictions`)")
    
    with col_info:
        # Panel lateral informativo
        st.subheader("📈 Información del Modelo")
        
        # Hiperparámetros
        with st.expander("⚙️ Hiperparámetros Óptimos", expanded=True):
            params = model.get_params()
            params_display = pd.DataFrame({
                'Parámetro': ['n_estimators', 'max_depth', 'learning_rate'],
                'Valor': [
                    params.get('n_estimators', 'N/A'),
                    params.get('max_depth', 'N/A'),
                    params.get('learning_rate', 'N/A')
                ]
            })
            st.dataframe(params_display, hide_index=True, use_container_width=True)
        
        # Importancia de características (si está disponible)
        try:
            if hasattr(model, 'feature_importances_'):
                st.subheader("🎯 Importancia de Features")
                importance_df = pd.DataFrame({
                    'Feature': columns,
                    'Importance': model.feature_importances_
                }).sort_values('Importance', ascending=True)
                
                # Top 5 features
                top_5 = importance_df.tail(5)
                st.bar_chart(top_5.set_index('Feature'), use_container_width=True)
        except:
            pass
        
        # Estadísticas rápidas
        st.subheader("📊 Guía Rápida")
        st.markdown("""
        **Variables Críticas:**
        - PAY_0: Estado de pago más reciente
        - LIMIT_BAL: Límite de crédito
        - BILL_AMT1: Monto de factura
        
        **Interpretación:**
        - 🔴 >70%: Alto riesgo
        - 🟡 30-70%: Riesgo medio
        - 🟢 <30%: Bajo riesgo
        """)
        
        # Conexión a BD
        st.divider()
        st.info("🔄 Las predicciones se guardan en MongoDB para auditoría y análisis posterior.")
