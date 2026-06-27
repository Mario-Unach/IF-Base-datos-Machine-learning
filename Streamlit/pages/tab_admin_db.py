import streamlit as st
import pandas as pd
from Streamlit.db_connections import get_sql_connection

def show_admin_db_tab():
    st.header("Administración, Auditoría y DRP (SQL Server)")
    
    conn = get_sql_connection()
    if not conn:
        st.warning("No hay conexión a SQL Server.")
        return

    tab_sql, tab_logs, tab_backup = st.tabs(["Ejecutar SQL", "Ver Logs (Triggers)", "Copias de Seguridad"])
    
    with tab_sql:
        st.subheader("Terminal SQL Interactiva")
        query = st.text_area("Ingresa tu consulta SQL:", height=150, placeholder="SELECT TOP 10 * FROM Clientes;")
        if st.button("Ejecutar Consulta"):
            try:
                df = pd.read_sql(query, conn)
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error en la consulta: {e}")
                
    with tab_logs:
        st.subheader("🛡️ Auditoría de Cambios (Histórico)")
        st.info("Leyendo tabla de auditoría generada por Triggers...")
        try:
            # Asume que creaste una tabla llamada Audit_Logs con tus triggers
            df_logs = pd.read_sql("SELECT TOP 50 * FROM Audit_Logs ORDER BY ChangeDate DESC", conn)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"No se encontró la tabla de logs o está vacía: {e}")
            
    with tab_backup:
        st.subheader("💾 Plan de Recuperación ante Desastres (DRP)")
        st.markdown("Genera un backup manual de la base de datos directamente desde el dashboard.")
        backup_path = st.text_input("Ruta de destino en el servidor SQL:", "C:\\Backups\\CreditCardDefault.bak")
        if st.button("Iniciar Backup Completo"):
            backup_query = f"""
            BACKUP DATABASE CreditCardDefault 
            TO DISK = '{backup_path}'
            WITH FORMAT, MEDIANAME = 'SQLServerBackups', NAME = 'Full Backup';
            """
            try:
                cursor = conn.cursor()
                cursor.execute(backup_query)
                conn.commit()
                st.success("✅ Backup iniciado correctamente en el servidor.")
            except Exception as e:
                st.error(f"Error al ejecutar backup: {e}")