import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio Streamlit al path para importar db_connections
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connections import get_sql_connection, get_mongo_db
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Administración de Base de Datos",
    page_icon="🛠️",
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
    
    /* User cards */
    .user-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        margin: 1rem 0;
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

st.markdown('<p class="page-header">🛠️ Administración de Base de Datos</p>', unsafe_allow_html=True)

# Pestañas principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Usuarios y Roles",
    "🔒 Auditoría y Triggers",
    "💾 Backups y DRP",
    "❤️ Health Check",
    "⌨️ Terminal SQL"
])

with tab1:
    st.markdown("### 👥 Gestión de Usuarios y Roles")
    
    st.info("""
    **Roles Implementados:**
    
    - **rol_analista:** Permisos de lectura sobre vistas y tablas dimensionales
    - **rol_admin:** Control total de la infraestructura (CONTROL ON DATABASE)
    
    **Usuarios Creados:**
    - **analista:** Miembro de rol_analista (solo lectura)
    - **admin:** Miembro de rol_admin (permisos completos)
    """)
    
    col_user1, col_user2 = st.columns(2)
    
    with col_user1:
        st.markdown("""
        <div class="user-card">
            <h3>👤 Analista</h3>
            <p><strong>Login:</strong> analista</p>
            <p><strong>Rol:</strong> rol_analista</p>
            <p><strong>Permisos:</strong></p>
            <ul>
                <li>SELECT en vistas ML</li>
                <li>SELECT en tablas dimensión</li>
                <li>SELECT en historial_pagos</li>
                <li>❌ Sin INSERT/UPDATE/DELETE</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_user2:
        st.markdown("""
        <div class="user-card">
            <h3>👨‍💼 Administrador</h3>
            <p><strong>Login:</strong> admin</p>
            <p><strong>Rol:</strong> rol_admin</p>
            <p><strong>Permisos:</strong></p>
            <ul>
                <li>CONTROL ON DATABASE</li>
                <li>✅ Todos los privilegios</li>
                <li>Gestión completa de BD</li>
                <li>Ejecución de backups</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📜 Script SQL de Creación de Usuarios")
    
    sql_usuarios = """
    -- Crear roles
    CREATE ROLE rol_analista;
    CREATE ROLE rol_admin;
    
    -- Asignar permisos al rol_analista (solo lectura)
    GRANT SELECT ON vw_ml_dataset TO rol_analista;
    GRANT SELECT ON vw_cliente_detallado TO rol_analista;
    GRANT SELECT ON dim_cliente TO rol_analista;
    GRANT SELECT ON dim_sexo TO rol_analista;
    GRANT SELECT ON dim_educacion TO rol_analista;
    GRANT SELECT ON dim_estado_civil TO rol_analista;
    GRANT SELECT ON historial_pagos TO rol_analista;
    GRANT SELECT ON riesgo_crediticio TO rol_analista;
    
    -- Permisos al rol_admin (todos los privilegios)
    GRANT CONTROL ON DATABASE::CC_Client TO rol_admin;
    
    -- Crear logins con contraseña (nivel servidor)
    CREATE LOGIN analista WITH PASSWORD = 'ContraseñaSegura123!';
    CREATE LOGIN admin WITH PASSWORD = 'ContraseñaSegura456!';
    
    -- Crear usuarios en la base vinculados a los logins
    CREATE USER analista FOR LOGIN analista;
    CREATE USER admin FOR LOGIN admin;
    
    -- Asignar roles a los usuarios
    ALTER ROLE rol_analista ADD MEMBER analista;
    ALTER ROLE rol_admin ADD MEMBER admin;
    """
    
    with st.expander("📜 Ver Script SQL Completo"):
        st.code(sql_usuarios, language='sql')
    
    if st.button("🔄 Verificar Usuarios Actuales"):
        try:
            conn = get_sql_connection()
            
            query_usuarios = """
                SELECT 
                    u.name AS usuario,
                    r.name AS rol,
                    l.create_date AS fecha_creacion
                FROM sys.database_principals u
                LEFT JOIN sys.database_role_members rm ON u.principal_id = rm.member_principal_id
                LEFT JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                LEFT JOIN sys.server_principals l ON u.sid = l.sid
                WHERE u.type = 'S'
                ORDER BY u.name
            """
            
            df_usuarios = pd.read_sql(query_usuarios, conn)
            st.dataframe(df_usuarios, use_container_width=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error al consultar usuarios: {str(e)}")

with tab2:
    st.markdown("### 🔒 Sistema de Auditoría con Triggers")
    
    st.success("""
    **Trigger Implementado:** `trg_Auditoria_Riesgo`
    
    Este trigger registra automáticamente en la tabla `auditoria_cambios`:
    - ✅ Inserciones (INSERT)
    - ✅ Actualizaciones (UPDATE)
    - ✅ Eliminaciones (DELETE)
    """)
    
    st.divider()
    
    st.markdown("### 📊 Registros de Auditoría Recientes")
    
    try:
        conn = get_sql_connection()
        
        query_auditoria = """
            SELECT TOP 50
                id_auditoria,
                tabla_afectada,
                operacion,
                id_registro_afectado,
                usuario,
                fecha_cambio,
                datos_antes,
                datos_despues
            FROM auditoria_cambios
            ORDER BY fecha_cambio DESC
        """
        
        df_auditoria = pd.read_sql(query_auditoria, conn)
        
        if not df_auditoria.empty:
            st.dataframe(df_auditoria, use_container_width=True)
        else:
            st.info("ℹ️ No hay registros de auditoría aún.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error al cargar auditoría: {str(e)}")
    
    st.divider()
    
    st.markdown("### 📜 Código del Trigger")
    
    trigger_code = """
CREATE OR ALTER TRIGGER trg_Auditoria_Riesgo
ON riesgo_crediticio
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (SELECT * FROM inserted) AND NOT EXISTS (SELECT * FROM deleted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_despues)
        SELECT 'riesgo_crediticio', 'I', id_cliente, 
               CONVERT(NVARCHAR(MAX), incumplimiento_proximo_mes)
        FROM inserted;
    END

    IF EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_antes, datos_despues)
        SELECT 'riesgo_crediticio', 'U', i.id_cliente,
               CONVERT(NVARCHAR(MAX), d.incumplimiento_proximo_mes),
               CONVERT(NVARCHAR(MAX), i.incumplimiento_proximo_mes)
        FROM inserted i
        JOIN deleted d ON i.id_cliente = d.id_cliente;
    END

    IF EXISTS (SELECT * FROM deleted) AND NOT EXISTS (SELECT * FROM inserted)
    BEGIN
        INSERT INTO auditoria_cambios (tabla_afectada, operacion, id_registro_afectado, datos_antes)
        SELECT 'riesgo_crediticio', 'D', id_cliente, 
               CONVERT(NVARCHAR(MAX), incumplimiento_proximo_mes)
        FROM deleted;
    END
END;
    """
    
    with st.expander("📜 Ver Código del Trigger"):
        st.code(trigger_code, language='sql')

with tab3:
    st.markdown("### 💾 Estrategia de Backups y DRP")
    
    st.warning("""
    **Plan de Recuperación ante Desastres (DRP)**
    
    La estrategia implementada incluye tres tipos de backup:
    
    1. **Backup Completo (Full):** Copia completa de la base de datos
    2. **Backup Diferencial (Diff):** Cambios desde el último full
    3. **Backup de Log Transaccional:** Todas las transacciones
    """)
    
    col_backup1, col_backup2 = st.columns(2)
    
    with col_backup1:
        st.markdown("""
        #### 📋 Scripts de Backup
        
        **Backup Completo:**
        ```sql
        BACKUP DATABASE CC_Client
        TO DISK = '/var/opt/mssql/backups/CC_Client_Full.bak'
        WITH FORMAT, INIT, NAME = 'Full Backup CC_Client';
        ```
        
        **Backup Diferencial:**
        ```sql
        BACKUP DATABASE CC_Client
        TO DISK = '/var/opt/mssql/backups/CC_Client_Diff.bak'
        WITH DIFFERENTIAL;
        ```
        """)
    
    with col_backup2:
        st.markdown("""
        #### 🔄 Proceso de Restauración
        
        **Paso 1:** Restaurar FULL con NORECOVERY
        ```sql
        RESTORE DATABASE CC_Client
        FROM DISK = '/var/opt/mssql/backups/CC_Client_Full.bak'
        WITH NORECOVERY;
        ```
        
        **Paso 2:** Restaurar DIFF con NORECOVERY
        ```sql
        RESTORE DATABASE CC_Client
        FROM DISK = '/var/opt/mssql/backups/CC_Client_Diff.bak'
        WITH NORECOVERY;
        ```
        
        **Paso 3:** Restaurar LOG con RECOVERY
        ```sql
        RESTORE LOG CC_Client
        FROM DISK = '/var/opt/mssql/backups/CC_Client_Log.trn'
        WITH RECOVERY;
        ```
        """)
    
    st.divider()
    
    st.markdown("### ⚡ Ejecutar Backup Ahora")
    
    backup_type = st.selectbox(
        "Selecciona el tipo de backup:",
        ["Completo (Full)", "Diferencial (Diff)", "Log Transaccional"]
    )
    
    if st.button("🚀 Ejecutar Backup", type="primary"):
        try:
            conn = get_sql_connection()
            cursor = conn.cursor()
            
            if backup_type == "Completo (Full)":
                backup_query = """
                BACKUP DATABASE CC_Client
                TO DISK = '/var/opt/mssql/backups/CC_Client_Full_Backup.bak'
                WITH FORMAT, INIT, NAME = 'Full Backup CC_Client - Manual';
                """
            elif backup_type == "Diferencial (Diff)":
                backup_query = """
                BACKUP DATABASE CC_Client
                TO DISK = '/var/opt/mssql/backups/CC_Client_Diff_Backup.bak'
                WITH DIFFERENTIAL, NAME = 'Differential Backup CC_Client - Manual';
                """
            else:
                backup_query = """
                BACKUP LOG CC_Client
                TO DISK = '/var/opt/mssql/backups/CC_Client_Log_Backup.trn'
                WITH NAME = 'Log Backup CC_Client - Manual';
                """
            
            cursor.execute(backup_query)
            conn.commit()
            
            st.success("✅ Backup ejecutado exitosamente!")
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error al ejecutar backup: {str(e)}")

with tab4:
    st.markdown("### ❤️ Health Check de la Base de Datos")
    
    st.info("Verifica el estado actual de la infraestructura de bases de datos")
    
    col_health1, col_health2 = st.columns(2)
    
    with col_health1:
        st.markdown("**SQL Server**")
        try:
            conn = get_sql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            st.success(f"✅ Conectado")
            st.caption(version[:200] + "...")
            conn.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with col_health2:
        st.markdown("**MongoDB**")
        try:
            mongo_client = get_mongo_connection()
            server_info = mongo_client.server_info()
            st.success(f"✅ Conectado")
            st.caption(f"Versión: {server_info.get('version', 'Desconocida')}")
            mongo_client.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    st.markdown("#### 📊 Métricas de SQL Server")
    
    try:
        conn = get_sql_connection()
        
        metrics_query = """
            SELECT 
                (SELECT COUNT(*) FROM dim_cliente) AS total_clientes,
                (SELECT COUNT(*) FROM historial_pagos) AS total_historial,
                (SELECT COUNT(*) FROM auditoria_cambios) AS total_auditoria,
                (SELECT COUNT(*) FROM sys.indexes) AS total_indices
        """
        
        df_metrics = pd.read_sql(metrics_query, conn)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric("👥 Clientes", f"{int(df_metrics['total_clientes'][0]):,}")
        
        with col_m2:
            st.metric("📜 Historial", f"{int(df_metrics['total_historial'][0]):,}")
        
        with col_m3:
            st.metric("🔒 Auditorías", f"{int(df_metrics['total_auditoria'][0]):,}")
        
        with col_m4:
            st.metric("📇 Índices", f"{int(df_metrics['total_indices'][0]):,}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error al cargar métricas: {str(e)}")

with tab5:
    st.markdown("### ⌨️ Terminal SQL Interactiva")
    
    st.warning("⚠️ Usa esta herramienta con precaución. Solo para usuarios con rol admin.")
    
    quick_queries = {
        "Ver todas las tablas": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
        "Contar registros por tabla": """
            SELECT t.name AS tabla, p.rows AS registros
            FROM sys.tables t
            INNER JOIN sys.partitions p ON t.object_id = p.OBJECT_ID
            WHERE p.index_id IN (0,1)
            ORDER BY p.rows DESC
        """,
        "Ver triggers": "SELECT name, parent_id FROM sys.triggers",
        "Ver roles": "SELECT name FROM sys.database_principals WHERE type = 'R'"
    }
    
    selected_query = st.selectbox("Selecciona una consulta rápida:", list(quick_queries.keys()))
    
    if st.button("▶️ Ejecutar Consulta Rápida"):
        try:
            conn = get_sql_connection()
            df = pd.read_sql(quick_queries[selected_query], conn)
            st.success(f"✅ {len(df)} registros")
            st.dataframe(df, use_container_width=True)
            conn.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    st.markdown("#### 📝 Editor SQL Avanzado")
    
    sql_code = st.text_area(
        "Escribe tu consulta SQL:",
        height=200,
        placeholder="SELECT TOP 100 * FROM dim_cliente..."
    )
    
    if st.button("🚀 Ejecutar", type="primary"):
        if sql_code.strip():
            try:
                conn = get_sql_connection()
                
                with st.expander("📜 SQL a ejecutar"):
                    st.code(sql_code, language='sql')
                
                df_result = pd.read_sql(sql_code, conn)
                
                st.success(f"✅ Consulta ejecutada: {len(df_result)} registros")
                st.dataframe(df_result, use_container_width=True)
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Error al ejecutar consulta: {str(e)}")
        else:
            st.warning("⚠️ Por favor escribe una consulta SQL")
