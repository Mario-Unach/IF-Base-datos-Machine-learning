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
auth.require_role(["Administrador", "Analista"]) # Roles permitidos

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
        
        st.subheader("📊 Resumen de Operaciones")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Registros", f"{int(resumen.iloc[0]['total']):,}")
        m2.metric("➕ Inserciones", f"{int(resumen.iloc[0]['inserts'] or 0):,}")
        m3.metric("✏️ Actualizaciones", f"{int(resumen.iloc[0]['updates'] or 0):,}")
        m4.metric("🗑️ Eliminaciones", f"{int(resumen.iloc[0]['deletes'] or 0):,}")
        
        st.divider()
        
        # Filtro y tabla
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            filtro = st.selectbox("Filtrar:", ["Todas", "I", "U", "D"])
        
        query = "SELECT TOP 50 * FROM dbo.auditoria_cambios"
        if filtro != "Todas":
            query += f" WHERE operacion = '{filtro}'"
        query += " ORDER BY fecha_cambio DESC"
        
        df_audit = pd.read_sql(text(query), engine)
        with col_f2:
            st.dataframe(df_audit, use_container_width=True, height=400)
        
        if not df_audit.empty:
            st.bar_chart(df_audit['operacion'].value_counts())
    else:
        st.warning("⚠️ La tabla de auditoría aún no existe en la base de datos.")
    
    conn.close()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")