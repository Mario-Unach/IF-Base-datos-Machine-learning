import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def load_and_preprocess_data():
    """
    Carga, limpia y preprocesa el dataset de clientes de tarjetas de crédito.
    Retorna los conjuntos de entrenamiento/prueba, el escalador entrenado y los nombres de features.
    """
    # 1. Definir ruta relativa del dataset (subiendo dos niveles desde Models/Random_Forest)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    DATASET_PATH = os.path.join(base_dir, '..', '..', 'Dataset', 'default of credit card clients.csv')
    
    # 2. Cargar el dataset
    df = pd.read_csv(DATASET_PATH)
    
    # LIMPIEZA: Eliminar la primera fila (que contiene texto) y reiniciar los índices
    df = df.iloc[1:].reset_index(drop=True)
    
    # LIMPIEZA: Convertir todo a números
    df = df.apply(pd.to_numeric)
    
    # Asegurarnos de que no hay nulos
    df = df.dropna()
    
    # Separar variables predictoras (X) de la variable objetivo (y)
    if 'ID' in df.columns:
        X = df.drop(columns=['ID', 'Y'])
    else:
        X = df.drop(columns=['Y'])
        
    y = df['Y']
    feature_names = list(X.columns)
    
    # Dividir los datos (Hold-out estratificado)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Escalamiento de variables
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_names