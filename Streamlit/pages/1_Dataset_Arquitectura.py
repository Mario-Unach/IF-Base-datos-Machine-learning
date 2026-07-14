import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
from sqlalchemy import create_engine, text
from db_connections import get_sql_connection

# 1. Agregar la carpeta raíz (Streamlit/) al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 2. Importar el módulo de autenticación
import auth

# 3. Inicializar y proteger la página
auth.init_session_state()
auth.require_role(["Administrador", "Analista"]) # Roles permitidos

st.set_page_config(page_title="Dataset & Arquitectura", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.page-header { font-size: 2.6rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">📊 Dataset & Arquitectura</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"`{st.session_state.login_user}`")
    st.divider()
    auth.render_role_menu()
    st.divider()
    

tab1, tab2, tab3, tab4 = st.tabs([
    "🗄️ Explorador", "🏗️ Modelo ER", "📈 Análisis", "🔍 SQL"
])

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    with tab1:
        tabla = st.selectbox("Tabla / Vista:", [
            "dim_cliente", "dim_sexo", "dim_educacion", "dim_estado_civil",
            "historial_pagos", "riesgo_crediticio", "vw_ml_dataset", "vw_cliente_detallado"
        ])
        top_n = st.slider("Registros:", 10, 500, 50)
        
        df = pd.read_sql(text(f"SELECT TOP {top_n} * FROM {tabla}"), engine)
        st.success(f"✅ {len(df)} registros")
        st.dataframe(df, use_container_width=True, height=400)
        
        with st.expander("📊 Estadísticas"):
            st.write(df.describe())
    
    with tab2:
        st.subheader("🏗️ Modelo Entidad-Relación Normalizado")
        er_image = Path(__file__).resolve().parents[2] / "Anexos" / "Entidad - Relacion.jpeg"
        if er_image.exists():
            st.image(str(er_image), use_container_width=True)
        else:
            st.warning(f"⚠️ Imagen no encontrada en: {er_image}")
        
        st.divider()
        st.subheader("📋 Tablas del Sistema")
        tablas = pd.read_sql(text("""
            SELECT TABLE_NAME, TABLE_TYPE 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME
        """), engine)
        st.dataframe(tablas, use_container_width=True)
    
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            df_hist = pd.read_sql(text("SELECT limite_credito FROM dim_cliente"), engine)
            fig1 = px.histogram(df_hist, x='limite_credito', nbins=50,
                               title='💰 Distribución Límite Crédito',
                               color_discrete_sequence=['#00d4ff'])
            fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font=dict(color='#e2e8f0'))
            st.plotly_chart(fig1, use_container_width=True)
        
        with c2:
            df_box = pd.read_sql(text("""
                SELECT s.descripcion_sexo, c.edad
                FROM dim_cliente c INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
            """), engine)
            fig2 = px.box(df_box, x='descripcion_sexo', y='edad',
                         title='📊 Edad por Género', color='descripcion_sexo',
                         color_discrete_map={'Masculino': '#00d4ff', 'Femenino': '#7b2cbf'})
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font=dict(color='#e2e8f0'))
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab4:
        consultas = {
            "Top 10 mayor límite": """
                SELECT TOP 10 c.id_cliente, e.nivel_educativo, c.edad, c.limite_credito, r.incumplimiento_proximo_mes
                FROM dim_cliente c
                INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
                INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
                ORDER BY c.limite_credito DESC
            """,
            "Default por educación": """
                SELECT e.nivel_educativo, COUNT(*) as total,
                    SUM(CAST(r.incumplimiento_proximo_mes AS INT)) as defaults,
                    SUM(CAST(r.incumplimiento_proximo_mes AS FLOAT)) * 100.0 / COUNT(*) as pct
                FROM dim_cliente c
                INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
                INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
                GROUP BY e.nivel_educativo
            """
        }
        
        sel = st.selectbox("Consulta:", list(consultas.keys()))
        if st.button("▶️ Ejecutar", type="primary"):
            df_r = pd.read_sql(text(consultas[sel]), engine)
            st.dataframe(df_r, use_container_width=True)
        
        with st.expander("⌨️ SQL Personalizado"):
            sql = st.text_area("Query:", height=120, placeholder="SELECT TOP 100 * FROM vw_ml_dataset...")
            if st.button("🚀 Ejecutar"):
                if sql.strip():
                    df_c = pd.read_sql(text(sql), engine)
                    st.dataframe(df_c, use_container_width=True)
    
    conn.close()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")