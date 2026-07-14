import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from sqlalchemy import create_engine, text
from db_connections import get_sql_connection, get_mongo_connection

# 1. Agregar la carpeta raíz (Streamlit/) al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 2. Importar el módulo de autenticación
import auth

# 3. Inicializar y proteger la página
auth.init_session_state()
auth.require_role(["Administrador"]) # Roles permitidos

st.set_page_config(page_title="Administración BD", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.page-header { font-size: 2.6rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">🛠️ Administración BD</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"`{st.session_state.login_user}`")
    st.divider()
    auth.render_role_menu()
    st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["👥 Usuarios", "💾 Backups", "❤️ Health Check", "⌨️ Terminal SQL"])

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    with tab1:
        st.subheader("👥 Usuarios y Roles")
        df_users = pd.read_sql(text("""
            SELECT u.name AS usuario, r.name AS rol, l.create_date
            FROM sys.database_principals u
            LEFT JOIN sys.database_role_members rm ON u.principal_id = rm.member_principal_id
            LEFT JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
            LEFT JOIN sys.server_principals l ON u.sid = l.sid
            WHERE u.type = 'S' AND u.name NOT IN ('dbo', 'guest')
            ORDER BY u.name
        """), engine)
        st.dataframe(df_users, use_container_width=True)
    
    with tab2:
        st.subheader("💾 Ejecutar Backup")
        tipo = st.selectbox("Tipo:", ["Completo (Full)", "Diferencial (Diff)", "Log Transaccional"])
        
        if st.button("🚀 Ejecutar Backup", type="primary"):
            queries = {
                "Completo (Full)": "BACKUP DATABASE CC_Client TO DISK = '/var/opt/mssql/backups/CC_Client_Full.bak' WITH FORMAT, INIT",
                "Diferencial (Diff)": "BACKUP DATABASE CC_Client TO DISK = '/var/opt/mssql/backups/CC_Client_Diff.bak' WITH DIFFERENTIAL",
                "Log Transaccional": "BACKUP LOG CC_Client TO DISK = '/var/opt/mssql/backups/CC_Client_Log.trn'"
            }
            try:
                cursor = conn.cursor()
                cursor.execute(queries[tipo])
                conn.commit()
                st.success(f"✅ Backup **{tipo}** ejecutado correctamente")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with tab3:
        st.subheader("❤️ Estado de Servicios")
        c1, c2 = st.columns(2)
        with c1:
            try:
                version = pd.read_sql(text("SELECT @@VERSION AS v"), engine).iloc[0]['v']
                st.success("✅ SQL Server Conectado")
                st.caption(version[:150] + "...")
            except Exception as e:
                st.error(f"❌ SQL Server: {str(e)}")
        
        with c2:
            try:
                client = get_mongo_connection()
                info = client.server_info()
                st.success("✅ MongoDB Conectado")
                st.caption(f"Versión: {info.get('version', 'N/A')}")
                client.close()
            except Exception as e:
                st.error(f"❌ MongoDB: {str(e)}")
        
        st.divider()
        metrics = pd.read_sql(text("""
            SELECT 
                (SELECT COUNT(*) FROM dim_cliente) AS clientes,
                (SELECT COUNT(*) FROM historial_pagos) AS historial,
                (SELECT COUNT(*) FROM auditoria_cambios) AS auditorias,
                (SELECT COUNT(*) FROM sys.indexes) AS indices
        """), engine)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("👥 Clientes", f"{int(metrics.iloc[0]['clientes']):,}")
        m2.metric("📜 Historial", f"{int(metrics.iloc[0]['historial']):,}")
        m3.metric("🔒 Auditorías", f"{int(metrics.iloc[0]['auditorias']):,}")
        m4.metric("📇 Índices", f"{int(metrics.iloc[0]['indices']):,}")
    
    with tab4:
        st.subheader("⌨️ Terminal SQL")
        st.warning("⚠️ Solo para administradores")
        sql = st.text_area("SQL:", height=150, placeholder="SELECT TOP 10 * FROM dim_cliente")
        if st.button("🚀 Ejecutar", type="primary"):
            if sql.strip():
                try:
                    df_r = pd.read_sql(text(sql), engine)
                    st.dataframe(df_r, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ {str(e)}")
    
    conn.close()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")