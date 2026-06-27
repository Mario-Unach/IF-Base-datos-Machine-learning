import pyodbc
import pymongo
import streamlit as st

def get_sql_connection():
    # Para Linux, usa autenticación SQL (no Trusted_Connection)
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"  # Especifica el puerto
        "DATABASE=CreditCardDefault;"
        "UID=sa;"
        "PWD=Soymario.7;"  # La misma contraseña que en tu docker-compose
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Error SQL Server: {e}")
        return None

def get_mongo_db():
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        return client["ML_Experiments"]
    except Exception as e:
        st.error(f"Error MongoDB: {e}")
        return None