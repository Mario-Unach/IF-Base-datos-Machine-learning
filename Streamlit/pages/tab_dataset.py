import streamlit as st
import pandas as pd
import plotly.express as px
from Streamlit.db_connections import get_sql_connection

def show_dataset_tab(ROOT_DIR):
    st.header("Análisis Exploratorio (EDA) y Esquema Relacional")
    
    # Cargar dataset local para EDA
    df = pd.read_csv(ROOT_DIR / "Dataset" / "dataset_impagos_limpio.csv")
    
    # Nombres reales de las columnas en tu CSV limpio
    target_col = 'Incumplimiento'
    age_col = 'Edad'
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución de Variable Objetivo")
        fig = px.pie(df, names=target_col, title='Proporción de Defaults',
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Edad vs Probabilidad de Impago")
        fig = px.histogram(df, x=age_col, color=target_col, barmode='overlay',
                           title='Distribución por Edad', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🗄️ Esquema de Base de Datos Relacional (SQL Server)")
    st.info("Consulta interactiva a `INFORMATION_SCHEMA` para validar la normalización (3FN) y diccionario de datos.")
    
    conn = get_sql_connection()
    if conn:
        query = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """
        try:
            schema_df = pd.read_sql(query, conn)
            st.dataframe(schema_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"No se pudo leer el esquema: {e}")