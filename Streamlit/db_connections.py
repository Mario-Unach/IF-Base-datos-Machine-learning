import pyodbc
import pymongo
import streamlit as st

def get_sql_connection():
    # Ajusta el DRIVER según tu versión de ODBC instalada en Windows
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=CreditCardDefault;" # Cambia al nombre real de tu BD en SQL Server
        "Trusted_Connection=yes;"
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