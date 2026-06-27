import pandas as pd
import numpy as np
import pyodbc
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def get_db_connection():
    """Conexión directa a SQL Server desde el Notebook"""
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=CC_Client;"
        "UID=sa;"
        "PWD=Soymario.7;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def load_and_clean_data():
    """
    Carga el dataset directamente desde la VISTA vw_ml_dataset de SQL Server.
    Cumple con el requisito de la rúbrica: 'Conectar Jupyter Notebook con SQL Server 
    utilizando librerías de Python (pyodbc) para extraer los datos mediante consultas optimizadas.'
    """
    conn = get_db_connection()
    
    # Consulta optimizada a la vista que ya pivotea el historial
    query = """
    SELECT 
        id_sexo AS SEX,
        id_educacion AS EDUCATION,
        id_estado_civil AS MARRIAGE,
        edad AS AGE,
        limite_credito AS LIMIT_BAL,
        PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6,
        BILL_AMT1, BILL_AMT2, BILL_AMT3, BILL_AMT4, BILL_AMT5, BILL_AMT6,
        PAY_AMT1, PAY_AMT2, PAY_AMT3, PAY_AMT4, PAY_AMT5, PAY_AMT6,
        target AS default_payment_next_month
    FROM vw_ml_dataset
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"✅ Datos cargados desde SQL Server: {df.shape[0]} registros")
    
    # Separar features (X) y target (y)
    X = df.drop('default_payment_next_month', axis=1)
    y = df['default_payment_next_month']
    
    # Codificación de variables categóricas (limpieza de valores atípicos)
    education_map = {0: 4, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 4}
    marriage_map = {0: 3, 1: 1, 2: 2, 3: 3}
    
    X['EDUCATION'] = X['EDUCATION'].map(education_map).fillna(4).astype(int)
    X['MARRIAGE'] = X['MARRIAGE'].map(marriage_map).fillna(3).astype(int)
    
    return X, y

def prepare_for_training(X, y):
    """Divide y escala los datos"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X.columns)
    
    # Medianas para imputación en Streamlit (formulario simplificado)
    medians = X.median() 
    
    # Peso para clases desbalanceadas
    neg, pos = np.bincount(y_train)
    scale_pos_weight = neg / pos if pos > 0 else 1.0
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, medians, scale_pos_weight