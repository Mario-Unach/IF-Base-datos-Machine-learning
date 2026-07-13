import pyodbc
import streamlit as st
import pandas as pd

try:
    import pymongo
except ImportError:
    pymongo = None

# ---------------------------------------------------------
# CONEXIÓN A SQL SERVER (Docker en Arch Linux)
# ---------------------------------------------------------
def get_sql_connection(username=None, password=None, **kwargs):
    """
    Conecta con SQL Server en Docker.
    - SERVER=localhost,1433  (puerto expuesto en docker-compose)
    - DATABASE=CC_Client     (la BD que creaste en tu script)
    - TrustServerCertificate=yes (OBLIGATORIO en Linux/Docker para evitar errores SSL)
    """
    sql_user = username or kwargs.get("nombre de usuario") or kwargs.get("nombre_usuario") or kwargs.get("usuario") or "sa"
    sql_password = password or kwargs.get("contraseña") or kwargs.get("contrasena") or kwargs.get("clave") or "Flaquis2026*"

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=CC_Client;"
        f"UID={sql_user};"
        f"PWD={sql_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"❌ Error SQL Server: {e}")
        return None

# ---------------------------------------------------------
# CONEXIÓN A MONGODB (Arquitectura Híbrida)
# ---------------------------------------------------------
def get_mongo_connection():
    """
    Retorna la conexión al cliente MongoDB.
    """
    if pymongo is None:
        st.error("❌ pymongo no está instalado en este entorno.")
        return None

    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ Error MongoDB: {e}")
        return None

def get_mongo_db():
    """
    Retorna la base de datos ML_Experiments de MongoDB.
    """
    try:
        client = get_mongo_connection()
        if client:
            return client["ML_Experiments"]
        return None
    except Exception as e:
        st.error(f"❌ Error MongoDB: {e}")
        return None

# ---------------------------------------------------------
# CARGA DE DATOS DESDE LA VISTA vw_ml_dataset
# ---------------------------------------------------------
def load_dataset_from_sql():
    """
    Carga el dataset plano directamente desde la vista vw_ml_dataset.
    Renombra las columnas para que coincidan con los nombres estándar del modelo.
    """
    conn = get_sql_connection()
    if conn is None:
        return None
    
    # Usamos la vista que YA tienes creada en SQL Server
    query = """
    SELECT 
        id_cliente AS ID,
        id_sexo AS SEX,
        id_educacion AS EDUCATION,
        id_estado_civil AS MARRIAGE,
        edad AS AGE,
        limite_credito AS LIMIT_BAL,
        PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
        BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
        PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
        target AS [default payment next month]
    FROM vw_ml_dataset
    """
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar dataset: {e}")
        if conn: conn.close()
        return None

# ---------------------------------------------------------
# CARGA DE DATOS CON DESCRIPCIONES (Para EDA visual)
# ---------------------------------------------------------
def load_dataset_detallado():
    """Carga la vista vw_cliente_detallado con textos descriptivos"""
    conn = get_sql_connection()
    if conn is None:
        return None
    
    query = "SELECT * FROM vw_cliente_detallado"
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar dataset detallado: {e}")
        if conn: conn.close()
        return None