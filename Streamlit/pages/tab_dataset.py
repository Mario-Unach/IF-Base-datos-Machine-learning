import streamlit as st
import pandas as pd
import plotly.express as px
from Streamlit.db_connections import get_sql_connection, load_dataset_from_sql, load_dataset_detallado

def show_dataset_tab(ROOT_DIR):
    # CSS personalizado para esta pestaña
    st.markdown("""
    <style>
    .data-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stat-box {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("📊 Exploración de Datos & Arquitectura")
    st.markdown("### Análisis Exploratorio (EDA) desde SQL Server")
    
    # Badge de conexión en vivo
    st.info("🔌 **Conexión EN VIVO**: Todos los datos se leen directamente desde la vista `vw_ml_dataset` en SQL Server (Docker)")
    
    # Cargar dataset directamente desde la BD
    with st.spinner("⏳ Conectando a SQL Server y ejecutando consulta..."):
        df = load_dataset_from_sql()
    
    if df is None:
        st.error("❌ No se pudo cargar el dataset. Verifica que el contenedor Docker esté corriendo.")
        st.stop()
    
    # Mostrar estadísticas clave en columnas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Clientes", f"{df.shape[0]:,}")
    with col2:
        st.metric("📋 Variables", df.shape[1])
    with col3:
        default_count = (df['default payment next month'] == 1).sum()
        st.metric("⚠️ Defaults", f"{default_count:,}")
    with col4:
        default_rate = (df['default payment next month'] == 1).mean() * 100
        st.metric("📈 Tasa Default", f"{default_rate:.2f}%")
    
    st.divider()
    
    # ----- EDA con Plotly -----
    st.subheader("📈 Visualizaciones Interactivas")
    
    tab_viz1, tab_viz2, tab_viz3 = st.tabs(["Distribución", "Correlaciones", "Por Edad"])
    
    with tab_viz1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Distribución de Variable Objetivo**")
            fig_pie = px.pie(
                df, 
                names='default payment next month', 
                title='Proporción de Defaults vs No Defaults',
                color_discrete_sequence=px.colors.sequential.RdBu,
                hole=0.4
            )
            fig_pie.update_traces(labels=['No Default (0)', 'Default (1)'])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.markdown("**Distribución de Límite de Crédito**")
            fig_hist = px.histogram(
                df, 
                x='LIMIT_BAL', 
                nbins=50,
                title='Distribución de Límites de Crédito',
                color_discrete_sequence=['#636EFA']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab_viz2:
        st.markdown("**Matriz de Correlaciones (Heatmap)**")
        # Seleccionar columnas numéricas principales
        corr_cols = ['LIMIT_BAL', 'AGE', 'PAY_0', 'BILL_AMT1', 'PAY_AMT1', 'default payment next month']
        corr_df = df[corr_cols].copy()
        corr_matrix = corr_df.corr()
        
        fig_heatmap = px.imshow(
            corr_matrix,
            labels=dict(color="Correlación"),
            title='Matriz de Correlaciones',
            color_continuous_scale='RdBu_r',
            aspect='auto'
        )
        fig_heatmap.update_layout(height=500)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab_viz3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Edad vs Probabilidad de Impago**")
            fig_age = px.histogram(
                df, 
                x='AGE', 
                color='default payment next month',
                barmode='overlay',
                title='Distribución por Edad',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                nbins=30
            )
            fig_age.update_traces(name='No Default', selector=dict(name=0))
            fig_age.update_traces(name='Default', selector=dict(name=1))
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            st.markdown("**Límite de Crédito por Edad**")
            fig_scatter = px.scatter(
                df.sample(1000),  # Muestreo para mejor rendimiento
                x='AGE',
                y='LIMIT_BAL',
                color='default payment next month',
                title='Límite de Crédito vs Edad (Sample: 1000)',
                color_continuous_scale='Reds',
                opacity=0.6
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.divider()
    
    # ----- Explorador Interactivo de la BD -----
    st.subheader("🗄️ Explorador de Base de Datos Relacional")
    
    col_select, col_info = st.columns([3, 1])
    with col_select:
        vista_seleccionada = st.selectbox(
            "Selecciona la vista de SQL Server a consultar:",
            ["vw_ml_dataset (Plano para ML)", "vw_cliente_detallado (Con descripciones)"]
        )
    
    if "detallado" in vista_seleccionada:
        df_view = load_dataset_detallado()
        st.caption("📝 Vista con descripciones textuales de las variables categóricas")
    else:
        df_view = df
        st.caption("📊 Vista plana optimizada para Machine Learning")
    
    if df_view is not None:
        # Filtros opcionales dentro del expander
        df_filtered = df_view  # Por defecto sin filtros
        
        with st.expander("🔍 Aplicar Filtros"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                age_filter = st.slider("Filtrar por Edad", int(df['AGE'].min()), int(df['AGE'].max()), (21, 79))
            with col_f2:
                limit_filter = st.slider("Filtrar por Límite de Crédito", int(df['LIMIT_BAL'].min()), int(df['LIMIT_BAL'].max()), (int(df['LIMIT_BAL'].min()), int(df['LIMIT_BAL'].max())))
            
            df_filtered = df_view[(df_view['AGE'] >= age_filter[0]) & (df_view['AGE'] <= age_filter[1])]
            if 'LIMIT_BAL' in df_filtered.columns:
                df_filtered = df_filtered[(df_filtered['LIMIT_BAL'] >= limit_filter[0]) & (df_filtered['LIMIT_BAL'] <= limit_filter[1])]
        
        # Mostrar dataframe
        st.dataframe(
            df_filtered.head(100), 
            use_container_width=True, 
            hide_index=True,
            height=400
        )
        st.caption(f"📄 Mostrando primeros 100 registros de un total de {len(df_filtered):,} registros")
        
        # Botón de descarga
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Dataset Completo (CSV)",
            data=csv,
            file_name='dataset_creditos.csv',
            mime='text/csv',
        )
    
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
            st.dataframe(schema_df, use_container_width=True, hide_index=True, height=300)
        except Exception as e:
            st.warning(f"No se pudo leer el esquema: {e}")
