import sys
from pathlib import Path
import importlib

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Agregar el directorio Streamlit al path para importar db_connections
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connections import get_sql_connection
import auth as auth_module
auth_module = importlib.reload(auth_module)


st.set_page_config(
    page_title="Inicio Auditorías",
    page_icon="🔎",
    layout="wide",
)

st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0d1117 100%);
    }
    .page-header {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .info-card {
        background: rgba(30, 41, 59, 0.88);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }
    .stMarkdown, .stDataFrame, .stTable {
        color: #e2e8f0;
    }
    h1, h2, h3, h4 {
        color: #f1f5f9 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

auth_module.require_login()

with st.sidebar:
    st.markdown("### 🔐 Sesión")
    st.caption(f"Usuario: {st.session_state.login_user}")
    st.caption(f"Perfil: {st.session_state.login_profile}")
    auth_module.render_role_menu()
    auth_module.logout_button()


def leer_uno(engine, query_sql, params=None):
    df = pd.read_sql(text(query_sql), engine, params=params or {})
    return df.iloc[0] if not df.empty else None


def existe_tabla(engine, schema_name, table_name):
    query_sql = """
        SELECT CASE
            WHEN EXISTS (
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = :schema_name
                  AND TABLE_NAME = :table_name
            ) THEN 1 ELSE 0
        END AS existe
    """
    fila = leer_uno(engine, query_sql, {"schema_name": schema_name, "table_name": table_name})
    return bool(int(fila["existe"])) if fila is not None else False


def existe_trigger(engine, trigger_name):
    query_sql = """
        SELECT CASE
            WHEN EXISTS (
                SELECT 1
                FROM sys.triggers
                WHERE name = :trigger_name
            ) THEN 1 ELSE 0
        END AS existe
    """
    fila = leer_uno(engine, query_sql, {"trigger_name": trigger_name})
    return bool(int(fila["existe"])) if fila is not None else False


st.markdown('<p class="page-header">🔎 Inicio de Auditorías</p>', unsafe_allow_html=True)
st.caption("Página de diagnóstico para verificar acceso, trigger de auditoría y registros de migración.")

col_info_1, col_info_2 = st.columns([2, 1])
with col_info_1:
    st.markdown(
        """
        <div class="info-card">
            <strong>Objetivo:</strong> validar si la base de datos expone correctamente la tabla de auditoría,
            el trigger y el usuario con el que se conecta Streamlit.
            Si no ves auditorías, esta página te ayuda a distinguir si el problema es de datos, permisos o estructura.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_info_2:
    if st.button("🔄 Actualizar diagnóstico", use_container_width=True):
        st.rerun()

try:
    conn = get_sql_connection()
    engine = create_engine("mssql+pyodbc://", creator=lambda: conn, echo=False)

    usuario_sql = leer_uno(
        engine,
        """
        SELECT
            SUSER_SNAME() AS login_actual,
            SYSTEM_USER AS system_user,
            USER_NAME() AS db_user,
            ORIGINAL_LOGIN() AS original_login,
            IS_SRVROLEMEMBER('sysadmin') AS es_sysadmin,
            COALESCE(IS_MEMBER('rol_admin'), 0) AS es_rol_admin,
            COALESCE(IS_MEMBER('rol_analista'), 0) AS es_rol_analista
        """,
    )

    total_auditoria = 0
    ultimo_registro = "Sin registros"
    conteo_insert = 0
    conteo_update = 0
    conteo_delete = 0

    tabla_auditoria_ok = existe_tabla(engine, "dbo", "auditoria_cambios")
    trigger_ok = existe_trigger(engine, "trg_Auditoria_Riesgo")

    if tabla_auditoria_ok:
        resumen_auditoria = leer_uno(
            engine,
            """
            SELECT
                COUNT(*) AS total_auditoria,
                SUM(CASE WHEN operacion = 'I' THEN 1 ELSE 0 END) AS total_inserts,
                SUM(CASE WHEN operacion = 'U' THEN 1 ELSE 0 END) AS total_updates,
                SUM(CASE WHEN operacion = 'D' THEN 1 ELSE 0 END) AS total_deletes,
                MAX(fecha_cambio) AS ultimo_registro
            FROM dbo.auditoria_cambios
            """,
        )

        if resumen_auditoria is not None:
            total_auditoria = int(resumen_auditoria["total_auditoria"] or 0)
            conteo_insert = int(resumen_auditoria["total_inserts"] or 0)
            conteo_update = int(resumen_auditoria["total_updates"] or 0)
            conteo_delete = int(resumen_auditoria["total_deletes"] or 0)
            ultimo_registro = str(resumen_auditoria["ultimo_registro"])

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Usuario SQL", usuario_sql["login_actual"] if usuario_sql is not None else "Desconocido")
    with col_m2:
        st.metric("Tabla auditoría", "OK" if tabla_auditoria_ok else "Falta")
    with col_m3:
        st.metric("Trigger", "OK" if trigger_ok else "Falta")
    with col_m4:
        st.metric("Total auditorías", f"{total_auditoria:,}")

    st.divider()

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown("### 👤 Usuario y roles detectados")
        if usuario_sql is not None:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "login_actual": usuario_sql["login_actual"],
                            "system_user": usuario_sql["system_user"],
                            "db_user": usuario_sql["db_user"],
                            "original_login": usuario_sql["original_login"],
                            "es_sysadmin": usuario_sql["es_sysadmin"],
                            "es_rol_admin": usuario_sql["es_rol_admin"],
                            "es_rol_analista": usuario_sql["es_rol_analista"],
                        }
                    ]
                ),
                use_container_width=True,
            )
        else:
            st.error("No fue posible leer el usuario actual de SQL Server.")

    with col_u2:
        st.markdown("### 🧭 Estado de auditoría")
        st.write(f"**Último registro:** {ultimo_registro}")
        st.write(f"**Inserciones:** {conteo_insert}")
        st.write(f"**Actualizaciones:** {conteo_update}")
        st.write(f"**Eliminaciones:** {conteo_delete}")

        if not tabla_auditoria_ok:
            st.error("La tabla dbo.auditoria_cambios no existe en la base activa.")
        elif total_auditoria == 0:
            st.warning("La tabla existe, pero todavía no hay movimientos registrados.")
        elif not trigger_ok:
            st.warning("Hay auditorías, pero el trigger trg_Auditoria_Riesgo no está visible o no existe.")
        else:
            st.success("La estructura de auditoría parece estar correcta.")

    st.divider()

    st.markdown("### 📋 Auditorías recientes")

    if tabla_auditoria_ok:
        filtro_operacion = st.selectbox(
            "Filtrar por operación:",
            ["Todas", "I", "U", "D"],
            index=0,
        )

        query_recientes = """
            SELECT TOP 50
                id_auditoria,
                tabla_afectada,
                operacion,
                id_registro_afectado,
                usuario,
                fecha_cambio,
                datos_antes,
                datos_despues
            FROM dbo.auditoria_cambios
        """

        params = {}
        if filtro_operacion != "Todas":
            query_recientes += " WHERE operacion = :operacion"
            params["operacion"] = filtro_operacion

        query_recientes += " ORDER BY fecha_cambio DESC, id_auditoria DESC"

        df_recientes = pd.read_sql(text(query_recientes), engine, params=params)

        if df_recientes.empty:
            st.info("No hay registros de auditoría para mostrar con el filtro actual.")
        else:
            st.dataframe(df_recientes, use_container_width=True)

            st.bar_chart(
                df_recientes["operacion"].value_counts().rename_axis("operacion").to_frame("cantidad")
            )
    else:
        st.info("Primero debes crear la tabla auditoria_cambios y el trigger en la base de datos activa.")

    conn.close()

except Exception as e:
    st.error(f"❌ No fue posible cargar el diagnóstico de auditorías: {str(e)}")
