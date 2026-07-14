import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connections import get_sql_connection, get_mongo_connection
import auth

auth.init_session_state()
auth.require_role(["Administrador", "SA"])

st.set_page_config(page_title="Administración BD", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%); }
.page-header { font-size: 2.6rem; font-weight: 800; background: linear-gradient(90deg, #00d4ff, #7b2cbf);
-webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown { color: #e2e8f0; }
.metric-card {
    background: rgba(30, 41, 59, 0.8);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #00d4ff;
    margin: 0.5rem 0;
}
.success-box {
    background: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.5);
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
.error-box {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.5);
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
.warning-box {
    background: rgba(251, 191, 36, 0.2);
    border: 1px solid rgba(251, 191, 36, 0.5);
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="page-header">🛠️ Administración BD</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.login_profile}")
    st.caption(f"`{st.session_state.login_user}`")
    st.divider()
    auth.render_role_menu()
    st.divider()
    auth.logout_button()

tab1, tab2, tab3, tab4 = st.tabs(["👥 Usuarios", "💾 Backups", "❤️ Estado de Servicios", "⌨️ Terminal SQL"])

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)
    
    # ==========================================
    # TAB 1: GESTIÓN DE USUARIOS MEJORADA
    # ==========================================
    with tab1:
        st.subheader("👥 Gestión Completa de Usuarios y Roles")
        
        # Mostrar usuarios actuales
        df_users = pd.read_sql(text("""
            SELECT 
                dp.name AS usuario,
                dp.type_desc AS tipo,
                dp.create_date AS creado,
                dp.modify_date AS modificado,
                STRING_AGG(r.name, ', ') AS roles
            FROM sys.database_principals dp
            LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
            LEFT JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
            WHERE dp.type IN ('S', 'U') AND dp.name NOT IN ('dbo', 'guest', 'INFORMATION_SCHEMA', 'sys')
            GROUP BY dp.name, dp.type_desc, dp.create_date, dp.modify_date
            ORDER BY dp.name
        """), engine)
        
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Operaciones de usuarios
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ➕ Crear Nuevo Usuario")
            with st.form("crear_usuario_form"):
                nuevo_usuario = st.text_input("Nombre de usuario")
                nueva_password = st.text_input("Contraseña", type="password")
                roles_disponibles = pd.read_sql(text("""
                    SELECT name FROM sys.database_principals 
                    WHERE type = 'R' AND name NOT IN ('public', 'db_owner', 'db_accessadmin', 
                    'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 'db_datareader', 
                    'db_datawriter', 'db_denydatareader', 'db_denydatawriter')
                """), engine)
                
                rol_seleccionado = st.selectbox("Rol inicial", 
                    roles_disponibles['name'].tolist() if not roles_disponibles.empty else ["rol_analista", "rol_admin"])
                
                if st.form_submit_button("Crear Usuario", type="primary"):
                    if nuevo_usuario and nueva_password:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(f"""
                                IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = '{nuevo_usuario}')
                                CREATE LOGIN [{nuevo_usuario}] WITH PASSWORD = '{nueva_password}', 
                                DEFAULT_DATABASE = [CC_Client], CHECK_POLICY = OFF
                            """)
                            
                            cursor.execute(f"""
                                IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '{nuevo_usuario}')
                                CREATE USER [{nuevo_usuario}] FOR LOGIN [{nuevo_usuario}]
                            """)
                            
                            cursor.execute(f"ALTER ROLE [{rol_seleccionado}] ADD MEMBER [{nuevo_usuario}]")
                            conn.commit()
                            
                            st.success(f"✅ Usuario '{nuevo_usuario}' creado exitosamente con rol '{rol_seleccionado}'")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear usuario: {str(e)}")
                    else:
                        st.warning("⚠️ Completa todos los campos")
        
        with col2:
            st.markdown("### 🗑️ Eliminar Usuario")
            with st.form("eliminar_usuario_form"):
                if not df_users.empty:
                    usuario_eliminar = st.selectbox("Seleccionar usuario", df_users['usuario'].tolist())
                    
                    if st.form_submit_button("Eliminar Usuario", type="primary"):
                        try:
                            cursor = conn.cursor()
                            
                            cursor.execute(f"""
                                DECLARE @sql NVARCHAR(MAX) = N'';
                                SELECT @sql += N'ALTER ROLE [' + r.name + '] DROP MEMBER [{usuario_eliminar}];'
                                FROM sys.database_role_members drm
                                JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
                                JOIN sys.database_principals u ON drm.member_principal_id = u.principal_id
                                WHERE u.name = '{usuario_eliminar}';
                                EXEC sp_executesql @sql;
                            """)
                            
                            cursor.execute(f"""
                                IF EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '{usuario_eliminar}')
                                DROP USER [{usuario_eliminar}]
                            """)
                            
                            cursor.execute(f"""
                                IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = '{usuario_eliminar}')
                                DROP LOGIN [{usuario_eliminar}]
                            """)
                            
                            conn.commit()
                            st.success(f"✅ Usuario '{usuario_eliminar}' eliminado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al eliminar usuario: {str(e)}")
                else:
                    st.info("No hay usuarios para eliminar")
        
        st.divider()
        
        # Modificar roles de usuario
        st.markdown("### 🔄 Modificar Roles de Usuario")
        if not df_users.empty:
            col_mod1, col_mod2 = st.columns(2)
            
            with col_mod1:
                usuario_modificar = st.selectbox("Usuario", df_users['usuario'].tolist(), key="usuario_mod")
            
            with col_mod2:
                accion = st.selectbox("Acción", ["Agregar a rol", "Quitar de rol"], key="accion_mod")
            
            rol_modificar = st.selectbox("Rol", 
                roles_disponibles['name'].tolist() if not roles_disponibles.empty else ["rol_analista", "rol_admin"], 
                key="rol_mod")
            
            if st.button("Aplicar Cambio", type="primary"):
                try:
                    cursor = conn.cursor()
                    if accion == "Agregar a rol":
                        cursor.execute(f"ALTER ROLE [{rol_modificar}] ADD MEMBER [{usuario_modificar}]")
                        st.success(f"✅ Usuario '{usuario_modificar}' agregado al rol '{rol_modificar}'")
                    else:
                        cursor.execute(f"ALTER ROLE [{rol_modificar}] DROP MEMBER [{usuario_modificar}]")
                        st.success(f"✅ Usuario '{usuario_modificar}' removido del rol '{rol_modificar}'")
                    conn.commit()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        # Cambiar contraseña
        st.markdown("### 🔑 Cambiar Contraseña")
        if not df_users.empty:
            col_pass1, col_pass2 = st.columns(2)
            
            with col_pass1:
                usuario_pass = st.selectbox("Usuario", df_users['usuario'].tolist(), key="usuario_pass")
            
            with col_pass2:
                nueva_pass = st.text_input("Nueva contraseña", type="password", key="nueva_pass")
            
            if st.button("Cambiar Contraseña", type="primary"):
                if nueva_pass:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(f"ALTER LOGIN [{usuario_pass}] WITH PASSWORD = '{nueva_pass}'")
                        conn.commit()
                        st.success(f"✅ Contraseña de '{usuario_pass}' actualizada")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Ingresa una contraseña válida")
    
    # ==========================================
    # TAB 2: BACKUPS MEJORADO CON HISTORIAL
    # ==========================================
    with tab2:
        st.subheader("💾 Gestión Completa de Backups y Restauración")
        
        # Crear tabla de historial si no existe
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'backup_history')
            CREATE TABLE backup_history (
                id INT IDENTITY(1,1) PRIMARY KEY,
                backup_type VARCHAR(50),
                backup_path VARCHAR(500),
                backup_date DATETIME DEFAULT GETDATE(),
                file_size_mb DECIMAL(10,2),
                status VARCHAR(20),
                usuario VARCHAR(100),
                notas NVARCHAR(MAX)
            )
        """)
        conn.commit()
        
        # Mostrar historial de backups
        st.markdown("### 📋 Historial de Backups")
        df_backups = pd.read_sql(text("""
            SELECT TOP 50 
                id,
                backup_type AS tipo,
                backup_path AS ruta,
                backup_date AS fecha,
                file_size_mb AS tamaño_mb,
                status AS estado,
                usuario,
                notas
            FROM backup_history
            ORDER BY backup_date DESC
        """), engine)
        
        if not df_backups.empty:
            st.dataframe(df_backups, use_container_width=True, hide_index=True)
            
            # Estadísticas de backups
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                total_backups = len(df_backups)
                st.metric("Total Backups", total_backups)
            with col_stat2:
                hoy = pd.Timestamp(datetime.now().date())
                backups_hoy = len(df_backups[df_backups['fecha'] >= hoy])
                st.metric("Backups Hoy", backups_hoy)
            with col_stat3:
                espacio_total = df_backups['tamaño_mb'].sum()
                # Manejo seguro por si hay valores nulos en el tamaño
                espacio_total = 0.0 if pd.isna(espacio_total) else espacio_total
                st.metric("Espacio Total", f"{espacio_total:.2f} MB")
            with col_stat4:
                ultimo_backup = df_backups['fecha'].max()
                st.metric("Último Backup", ultimo_backup.strftime("%Y-%m-%d %H:%M") if pd.notna(ultimo_backup) else "N/A")
        else:
            st.info("ℹ️ No hay backups registrados aún")
        
        st.divider()
        
        # Crear nuevo backup
        st.markdown("### ➕ Crear Nuevo Backup")
        col_backup1, col_backup2 = st.columns(2)
        
        with col_backup1:
            backup_type = st.selectbox("Tipo de Backup", 
                ["Completo (Full)", "Diferencial (Diff)", "Log Transaccional"])
            
            notas_backup = st.text_area("Notas (opcional)", 
                placeholder="Describe el motivo del backup...")
        
        with col_backup2:
            st.info("💡 El backup se guardará en: `/var/opt/mssql/backups/`")
            
            if st.button("🚀 Ejecutar Backup Ahora", type="primary"):
                try:
                    backup_conn = get_sql_connection()
                    backup_conn.autocommit = True
                    cursor = backup_conn.cursor()

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"/var/opt/mssql/backups/CC_Client_{backup_type}_{timestamp}.bak"

                    if backup_type == "Completo (Full)":
                        cursor.execute(f"""
                            BACKUP DATABASE CC_Client
                            TO DISK = '{backup_path}'
                            WITH FORMAT, INIT, NAME = 'Full Backup CC_Client', COMPRESSION
                        """)
                    elif backup_type == "Diferencial (Diff)":
                        cursor.execute(f"""
                            BACKUP DATABASE CC_Client
                            TO DISK = '{backup_path}'
                            WITH DIFFERENTIAL, NAME = 'Differential Backup CC_Client', COMPRESSION
                        """)
                    else:
                        backup_path = f"/var/opt/mssql/backups/CC_Client_Log_{timestamp}.trn"
                        cursor.execute(f"""
                            BACKUP LOG CC_Client
                            TO DISK = '{backup_path}'
                            WITH NAME = 'Log Backup CC_Client', COMPRESSION
                        """)

                    cursor.execute(f"""
                        INSERT INTO backup_history (backup_type, backup_path, status, usuario, notas)
                        VALUES ('{backup_type}', '{backup_path}', 'Completado', '{st.session_state.login_user}', '{notas_backup}')
                    """)
                    backup_conn.close() # Cerramos la conexión específica

                    st.success(f"✅ Backup {backup_type} completado exitosamente")
                    st.info(f"📁 Archivo: {backup_path}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al ejecutar backup: {str(e)}")
        
        st.divider()
        
        # Programar backups automáticos
        st.markdown("### ⏰ Programación de Backups Automáticos")
        
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'backup_schedule')
            CREATE TABLE backup_schedule (
                id INT IDENTITY(1,1) PRIMARY KEY,
                schedule_name VARCHAR(100),
                backup_type VARCHAR(50),
                frequency VARCHAR(50),
                time_of_day TIME,
                enabled BIT DEFAULT 1,
                created_date DATETIME DEFAULT GETDATE(),
                last_run DATETIME NULL,
                next_run DATETIME NULL
            )
        """)
        conn.commit()
        
        df_schedules = pd.read_sql(text("""
            SELECT 
                id,
                schedule_name AS nombre,
                backup_type AS tipo,
                frequency AS frecuencia,
                time_of_day AS hora,
                CASE WHEN enabled = 1 THEN 'Activo' ELSE 'Inactivo' END AS estado,
                last_run AS ultima_ejecucion,
                next_run AS proxima_ejecucion
            FROM backup_schedule
            ORDER BY enabled DESC, schedule_name
        """), engine)
        
        if not df_schedules.empty:
            st.dataframe(df_schedules, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ No hay programaciones configuradas")
        
        with st.expander("➕ Crear Nueva Programación"):
            with st.form("crear_schedule_form"):
                schedule_name = st.text_input("Nombre de la programación")
                sched_backup_type = st.selectbox("Tipo de Backup", 
                    ["Completo (Full)", "Diferencial (Diff)", "Log Transaccional"], key="sched_type")
                frequency = st.selectbox("Frecuencia", 
                    ["Diario", "Semanal", "Mensual", "Cada 6 horas", "Cada 12 horas"])
                time_of_day = st.time_input("Hora de ejecución", value=datetime.strptime("02:00", "%H:%M").time())
                
                if st.form_submit_button("Crear Programación"):
                    if schedule_name:
                        try:
                            cursor.execute(f"""
                                INSERT INTO backup_schedule (schedule_name, backup_type, frequency, time_of_day)
                                VALUES ('{schedule_name}', '{sched_backup_type}', '{frequency}', '{time_of_day}')
                            """)
                            conn.commit()
                            st.success(f"✅ Programación '{schedule_name}' creada")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    else:
                        st.warning("⚠️ Ingresa un nombre válido")
        
        st.divider()
        
        # Restaurar backup
        st.markdown("### 🔄 Restaurar Backup")
        
        if not df_backups.empty:
            with st.form("restaurar_form"):
                backup_seleccionado = st.selectbox("Seleccionar backup a restaurar", 
                    df_backups.apply(lambda x: f"{x['id']} - {x['tipo']} - {x['fecha']} ({x['tamaño_mb']} MB)", axis=1).tolist())
                
                modo_restauracion = st.radio("Modo de restauración",
                    ["Sobrescribir base de datos actual", "Restaurar con nuevo nombre"],
                    help="⚠️ Sobrescribir reemplazará todos los datos actuales")
                
                nuevo_nombre = None
                if modo_restauracion == "Restaurar con nuevo nombre":
                    nuevo_nombre = st.text_input("Nombre de la nueva base de datos", 
                        placeholder="CC_Client_Restaurada")
                
                confirmar = st.checkbox("Confirmo que entiendo los riesgos de esta operación")
                
                if st.form_submit_button("🔄 Restaurar Backup", type="primary"):
                    if confirmar:
                        try:
                            backup_id = int(backup_seleccionado.split(' - ')[0])
                            backup_info = df_backups[df_backups['id'] == backup_id].iloc[0]

                            # ✅ CORREGIDO: Conexión independiente con autocommit para RESTORE
                            restore_conn = get_sql_connection()
                            restore_conn.autocommit = True
                            cursor = restore_conn.cursor()

                            cursor.execute("ALTER DATABASE CC_Client SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                            if backup_info['tipo'] == "Completo (Full)":
                                if modo_restauracion == "Sobrescribir base de datos actual":
                                    cursor.execute(f"""
                                        RESTORE DATABASE CC_Client
                                        FROM DISK = '{backup_info['ruta']}'
                                        WITH REPLACE, RECOVERY
                                    """)
                                else:
                                    cursor.execute(f"""
                                        RESTORE DATABASE [{nuevo_nombre}]
                                        FROM DISK = '{backup_info['ruta']}'
                                        WITH MOVE 'CC_Client' TO '/var/opt/mssql/data/{nuevo_nombre}.mdf',
                                             MOVE 'CC_Client_log' TO '/var/opt/mssql/data/{nuevo_nombre}_log.ldf',
                                             RECOVERY
                                    """)
                            else:
                                st.warning("⚠️ Solo se pueden restaurar backups completos directamente")

                            cursor.execute("ALTER DATABASE CC_Client SET MULTI_USER")
                            restore_conn.close()
                     
                            st.success("✅ Restauración completada exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al restaurar: {str(e)}")
                            try:
                               # Intentar dejar la BD en multi_usuario en caso de fallo
                               fail_conn = get_sql_connection()
                               fail_conn.autocommit = True
                               fail_cursor = fail_conn.cursor()
                               fail_cursor.execute("ALTER DATABASE CC_Client SET MULTI_USER")
                               fail_conn.close()
                            except:
                                pass
                    else:
                        st.warning("⚠️ Debes confirmar la operación")
        else:
            st.info("ℹ️ No hay backups disponibles para restaurar")
    
    # ==========================================
    # TAB 3: ESTADO DE SERVICIOS MEJORADO
    # ==========================================
    with tab3:
        st.subheader("❤️ Monitoreo y Control de Servicios")
        
        st.markdown("### 🖥️ Información del Servidor SQL Server")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown("#### 📊 Estado del Servicio")
            try:
                server_info = pd.read_sql(text("""
                    SELECT 
                         CAST(SERVERPROPERTY('ServerName') AS VARCHAR(128)) AS servidor,
                         CAST(SERVERPROPERTY('ProductVersion') AS VARCHAR(128)) AS version,
                         CAST(SERVERPROPERTY('ProductLevel') AS VARCHAR(128)) AS nivel,
                         CAST(SERVERPROPERTY('Edition') AS VARCHAR(128)) AS edicion,
                         CAST(SERVERPROPERTY('EngineEdition') AS INT) AS motor,
                         CAST(@@VERSION AS VARCHAR(8000)) AS version_completa
                """), engine)
                st.success("✅ SQL Server Activo")
                st.info(f"**Servidor:** {server_info.iloc[0]['servidor']}")
                st.info(f"**Versión:** {server_info.iloc[0]['version']}")
                st.info(f"**Edición:** {server_info.iloc[0]['edicion']}")
                with st.expander("Ver versión completa"):
                    st.code(server_info.iloc[0]['version_completa'], language="text")
            except Exception as e:
                    st.error(f"❌ Error al obtener información: {str(e)}")
        
        with col_info2:
            st.markdown("#### 📈 Recursos del Sistema")
            try:
                recursos = pd.read_sql(text("""
                    SELECT 
                        cpu_count AS cpus,
                        hyperthread_ratio AS hilos_por_cpu,
                        physical_memory_kb / 1024 AS memoria_total_mb,
                        committed_kb / 1024 AS memoria_usada_mb,
                        (committed_kb * 100.0 / physical_memory_kb) AS porcentaje_uso
                    FROM sys.dm_os_sys_info
                """), engine)
                
                if not recursos.empty:
                    st.metric("CPUs Totales", recursos.iloc[0]['cpus'])
                    st.metric("Memoria Total", f"{recursos.iloc[0]['memoria_total_mb']:.0f} MB")
                    st.metric("Memoria Usada", f"{recursos.iloc[0]['memoria_usada_mb']:.0f} MB")
                    
                    porcentaje = recursos.iloc[0]['porcentaje_uso']
                    st.progress(porcentaje / 100)
                    st.caption(f"Uso de memoria: {porcentaje:.1f}%")
            except Exception as e:
                st.error(f"❌ Error al obtener recursos: {str(e)}")
        
        st.divider()
        
        st.markdown("### 📊 Métricas de la Base de Datos")
        
        try:
            db_metrics = pd.read_sql(text("""
                SELECT 
                 (SELECT COUNT(*) FROM dim_cliente) AS total_clientes,
                 (SELECT COUNT(*) FROM historial_pagos) AS total_historial,
                 (SELECT COUNT(*) FROM riesgo_crediticio) AS total_riesgo,
                 (SELECT COUNT(*) FROM auditoria_cambios) AS total_auditorias,
                 (SELECT COUNT(*) FROM sys.tables) AS total_tablas,
                 (SELECT COUNT(*) FROM sys.indexes WHERE type > 0) AS total_indices,
                 (SELECT SUM(ISNULL(reserved_page_count, 0)) * 8 / 1024 FROM sys.dm_db_partition_stats WHERE index_id IN (0,1)) AS espacio_total_mb
            """), engine)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("👥 Clientes", f"{int(db_metrics.iloc[0]['total_clientes']):,}")
                st.metric("📜 Historial", f"{int(db_metrics.iloc[0]['total_historial']):,}")
            with col_m2:
                st.metric("⚠️ Riesgo", f"{int(db_metrics.iloc[0]['total_riesgo']):,}")
                st.metric("🔒 Auditorías", f"{int(db_metrics.iloc[0]['total_auditorias']):,}")
            with col_m3:
                st.metric("📋 Tablas", int(db_metrics.iloc[0]['total_tablas']))
                st.metric("📇 Índices", int(db_metrics.iloc[0]['total_indices']))
            with col_m4:
                st.metric("💾 Espacio Total", f"{db_metrics.iloc[0]['espacio_total_mb']:.2f} MB")
                
        except Exception as e:
            st.error(f"❌ Error al obtener métricas: {str(e)}")
        
        st.divider()
        
        st.markdown("### 🔌 Conexiones Activas")
        
        try:
            conexiones = pd.read_sql(text("""
                SELECT TOP 20
                    session_id,
                    login_name,
                    host_name,
                    program_name,
                    status,
                    cpu_time,
                    memory_usage,
                    login_time,
                    last_request_start_time
                FROM sys.dm_exec_sessions
                WHERE is_user_process = 1
                ORDER BY login_time DESC
            """), engine)
            
            if not conexiones.empty:
                st.dataframe(conexiones, use_container_width=True, hide_index=True)
                st.info(f"Total de conexiones activas: {len(conexiones)}")
            else:
                st.info("ℹ️ No hay conexiones activas")
        except Exception as e:
            st.error(f"❌ Error al obtener conexiones: {str(e)}")
        
        st.divider()
        
        st.markdown("### 🎛️ Control de Servicios")
        
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        
        with col_ctrl1:
            st.markdown("#### 🔄 Reiniciar Servicio")
            if st.button("Reiniciar SQL Server", type="secondary"):
                st.warning("⚠️ Esta operación requiere permisos de administrador del sistema")
                st.info("💡 Ejecuta manualmente: `sudo systemctl restart mssql-server`")
        
        with col_ctrl2:
            st.markdown("#### 🛑 Detener Servicio")
            if st.button("Detener SQL Server", type="secondary"):
                st.warning("⚠️ Esta operación detendrá todos los servicios")
                st.info("💡 Ejecuta manualmente: `sudo systemctl stop mssql-server`")
        
        with col_ctrl3:
            st.markdown("#### ▶️ Iniciar Servicio")
            if st.button("Iniciar SQL Server", type="secondary"):
                st.info("💡 Ejecuta manualmente: `sudo systemctl start mssql-server`")
        
        st.divider()
        
        st.markdown("### 🍃 Estado de MongoDB")
        try:
            mongo_client = get_mongo_connection()
            if mongo_client:
                server_info = mongo_client.server_info()
                col_mongo1, col_mongo2 = st.columns(2)                   
                with col_mongo1:
                    st.success("✅ MongoDB Conectado")
                    st.info(f"**Versión:** {server_info.get('version', 'Desconocida')}")
                    
                with col_mongo2:                        
                    db = mongo_client['ML_Experiments']
                    colecciones = db.list_collection_names()
                    st.info(f"**Colecciones:** {len(colecciones)}")
                    for col in colecciones:
                        count = db[col].count_documents({})
                        st.caption(f"• {col}: {count} documentos")
                
                st.markdown("---")
                st.markdown("#### 📊 Registro de Experimentos de Machine Learning")
                if 'registro_experimentos' in colecciones:                       
                    collection = db['registro_experimentos']
                    # Obtener los últimos 10 experimentos ordenados por fecha descendente
                    experimentos = list(collection.find().sort("fecha", -1).limit(10))
                    if experimentos:                             # Convertir a lista de diccionarios para mostrar en DataFrame
                        datos_exp = []
                        for exp in experimentos:
                            datos_exp.append({
                                "Fecha": str(exp.get("fecha", "N/A"))[:19], # Recortar para formato limpio
                                "Algoritmo": exp.get("algoritmo", "N/A"),
                                "Clusters": exp.get("hiperparametros", {}).get("n_clusters", "N/A"),
                                "Silhouette": exp.get("metricas", {}).get("silhouette_score", "N/A"),
                                "Inercia": exp.get("metricas", {}).get("inertia", "N/A"),
                                "Registros": exp.get("metricas", {}).get("total_registros_procesados", "N/A")
                            })
                        df_exp= pd.DataFrame(datos_exp)
                        st.dataframe(df_exp, use_container_width=True, hide_index=True)
                        # Expander para ver el documento JSON completo                           
                        with st.expander("🔍 Ver detalles completos (JSON) de los experimentos"):
                            for exp in experimentos:
                                st.json(exp)
                    else:
                        st.info("ℹ️ No hay experimentos registrados aún en la colección 'registro_experimentos'.")
                else:
                    st.warning("⚠️ La colección 'registro_experimentos' no existe. Ejecuta el notebook `K-Means.ipynb` para generar y guardar los datos.")
                mongo_client.close()                 
            else:
                st.error("❌ No se pudo establecer conexión con MongoDB.")
        except Exception as e:
            st.error(f"❌ Error al obtener información de MongoDB: {str(e)}")
        # ==========================================
    # TAB 4: TERMINAL SQL
    # ==========================================
    with tab4:
        st.subheader("⌨️ Terminal SQL Interactiva")
        
        st.warning("⚠️ Usa esta herramienta con precaución. Solo para usuarios con permisos de administrador.")
        
        st.markdown("### ⚡ Consultas Rápidas")
        
        quick_queries = {
            "Ver todas las tablas": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
            "Contar registros por tabla": """
                SELECT t.name AS tabla, p.rows AS registros
                FROM sys.tables t
                INNER JOIN sys.partitions p ON t.object_id = p.OBJECT_ID
                WHERE p.index_id IN (0,1)
                ORDER BY p.rows DESC
            """,
            "Ver triggers": "SELECT name, parent_id, is_disabled FROM sys.triggers",
            "Ver roles": "SELECT name FROM sys.database_principals WHERE type = 'R'",
            "Ver índices": """
                SELECT 
                    t.name AS tabla,
                    i.name AS indice,
                    i.type_desc AS tipo
                FROM sys.indexes i
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                WHERE i.name IS NOT NULL
                ORDER BY t.name, i.name
            """,
            "Ver espacio usado por tabla": """
                SELECT 
                    t.name AS tabla,
                    SUM(p.rows) AS filas,
                    SUM(a.total_pages) * 8 / 1024 AS espacio_mb
                FROM sys.tables t
                INNER JOIN sys.partitions p ON t.object_id = p.object_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE p.index_id IN (0,1)
                GROUP BY t.name
                ORDER BY espacio_mb DESC
            """
        }
        
        selected_query = st.selectbox("Selecciona una consulta rápida:", list(quick_queries.keys()))
        
        if st.button("▶️ Ejecutar Consulta Rápida"):
            try:
                df = pd.read_sql(text(quick_queries[selected_query]), engine)
                st.success(f"✅ {len(df)} registros")
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        st.markdown("### 📝 Editor SQL Avanzado")
        
        sql_code = st.text_area(
            "Escribe tu consulta SQL:",
            height=200,
            placeholder="SELECT TOP 100 * FROM dim_cliente..."
        )
        
        col_exec1, col_exec2 = st.columns([3, 1])
        
        with col_exec1:
            if st.button("🚀 Ejecutar Consulta", type="primary"):
                if sql_code.strip():
                    try:
                        with st.expander("📜 SQL a ejecutar"):
                            st.code(sql_code, language='sql')
                        
                        if sql_code.strip().upper().startswith(('SELECT', 'WITH', 'EXEC')):
                            df_result = pd.read_sql(text(sql_code), engine)
                            st.success(f"✅ Consulta ejecutada: {len(df_result)} registros")
                            st.dataframe(df_result, use_container_width=True, hide_index=True)
                        else:
                            cursor = conn.cursor()
                            cursor.execute(sql_code)
                            conn.commit()
                            rows_affected = cursor.rowcount
                            st.success(f"✅ Operación ejecutada: {rows_affected} filas afectadas")
                    except Exception as e:
                        st.error(f"❌ Error al ejecutar consulta: {str(e)}")
                else:
                    st.warning("⚠️ Por favor escribe una consulta SQL")
        
        with col_exec2:
            if st.button("🧹 Limpiar"):
                st.rerun()
    
    conn.close()
    
except Exception as e:
    st.error(f"❌ Error general: {str(e)}")