import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

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
        query = f"SELECT TOP {top_n} * FROM {tabla_seleccionada}"
        df = pd.read_sql(query, conn)
        
        st.success(f"✅ {len(df)} registros cargados exitosamente")
        
        # Mostrar datos con formato
        st.dataframe(
            df.style.format(precision=2).background_gradient(cmap="Blues", subset=df.select_dtypes(include=['float', 'int']).columns),
            use_container_width=True,
            height=400
        )
        
        # Estadísticas descriptivas
        st.markdown("#### 📊 Estadísticas Descriptivas")
        if not df.empty:
            st.write(df.describe())
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
    
    # Información de la estructura
    st.divider()
    st.markdown("### 📋 Estructura de la Base de Datos")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        #### Tablas de Dimensión (Catálogos)
        
        **dim_sexo**
        - `id_sexo` (PK): Identificador del sexo
        - `descripcion_sexo`: Masculino/Femenino
        
        **dim_educacion**
        - `id_educacion` (PK): Identificador del nivel educativo
        - `nivel_educativo`: Posgrado, Universidad, Bachillerato, etc.
        
        **dim_estado_civil**
        - `id_estado_civil` (PK): Identificador del estado civil
        - `descripcion_estado_civil`: Casado, Soltero, Otros
        
        **dim_tiempo_mes**
        - `id_mes` (PK): Identificador del mes
        - `mes_referencia`: Descripción del mes (ej. Septiembre 2005)
        - `orden_historial`: Orden cronológico
        """)
    
    with col_info2:
        st.markdown("""
        #### Tablas Principales
        
        **dim_cliente**
        - `id_cliente` (PK): Identificador único del cliente
        - `id_sexo` (FK): Referencia a dim_sexo
        - `id_educacion` (FK): Referencia a dim_educacion
        - `id_estado_civil` (FK): Referencia a dim_estado_civil
        - `edad`: Edad del cliente
        - `limite_credito`: Límite de crédito aprobado
        
        **historial_pagos**
        - `id_historial` (PK): Identificador del registro histórico
        - `id_cliente` (FK): Referencia al cliente
        - `id_mes` (FK): Referencia al mes
        - `id_estatus_pago` (FK): Estado del pago
        - `monto_estado_cuenta`: Monto facturado
        - `monto_pago_anterior`: Monto pagado
        
        **riesgo_crediticio**
        - `id_cliente` (PK/FK): Referencia al cliente
        - `incumplimiento_proximo_mes`: Target (0/1)
        """)

with tab2:
    st.markdown("### 🏗️ Modelo Entidad-Relación Normalizado")
    
    st.markdown("""
    #### Diagrama Conceptual de la Base de Datos
    
    La base de datos sigue un diseño normalizado en **3ra Forma Normal (3NF)** para garantizar:
    - ✅ Integridad referencial
    - ✅ Minimización de redundancia
    - ✅ Optimización de consultas analíticas
    """)
    
    # Crear diagrama ER simplificado con Plotly
    fig = go.Figure()
    
    # Agregar nodos (tablas)
    tables = {
        'dim_cliente': (0, 0),
        'dim_sexo': (-2, 2),
        'dim_educacion': (0, 2),
        'dim_estado_civil': (2, 2),
        'historial_pagos': (-2, -2),
        'riesgo_crediticio': (2, -2)
    }
    
    for table, pos in tables.items():
        fig.add_trace(go.Scatter(
            x=[pos[0]], y=[pos[1]],
            mode='markers+text',
            marker=dict(size=40, symbol='square', color='#1f77b4'),
            text=[table],
            textposition='middle center',
            textfont=dict(size=10, color='white'),
            name=table
        ))
    
    fig.update_layout(
        title='🗺️ Diagrama Simplificado de Relaciones',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=800,
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    #### Índices Implementados
    
    **Índices Clustered:**
    - PK en todas las tablas principales
    
    **Índices Non-Clustered:**
    ```sql
    CREATE NONCLUSTERED INDEX idx_historial_cliente_mes 
    ON historial_pagos (id_cliente, id_mes)
    INCLUDE (id_estatus_pago, monto_estado_cuenta, monto_pago_anterior);
    
    CREATE NONCLUSTERED INDEX idx_riesgo_target 
    ON riesgo_crediticio (incumplimiento_proximo_mes)
    INCLUDE (id_cliente);
    ```
    
    #### Vistas Estructuradas
    
    **vw_ml_dataset:** Vista optimizada para consumo de algoritmos ML
    - Combina cliente, historial pivotado y target
    - Elimina necesidad de joins complejos en Python
    
    **vw_cliente_detallado:** Vista para análisis exploratorio
    - Incluye descripciones de catálogos
    - Ideal para reporting ejecutivo
    """)

with tab3:
    st.markdown("### 📈 Visualizaciones Avanzadas del Dataset")
    
    try:
        conn = get_sql_connection()
        
        # KPIs principales
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        query_kpis = """
            SELECT 
                COUNT(DISTINCT c.id_cliente) AS total_clientes,
                AVG(c.limite_credito) AS avg_limite,
                MIN(c.limite_credito) AS min_limite,
                MAX(c.limite_credito) AS max_limite,
                AVG(c.edad) AS avg_edad,
                SUM(r.incumplimiento_proximo_mes) * 100.0 / COUNT(*) AS tasa_default
            FROM dim_cliente c
            INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
        """
        df_kpis = pd.read_sql(query_kpis, conn)
        
        with col_kpi1:
            st.metric("👥 Total Clientes", f"{int(df_kpis['total_clientes'][0]):,}")
        
        with col_kpi2:
            st.metric("💰 Límite Promedio", f"${df_kpis['avg_limite'][0]:,.2f}")
        
        with col_kpi3:
            st.metric("📅 Edad Promedio", f"{df_kpis['avg_edad'][0]:.1f} años")
        
        with col_kpi4:
            st.metric("⚠️ Tasa Incumplimiento", f"{df_kpis['tasa_default'][0]:.2f}%")
        
        st.divider()
        
        # Gráficos en dos filas
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            # Distribución de límites de crédito
            query_hist = "SELECT limite_credito FROM dim_cliente"
            df_hist = pd.read_sql(query_hist, conn)
            
            fig_hist = px.histogram(df_hist, x='limite_credito', nbins=50,
                                    title='💰 Distribución de Límites de Crédito',
                                    labels={'limite_credito': 'Límite de Crédito ($)'},
                                    color_discrete_sequence=['#1f77b4'])
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with row1_col2:
            # Distribución por educación y estado civil
            query_pie = """
                SELECT e.nivel_educativo, COUNT(*) as cantidad
                FROM dim_cliente c
                INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
                GROUP BY e.nivel_educativo
                ORDER BY cantidad DESC
            """
            df_pie = pd.read_sql(query_pie, conn)
            
            fig_pie = px.pie(df_pie, values='cantidad', names='nivel_educativo',
                             title='📚 Nivel Educativo',
                             color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            # Análisis de edad por género
            query_box = """
                SELECT s.descripcion_sexo, c.edad
                FROM dim_cliente c
                INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
            """
            df_box = pd.read_sql(query_box, conn)
            
            fig_box = px.box(df_box, x='descripcion_sexo', y='edad',
                             title='📊 Distribución de Edad por Género',
                             color='descripcion_sexo',
                             color_discrete_map={'Masculino': '#1f77b4', 'Femenino': '#ff7f0e'})
            st.plotly_chart(fig_box, use_container_width=True)
        
        with row2_col2:
            # Heatmap de correlación (datos numéricos)
            query_corr = """
                SELECT TOP 1000
                    c.limite_credito,
                    c.edad,
                    r.incumplimiento_proximo_mes
                FROM dim_cliente c
                INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
            """
            df_corr = pd.read_sql(query_corr, conn)
            
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
        
        "Historial completo de un cliente específico (ID=52)": """
            SELECT 
                hp.id_cliente,
                tm.mes_referencia,
                ep.descripcion_estatus AS estado_de_pago,
                hp.monto_estado_cuenta,
                hp.monto_pago_anterior
            FROM historial_pagos hp
            INNER JOIN dim_tiempo_mes tm ON hp.id_mes = tm.id_mes
            INNER JOIN dim_estatus_pago ep ON hp.id_estatus_pago = ep.id_estatus
            WHERE hp.id_cliente = 52
            ORDER BY tm.orden_historial
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
            query = consultas[consulta_seleccionada]
            
            # Mostrar la consulta SQL
            with st.expander("📜 Ver SQL"):
                st.code(query, language='sql')
            
            df_result = pd.read_sql(query, conn)
            
            st.success(f"✅ Consulta ejecutada: {len(df_result)} registros")
            st.dataframe(df_result, use_container_width=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error al ejecutar consulta: {str(e)}")
    
    # Editor SQL personalizado
    st.divider()
    st.markdown("### ⌨️ Editor SQL Personalizado")
    
    sql_custom = st.text_area(
        "Escribe tu consulta SQL:",
        height=150,
        placeholder="SELECT TOP 100 * FROM vw_ml_dataset..."
    )
    
    if st.button("🚀 Ejecutar Consulta Personalizada"):
        if sql_custom.strip():
            try:
                conn = get_sql_connection()
                df_custom = pd.read_sql(sql_custom, conn)
                st.success(f"✅ Consulta ejecutada: {len(df_custom)} registros")
                st.dataframe(df_custom, use_container_width=True)
                conn.close()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Por favor escribe una consulta SQL")
