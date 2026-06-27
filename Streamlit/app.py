import streamlit as st
from pathlib import Path
import sys

# Agregar la raíz al path para importar módulos
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from Streamlit.pages.tab_dataset import show_dataset_tab
from Streamlit.pages.tab_modelo import show_modelo_tab
from Streamlit.pages.tab_admin_db import show_admin_db_tab

st.set_page_config(page_title="Dashboard Analítico - Impagos", layout="wide", page_icon="💳")

st.title("💳 Infraestructura Híbrida y ML para Predicción de Impagos")
st.markdown("### Dashboard Académico de Analítica Predictiva | *UCI Default of Credit Card Clients*")

tab1, tab2, tab3 = st.tabs([
    "📊 Dataset & Arquitectura Relacional", 
    "🤖 Modelo ML & Predicciones", 
    "🛠️ Administración de Base de Datos"
])

with tab1:
    show_dataset_tab(ROOT_DIR)
with tab2:
    show_modelo_tab(ROOT_DIR)
with tab3:
    show_admin_db_tab()