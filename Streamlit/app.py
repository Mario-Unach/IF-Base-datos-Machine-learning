import streamlit as st
from pathlib import Path
import sys

# Agregar la raíz al path para importar módulos
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from Streamlit.pages.tab_dataset import show_dataset_tab
from Streamlit.pages.tab_modelo import show_modelo_tab
from Streamlit.pages.tab_admin_db import show_admin_db_tab

# Configuración de página mejorada
st.set_page_config(
    page_title="Dashboard Predictivo - Impagos", 
    layout="wide", 
    page_icon="💳",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar el diseño
st.markdown("""
<style>
    /* Mejorar el header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    /* Mejorar tarjetas de métricas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    /* Tabs más visibles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header principal mejorado
st.markdown('<p class="main-header">💳 Sistema Predictivo de Impagos</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Dashboard Académico de Analítica Predictiva | UCI Default of Credit Card Clients</p>', unsafe_allow_html=True)

# Sidebar con información adicional
with st.sidebar:
    st.image("https://img.icons8.com/color/96/credit-card.png", width=80)
    st.markdown("### 🎯 Navegación")
    st.info("Utiliza las pestañas superiores para navegar entre las diferentes funcionalidades del sistema.")
    
    st.divider()
    st.markdown("### 📋 Características")
    st.markdown("""
    - 📊 **Dataset**: Exploración de datos desde SQL Server
    - 🤖 **Modelo ML**: Predicciones en tiempo real con XGBoost
    - 🛠️ **Admin DB**: Gestión, auditoría y backups
    """)
    
    st.divider()
    st.markdown("### 🔗 Conexiones Activas")
    st.caption("✅ SQL Server (Docker)")
    st.caption("✅ MongoDB (Logs de predicciones)")

# Pestañas principales con iconos mejorados
tab1, tab2, tab3 = st.tabs([
    "📊 Dataset & Arquitectura", 
    "🤖 Modelo ML & Predicciones", 
    "🛠️ Administración BD"
])

with tab1:
    show_dataset_tab(ROOT_DIR)
    
with tab2:
    show_modelo_tab(ROOT_DIR)
    
with tab3:
    show_admin_db_tab()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Dashboard desarrollado para proyecto académico de Machine Learning | 
    Arquitectura Híbrida SQL Server + MongoDB</small>
</div>
""", unsafe_allow_html=True)