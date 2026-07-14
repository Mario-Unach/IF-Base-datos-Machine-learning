import streamlit as st
from db_connections import get_sql_connection

AUTH_PROFILES = {
    "Administrador": {
        "username": "admin",
        "password": "ContraseñaSegura456!",
        "role": "Administrador",  # ✅ Usar el mismo nombre que en AUTH_PROFILES
    },
    "Analista": {
        "username": "analista", 
        "password": "ContraseñaSegura123!",
        "role": "Analista",
    },
    "SA": {
        "username": "sa",
        "password": "Flaquis2026*",
        "role": "SA",
    },
}

# PÁGINAS POR ROL - Usar rutas relativas correctas
ROLE_PAGES = {
    "SA": [
        ("🏠 CreditFlow Analytics", "app.py"),
        ("Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("📊 Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("🤖 Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
        ("🛠️ Administración BD", "pages/3_Administracion_BD.py"),
    ],
    "Administrador": [
        ("🏠 CreditFlow Analytics", "app.py"),
        ("Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("📊 Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("🤖 Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
        ("🛠️ Administración BD", "pages/3_Administracion_BD.py"),
    ],
    "Analista": [
        ("🏠 CreditFlow Analytics", "app.py"),
        ("🔎 Inicio Auditorías", "pages/0_Inicio_Auditorias.py"),
        ("📊 Dataset & Arquitectura", "pages/1_Dataset_Arquitectura.py"),
        ("🤖 Modelo ML & Predicciones", "pages/2_Modelo_ML_Predicciones.py"),
    ],
}

def init_session_state():
    """Inicializa variables de sesión si no existen"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_user" not in st.session_state:
        st.session_state.login_user = None
    if "login_profile" not in st.session_state:
        st.session_state.login_profile = None

def login_panel():
    """Panel de inicio de sesión"""
    init_session_state()
    st.markdown("### 🔐 Inicio de sesión")
    
    profile_name = st.selectbox(
        "Perfil", 
        list(AUTH_PROFILES.keys()), 
        key="auth_profile_select"
    )
    
    username = st.text_input(
        "Usuario", 
        value=AUTH_PROFILES[profile_name]["username"], 
        key="auth_username_input"
    )
    
    password = st.text_input(
        "Contraseña", 
        type="password", 
        key="auth_password_input"
    )
    
    col_login, col_clear = st.columns(2)
    
    with col_login:
        if st.button("Ingresar", type="primary", use_container_width=True, key="btn_login"):
            expected = AUTH_PROFILES[profile_name]
            
            if username.strip() != expected["username"] or password != expected["password"]:
                st.error("❌ Credenciales inválidas.")
            else:
                try:
                    # Validar conexión a SQL Server
                    conn = get_sql_connection(
                        username=expected["username"], 
                        password=expected["password"]
                    )
                    conn.close()
                    
                    # ✅ Guardar el perfil exacto como está en AUTH_PROFILES
                    st.session_state.authenticated = True
                    st.session_state.login_user = expected["username"]
                    st.session_state.login_profile = profile_name  # ✅ Importante: "Administrador", "Analista", "SA"
                    
                    st.success(f"✅ Sesión iniciada como {profile_name}")
                    st.rerun()
                    
                except Exception as exc:
                    st.error(f"No se pudo validar la conexión: {exc}")
    
    with col_clear:
        if st.button("Limpiar", use_container_width=True, key="btn_clear"):
            st.session_state.authenticated = False
            st.session_state.login_user = None
            st.session_state.login_profile = None
            st.rerun()

def require_login():
    """Requiere login para acceder"""
    init_session_state()
    if not st.session_state.authenticated:
        st.warning(" Debes iniciar sesión para acceder a esta página.")
        login_panel()
        st.stop()

def logout_button():
    """Botón de cerrar sesión"""
    init_session_state()
    if st.session_state.authenticated:
        if st.sidebar.button("🚪 Cerrar sesión", key="btn_logout"):
            st.session_state.authenticated = False
            st.session_state.login_user = None
            st.session_state.login_profile = None
            st.rerun()

def render_role_menu():
    """Renderiza el menú según el rol"""
    init_session_state()
    profile = st.session_state.login_profile
    
    if not profile or profile not in ROLE_PAGES:
        st.error("Perfil no válido")
        return
    
    pages = ROLE_PAGES.get(profile, ROLE_PAGES["Analista"])
    
    st.markdown("### 🧭 Menú del sistema")
    st.markdown("---")
    
    for label, path in pages:
        st.page_link(path, label=label)

def require_role(*allowed_profiles):
    init_session_state()
    
    # Si se pasó una lista como único argumento, la desenpaquetamos
    if len(allowed_profiles) == 1 and isinstance(allowed_profiles[0], (list, tuple)):
        allowed_profiles = tuple(allowed_profiles[0])
    
    if not st.session_state.authenticated:
        st.warning("🔒 Debes iniciar sesión para acceder a esta página.")
        login_panel()
        st.stop()
    
    current_profile = st.session_state.login_profile
    
    if not current_profile:
        st.error("❌ No se pudo determinar tu perfil.")
        st.stop()
    
    if not allowed_profiles:
        return
    
    if current_profile not in allowed_profiles:
        st.error(f"❌ **Acceso Denegado**\n\n"
                f"Tu rol actual es: **{current_profile}**\n\n"
                f"Se requiere uno de los siguientes roles: {', '.join(allowed_profiles)}")
        st.stop()