import streamlit as st
import pandas as pd
import plotly.express as px
from Streamlit.db_connections import get_sql_connection, load_dataset_from_sql, load_dataset_detallado

def show_dataset_tab(ROOT_DIR):
    st.header("📊 Análisis Exploratorio (EDA) desde SQL Server")
    st.info("🔌 **Todos los datos se leen EN VIVO desde la vista `vw_ml_dataset` en SQL Server (Docker).**")
    
    # Cargar dataset directamente desde la BD
    with st.spinner("Conectando a SQL Server y ejecutando consulta..."):
        df = load_dataset_from_sql()
    
    if df is None:
        st.error("No se pudo cargar el dataset. Verifica que el contenedor Docker esté corriendo.")
        st.stop()
    
    st.success(f"✅ Dataset cargado: **{df.shape[0]:,}** clientes | **{df.shape[1]}** variables")
    
    # ----- EDA con Plotly -----
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución de Variable Objetivo")
        fig = px.pie(df, names='default payment next month', title='Proporción de Defaults',
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Edad vs Probabilidad de Impago")
        fig = px.histogram(df, x='AGE', color='default payment next month', barmode='overlay',
                           title='Distribución por Edad', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # ----- Explorador Interactivo de la BD -----
    st.subheader("🗄️ Explorador Interactivo de Base de Datos Relacional")
    
    vista_seleccionada = st.selectbox(
        "Selecciona la vista de SQL Server a consultar:",
        ["vw_ml_dataset (Plano para ML)", "vw_cliente_detallado (Con descripciones)"]
    )
    
    if "detallado" in vista_seleccionada:
        df_view = load_dataset_detallado()
    else:
        df_view = df
    
    if df_view is not None:
        st.dataframe(df_view.head(100), use_container_width=True, hide_index=True)
        st.caption(f"Mostrando primeros 100 registros de un total de {len(df_view):,}")
        
    # ----- Esquema de la BD (INFORMATION_SCHEMA) -----
    st.divider()
    st.subheader("📐 Esquema Relacional (3FN) - Catálogo de Tablas")
    
    conn = get_sql_connection()
    if conn:
        query = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_CATALOG = 'CC_Client'
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """
        try:
            schema_df = pd.read_sql(query, conn)
            st.dataframe(schema_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"No se pudo leer el esquema: {e}")