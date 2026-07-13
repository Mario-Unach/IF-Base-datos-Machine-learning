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

# Agregar la ruta raíz al path para importar db_connections
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de página
st.set_page_config(
    page_title="Modelos ML - Predicciones",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CORRECCIÓN DE RUTAS - Navegar correctamente en la estructura
# 2_Modelo_ML_Predicciones.py está en: Streamlit/pages/
# Necesitamos subir 2 niveles para llegar a la raíz del proyecto
current_file = os.path.abspath(__file__)  # Ruta del archivo actual
pages_dir = os.path.dirname(current_file)  # Streamlit/pages/
streamlit_dir = os.path.dirname(pages_dir)  # Streamlit/
ROOT_DIR = os.path.dirname(streamlit_dir)  # Carpeta raíz del proyecto

# Ahora construir las rutas correctas
KMEANS_MODEL_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "kmeans_model.pkl")
KMEANS_SCALER_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "scaler.pkl")
KMEANS_CENTERS_PATH = os.path.join(ROOT_DIR, "Models", "K-Means", "cluster_centers.pkl")
RF_MODEL_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "random_forest_optimizado.pkl")
RF_SCALER_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "scaler.pkl")
RF_FEATURES_PATH = os.path.join(ROOT_DIR, "Models", "Random_Forest", "feature_names.pkl")
DATASET_PATH = os.path.join(ROOT_DIR, "Dataset", "default of credit card clients.csv")

# Cargar modelos con cache
@st.cache_resource
def load_kmeans_models():
    """Carga los modelos K-Means"""
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
    """Carga los modelos Random Forest"""
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
    """Carga el dataset"""
    try:
        df = pd.read_csv(DATASET_PATH, header=1)
        return df
    except FileNotFoundError:
        st.error(f"❌ No se encontró el dataset en {DATASET_PATH}")
        return None

# Título principal
st.title("🤖 Modelos de Machine Learning - Predicciones")
st.markdown("---")

# Cargar datos y modelos
df = load_dataset()
kmeans_model, kmeans_scaler, kmeans_centers = load_kmeans_models()
rf_model, rf_scaler, rf_features = load_rf_models()

if df is None or kmeans_model is None or rf_model is None:
    st.stop()

# Sidebar para selección de modelo
st.sidebar.header("⚙️ Configuración")
model_choice = st.sidebar.selectbox(
    "Selecciona el Modelo",
    ["K-Means (Clustering)", "Random Forest (Clasificación)"]
)

# Preparar datos según el modelo seleccionado
if model_choice == "K-Means (Clustering)":
    # K-Means: eliminar ID y target
    features_to_drop = ['ID', 'default payment next month']
    X = df.drop(columns=features_to_drop, errors='ignore')
    X_scaled = kmeans_scaler.transform(X.values)
    df['Cluster'] = kmeans_model.predict(X_scaled)
    
if model_choice == "Random Forest (Clasificación)":
    # Obtener los nombres reales de las columnas (excluyendo 'ID')
    real_feature_names = [col for col in df.columns if col != 'ID']
    
    # Crear mapeo si rf_features tiene nombres genéricos como 'X0', 'X1', etc.
    if rf_features and rf_features[0].startswith('X'):
        feature_mapping = {f'X{i}': name for i, name in enumerate(real_feature_names)}
        # Mapear los nombres en feature_importance
        feature_importance['Feature'] = feature_importance['Feature'].map(
            lambda x: feature_mapping.get(x, x)
        )
    
    # Usar DataFrame con nombres de columnas correctos para el transform
    X = df.drop(columns=['ID'], errors='ignore')
    # Renombrar columnas si es necesario para que coincidan con lo que espera el scaler
    if hasattr(rf_scaler, 'feature_names_in_'):
        expected_names = rf_scaler.feature_names_in_
        # Asegurarse de que X tenga los nombres esperados
        if list(X.columns) != list(expected_names):
            X.columns = expected_names
    X_scaled = rf_scaler.transform(X)

# Tabs para diferentes funcionalidades
tab1, tab2, tab3 = st.tabs(["📊 Análisis del Modelo", "🔮 Predicción Individual", "📈 Visualización"])

with tab1:
    if model_choice == "K-Means (Clustering)":
        st.header("📊 Análisis de Clusters con K-Means")
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Clientes", len(df))
        with col2:
            st.metric("Número de Clusters", kmeans_model.n_clusters)
        with col3:
            default_rate = df['default payment next month'].mean() * 100
            st.metric("Tasa Default Global", f"{default_rate:.2f}%")
        
        # Perfil de clusters
        st.subheader("Perfil de Clusters")
        key_vars = ['LIMIT_BAL', 'AGE', 'PAY_0', 'BILL_AMT1', 'PAY_AMT1', 'default payment next month']
        cluster_profile = df.groupby('Cluster')[key_vars].mean()
        default_rate_cluster = df.groupby('Cluster')['default payment next month'].mean() * 100
        cluster_profile['Tasa_Default_%'] = default_rate_cluster
        
        st.dataframe(cluster_profile.round(2), use_container_width=True)
        
        # Gráfico de tasa de default por cluster
        fig = px.bar(
            cluster_profile.reset_index(),
            x='Cluster',
            y='Tasa_Default_%',
            title='Tasa de Impago por Cluster',
            color='Cluster',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:  # Random Forest
        st.header("📊 Análisis de Random Forest")
        
        # Predicciones en el dataset completo
        y_true = df['default payment next month']
        y_pred = rf_model.predict(X_scaled)
        
        # Métricas del modelo
        st.subheader("Métricas del Modelo")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            accuracy = accuracy_score(y_true, y_pred)
            st.metric("Accuracy", f"{accuracy:.4f}")
        with col2:
            precision = precision_score(y_true, y_pred)
            st.metric("Precision", f"{precision:.4f}")
        with col3:
            recall = recall_score(y_true, y_pred)
            st.metric("Recall", f"{recall:.4f}")
        with col4:
            f1 = f1_score(y_true, y_pred)
            st.metric("F1-Score", f"{f1:.4f}")
        
        # Matriz de confusión
        st.subheader("Matriz de Confusión")
        cm = confusion_matrix(y_true, y_pred)
        fig_cm = px.imshow(
            cm,
            text_auto=True,
            aspect="auto",
            title="Matriz de Confusión",
            labels=dict(x="Predicho", y="Real", color="Cantidad"),
            x=["No Default", "Default"],
            y=["No Default", "Default"],
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_cm, use_container_width=True)
        
        # Importancia de características
        st.subheader("Importancia de Características")

        # Usamos las columnas del DataFrame X que se usó para el escalado.
        # Esto garantiza que la longitud coincida exactamente con la del modelo.
        feature_names = X.columns.tolist()

        feature_importance = pd.DataFrame({
            'Feature': feature_names,
            'Importance': rf_model.feature_importances_
        }).sort_values('Importance', ascending=False)

        fig_imp = px.bar(
            feature_importance.head(15),
            x='Importance',
            y='Feature',
            orientation='h',
            title='Top 15 Características Más Importantes',
            color='Importance',
            color_continuous_scale='Viridis'
        )
        fig_imp.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_imp, use_container_width=True)
        
        # Distribución de predicciones
        st.subheader("Distribución de Predicciones")
        pred_df = pd.DataFrame({
            'Real': y_true,
            'Predicho': y_pred
        })
        
        col1, col2 = st.columns(2)
        with col1:
            fig_real = px.pie(
                pred_df,
                names='Real',
                title='Distribución Real',
                color='Real',
                color_discrete_map={0: '#636EFA', 1: '#EF553B'}
            )
            st.plotly_chart(fig_real, use_container_width=True)
        with col2:
            fig_pred = px.pie(
                pred_df,
                names='Predicho',
                title='Distribución Predicha',
                color='Predicho',
                color_discrete_map={0: '#636EFA', 1: '#EF553B'}
            )
            st.plotly_chart(fig_pred, use_container_width=True)

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
        pay_0 = st.number_input("Estado Pago Mes Anterior (-1=Pagado, 0=Uso, 1-9=Retraso)", value=0)
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
        # Crear array con las características en el orden correcto
        new_data = np.array([[
            limit_bal, sex, education, marriage, age,
            pay_0, pay_2, pay_3, pay_4, pay_5, pay_6,
            bill_amt1, bill_amt2, bill_amt3, bill_amt4, bill_amt5, bill_amt6,
            pay_amt1, pay_amt2, pay_amt3, pay_amt4, pay_amt5, pay_amt6,
            0  # Valor dummy para la columna target (no se usa en predicción)
        ]])
        
        if model_choice == "K-Means (Clustering)":
            # Para K-Means, usar solo las 23 características sin el target
            new_data_kmeans = new_data[:, :23]
            new_data_scaled = kmeans_scaler.transform(new_data_kmeans)
            cluster_pred = kmeans_model.predict(new_data_scaled)[0]
            
            st.success(f"✅ El cliente pertenece al **Cluster {cluster_pred}**")
            
            # Mostrar características del cluster
            cluster_info = df[df['Cluster'] == cluster_pred]
            
            st.info(f"""
            **Características del Cluster {cluster_pred}:**
            - Clientes en este cluster: {len(cluster_info)}
            - Tasa de default: {cluster_info['default payment next month'].mean()*100:.2f}%
            - Límite de crédito promedio: ${cluster_info['LIMIT_BAL'].mean():,.0f}
            - Edad promedio: {cluster_info['AGE'].mean():.1f} años
            """)
        else:
            # Para Random Forest, usar las 24 características
            new_data_scaled = rf_scaler.transform(new_data)  # new_data ya es numpy array, no debería fallar
            rf_pred = rf_model.predict(new_data_scaled)[0]
            rf_proba = rf_model.predict_proba(new_data_scaled)[0]
            
            if rf_pred == 1:
                st.error(f"⚠️ **Alto Riesgo**: El cliente tiene alta probabilidad de default ({rf_proba[1]*100:.2f}%)")
            else:
                st.success(f"✅ **Bajo Riesgo**: El cliente tiene baja probabilidad de default ({rf_proba[0]*100:.2f}%)")
            
            # Mostrar probabilidades
            proba_df = pd.DataFrame({
                'Clase': ['No Default', 'Default'],
                'Probabilidad': rf_proba * 100
            })
            
            fig_proba = px.bar(
                proba_df,
                x='Clase',
                y='Probabilidad',
                title='Probabilidades de Predicción',
                color='Clase',
                color_discrete_map={'No Default': '#636EFA', 'Default': '#EF553B'}
            )
            st.plotly_chart(fig_proba, use_container_width=True)

with tab3:
    st.header("📈 Visualización")
    
    if model_choice == "K-Means (Clustering)":
        # Visualización PCA para K-Means
        st.subheader("Distribución de Clientes en 2D (PCA)")
        
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        pca_df = pd.DataFrame({
            'PCA1': X_pca[:, 0],
            'PCA2': X_pca[:, 1],
            'Cluster': df['Cluster'].astype(str),
            'Default': df['default payment next month'].map({0: 'No', 1: 'Sí'})
        })
        
        fig = px.scatter(
            pca_df,
            x='PCA1',
            y='PCA2',
            color='Cluster',
            symbol='Default',
            title='Distribución de Clientes por Cluster',
            hover_data=['Cluster', 'Default']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Información adicional
        st.info("""
        **Interpretación:**
        - Los puntos de colores representan los clientes agrupados por cluster
        - Los símbolos indican si el cliente hizo default o no
        - Los clusters agrupan clientes con comportamientos similares
        """)
        
    else: # Random Forest
        # Visualización de distribución de características importantes
        st.subheader("Distribución de Características Importantes")

        if hasattr(rf_model, 'feature_importances_'):
            importances = rf_model.feature_importances_
            
            # SOLUCIÓN: Extraemos los nombres reales del DataFrame cargado.
            # El modelo fue entrenado con 24 columnas (todas excepto 'ID').
            correct_feature_names = [col for col in df.columns if col != 'ID']
            
            # Creamos el DataFrame con los 24 nombres reales y las 24 importancias
            feature_importance = pd.DataFrame({
                'Feature': correct_feature_names,
                'Importance': importances
            }).sort_values('Importance', ascending=False)

            # Seleccionar las 5 características más importantes
            top_features = feature_importance.head(5)['Feature'].tolist()

            # Crear subplots
            fig_dist = make_subplots(
                rows=2, cols=3,
                subplot_titles=top_features + ['Accuracy'],
                specs=[[{"type": "histogram"}, {"type": "histogram"}, {"type": "histogram"}],
                       [{"type": "histogram"}, {"type": "histogram"}, {"type": "indicator"}]]
            )

            # Agregar histogramas para cada característica importante
            for i, feature in enumerate(top_features):
                row = i // 3 + 1
                col = i % 3 + 1
                fig_dist.add_trace(
                    go.Histogram(
                        x=df[feature], # Ahora 'feature' es un nombre real como 'PAY_0' o 'LIMIT_BAL'
                        name=feature,
                        marker_color='#636EFA',
                        showlegend=False
                    ),
                    row=row, col=col
                )

            # Agregar indicador de accuracy
            # Calculamos el accuracy usando el dataset completo para el gauge
            y_true = df['default payment next month']
            # .values convierte el DataFrame a un array de NumPy, ignorando la validación estricta de nombres
            X_rf_array = df.drop(columns=['ID']).values
            X_scaled = rf_scaler.transform(X_rf_array)
            y_pred = rf_model.predict(X_scaled)
            acc_val = accuracy_score(y_true, y_pred) * 100

            fig_dist.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=acc_val,
                    title={'text': "Accuracy (%)"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#636EFA"},
                        'steps': [
                            {'range': [0., 50.], 'color': "#EF553B"},
                            {'range': [50., 75.], 'color': "#FFA15A"},
                            {'range': [75., 100.], 'color': "#00CC96"}
                        ]
                    }
                ),
                row=2, col=3
            )

            fig_dist.update_layout(height=600, showlegend=False, title_text="Distribución de las 5 Características Más Importantes")
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Información adicional
            st.info("""
            **Interpretación:**
            - Los histogramas muestran la distribución de las características que más peso tienen en la decisión del modelo.
            - El gauge indica el Accuracy (precisión) global del modelo.
            """)

# Información adicional en el sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Información")
st.sidebar.markdown("""
**Modelos disponibles:**
- **K-Means**: Clustering para segmentación de clientes
- **Random Forest**: Clasificación para predicción de default

**Dataset:**
- 30,000 clientes
- 23 características
- Target: default payment next month
""")