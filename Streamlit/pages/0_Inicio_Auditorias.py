import streamlit as st
import pandas as pd
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
auth.require_role(["Administrador"]) # Roles permitidos

st.set_page_config(page_title="Auditorías", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.page-header { font-size: 2.6rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">🔎 Auditoría y Triggers</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"`{st.session_state.login_user}`")
    st.divider()
    auth.render_role_menu()
    st.divider()
    

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    # Diagnóstico rápido
    diag = pd.read_sql(text("""
        SELECT 
            SUSER_SNAME() AS login_actual,
            COALESCE(IS_MEMBER('rol_admin'), 0) AS es_admin,
            COALESCE(IS_MEMBER('rol_analista'), 0) AS es_analista
    """), engine)
    
    tabla_ok = pd.read_sql(text("""
        SELECT CASE WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'auditoria_cambios') THEN 1 ELSE 0 END AS existe
    """), engine).iloc[0]['existe']
    
    trigger_ok = pd.read_sql(text("""
        SELECT CASE WHEN EXISTS (SELECT 1 FROM sys.triggers 
            WHERE name = 'trg_Auditoria_Riesgo') THEN 1 ELSE 0 END AS existe
    """), engine).iloc[0]['existe']
    
    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Usuario SQL", diag.iloc[0]['login_actual'])
    c2.metric("📋 Tabla Auditoría", "✅ OK" if tabla_ok else "❌ Falta")
    c3.metric("⚡ Trigger", "✅ OK" if trigger_ok else "❌ Falta")
    c4.metric("🔑 Rol Activo", 
              "Admin" if diag.iloc[0]['es_admin'] else ("Analista" if diag.iloc[0]['es_analista'] else "Otro"))
    
    st.divider()
    
     # Sección de auditoría de cambios (tabla auditoria_cambios)
    if tabla_ok:
        resumen = pd.read_sql(text("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN operacion = 'I' THEN 1 ELSE 0 END) AS inserts,
                SUM(CASE WHEN operacion = 'U' THEN 1 ELSE 0 END) AS updates,
                SUM(CASE WHEN operacion = 'D' THEN 1 ELSE 0 END) AS deletes,
                MAX(fecha_cambio) AS ultimo
            FROM dbo.auditoria_cambios
        """), engine)
        
        st.subheader("📝 Registro de Cambios (auditoria_cambios)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Registros", f"{int(resumen.iloc[0]['total']):,}")
        m2.metric("➕ Inserciones", f"{int(resumen.iloc[0]['inserts'] or 0):,}")
        m3.metric("✏️ Actualizaciones", f"{int(resumen.iloc[0]['updates'] or 0):,}")
        m4.metric("🗑️ Eliminaciones", f"{int(resumen.iloc[0]['deletes'] or 0):,}")
        
        st.divider()
        # Filtro y tabla
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            filtro = st.selectbox("Filtrar por operación:", ["Todas", "I", "U", "D"])
        
        query = "SELECT TOP 50 * FROM dbo.auditoria_cambios"
        if filtro != "Todas":
            query += f" WHERE operacion = '{filtro}'"
        query += " ORDER BY fecha_cambio DESC"
        
        df_audit = pd.read_sql(text(query), engine)
        with col_f2:
            st.dataframe(df_audit, use_container_width=True, height=400)
     
        st.divider()
    
    # Obtener todas las tablas de la base de datos
    st.subheader("📁 Tablas de la Base de Datos")
    tablas_query = text("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        AND TABLE_NAME NOT IN ('auditoria_cambios', 'sysdiagrams')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    tablas_df = pd.read_sql(tablas_query, engine)
    
    if not tablas_df.empty:
        # Crear lista de tablas completas (schema.table)
        tablas_df['full_name'] = tablas_df['TABLE_SCHEMA'] + '.' + tablas_df['TABLE_NAME']
        tabla_seleccionada = st.selectbox(
            "Selecciona una tabla para auditar:",
            options=["Todas"] + list(tablas_df['full_name']),
            index=0
        )
        
        st.divider()
        
        # Función para obtener estadísticas de una tabla específica o todas
        def get_table_stats(table_filter=None):
            if table_filter and table_filter != "Todas":
                schema, table = table_filter.split('.')
                where_clause = f"AND t.TABLE_SCHEMA = '{schema}' AND t.TABLE_NAME = '{table}'"
            else:
                where_clause = ""
            
            query = text(f"""
                SELECT 
                    t.TABLE_SCHEMA,
                    t.TABLE_NAME,
                    p.rows AS row_count,
                    SUM(a.used_pages) * 8 AS size_kb
                FROM INFORMATION_SCHEMA.TABLES t
                INNER JOIN sys.tables st ON t.TABLE_NAME = st.name AND t.TABLE_SCHEMA = SCHEMA_NAME(st.schema_id)
                INNER JOIN sys.indexes i ON st.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE t.TABLE_TYPE = 'BASE TABLE' 
                AND t.TABLE_NAME NOT IN ('auditoria_cambios', 'sysdiagrams')
                {where_clause}
                GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, p.rows
                ORDER BY p.rows DESC
            """)
            return pd.read_sql(query, engine)
        
        stats_df = get_table_stats(tabla_seleccionada)
        
        if not stats_df.empty:
            st.subheader("📊 Estadísticas de Tablas")
            
            # Mostrar métricas resumen
            total_tablas = len(stats_df)
            total_filas = stats_df['row_count'].sum()
            total_size_kb = stats_df['size_kb'].sum()
            avg_filas = int(total_filas / total_tablas) if total_tablas > 0 else 0
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Tablas", total_tablas)
            m2.metric("Total Filas", f"{total_filas:,}")
            m3.metric("Espacio Total", f"{total_size_kb / 1024:.2f} MB")
            m4.metric("Promedio Filas/Tabla", f"{avg_filas:,}")
            
            st.divider()
            
            # Mostrar tabla con detalles
            st.dataframe(
                stats_df[['TABLE_SCHEMA', 'TABLE_NAME', 'row_count', 'size_kb']],
                use_container_width=True,
                height=400,
                column_config={
                    "TABLE_SCHEMA": "Schema",
                    "TABLE_NAME": "Tabla",
                    "row_count": "Filas",
                    "size_kb": "Tamaño (KB)"
                }
            )
            
            # Gráfico de distribución
            if len(stats_df) <= 20:
                st.subheader("📈 Distribución de Filas por Tabla")
                chart_data = stats_df.set_index('TABLE_NAME')['row_count']
                st.bar_chart(chart_data)
        else:
            st.warning("⚠️ No se encontraron tablas para auditar.")
    else:
        st.warning("⚠️ No hay tablas disponibles en la base de datos.")
    
    st.divider()
    
    
    conn.close()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")