import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import os
import sys
from pathlib import Path

# Agregar la ruta raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de página
st.set_page_config(
    page_title="Modelos ML - Predicciones",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Construir las rutas correctas
current_file = os.path.abspath(__file__)
pages_dir = os.path.dirname(current_file)
streamlit_dir = os.path.dirname(pages_dir)
ROOT_DIR = os.path.dirname(streamlit_dir)

KMEANS_MODEL_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "kmeans_model.pkl")
KMEANS_SCALER_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "scaler.pkl")
KMEANS_CENTERS_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "cluster_centers.pkl")
RF_MODEL_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "random_forest_optimizado.pkl")
RF_SCALER_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "scaler.pkl")
RF_FEATURES_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "feature_names.pkl")

@st.cache_resource
def load_kmeans_models():
    try:
        kmeans = joblib.load(KMEANS_MODEL_PATH)
        scaler = joblib.load(KMEANS_SCALER_PATH)
        centers = joblib.load(KMEANS_CENTERS_PATH)
        return kmeans, scaler, centers
    except FileNotFoundError as e:
        st.error(f"❌ Error cargando modelos K-Means: {e}")
        return None, None, None

@st.cache_resource
def load_rf_models():
    try:
        rf_model = joblib.load(RF_MODEL_PATH)
        rf_scaler = joblib.load(RF_SCALER_PATH)
        rf_features = joblib.load(RF_FEATURES_PATH)
        return rf_model, rf_scaler, rf_features
    except FileNotFoundError as e:
        st.error(f"❌ Error cargando modelos Random Forest: {e}")
        return None, None, None

@st.cache_data
def load_dataset():
    """Carga el dataset directamente desde SQL Server"""
    import pyodbc
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost,1433;"
            "DATABASE=CC_Client;"
            "UID=sa;"
            "PWD=Soymario.7;"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        
        query = """
            SELECT 
                id_cliente AS ID,
                id_sexo AS SEX,
                id_educacion AS EDUCATION,
                id_estado_civil AS MARRIAGE,
                edad AS AGE,
                limite_credito AS LIMIT_BAL,
                PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
                BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
                PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
                target AS [default payment next month]
            FROM vw_ml_dataset
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error cargando datos desde SQL Server: {e}")
        return None

st.title("🤖 Modelos de Machine Learning - Predicciones")
st.markdown("---")

df = load_dataset()
kmeans_model, kmeans_scaler, kmeans_centers = load_kmeans_models()
rf_model, rf_scaler, rf_features = load_rf_models()

if df is None or kmeans_model is None or rf_model is None:
    st.stop()

st.sidebar.header("⚙️ Configuración")
model_choice = st.sidebar.selectbox(
    "Selecciona el Modelo",
    ["K-Means (Clustering)", "Random Forest (Clasificación)"]
)

# ==========================================
# PREPARACIÓN DE DATOS (CORREGIDO PARA AMBOS MODELOS)
# ==========================================
X_scaled = None  # Variable global para usar en tab3

if model_choice == "K-Means (Clustering)":
    features_to_drop = ['ID', 'default payment next month', 'Cluster']
    X = df.drop(columns=features_to_drop, errors='ignore')
    
    # 🔥 CORRECCIÓN CRÍTICA: Renombrar columnas para que coincidan con el scaler
    if hasattr(kmeans_scaler, 'feature_names_in_'):
        expected_names = kmeans_scaler.feature_names_in_
        if len(X.columns) == len(expected_names):
            X.columns = expected_names
    
    X_scaled = kmeans_scaler.transform(X)
    df['Cluster'] = kmeans_model.predict(X_scaled)

elif model_choice == "Random Forest (Clasificación)":
    X = df.drop(columns=['ID'], errors='ignore')
    
    # 🔥 CORRECCIÓN CRÍTICA: Renombrar columnas para que coincidan con el scaler
    if hasattr(rf_scaler, 'feature_names_in_'):
        expected_names = rf_scaler.feature_names_in_
        if len(X.columns) == len(expected_names):
            X.columns = expected_names
        else:
            st.error(f"❌ Error de dimensiones: El modelo espera {len(expected_names)} características, pero se recibieron {len(X.columns)}.")
            st.stop()
    
    X_scaled = rf_scaler.transform(X)

# ==========================================
# PESTAÑAS DE LA APLICACIÓN
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Análisis del Modelo", "🔮 Predicción Individual", "📈 Visualización"])

with tab1:
    if model_choice == "K-Means (Clustering)":
        st.header("📊 Análisis de Clusters con K-Means")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Clientes", len(df))
        with col2:
            st.metric("Número de Clusters", kmeans_model.n_clusters)
        with col3:
            default_rate = df['default payment next month'].mean() * 100
            st.metric("Tasa Default Global", f"{default_rate:.2f}%")
        
        st.subheader("Perfil de Clusters")
        key_vars = ['LIMIT_BAL', 'AGE', 'PAY_0', 'BILL_AMT1', 'PAY_AMT1', 'default payment next month']
        cluster_profile = df.groupby('Cluster')[key_vars].mean()
        cluster_profile['Tasa_Default_%'] = df.groupby('Cluster')['default payment next month'].mean() * 100
        st.dataframe(cluster_profile.round(2), use_container_width=True)
        
        fig = px.bar(
            cluster_profile.reset_index(),
            x='Cluster', y='Tasa_Default_%',
            title='Tasa de Impago por Cluster',
            color='Cluster', color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.header("📊 Análisis de Random Forest")
        y_true = df['default payment next month']
        y_pred = rf_model.predict(X_scaled)
        
        st.subheader("Métricas del Modelo")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Accuracy", f"{accuracy_score(y_true, y_pred):.4f}")
        with col2: st.metric("Precision", f"{precision_score(y_true, y_pred):.4f}")
        with col3: st.metric("Recall", f"{recall_score(y_true, y_pred):.4f}")
        with col4: st.metric("F1-Score", f"{f1_score(y_true, y_pred):.4f}")
        
        st.subheader("Matriz de Confusión")
        cm = confusion_matrix(y_true, y_pred)
        fig_cm = px.imshow(cm, text_auto=True, aspect="auto", title="Matriz de Confusión",
                           labels=dict(x="Predicho", y="Real", color="Cantidad"),
                           x=["No Default", "Default"], y=["No Default", "Default"], color_continuous_scale='Blues')
        st.plotly_chart(fig_cm, use_container_width=True)

with tab2:
    st.header("🔮 Predicción Individual")
    st.info("💡 Ingresa solo las 6 variables más importantes. El sistema completará automáticamente el resto con los promedios del dataset para realizar la predicción.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        limit_bal = st.number_input("💰 Límite de Crédito", 10000, 1000000, 150000, step=10000)
        age = st.slider("📅 Edad", 18, 80, 30)
    with c2:
        pay_0 = st.slider("📊 Estado Pago Mes Actual (-1=puntual, 0-9=retraso)", -2, 8, 0)
        pay_2 = st.slider("📊 Estado Pago Mes 2", -2, 8, 0)
    with c3:
        bill_amt1 = st.number_input("💵 Factura Mes 1", 0, 1000000, 50000, step=1000)
        pay_amt1 = st.number_input("💳 Pago Realizado Mes 1", 0, 1000000, 5000, step=500)
    
    if st.button("🎯 Predecir", type="primary", use_container_width=True):
        # 1. Obtener las medias del dataset para rellenar las variables faltantes
        cols_to_drop = ['ID', 'default payment next month', 'Cluster', 'target']
        means = df.drop(columns=[c for c in cols_to_drop if c in df.columns]).mean()
        new_row = means.copy()
        
        # 2. Asignar los valores ingresados por el usuario
        new_row['LIMIT_BAL'] = float(limit_bal)
        new_row['AGE'] = float(age)
        new_row['PAY_0'] = float(pay_0)
        new_row['PAY_2'] = float(pay_2)
        new_row['BILL_AMT1'] = float(bill_amt1)
        new_row['PAY_AMT1'] = float(pay_amt1)
        
        # Convertir a array de numpy para evitar errores de índices de Pandas
        X_new_array = new_row.values.reshape(1, -1)
        
        if model_choice == "Random Forest (Clasificación)":
            # 🔥 CORRECCIÓN DEFINITIVA: Ajustar dimensiones al vuelo
            expected_features = rf_scaler.n_features_in_
            current_features = X_new_array.shape[1]
            
            if current_features < expected_features:
                # El scaler espera más columnas (probablemente incluyó el target o un índice al entrenar)
                padding = np.zeros((1, expected_features - current_features))
                X_new_array = np.hstack([X_new_array, padding])
            elif current_features > expected_features:
                X_new_array = X_new_array[:, :expected_features]
            
            # Escalar y predecir
            X_new_scaled = rf_scaler.transform(X_new_array)
            pred = rf_model.predict(X_new_scaled)[0]
            proba = rf_model.predict_proba(X_new_scaled)[0]
            
            if pred == 1:
                st.error(f"⚠️ **ALTO RIESGO DE DEFAULT** · Probabilidad: **{proba[1]*100:.1f}%**")
            else:
                st.success(f"✅ **BAJO RIESGO** · Probabilidad de default: **{proba[1]*100:.1f}%**")
            
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                proba_df = pd.DataFrame({'Clase': ['No Default', 'Default'], 'Prob': proba * 100})
                fig_p = px.bar(proba_df, x='Clase', y='Prob', color='Clase',
                              color_discrete_map={'No Default': '#00d4ff', 'Default': '#EF553B'})
                fig_p.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   font=dict(color='#e2e8f0'), showlegend=False)
                st.plotly_chart(fig_p, use_container_width=True)
                
        elif model_choice == "K-Means (Clustering)":
            # 🔥 Ajustar dimensiones para K-Means también por seguridad
            expected_features = kmeans_scaler.n_features_in_
            current_features = X_new_array.shape[1]
            
            if current_features < expected_features:
                padding = np.zeros((1, expected_features - current_features))
                X_new_array = np.hstack([X_new_array, padding])
            elif current_features > expected_features:
                X_new_array = X_new_array[:, :expected_features]
                
            X_new_scaled = kmeans_scaler.transform(X_new_array)
            cluster_pred = kmeans_model.predict(X_new_scaled)[0]
            st.success(f"✅ El cliente pertenece al **Cluster {cluster_pred}**")
            
            cluster_info = df[df['Cluster'] == cluster_pred]
            st.markdown(f"""
            <div class="pred-card">
            <b>📊 Perfil del Cluster {cluster_pred}:</b><br>
            • Clientes en este cluster: <b>{len(cluster_info):,}</b><br>
            • Tasa de default: <b>{cluster_info['default payment next month'].mean()*100:.1f}%</b><br>
            • Límite de crédito promedio: <b>${cluster_info['LIMIT_BAL'].mean():,.0f}</b><br>
            • Edad promedio: <b>{cluster_info['AGE'].mean():.1f} años</b>
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.header("📈 Visualización")
    
    if model_choice == "K-Means (Clustering)":
        st.subheader("Distribución de Clientes en 2D (PCA)")
        
        # Verificar que X_scaled existe y tiene datos
        if X_scaled is None or len(X_scaled) == 0:
            st.error("❌ No hay datos escalados para visualizar. Revisa la preparación de datos.")
            st.stop()
        
        # Verificar que la columna Cluster existe
        if 'Cluster' not in df.columns:
            st.error("❌ La columna 'Cluster' no existe en el DataFrame.")
            st.stop()
        
        # Aplicar PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Crear DataFrame para graficar
        pca_df = pd.DataFrame({
            'PCA1': X_pca[:, 0].astype(float),
            'PCA2': X_pca[:, 1].astype(float),
            'Cluster': df['Cluster'].astype(str),
            'Default': df['default payment next month'].astype(int).map({0: 'No', 1: 'Sí'})
        })
        
        # Verificar que hay datos válidos
        if pca_df.isna().any().any():
            st.warning("⚠️ Hay valores NaN en los datos, se eliminarán")
            pca_df = pca_df.dropna()
        
        # Crear gráfico
        fig = px.scatter(
            pca_df,
            x='PCA1',
            y='PCA2',
            color='Cluster',
            symbol='Default',
            title='Distribución de Clientes por Cluster',
            hover_data=['Cluster', 'Default'],
            opacity=0.7,
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        
        fig.update_layout(
            xaxis_title="Componente Principal 1",
            yaxis_title="Componente Principal 2",
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True, key="pca_kmeans")
        
        st.info("""
        **Interpretación:**
        - Los puntos de colores representan los clientes agrupados por cluster
        - Los símbolos indican si el cliente hizo default o no
        - Los clusters agrupan clientes con comportamientos similares
        """)
    
    else:  # Random Forest
        st.subheader("Análisis Visual del Modelo Random Forest")
        
        # Verificar que X_scaled existe
        if X_scaled is None or len(X_scaled) == 0:
            st.error("❌ No hay datos escalados para visualizar.")
            st.stop()
        
        # 1. Importancia de Características
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 🎯 Top 15 Variables Más Importantes")
            feature_importance = pd.DataFrame({
                'Feature': X.columns,
                'Importancia': rf_model.feature_importances_
            }).sort_values('Importancia', ascending=False).head(15)
            
            fig_imp = px.bar(
                feature_importance,
                x='Importancia',
                y='Feature',
                orientation='h',
                title='Importancia de Variables en la Predicción',
                color='Importancia',
                color_continuous_scale='Viridis'
            )
            fig_imp.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=500,
                showlegend=False
            )
            st.plotly_chart(fig_imp, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Métricas del Modelo")
            y_pred = rf_model.predict(X_scaled)
            y_true = df['default payment next month']
            
            accuracy = accuracy_score(y_true, y_pred)
            st.metric("🎯 Accuracy", f"{accuracy:.2%}")
            st.metric("📈 Precision", f"{precision_score(y_true, y_pred):.2%}")
            st.metric("🔍 Recall", f"{recall_score(y_true, y_pred):.2%}")
            st.metric("⚖️ F1-Score", f"{f1_score(y_true, y_pred):.2%}")
        
        st.divider()
        
        # 2. Matriz de Confusión y Distribución
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 🔢 Matriz de Confusión")
            cm = confusion_matrix(y_true, y_pred)
            fig_cm = px.imshow(
                cm,
                text_auto=True,
                aspect="auto",
                title='Predicciones vs Valores Reales',
                labels=dict(x="Predicho", y="Real", color="Cantidad"),
                x=["No Default (0)", "Default (1)"],
                y=["No Default (0)", "Default (1)"],
                color_continuous_scale='Blues'
            )
            fig_cm.update_layout(height=400)
            st.plotly_chart(fig_cm, use_container_width=True)
        
        with col4:
            st.markdown("#### 📈 Distribución de Predicciones")
            pred_df = pd.DataFrame({
                'Tipo': ['Real', 'Predicho'],
                'No Default': [
                    (y_true == 0).sum(),
                    (y_pred == 0).sum()
                ],
                'Default': [
                    (y_true == 1).sum(),
                    (y_pred == 1).sum()
                ]
            })
            
            fig_dist = px.bar(
                pred_df,
                x='Tipo',
                y=['No Default', 'Default'],
                barmode='group',
                title='Comparación: Real vs Predicho',
                color_discrete_sequence=['#00d4ff', '#EF553B']
            )
            fig_dist.update_layout(
                height=400,
                xaxis_title="",
                yaxis_title="Cantidad de Clientes"
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        
        st.divider()
        
        # 3. Análisis de Probabilidades
        st.markdown("#### 🎲 Distribución de Probabilidades de Default")
        y_proba = rf_model.predict_proba(X_scaled)[:, 1]
        
        proba_df = pd.DataFrame({
            'Probabilidad': y_proba,
            'Clase_Real': df['default payment next month'].map({0: 'No Default', 1: 'Default'})
        })
        
        fig_proba = px.histogram(
            proba_df,
            x='Probabilidad',
            color='Clase_Real',
            nbins=50,
            title='Distribución de Probabilidades Predichas',
            labels={'Probabilidad': 'Probabilidad de Default'},
            color_discrete_map={'No Default': '#00d4ff', 'Default': '#EF553B'},
            opacity=0.7
        )
        fig_proba.update_layout(
            height=400,
            xaxis_title="Probabilidad de Default",
            yaxis_title="Cantidad de Clientes",
            barmode='overlay'
        )
        st.plotly_chart(fig_proba, use_container_width=True)
        
        st.info("""
        **Interpretación:**
        - **Importancia de Variables:** Muestra qué características tienen más peso en la decisión del modelo
        - **Matriz de Confusión:** Compara las predicciones del modelo con los valores reales
        - **Distribución de Predicciones:** Visualiza cuántos clientes se predijeron correctamente
        - **Probabilidades:** Muestra cómo el modelo asigna probabilidades a cada cliente
        """)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Información")
st.sidebar.markdown("""
**Modelos disponibles:**
- K-Means: Clustering para segmentación
- Random Forest: Clasificación para predicción

**Dataset:**
- 30,000 clientes
- 23 características
- Target: default payment next month
""")