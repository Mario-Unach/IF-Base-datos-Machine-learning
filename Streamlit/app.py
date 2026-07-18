import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
from db_connections import get_sql_connection
import auth as auth_module

auth_module.init_session_state()

st.set_page_config(
    page_title="CreditFlow Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.main-header { font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
-webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1rem 0; }
.sub-header { font-size: 1.2rem; color: #a0aec0; text-align: center; margin-bottom: 2rem; }
[data-testid="stMetricValue"] { font-size: 2.2rem; color: #00d4ff !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: #94a3b8; font-weight: 500; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header"> CreditFlow Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Sistema Predictivo de Riesgo Crediticio · SQL Server + MongoDB</p>', unsafe_allow_html=True)

# ==========================================
# LOGIN
# ==========================================
if not st.session_state.authenticated:
    auth_module.login_panel()
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"Usuario: `{st.session_state.login_user}`")
    st.divider()
    
    auth_module.logout_button()

# ==========================================
# CONTENIDO DEL DASHBOARD (app.py es el dashboard)
# ==========================================
try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    df_kpis = pd.read_sql(text("""
        SELECT 
            COUNT(DISTINCT c.id_cliente) AS total,
            AVG(c.limite_credito) AS avg_limite,
            AVG(c.edad) AS avg_edad,
            SUM(CAST(r.incumplimiento_proximo_mes AS INT)) * 100.0 / COUNT(*) AS tasa
        FROM dim_cliente c
        INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
    """), engine)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Clientes", f"{int(df_kpis['total'][0]):,}")
    c2.metric("💰 Límite Promedio", f"${df_kpis['avg_limite'][0]:,.0f}")
    c3.metric("📅 Edad Promedio", f"{df_kpis['avg_edad'][0]:.1f}")
    c4.metric("⚠️ Tasa Default", f"{df_kpis['tasa'][0]:.2f}%")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        df_edu = pd.read_sql(text("""
            SELECT e.nivel_educativo, COUNT(*) as cantidad
            FROM dim_cliente c INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
            GROUP BY e.nivel_educativo
        """), engine)
        fig1 = px.pie(df_edu, values='cantidad', names='nivel_educativo',
                     title='📚 Distribución Educativa',
                     color_discrete_sequence=['#00d4ff', '#7b2cbf', '#2ca02c', '#ff7f0e'])
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='#e2e8f0'), title_font=dict(color='#00d4ff'))
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        df_civil = pd.read_sql(text("""
            SELECT ec.descripcion_estado_civil, COUNT(*) as cantidad
            FROM dim_cliente c INNER JOIN dim_estado_civil ec ON c.id_estado_civil = ec.id_estado_civil
            GROUP BY ec.descripcion_estado_civil
        """), engine)
        fig2 = px.bar(df_civil, x='descripcion_estado_civil', y='cantidad',
                     title='💍 Estado Civil', color='cantidad',
                     color_continuous_scale=['#00d4ff', '#7b2cbf'])
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='#e2e8f0'), title_font=dict(color='#00d4ff'))
        st.plotly_chart(fig2, use_container_width=True)
    
    conn.close()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")