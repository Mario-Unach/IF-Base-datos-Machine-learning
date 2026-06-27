import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from sqlalchemy import create_engine, text

# Agregar el directorio actual al path para importar db_connections
sys.path.insert(0, str(Path(__file__).parent))
from db_connections import get_sql_connection, get_mongo_connection

# Configuración de página
st.set_page_config(
    page_title="CreditFlow Analytics", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Tema oscuro profesional
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%);
    }
    
    /* Headers */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        padding: 2rem 0;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
    }
    
    .sub-header {
        font-size: 1.4rem;
        color: #a0aec0;
        text-align: center;
        margin-bottom: 2.5rem;
        font-weight: 300;
    }
    
    /* Tarjetas de métricas */
    .metric-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        padding: 1.8rem;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d4ff !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #94a3b8;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #1a202e 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    /* Contenedores */
    .info-box {
        background: rgba(30, 41, 59, 0.8);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #00d4ff;
        margin: 1rem 0;
    }
    
    /* Texto general */
    .stMarkdown, .stDataFrame, .stTable {
        color: #e2e8f0;
    }
    
    /* Títulos de sección */
    h1, h2, h3, h4 {
        color: #f1f5f9 !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(148, 163, 184, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header principal con logo SVG embebido
logo_svg = """
<svg width="80" height="80" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7b2cbf;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="45" fill="url(#grad1)" opacity="0.2"/>
  <path d="M30 50 L45 65 L70 35" stroke="url(#grad1)" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="30" cy="50" r="4" fill="#00d4ff"/>
  <circle cx="45" cy="65" r="4" fill="#00d4ff"/>
  <circle cx="70" cy="35" r="4" fill="#7b2cbf"/>
</svg>
"""

col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown(logo_svg, unsafe_allow_html=True)
with col_title:
    st.markdown('<p class="main-header">CreditFlow Analytics</p>', unsafe_allow_html=True)

st.markdown('<p class="sub-header">Sistema Predictivo de Riesgo Crediticio | Arquitectura Híbrida SQL Server + MongoDB</p>', unsafe_allow_html=True)

# Sidebar simplificado
with st.sidebar:
    st.markdown("### 🎯 Navegación")
    st.markdown("---")
    
    st.markdown("""
    - **📊 Dashboard**: Vista general del proyecto
    - **📑 Dataset & Arquitectura**: Exploración de datos y modelo ER
    - **🤖 Modelo ML & Predicciones**: Interfaz predictiva en tiempo real
    - **🛠️ Administración BD**: Gestión de usuarios, auditoría y backups
    """)
    
    st.markdown("---")
    st.markdown("### ℹ️ Acerca del Proyecto")
    
    with st.expander("Ver detalles", expanded=False):
        st.markdown("""
        **Objetivo:** Diseñar e implementar una solución analítica integral que combine arquitectura híbrida con modelos ML.
        
        **Tecnologías:** SQL Server | MongoDB | XGBoost | Streamlit
        """)

# Contenido principal - Dashboard general
st.markdown("---")

# KPIs principales en columnas
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    query_kpis = text("""
        SELECT 
            COUNT(DISTINCT c.id_cliente) AS total_clientes,
            AVG(c.limite_credito) AS avg_limite_credito,
            AVG(c.edad) AS avg_edad,
            SUM(CAST(r.incumplimiento_proximo_mes AS INT)) * 100.0 / COUNT(*) AS tasa_incumplimiento
        FROM dim_cliente c
        INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
    """)
    df_kpis = pd.read_sql(query_kpis, engine)
    
    with col_kpi1:
        st.metric("👥 Total Clientes", f"{int(df_kpis['total_clientes'][0]):,}")
    with col_kpi2:
        st.metric("💰 Límite Promedio", f"${df_kpis['avg_limite_credito'][0]:,.2f}")
    with col_kpi3:
        st.metric("📅 Edad Promedio", f"{df_kpis['avg_edad'][0]:.1f} años")
    with col_kpi4:
        st.metric("⚠️ Tasa Incumplimiento", f"{df_kpis['tasa_incumplimiento'][0]:.2f}%")
    
    conn.close()
except Exception as e:
    st.error(f"Error al cargar KPIs: {str(e)}")

st.markdown("---")

# Gráficos principales
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    try:
        conn = get_sql_connection()
        engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
        
        # Distribución por educación
        query_edu = text("""
            SELECT e.nivel_educativo, COUNT(*) as cantidad
            FROM dim_cliente c
            INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
            GROUP BY e.nivel_educativo
            ORDER BY cantidad DESC
        """)
        df_edu = pd.read_sql(query_edu, engine)
        
        fig_pie = px.pie(df_edu, values='cantidad', names='nivel_educativo', 
                         title='📚 Distribución por Nivel Educativo',
                         color_discrete_sequence=['#00d4ff', '#7b2cbf', '#2ca02c', '#ff7f0e', '#e377c2'])
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', size=12),
            title_font=dict(color='#00d4ff', size=16)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar gráfico educativo: {str(e)}")

with col_graf2:
    try:
        conn = get_sql_connection()
        engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
        
        # Distribución por estado civil
        query_civil = text("""
            SELECT ec.descripcion_estado_civil, COUNT(*) as cantidad
            FROM dim_cliente c
            INNER JOIN dim_estado_civil ec ON c.id_estado_civil = ec.id_estado_civil
            GROUP BY ec.descripcion_estado_civil
        """)
        df_civil = pd.read_sql(query_civil, engine)
        
        fig_bar = px.bar(df_civil, x='descripcion_estado_civil', y='cantidad',
                         title='💍 Distribución por Estado Civil',
                         color='cantidad',
                         color_continuous_scale=['#00d4ff', '#7b2cbf'])
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', size=12),
            title_font=dict(color='#00d4ff', size=16),
            xaxis=dict(title="Estado Civil", tickfont=dict(color='#94a3b8')),
            yaxis=dict(title="Cantidad", tickfont=dict(color='#94a3b8'))
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar gráfico estado civil: {str(e)}")

# Footer simplificado
st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b; padding: 1rem;'><small>CreditFlow Analytics © 2025 | Arquitectura Híbrida SQL Server + MongoDB</small></div>", unsafe_allow_html=True)
