import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import pyodbc
from pathlib import Path
import sys
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from db_connections import get_sql_connection, get_mongo_connection

# 1. Agregar la carpeta raíz (Streamlit/) al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 2. Importar el módulo de autenticación
import auth

# 3. Inicializar y proteger la página
auth.init_session_state()
auth.require_role(["Administrador", "Analista"]) # Roles permitidos

st.set_page_config(page_title="Modelos ML", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.page-header { font-size: 2.6rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
.pred-card { background: rgba(30, 41, 59, 0.8); padding: 1.5rem; border-radius: 12px;
  border-left: 4px solid #00d4ff; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">🤖 Modelos ML & Predicciones</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"`{st.session_state.login_user}`")
    st.divider()
    auth.render_role_menu()
    st.divider()

# Rutas
ROOT = Path(__file__).resolve().parents[2]
KM_PATH = ROOT / "Models" / "K-Means" / "kmeans_model.pkl"
KM_SC_PATH = ROOT / "Models" / "K-Means" / "scaler.pkl"
RF_PATH = ROOT / "Models" / "Random_Forest" / "random_forest_optimizado.pkl"
RF_SC_PATH = ROOT / "Models" / "Random_Forest" / "scaler.pkl"

@st.cache_resource
def load_models():
    return {
        'kmeans': joblib.load(KM_PATH),
        'km_scaler': joblib.load(KM_SC_PATH),
        'rf': joblib.load(RF_PATH),
        'rf_scaler': joblib.load(RF_SC_PATH)
    }

@st.cache_data
def load_data():
    conn_str = ("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;"
                "DATABASE=CC_Client;UID=sa;PWD=Soymario.7;TrustServerCertificate=yes;")
    conn = pyodbc.connect(conn_str)
    df = pd.read_sql("""
        SELECT id_cliente AS ID, id_sexo AS SEX, id_educacion AS EDUCATION,
            id_estado_civil AS MARRIAGE, edad AS AGE, limite_credito AS LIMIT_BAL,
            PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
            BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
            PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
            target AS [default payment next month]
        FROM vw_ml_dataset
    """, conn)
    conn.close()
    return df

models = load_models()
df = load_data()

modelo = st.selectbox("🎯 Modelo:", ["Random Forest (Clasificación)", "K-Means (Clustering)", "📜 Historial MongoDB"])

# ============ RANDOM FOREST ============
if modelo == "Random Forest (Clasificación)":
    tab1, tab2 = st.tabs(["📊 Métricas del Modelo", "🔮 Predicción en Vivo"])
    
    X = df.drop(columns=['ID', 'default payment next month'])
    X_scaled = models['rf_scaler'].transform(X)
    y_true = df['default payment next month']
    y_pred = models['rf'].predict(X_scaled)
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎯 Accuracy", f"{accuracy_score(y_true, y_pred):.2%}")
        c2.metric("🎯 Precision", f"{precision_score(y_true, y_pred):.2%}")
        c3.metric("🎯 Recall", f"{recall_score(y_true, y_pred):.2%}")
        c4.metric("🎯 F1-Score", f"{f1_score(y_true, y_pred):.2%}")
        
        col1, col2 = st.columns(2)
        with col1:
            cm = confusion_matrix(y_true, y_pred)
            fig_cm = px.imshow(cm, text_auto=True, aspect="auto", title="Matriz de Confusión",
                              x=["No Default", "Default"], y=["No Default", "Default"],
                              color_continuous_scale='Blues')
            st.plotly_chart(fig_cm, use_container_width=True)
        
        with col2:
            feat_imp = pd.DataFrame({
                'Feature': X.columns,
                'Importancia': models['rf'].feature_importances_
            }).sort_values('Importancia', ascending=False).head(10)
            fig_imp = px.bar(feat_imp, x='Importancia', y='Feature', orientation='h',
                            title='Top 10 Variables Importantes', color='Importancia',
                            color_continuous_scale='Viridis')
            fig_imp.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_imp, use_container_width=True)
    
    with tab2:
        st.markdown("### 🔮 Predicción en Tiempo Real")
        st.info("💡 Ingresa solo las **6 variables más importantes**. Las demás se calculan automáticamente con la media del dataset.")
        
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
            # Construir fila completa con medias para variables no ingresadas
            means = df.drop(columns=['ID', 'default payment next month']).mean()
            new_row = means.copy()
            new_row['LIMIT_BAL'] = limit_bal
            new_row['AGE'] = age
            new_row['PAY_0'] = pay_0
            new_row['PAY_2'] = pay_2
            new_row['BILL_AMT1'] = bill_amt1
            new_row['PAY_AMT1'] = pay_amt1
            
            X_new = models['rf_scaler'].transform(new_row.values.reshape(1, -1))
            pred = models['rf'].predict(X_new)[0]
            proba = models['rf'].predict_proba(X_new)[0]
            
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

# ============ K-MEANS ============
elif modelo == "K-Means (Clustering)":
    tab1, tab2 = st.tabs(["📊 Perfil de Clusters", "🔮 Clasificar Cliente"])
    
    X = df.drop(columns=['ID', 'default payment next month'])
    X_scaled = models['km_scaler'].transform(X)
    df['Cluster'] = models['kmeans'].predict(X_scaled)
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("🔢 Clusters", models['kmeans'].n_clusters)
        c2.metric("👥 Clientes", f"{len(df):,}")
        c3.metric("📏 Silueta", f"{0.1853:.3f}")
        
        st.subheader("📊 Segmentación 2D (PCA)")
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        pca_df = pd.DataFrame({
            'PC1': X_pca[:, 0], 'PC2': X_pca[:, 1],
            'Cluster': df['Cluster'].astype(str),
            'Default': df['default payment next month'].map({0: 'No', 1: 'Sí'})
        })
        fig = px.scatter(pca_df, x='PC1', y='PC2', color='Cluster', symbol='Default',
                        title='Clientes por Cluster', opacity=0.7,
                        color_discrete_sequence=['#00d4ff', '#7b2cbf', '#ff7f0e'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📈 Tasa de Default por Cluster")
        profile = df.groupby('Cluster').agg({
            'LIMIT_BAL': 'mean', 'AGE': 'mean',
            'default payment next month': 'mean'
        }).reset_index()
        profile['Tasa_Default_%'] = profile['default payment next month'] * 100
        
        fig2 = px.bar(profile, x='Cluster', y='Tasa_Default_%', color='Cluster',
                     title='Riesgo por Segmento', color_discrete_sequence=['#00d4ff', '#7b2cbf', '#ff7f0e'])
        st.plotly_chart(fig2, use_container_width=True)
        
        st.dataframe(profile.round(2), use_container_width=True)
    
    with tab2:
        st.markdown("### 🔮 Asignar Cluster a Nuevo Cliente")
        c1, c2 = st.columns(2)
        with c1:
            limit_bal = st.number_input("💰 Límite de Crédito", 10000, 1000000, 150000, step=10000)
            age = st.slider("📅 Edad", 18, 80, 30)
            pay_0 = st.slider("📊 Estado Pago Actual", -2, 8, 0)
        with c2:
            bill_amt1 = st.number_input("💵 Factura Mes 1", 0, 1000000, 50000, step=1000)
            pay_amt1 = st.number_input("💳 Pago Realizado", 0, 1000000, 5000, step=500)
            sex = st.selectbox("👤 Sexo", [1, 2], format_func=lambda x: "Masculino" if x==1 else "Femenino")
        
        if st.button("🎯 Clasificar", type="primary", use_container_width=True):
            means = df.drop(columns=['ID', 'default payment next month', 'Cluster']).mean()
            new_row = means.copy()
            new_row['LIMIT_BAL'] = limit_bal
            new_row['AGE'] = age
            new_row['PAY_0'] = pay_0
            new_row['BILL_AMT1'] = bill_amt1
            new_row['PAY_AMT1'] = pay_amt1
            new_row['SEX'] = sex
            
            X_new = models['km_scaler'].transform(new_row.values.reshape(1, -1))
            cluster = models['kmeans'].predict(X_new)[0]
            
            info = df[df['Cluster'] == cluster]
            st.success(f"✅ Cliente asignado al **Cluster {cluster}**")
            st.markdown(f"""
            <div class="pred-card">
            <b>📊 Perfil del Cluster {cluster}:</b><br>
            • Clientes: <b>{len(info):,}</b><br>
            • Tasa de default: <b>{info['default payment next month'].mean()*100:.1f}%</b><br>
            • Límite promedio: <b>${info['LIMIT_BAL'].mean():,.0f}</b><br>
            • Edad promedio: <b>{info['AGE'].mean():.1f} años</b>
            </div>
            """, unsafe_allow_html=True)

# ============ MONGODB ============
else:
    st.markdown("### 📜 Historial de Experimentos ML (MongoDB)")
    try:
        client = get_mongo_connection()
        db = client["ML_Experiments"]
        collection = db["registro_experimentos"]
        
        docs = list(collection.find().sort("fecha", -1).limit(20))
        
        if docs:
            st.success(f"✅ {collection.count_documents({})} experimentos registrados")
            
            for doc in docs:
                with st.expander(f"🧪 {doc.get('algoritmo', 'N/A')} · {doc.get('fecha', 'N/A')[:19]}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**🔧 Hiperparámetros:**")
                        st.json(doc.get('hiperparametros', {}))
                    with c2:
                        st.markdown("**📈 Métricas:**")
                        st.json(doc.get('metricas', {}))
        else:
            st.info("ℹ️ No hay experimentos registrados aún.")
        
        client.close()
    except Exception as e:
        st.error(f"❌ Error MongoDB: {str(e)}")