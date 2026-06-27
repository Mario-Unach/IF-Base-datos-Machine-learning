import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def load_and_clean_data(filepath):
    """Carga y limpia el dataset de forma robusta"""
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath, header=1)
        
    # 1. Eliminar columnas de índice fantasma (ej. 'Unnamed: 0') si las hay
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
    
    # 2. Limpiar nombres de columnas (quitar espacios y pasar a mayúsculas para evitar errores)
    df.columns = df.columns.str.strip().str.upper()
    
    # 3. Identificar la variable objetivo (Target) de forma inteligente
    # Buscamos la columna que contenga 'DEFAULT' o 'Y'
    target_cols = [c for c in df.columns if 'DEFAULT' in c or c == 'Y']
    if target_cols:
        target_col = target_cols[0]
    else:
        target_col = df.columns[-1] # Si no la encuentra por nombre, asume que es la última
        
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    
    # 4. Eliminar ID si existe
    if 'ID' in X.columns: 
        X = X.drop('ID', axis=1)
        
    # 5. Codificación de variables categóricas (solo si existen en el dataset)
    education_map = {0: 4, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 4}
    marriage_map = {0: 3, 1: 1, 2: 2, 3: 3}
    
    if 'EDUCATION' in X.columns:
        X['EDUCATION'] = X['EDUCATION'].map(education_map).fillna(4).astype(int)
    if 'MARRIAGE' in X.columns:
        X['MARRIAGE'] = X['MARRIAGE'].map(marriage_map).fillna(3).astype(int)
        
    print(f"✅ Dataset cargado. Features: {X.shape[1]}, Target: '{target_col}'")
    return X, y

def prepare_for_training(X, y):
    """Divide y escala los datos"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X.columns)
    
    # Guardamos las medianas para imputar datos faltantes en el formulario de Streamlit
    medians = X.median() 
    
    # Calcular peso para clases desbalanceadas
    neg, pos = np.bincount(y_train)
    scale_pos_weight = neg / pos if pos > 0 else 1.0
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, medians, scale_pos_weight