import streamlit as st

from db_connections import get_sql_connection

AUTH_PROFILES = {
    "Administrador": {
        "username": "admin",
        "password": "ContraseñaSegura456!",
        "role": "rol_admin",
    },
    "Analista": {
        "username": "analista",
        "password": "ContraseñaSegura123!",
        "role": "rol_analista",
    },
    "SA": {
        "username": "sa",
        "password": "Flaquis2026*",
        "role": "sysadmin",
    },
}

ROLE_PAGES = {
    "SA": [
        ("CreditFlow Analytics", "app.py"),
        ("Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
        ("Administración BD", "pages/3_Administracion_BD.py"),
    ],
    "Administrador": [
        ("CreditFlow Analytics", "app.py"),
        ("Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
        ("Administración BD", "pages/3_Administracion_BD.py"),
    ],
    "Analista": [
        ("CreditFlow Analytics", "app.py"),
        ("Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
    ],
}


def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_user" not in st.session_state:
        st.session_state.login_user = None
    if "login_role" not in st.session_state:
        st.session_state.login_role = None


def login_panel():
    init_session_state()

    st.markdown("### 🔐 Inicio de sesión")
    profile_name = st.selectbox("Perfil", list(AUTH_PROFILES.keys()), key="auth_profile")
    username = st.text_input("Usuario", value=AUTH_PROFILES[profile_name]["username"], key="auth_username")
    password = st.text_input("Contraseña", type="password", key="auth_password")

    col_login, col_clear = st.columns(2)
    with col_login:
        if st.button("Ingresar", type="primary", use_container_width=True):
            expected = AUTH_PROFILES[profile_name]
            if username.strip() != expected["username"] or password != expected["password"]:
                st.error("Credenciales inválidas.")
            else:
                try:
                    conn = get_sql_connection(username=expected["username"], password=expected["password"])
                    conn.close()
                    st.session_state.authenticated = True
                    st.session_state.login_user = expected["username"]
                    st.session_state.login_role = expected["role"]
                    st.session_state.login_profile = profile_name
                    st.success(f"Sesión iniciada como {profile_name}.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"No se pudo validar la conexión: {exc}")

    with col_clear:
        if st.button("Limpiar", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.login_user = None
            st.session_state.login_role = None
            st.session_state.login_profile = None
            st.rerun()


def require_login():
    init_session_state()
    if not st.session_state.authenticated:
        st.warning("Debes iniciar sesión para acceder a esta página.")
        login_panel()
        st.stop()


def logout_button():
    init_session_state()
    if st.session_state.authenticated and st.sidebar.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.session_state.login_user = None
        st.session_state.login_role = None
        st.session_state.login_profile = None
        st.rerun()


def render_role_menu():
    init_session_state()
    profile = st.session_state.login_profile
    pages = ROLE_PAGES.get(profile, ROLE_PAGES["Analista"])

    st.markdown("### 🧭 Menú del sistema")
    for label, path in pages:
        st.page_link(path, label=label)


def require_role(*allowed_profiles):
    init_session_state()
    if not st.session_state.authenticated:
        st.warning("Debes iniciar sesión para acceder a esta página.")
        login_panel()
        st.stop()

    if allowed_profiles and st.session_state.login_profile not in allowed_profiles:
        st.error("No tienes permisos para acceder a esta sección.")
        st.stop()
