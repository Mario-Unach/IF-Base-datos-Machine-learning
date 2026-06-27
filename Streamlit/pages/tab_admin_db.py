import streamlit as st
import pandas as pd
from Streamlit.db_connections import get_sql_connection

def show_admin_db_tab():
    # CSS personalizado para esta pestaña
    st.markdown("""
    <style>
    .sql-terminal {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
    }
    .admin-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("🛠️ Administración, Auditoría y DRP")
    st.markdown("### Gestión de SQL Server")
    
    conn = get_sql_connection()
    if not conn:
        st.warning("⚠️ No hay conexión a SQL Server. Verifica que el contenedor esté corriendo.")
        return
    
    # Mostrar estado de conexión
    st.success("✅ Conectado a SQL Server - Base de Datos: CC_Client")
    
    tab_sql, tab_logs, tab_backup, tab_health = st.tabs([
        "💻 Terminal SQL", 
        "🛡️ Auditoría (Logs)", 
        "💾 Backup & DRP",
        "🏥 Health Check"
    ])
    
    with tab_sql:
        st.subheader("Terminal SQL Interactiva")
        st.markdown("*Ejecuta consultas personalizadas directamente sobre la base de datos*")
        
        # Queries predefinidas
        st.markdown("**Consultas Rápidas:**")
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            if st.button("📊 Top 10 Clientes"):
                st.session_state.query = "SELECT TOP 10 * FROM vw_ml_dataset ORDER BY LIMIT_BAL DESC;"
        with col_q2:
            if st.button("⚠️ Defaults Recientes"):
                st.session_state.query = "SELECT TOP 20 * FROM vw_ml_dataset WHERE [default payment next month] = 1 ORDER BY id_cliente;"
        with col_q3:
            if st.button("📈 Estadísticas Generales"):
                st.session_state.query = """
                SELECT 
                    COUNT(*) AS TotalClientes,
                    AVG(LIMIT_BAL) AS LimitePromedio,
                    AVG(edad) AS EdadPromedio,
                    SUM(CASE WHEN [default payment next month] = 1 THEN 1 ELSE 0 END) AS TotalDefaults
                FROM vw_ml_dataset;
                """
        
        query = st.text_area(
            "Ingresa tu consulta SQL:", 
            value=st.session_state.get('query', "SELECT TOP 10 * FROM vw_ml_dataset;"),
            height=150, 
            placeholder="SELECT * FROM Clientes;",
            help="Escribe tu consulta SQL aquí. Usa el formato T-SQL."
        )
        
        if st.button("▶️ Ejecutar Consulta", type="primary"):
            try:
                df = pd.read_sql(query, conn)
                st.dataframe(df, use_container_width=True, hide_index=True, height=400)
                
                # Mostrar resumen si hay datos
                if len(df) > 0:
                    st.caption(f"✅ Consulta ejecutada exitosamente. {len(df)} filas retornadas.")
            except Exception as e:
                st.error(f"❌ Error en la consulta: {e}")
                
    with tab_logs:
        st.subheader("🛡️ Auditoría de Cambios (Histórico)")
        st.info("ℹ️ Esta sección muestra los registros de auditoría generados por Triggers en la base de datos")
        
        try:
            # Intentar leer tabla de auditoría
            df_logs = pd.read_sql("SELECT TOP 50 * FROM Audit_Logs ORDER BY ChangeDate DESC", conn)
            
            if len(df_logs) > 0:
                st.dataframe(df_logs, use_container_width=True, hide_index=True, height=400)
                st.success(f"✅ {len(df_logs)} registros de auditoría encontrados.")
            else:
                st.warning("⚠️ La tabla de auditoría está vacía. No se han registrado cambios aún.")
        except Exception as e:
            st.warning(f"⚠️ No se encontró la tabla Audit_Logs o no hay permisos: {e}")
            st.info("💡 Para habilitar auditoría, crea triggers en las tablas principales.")
            
    with tab_backup:
        st.subheader("💾 Plan de Recuperación ante Desastres (DRP)")
        st.markdown("""
        **Política de Backups:**
        - 📅 Backup completo: Semanal
        - 📝 Backup diferencial: Diario
        - 📜 Backup de logs: Cada hora
        
        *Genera un backup manual de la base de datos directamente desde el dashboard.*
        """)
        
        col_backup1, col_backup2 = st.columns(2)
        with col_backup1:
            backup_path = st.text_input(
                "Ruta de destino en el servidor SQL:", 
                "C:\\Backups\\CreditCardDefault.bak",
                help="Ruta donde se guardará el archivo de backup"
            )
        
        with col_backup2:
            backup_type = st.selectbox(
                "Tipo de Backup:",
                ["Completo", "Diferencial", "Solo Logs"]
            )
        
        if st.button("🚀 Iniciar Backup", type="primary"):
            backup_map = {
                "Completo": "FULL",
                "Diferencial": "DIFFERENTIAL",
                "Solo Logs": "LOG"
            }
            
            backup_command = backup_map[backup_type]
            
            backup_query = f"""
            BACKUP DATABASE CC_Client 
            TO DISK = '{backup_path}'
            WITH {backup_command}, FORMAT, MEDIANAME = 'SQLServerBackups', 
            NAME = '{backup_type} Backup - CC_Client';
            """
            
            st.code(backup_query, language="sql")
            
            if st.button("Confirmar ejecución del backup"):
                try:
                    cursor = conn.cursor()
                    cursor.execute(backup_query)
                    conn.commit()
                    st.success("✅ Backup iniciado correctamente en el servidor.")
                    st.info("⏳ El proceso puede tomar varios minutos dependiendo del tamaño de la BD.")
                except Exception as e:
                    st.error(f"❌ Error al ejecutar backup: {e}")
                    
    with tab_health:
        st.subheader("🏥 Health Check de la Base de Datos")
        st.markdown("**Monitoreo del Estado del Sistema**")
        
        # Métricas de salud
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        
        try:
            # Total de tablas
            tables_query = """
            SELECT COUNT(*) AS TotalTablas 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE';
            """
            total_tables = pd.read_sql(tables_query, conn)['TotalTablas'].iloc[0]
            col_h1.metric("📊 Tablas", total_tables)
            
            # Total de vistas
            views_query = """
            SELECT COUNT(*) AS TotalVistas 
            FROM INFORMATION_SCHEMA.VIEWS;
            """
            total_views = pd.read_sql(views_query, conn)['TotalVistas'].iloc[0]
            col_h2.metric("👁️ Vistas", total_views)
            
            # Tamaño de la BD
            size_query = """
            SELECT 
                SUM(size * 8 / 1024) AS SizeMB 
            FROM sys.database_files;
            """
            try:
                db_size = pd.read_sql(size_query, conn)['SizeMB'].iloc[0]
                col_h3.metric("💾 Tamaño BD", f"{db_size:.2f} MB")
            except:
                col_h3.metric("💾 Tamaño BD", "N/A")
            
            # Conexiones activas
            conn_query = """
            SELECT COUNT(*) AS ConexionesActivas 
            FROM sys.dm_exec_sessions 
            WHERE is_user_process = 1;
            """
            try:
                active_conn = pd.read_sql(conn_query, conn)['ConexionesActivas'].iloc[0]
                col_h4.metric("🔗 Conexiones", active_conn)
            except:
                col_h4.metric("🔗 Conexiones", "N/A")
            
            st.divider()
            
            # Últimos errores
            st.markdown("**📋 Últimos Registros del Sistema**")
            error_query = """
            SELECT TOP 10 * 
            FROM sys.messages 
            WHERE severity > 10 
            ORDER BY message_id DESC;
            """
            try:
                df_errors = pd.read_sql(error_query, conn)
                if len(df_errors) > 0:
                    st.dataframe(df_errors, use_container_width=True, hide_index=True)
                else:
                    st.success("✅ No se encontraron errores críticos recientes.")
            except Exception as e:
                st.caption(f"No se pudo recuperar información de errores: {e}")
                
        except Exception as e:
            st.error(f"❌ Error al realizar health check: {e}")
