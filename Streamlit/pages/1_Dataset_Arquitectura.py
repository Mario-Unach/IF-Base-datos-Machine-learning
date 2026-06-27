import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Agregar el directorio Streamlit al path para importar db_connections
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connections import get_sql_connection

# Configuración de página específica para esta page
st.set_page_config(
    page_title="Dataset & Arquitectura",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado - Tema oscuro consistente
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%);
    }
    
    /* Header de página */
    .page-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 8px;
        padding: 8px 16px;
        color: #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(123, 44, 191, 0.2));
        border: 1px solid rgba(0, 212, 255, 0.3);
        color: #00d4ff;
    }
    
    /* Info boxes */
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
    
    h1, h2, h3, h4 {
        color: #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">📊 Dataset & Arquitectura de Datos</p>', unsafe_allow_html=True)

# Pestañas para organizar la información
tab1, tab2, tab3, tab4 = st.tabs([
    "🗄️ Explorador de Datos",
    "🏗️ Modelo Entidad-Relación",
    "📈 Visualizaciones Avanzadas",
    "🔍 Consultas SQL"
])

with tab1:
    st.markdown("### 🔍 Explorador de Tablas")
    
    # Selector de tabla
    tablas_disponibles = [
        "dim_cliente",
        "dim_sexo",
        "dim_educacion",
        "dim_estado_civil",
        "historial_pagos",
        "riesgo_crediticio",
        "auditoria_cambios",
        "vw_ml_dataset",
        "vw_cliente_detallado"
    ]
    
    tabla_seleccionada = st.selectbox("Selecciona una tabla o vista:", tablas_disponibles)
    
    col_filtros1, col_filtros2 = st.columns(2)
    
    with col_filtros1:
        top_n = st.slider("Cantidad de registros a mostrar:", 5, 100, 10)
    
    with col_filtros2:
        if st.button("🔄 Cargar Datos"):
            st.session_state.cargar_datos = True
    
    try:
        conn = get_sql_connection()
        engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
        query = text(f"SELECT TOP {top_n} * FROM {tabla_seleccionada}")
        df = pd.read_sql(query, engine)
        
        st.success(f"✅ {len(df)} registros cargados exitosamente")
        
        # Mostrar datos con formato
        st.dataframe(
            df.style.format(precision=2).background_gradient(cmap="Blues", subset=df.select_dtypes(include=['float', 'int']).columns),
            use_container_width=True,
            height=400
        )
        
        # Estadísticas descriptivas en expander
        with st.expander("📊 Ver Estadísticas Descriptivas"):
            if not df.empty:
                st.write(df.describe())
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")

with tab2:
    st.markdown("### 🏗️ Modelo Entidad-Relación Normalizado")
    
    # Diagrama ER usando Mermaid
    er_diagram = """
erDiagram
    dim_estado_civil {
        int id_estado_civil PK
        varchar descripcion_estado_civil
    }

    dim_sexo {
        int id_sexo PK
        varchar descripcion_sexo
    }

    dim_educacion {
        int id_educacion PK
        varchar nivel_educativo
    }

    dim_cliente {
        int id_cliente PK
        int id_sexo FK
        int id_educacion FK
        int id_estado_civil FK
        int edad
        float limite_credito
    }

    riesgo_crediticio {
        int id_cliente PK,FK
        int incumplimiento_proximo_mes
    }

    dim_estatus_pago {
        int id_estatus PK
        varchar descripcion_estatus
    }

    dim_tiempo_mes {
        int id_mes PK
        varchar mes_referencia
        int orden_historial
    }

    historial_pagos {
        int id_historial PK
        int id_cliente FK
        int id_mes FK
        int id_estatus_pago FK
        float monto_estado_cuenta
        float monto_pago_anterior
    }

    dim_estado_civil ||--o{ dim_cliente : "tiene"
    dim_sexo ||--o{ dim_cliente : "tiene"
    dim_educacion ||--o{ dim_cliente : "tiene"
    dim_cliente ||--o| riesgo_crediticio : "posee"
    dim_cliente ||--o{ historial_pagos : "realiza"
    dim_estatus_pago ||--o{ historial_pagos : "clasifica"
    dim_tiempo_mes ||--o{ historial_pagos : "registra"
    \"\"\"
    
    # Renderizar diagrama Mermaid correctamente
    st.markdown(f'''
    <div style="background: rgba(30, 41, 59, 0.4); padding: 20px; border-radius: 10px; border: 1px solid rgba(0, 212, 255, 0.2);">
    ```mermaid
    {er_diagram.strip()}
    ```
    </div>
    ''', unsafe_allow_html=True)

with tab3:
    st.markdown("### 📈 Visualizaciones Avanzadas del Dataset")
    
    try:
        conn = get_sql_connection()
        engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
        
        st.divider()
        
        # Gráficos en dos filas
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            # Distribución de límites de crédito
            query_hist = text("SELECT limite_credito FROM dim_cliente")
            df_hist = pd.read_sql(query_hist, engine)
            
            fig_hist = px.histogram(df_hist, x='limite_credito', nbins=50,
                                    title='💰 Distribución de Límites de Crédito',
                                    labels={'limite_credito': 'Límite de Crédito ($)'},
                                    color_discrete_sequence=['#1f77b4'])
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with row1_col2:
            # Distribución por educación y estado civil
            query_pie = text("""
                SELECT e.nivel_educativo, COUNT(*) as cantidad
                FROM dim_cliente c
                INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
                GROUP BY e.nivel_educativo
                ORDER BY cantidad DESC
            """)
            df_pie = pd.read_sql(query_pie, engine)
            
            fig_pie = px.pie(df_pie, values='cantidad', names='nivel_educativo',
                             title='📚 Nivel Educativo',
                             color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            # Análisis de edad por género
            query_box = text("""
                SELECT s.descripcion_sexo, c.edad
                FROM dim_cliente c
                INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
            """)
            df_box = pd.read_sql(query_box, engine)
            
            fig_box = px.box(df_box, x='descripcion_sexo', y='edad',
                             title='📊 Distribución de Edad por Género',
                             color='descripcion_sexo',
                             color_discrete_map={'Masculino': '#1f77b4', 'Femenino': '#ff7f0e'})
            st.plotly_chart(fig_box, use_container_width=True)
        
        with row2_col2:
            # Heatmap de correlación (datos numéricos)
            query_corr = text("""
                SELECT TOP 1000
                    c.limite_credito,
                    c.edad,
                    r.incumplimiento_proximo_mes
                FROM dim_cliente c
                INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
            """)
            df_corr = pd.read_sql(query_corr, engine)
            
            corr_matrix = df_corr.corr()
            
            fig_heatmap = px.imshow(corr_matrix, 
                                    title='🔥 Matriz de Correlación',
                                    color_continuous_scale='RdBu_r',
                                    text_auto='.2f')
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Error al cargar visualizaciones: {str(e)}")

with tab4:
    st.markdown("### 🔍 Consultas SQL Predefinidas")
    
    st.info("💡 Ejecuta consultas predefinidas para explorar los datos")
    
    consultas = {
        "Top 10 clientes con mayor límite de crédito": """
            SELECT TOP 10 
                c.id_cliente,
                s.descripcion_sexo,
                e.nivel_educativo,
                c.edad,
                c.limite_credito,
                r.incumplimiento_proximo_mes
            FROM dim_cliente c
            INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
            INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
            INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
            ORDER BY c.limite_credito DESC
        """,
        
        "Distribución de impagos por nivel educativo": """
            SELECT 
                e.nivel_educativo,
                COUNT(*) as total_clientes,
                SUM(r.incumplimiento_proximo_mes) as impagos,
                SUM(r.incumplimiento_proximo_mes) * 100.0 / COUNT(*) as porcentaje_impago
            FROM dim_cliente c
            INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
            INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
            GROUP BY e.nivel_educativo
            ORDER BY porcentaje_impago DESC
        """,
        
        "Estadísticas de auditoría": """
            SELECT 
                tabla_afectada,
                operacion,
                COUNT(*) as cantidad,
                MAX(fecha_cambio) as ultimo_cambio
            FROM auditoria_cambios
            GROUP BY tabla_afectada, operacion
            ORDER BY cantidad DESC
        """
    }
    
    consulta_seleccionada = st.selectbox("Selecciona una consulta:", list(consultas.keys()))
    
    if st.button("▶️ Ejecutar Consulta"):
        try:
            conn = get_sql_connection()
            engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
            query = text(consultas[consulta_seleccionada])
            
            # Mostrar la consulta SQL en expander
            with st.expander("📜 Ver SQL"):
                st.code(query.string, language='sql')
            
            df_result = pd.read_sql(query, engine)
            
            st.success(f"✅ Consulta ejecutada: {len(df_result)} registros")
            st.dataframe(df_result, use_container_width=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error al ejecutar consulta: {str(e)}")
    
    # Editor SQL personalizado
    st.divider()
    
    with st.expander("⌨️ Editor SQL Personalizado", expanded=False):
        sql_custom = st.text_area(
            "Escribe tu consulta SQL:",
            height=150,
            placeholder="SELECT TOP 100 * FROM vw_ml_dataset..."
        )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("🚀 Ejecutar Consulta Personalizada"):
                if sql_custom.strip():
                    try:
                        conn = get_sql_connection()
                        engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
                        df_custom = pd.read_sql(text(sql_custom), engine)
                        st.success(f"✅ Consulta ejecutada: {len(df_custom)} registros")
                        st.dataframe(df_custom, use_container_width=True)
                        conn.close()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Por favor escribe una consulta SQL")
        with col_btn2:
            if st.button("🧹 Limpiar"):
                st.session_state.sql_custom = ""
