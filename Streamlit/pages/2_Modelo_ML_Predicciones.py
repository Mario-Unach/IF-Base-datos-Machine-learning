import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import pyodbc
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import os
import sys

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
# PREPARACIÓN DE DATOS (CORREGIDO)
# ==========================================
if model_choice == "K-Means (Clustering)":
    features_to_drop = ['ID', 'default payment next month', 'Cluster']
    X = df.drop(columns=features_to_drop, errors='ignore')
    # ✅ CORRECCIÓN: Pasamos el DataFrame 'X', NO 'X.values'
    X_scaled = kmeans_scaler.transform(X)
    # ✅ CORRECCIÓN: Asignamos las predicciones al DataFrame para que el gráfico funcione
    df['Cluster'] = kmeans_model.predict(X_scaled)

elif model_choice == "Random Forest (Clasificación)":
    X = df.drop(columns=['ID'], errors='ignore')
    if hasattr(rf_scaler, 'feature_names_in_'):
        expected_names = rf_scaler.feature_names_in_
        if list(X.columns) != list(expected_names):
            X.columns = expected_names
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
        st.dataframe(cluster_profile.round(2), width="stretch")
        
        fig = px.bar(
            cluster_profile.reset_index(),
            x='Cluster', y='Tasa_Default_%',
            title='Tasa de Impago por Cluster',
            color='Cluster', color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, width="stretch")
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
        st.plotly_chart(fig_cm, width="stretch")

with tab2:
    st.header("🔮 Predicción Individual")
    st.markdown("Ingresa los datos de un nuevo cliente para realizar una predicción:")
    
    col1, col2 = st.columns(2)
    with col1:
        limit_bal = st.number_input("Límite de Crédito", min_value=0, value=100000, step=10000)
        sex = st.selectbox("Sexo (1=Masculino, 2=Femenino)", [1, 2])
        education = st.selectbox("Educación (1=Grad, 2=University, 3=High School, 4=Others)", [1, 2, 3, 4])
        marriage = st.selectbox("Estado Civil (1=Married, 2=Single, 3=Other)", [1, 2, 3])
        age = st.number_input("Edad", min_value=18, max_value=100, value=30)
        pay_0 = st.number_input("Estado Pago Mes Anterior", value=0)
        pay_2 = st.number_input("Estado Pago Mes 2", value=0)
        pay_3 = st.number_input("Estado Pago Mes 3", value=0)
        pay_4 = st.number_input("Estado Pago Mes 4", value=0)
        pay_5 = st.number_input("Estado Pago Mes 5", value=0)
        pay_6 = st.number_input("Estado Pago Mes 6", value=0)
    with col2:
        bill_amt1 = st.number_input("Monto Factura Mes 1", value=50000)
        bill_amt2 = st.number_input("Monto Factura Mes 2", value=50000)
        bill_amt3 = st.number_input("Monto Factura Mes 3", value=50000)
        bill_amt4 = st.number_input("Monto Factura Mes 4", value=50000)
        bill_amt5 = st.number_input("Monto Factura Mes 5", value=50000)
        bill_amt6 = st.number_input("Monto Factura Mes 6", value=50000)
        pay_amt1 = st.number_input("Pago Realizado Mes 1", value=2000)
        pay_amt2 = st.number_input("Pago Realizado Mes 2", value=2000)
        pay_amt3 = st.number_input("Pago Realizado Mes 3", value=2000)
        pay_amt4 = st.number_input("Pago Realizado Mes 4", value=2000)
        pay_amt5 = st.number_input("Pago Realizado Mes 5", value=2000)
        pay_amt6 = st.number_input("Pago Realizado Mes 6", value=2000)

    if st.button("🎯 Realizar Predicción", type="primary"):
        new_data = np.array([[
            limit_bal, sex, education, marriage, age,
            pay_0, pay_2, pay_3, pay_4, pay_5, pay_6,
            bill_amt1, bill_amt2, bill_amt3, bill_amt4, bill_amt5, bill_amt6,
            pay_amt1, pay_amt2, pay_amt3, pay_amt4, pay_amt5, pay_amt6, 0
        ]])
        
        if model_choice == "K-Means (Clustering)":
            new_data_kmeans = new_data[:, :23]
            new_data_scaled = kmeans_scaler.transform(new_data_kmeans)
            cluster_pred = kmeans_model.predict(new_data_scaled)[0]
            st.success(f"✅ El cliente pertenece al **Cluster {cluster_pred}**")
            
            cluster_info = df[df['Cluster'] == cluster_pred]
            st.info(f"""
            **Características del Cluster {cluster_pred}:**
            - Clientes en este cluster: {len(cluster_info)}
            - Tasa de default: {cluster_info['default payment next month'].mean()*100:.2f}%
            - Límite de crédito promedio: ${cluster_info['LIMIT_BAL'].mean():,.0f}
            - Edad promedio: {cluster_info['AGE'].mean():.1f} años
            """)
        else:
            new_data_scaled = rf_scaler.transform(new_data)
            rf_pred = rf_model.predict(new_data_scaled)[0]
            rf_proba = rf_model.predict_proba(new_data_scaled)[0]
            if rf_pred == 1:
                st.error(f"⚠️ **Alto Riesgo**: Probabilidad de default ({rf_proba[1]*100:.2f}%)")
            else:
                st.success(f"✅ **Bajo Riesgo**: Probabilidad de default ({rf_proba[0]*100:.2f}%)")

with tab3:
    st.header("📈 Visualización")
    
    if model_choice == "K-Means (Clustering)":
        st.subheader("Distribución de Clientes en 2D (PCA)")
        
        # Aplicar PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Crear DataFrame para graficar - ASEGURAR TIPOS CORRECTOS
        pca_df = pd.DataFrame({
            'PCA1': X_pca[:, 0].astype(float),
            'PCA2': X_pca[:, 1].astype(float),
            'Cluster': df['Cluster'].astype(str),
            'Default': df['default payment next month'].astype(int).map({0: 'No', 1: 'Sí'})
        })
        
        # Verificar que hay datos válidos
        if pca_df.isna().any().any():
            st.warning("⚠️ Hay valores NaN en los datos")
            pca_df = pca_df.dropna()
        
        # Crear gráfico con configuración explícita
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
        
        # Configurar el layout explícitamente
        fig.update_layout(
            xaxis_title="Componente Principal 1",
            yaxis_title="Componente Principal 2",
            height=600,
            showlegend=True
        )
        
        # MOSTRAR EL GRÁFICO
        st.plotly_chart(fig, use_container_width=True, key="pca_kmeans")
        
        st.info("""
        **Interpretación:**
        - Los puntos de colores representan los clientes agrupados por cluster
        - Los símbolos indican si el cliente hizo default o no
        - Los clusters agrupan clientes con comportamientos similares
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