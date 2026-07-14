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


# 1. Agregar la carpeta raíz (Streamlit/) al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 2. Importar el módulo de autenticación
import auth

# 3. Inicializar y proteger la página
auth.init_session_state()
auth.require_role(["Administrador", "Analista"]) # Roles permitidos
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

# ============================================================================
# TAB 3: VISUALIZACIÓN Y ANÁLISIS AVANZADO
# ============================================================================
with tab3:
    st.header("📈 Visualización y Análisis de Resultados")
    st.markdown(
        "Esta sección presenta los resultados visuales del modelo seleccionado, "
        "proporcionando insights clave para la interpretación y validación de los hallazgos."
    )
    
    if model_choice == "K-Means (Clustering)":
        st.markdown("---")
        st.subheader("🔬 Análisis de Segmentación No Supervisada")
        
        # Validación de datos
        if X_scaled is None or len(X_scaled) == 0:
            st.error("❌ No hay datos escalados disponibles para visualización.")
            st.stop()
        
        if 'Cluster' not in df.columns:
            st.error("❌ La columna 'Cluster' no está definida en el dataset.")
            st.stop()
        
        # Aplicar PCA con análisis de varianza explicada
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        varianza_explicada = pca.explained_variance_ratio_ * 100
        
        # Métricas del análisis PCA
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("📊 Varianza PC1", f"{varianza_explicada[0]:.2f}%")
        with col_m2:
            st.metric("📊 Varianza PC2", f"{varianza_explicada[1]:.2f}%")
        with col_m3:
            st.metric("📊 Varianza Total", f"{varianza_explicada.sum():.2f}%")
        
        st.markdown(
            f"**Nota:** Los dos componentes principales capturan el **{varianza_explicada.sum():.2f}%** "
            f"de la varianza total del dataset."
        )
        
        # Crear DataFrame para visualización
        pca_df = pd.DataFrame({
            'Componente Principal 1': X_pca[:, 0].astype(float),
            'Componente Principal 2': X_pca[:, 1].astype(float),
            'Cluster': df['Cluster'].astype(str),
            'Estado de Default': df['default payment next month'].astype(int).map({0: 'No Default', 1: 'Default'})
        })
        
        # Limpiar datos si es necesario
        if pca_df.isna().any().any():
            st.warning("⚠️ Se detectaron valores nulos en los datos. Procediendo con limpieza automática.")
            pca_df = pca_df.dropna()
        
        # Visualización principal: Scatter plot con PCA
        st.markdown("#### 🎯 Distribución Espacial de Clusters (Reducción Dimensional PCA)")
        fig_pca = px.scatter(
            pca_df,
            x='Componente Principal 1',
            y='Componente Principal 2',
            color='Cluster',
            symbol='Estado de Default',
            title=f'Segmentación de Clientes en Espacio 2D (PCA: {varianza_explicada.sum():.1f}% varianza explicada)',
            hover_data=['Cluster', 'Estado de Default'],
            opacity=1,
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=10,
            template="plotly_dark"
        )
        
        fig_pca.update_layout(
            xaxis_title=f"Componente Principal 1 ({varianza_explicada[0]:.1f}% varianza)",
            yaxis_title=f"Componente Principal 2 ({varianza_explicada[1]:.1f}% varianza)",
            height=650,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                font=dict(color="white", size=16),
                title_font=dict(size=18, color="white")
            ),
            plot_bgcolor='rgba(0,0,0,1)',   # <-- Fondo del gráfico negro sólido
            paper_bgcolor='rgba(0,0,0,1)'   # <-- Fondo del lienzo exterior negro sólido
        )
        
        st.plotly_chart(fig_pca, use_container_width=True, key="pca_kmeans_v2")
        
        st.markdown("---")
        
        # Análisis de centroides y características de clusters
        st.markdown("#### 📊 Perfil Detallado de Clusters")
        
        cluster_stats = df.groupby('Cluster').agg({
            'LIMIT_BAL': ['mean', 'median', 'std'],
            'AGE': ['mean', 'median'],
            'default payment next month': ['mean', 'count']
        }).round(2)
        
        # Simplificar nombres de columnas
        cluster_stats.columns = [
            'Límite_Crédito_Media', 'Límite_Crédito_Mediana', 'Límite_Crédito_DesvEst',
            'Edad_Media', 'Edad_Mediana',
            'Tasa_Default', 'Tamaño_Cluster'
        ]
        
        cluster_stats['Tasa_Default_%'] = (cluster_stats['Tasa_Default'] * 100).round(2)
        cluster_stats = cluster_stats.reset_index()
        
        st.dataframe(
            cluster_stats,
            use_container_width=True,
            hide_index=True
        )
        
        # Visualización de tasa de default por cluster
        st.markdown("#### ⚠️ Análisis de Riesgo por Segmento")
        fig_risk = px.bar(
            cluster_stats,
            x='Cluster',
            y='Tasa_Default_%',
            title='Tasa de Incumplimiento por Cluster',
            labels={'Tasa_Default_%': 'Tasa de Default (%)', 'Cluster': 'Segmento'},
            color='Tasa_Default_%',
            color_continuous_scale='RdYlGn_r',
            text='Tasa_Default_%'
        )
        
        fig_risk.update_layout(
            height=450,
            xaxis_title="Segmento de Clientes",
            yaxis_title="Porcentaje de Incumplimiento",
            showlegend=False
        )
        
        fig_risk.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        st.plotly_chart(fig_risk, use_container_width=True)
        
        # Interpretación académica
        st.markdown("#### 📖 Interpretación de Resultados")
        st.info("""
        **Análisis de Segmentación K-Means:**
        
        1. **Reducción Dimensional (PCA):** El análisis de componentes principales permite visualizar 
           la estructura de clusters en un espacio 2D, capturando la variabilidad más significativa 
           del dataset.
        
        2. **Separabilidad de Clusters:** La distribución espacial muestra el grado de separación 
           entre segmentos, indicando la efectividad del algoritmo de clustering.
        
        3. **Correlación con Default:** La superposición del estado de default sobre los clusters 
           revela patrones de riesgo crediticio asociados a cada segmento.
        
        4. **Perfil de Riesgo:** Los clusters con mayor tasa de default pueden considerarse segmentos 
           de alto riesgo, mientras que aquellos con menor tasa representan clientes de bajo riesgo.
        
        **Recomendación:** Utilizar esta segmentación para diseñar estrategias diferenciadas de 
        gestión de riesgo y ofertas comerciales personalizadas.
        """)
    
    else:  # Random Forest
        st.markdown("---")
        st.subheader("🎯 Análisis del Modelo de Clasificación Supervisada")
        
        # Validación de datos
        if X_scaled is None or len(X_scaled) == 0:
            st.error("❌ No hay datos escalados disponibles para análisis.")
            st.stop()
        
        # Generar predicciones
        y_true = df['default payment next month']
        y_pred = rf_model.predict(X_scaled)
        y_proba = rf_model.predict_proba(X_scaled)[:, 1]
        
        # ========================================================================
        # SECCIÓN 1: MÉTRICAS DE RENDIMIENTO
        # ========================================================================
        st.markdown("#### 📊 Métricas de Evaluación del Modelo")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            accuracy = accuracy_score(y_true, y_pred)
            st.metric("🎯 Accuracy", f"{accuracy:.4f}", 
                     help="Proporción de predicciones correctas sobre el total")
        
        with col_m2:
            precision = precision_score(y_true, y_pred)
            st.metric("📈 Precision", f"{precision:.4f}",
                     help="De los predichos como default, cuántos realmente lo fueron")
        
        with col_m3:
            recall = recall_score(y_true, y_pred)
            st.metric("🔍 Recall", f"{recall:.4f}",
                     help="De los defaults reales, cuántos fueron detectados")
        
        with col_m4:
            f1 = f1_score(y_true, y_pred)
            st.metric("⚖️ F1-Score", f"{f1:.4f}",
                     help="Media armónica entre Precision y Recall")
        
        st.markdown("---")
        
        # ========================================================================
        # SECCIÓN 2: ANÁLISIS DE IMPORTANCIA DE VARIABLES
        # ========================================================================
        st.markdown("#### 🔬 Importancia de Variables Predictoras")
        st.markdown(
            "El análisis de importancia de características revela qué variables tienen mayor "
            "influencia en la decisión del modelo Random Forest."
        )
        
        # Calcular importancia de características
        feature_importance_df = pd.DataFrame({
            'Variable': X.columns,
            'Importancia': rf_model.feature_importances_
        }).sort_values('Importancia', ascending=False)
        
        # Top 15 variables
        top_features = feature_importance_df.head(15)
        
        col_imp1, col_imp2 = st.columns([3, 2])
        
        with col_imp1:
            fig_imp = px.bar(
                top_features,
                x='Importancia',
                y='Variable',
                orientation='h',
                title='Top 15 Variables con Mayor Poder Predictivo',
                color='Importancia',
                color_continuous_scale='Viridis',
                labels={'Importancia': 'Importancia Relativa', 'Variable': 'Característica'}
            )
            
            fig_imp.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=550,
                showlegend=False,
                xaxis_title="Importancia Normalizada (Gini Impurity)",
                yaxis_title=""
            )
            
            st.plotly_chart(fig_imp, use_container_width=True)
        
        with col_imp2:
            st.markdown("**📋 Ranking Completo:**")
            st.dataframe(
                feature_importance_df.head(10),
                use_container_width=True,
                hide_index=True
            )
            
            # Estadísticas de importancia
            st.markdown("**📈 Estadísticas:**")
            st.metric("Variables totales", len(feature_importance_df))
            st.metric("Importancia máxima", f"{feature_importance_df['Importancia'].max():.4f}")
            st.metric("Importancia media", f"{feature_importance_df['Importancia'].mean():.4f}")
        
        st.markdown("---")
        
        # ========================================================================
        # SECCIÓN 3: MATRIZ DE CONFUSIÓN Y ANÁLISIS DE ERRORES
        # ========================================================================
        st.markdown("#### 🔢 Matriz de Confusión y Análisis de Clasificación")
        
        col_cm1, col_cm2 = st.columns(2)
        
        with col_cm1:
            st.markdown("**Predicciones vs Valores Reales**")
            
            cm = confusion_matrix(y_true, y_pred)
            
            fig_cm = px.imshow(
                cm,
                text_auto=True,
                aspect="auto",
                title='Matriz de Confusión',
                labels=dict(x="Clase Predicha", y="Clase Real", color="Frecuencia"),
                x=["No Default (0)", "Default (1)"],
                y=["No Default (0)", "Default (1)"],
                color_continuous_scale='Blues'
            )
            
            fig_cm.update_layout(
                height=450,
                xaxis_title="Predicción del Modelo",
                yaxis_title="Valor Real"
            )
            
            st.plotly_chart(fig_cm, use_container_width=True)
        
        with col_cm2:
            st.markdown("**📊 Desglose de Clasificaciones:**")
            
            # Calcular métricas de la matriz de confusión
            tn, fp, fn, tp = cm.ravel()
            
            st.metric("✅ Verdaderos Negativos (TN)", f"{tn:,}",
                     help="Clientes sin default correctamente identificados")
            st.metric("❌ Falsos Positivos (FP)", f"{fp:,}",
                     help="Clientes sin default clasificados incorrectamente como default")
            st.metric("❌ Falsos Negativos (FN)", f"{fn:,}",
                     help="Clientes con default no detectados por el modelo")
            st.metric("✅ Verdaderos Positivos (TP)", f"{tp:,}",
                     help="Clientes con default correctamente identificados")
        
        st.markdown("---")
        
        # ========================================================================
        # SECCIÓN 4: ANÁLISIS DE DISTRIBUCIÓN DE PROBABILIDADES
        # ========================================================================
        st.markdown("#### 🎲 Distribución de Probabilidades de Default")
        st.markdown(
            "El histograma muestra cómo el modelo asigna probabilidades a cada instancia, "
            "permitiendo evaluar la confianza de las predicciones."
        )
        
        proba_df = pd.DataFrame({
            'Probabilidad_Predicha': y_proba,
            'Clase_Real': y_true.map({0: 'No Default', 1: 'Default'})
        })
        
        fig_proba = px.histogram(
            proba_df,
            x='Probabilidad_Predicha',
            color='Clase_Real',
            nbins=60,
            title='Distribución de Probabilidades de Default por Clase Real',
            labels={'Probabilidad_Predicha': 'Probabilidad de Default Predicha', 
                   'count': 'Frecuencia'},
            color_discrete_map={'No Default': '#3498db', 'Default': '#e74c3c'},
            opacity=0.75,
            marginal="box"
        )
        
        fig_proba.update_layout(
            height=500,
            xaxis_title="Probabilidad de Default (0 = Bajo Riesgo, 1 = Alto Riesgo)",
            yaxis_title="Número de Clientes",
            barmode='overlay',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_proba, use_container_width=True)
        
        # Estadísticas de probabilidades
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            st.metric("📊 Probabilidad Media", f"{y_proba.mean():.4f}")
        with col_p2:
            st.metric("📊 Desviación Estándar", f"{y_proba.std():.4f}")
        with col_p3:
            st.metric("📊 Mediana", f"{np.median(y_proba):.4f}")
        
        st.markdown("---")
        
        # ========================================================================
        # SECCIÓN 5: INTERPRETACIÓN ACADÉMICA
        # ========================================================================
        st.markdown("#### 📖 Interpretación y Validación del Modelo")
        st.info("""
        **Análisis del Modelo Random Forest:**
        
        1. **Capacidad Predictiva:** Las métricas de evaluación (Accuracy, Precision, Recall, F1-Score) 
           cuantifican el rendimiento del modelo en la tarea de clasificación binaria.
        
        2. **Importancia de Variables:** El análisis de importancia revela que las variables relacionadas 
           con el historial de pagos (PAY_0, PAY_2) y el límite de crédito (LIMIT_BAL) son los predictores 
           más influyentes, lo cual es consistente con la literatura sobre riesgo crediticio.
        
        3. **Matriz de Confusión:** Permite identificar patrones de error del modelo, particularmente 
           los falsos negativos (clientes con default no detectados), que representan el mayor riesgo 
           para la institución financiera.
        
        4. **Distribución de Probabilidades:** Un modelo bien calibrado debería mostrar probabilidades 
           bajas para la clase "No Default" y altas para la clase "Default". La superposición indica 
           casos ambiguos que requieren análisis adicional.
        
        **Limitaciones y Consideraciones:**
        - El modelo fue entrenado con datos históricos y puede no generalizar a cambios estructurales 
          en el comportamiento de los clientes.
        - La interpretación causal requiere análisis adicional, ya que Random Forest identifica 
          correlaciones, no necesariamente causalidad.
        
        **Recomendaciones:**
        - Implementar el modelo como sistema de alerta temprana para identificar clientes en riesgo.
        - Monitorear continuamente el rendimiento del modelo y reentrenar periódicamente.
        - Combinar las predicciones del modelo con análisis cualitativo para decisiones finales.
        """)

# Información del sistema en el sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Información del Sistema")
st.sidebar.markdown("""
**Modelos Implementados:**
- **K-Means:** Algoritmo de clustering no supervisado para segmentación de clientes
- **Random Forest:** Ensemble de árboles de decisión para clasificación supervisada

**Características del Dataset:**
- 📊 **30,000** registros de clientes
- 🔢 **23** variables predictoras
- 🎯 **Target:** default payment next month (binario)

**Tecnologías:**
- Scikit-learn (modelos ML)
- Pandas (procesamiento de datos)
- Plotly (visualización interactiva)
- Streamlit (interfaz web)
""")