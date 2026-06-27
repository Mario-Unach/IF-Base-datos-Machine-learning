import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Streamlit.db_connections import get_sql_connection, get_mongo_connection

# Configuración de página
st.set_page_config(
    page_title="CreditFlow Analytics", 
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<p class="main-header">💳 CreditFlow Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Sistema Predictivo de Riesgo Crediticio | Arquitectura Híbrida SQL Server + MongoDB</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/100/credit-card.png", width=100)
    st.markdown("### 🎯 Navegación")
    
    st.divider()
    st.markdown("### 📊 KPIs en Tiempo Real")
    
    # Conexión a SQL Server para obtener KPIs
    try:
        conn = get_sql_connection()
        query_kpis = """
            SELECT 
                COUNT(DISTINCT c.id_cliente) AS total_clientes,
                AVG(c.limite_credito) AS avg_limite_credito,
                AVG(c.edad) AS avg_edad,
                SUM(r.incumplimiento_proximo_mes) * 100.0 / COUNT(*) AS tasa_incumplimiento
            FROM dim_cliente c
            INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
        """
        df_kpis = pd.read_sql(query_kpis, conn)
        
        with st.container():
            st.metric("👥 Total Clientes", f"{int(df_kpis['total_clientes'][0]):,}")
            st.metric("💰 Límite Promedio", f"${df_kpis['avg_limite_credito'][0]:,.2f}")
            st.metric("📅 Edad Promedio", f"{df_kpis['avg_edad'][0]:.1f} años")
            st.metric("⚠️ Tasa Incumplimiento", f"{df_kpis['tasa_incumplimiento'][0]:.2f}%")
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar KPIs: {str(e)}")
    
    st.divider()
    st.markdown("### ℹ️ Acerca del Proyecto")
    st.info("""
    **Objetivo:** Diseñar una solución analítica integral que combine arquitectura de persistencia híbrida con modelos de Machine Learning para predecir impagos crediticios.
    
    **Tecnologías:**
    - SQL Server: Base de datos relacional normalizada
    - MongoDB: Registro de experimentos ML
    - XGBoost: Modelo predictivo
    - Streamlit: Dashboard interactivo
    """)
    
    st.divider()
    st.caption("🔗 Conexiones Activas:")
    st.success("✅ SQL Server")
    st.success("✅ MongoDB")

# Contenido principal - Dashboard general
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎯 Objetivos del Proyecto
    
    1. **Arquitectura Híbrida:** Implementar repositorio relacional en SQL Server con integración NoSQL en MongoDB
    
    2. **Machine Learning:** Desarrollar pipeline de preparación de datos y modelos supervisados/no supervisados
    
    3. **Seguridad:** Garantizar auditoría mediante triggers y plan de recuperación ante desastres
    
    4. **Despliegue:** Dashboard interactivo en tiempo real con predicciones ML
    """)

with col2:
    try:
        conn = get_sql_connection()
        
        # Distribución por educación
        query_edu = """
            SELECT e.nivel_educativo, COUNT(*) as cantidad
            FROM dim_cliente c
            INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
            GROUP BY e.nivel_educativo
            ORDER BY cantidad DESC
        """
        df_edu = pd.read_sql(query_edu, conn)
        
        fig_pie = px.pie(df_edu, values='cantidad', names='nivel_educativo', 
                         title='📚 Distribución por Nivel Educativo',
                         color_discrete_sequence=px.colors.sequential.Blues)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar gráfico educativo: {str(e)}")

with col3:
    try:
        conn = get_sql_connection()
        
        # Distribución por estado civil
        query_civil = """
            SELECT ec.descripcion_estado_civil, COUNT(*) as cantidad
            FROM dim_cliente c
            INNER JOIN dim_estado_civil ec ON c.id_estado_civil = ec.id_estado_civil
            GROUP BY ec.descripcion_estado_civil
        """
        df_civil = pd.read_sql(query_civil, conn)
        
        fig_bar = px.bar(df_civil, x='descripcion_estado_civil', y='cantidad',
                         title='💍 Distribución por Estado Civil',
                         color='cantidad',
                         color_continuous_scale='Viridis')
        fig_bar.update_layout(xaxis_title="Estado Civil", yaxis_title="Cantidad")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar gráfico estado civil: {str(e)}")

# Sección de arquitectura
st.divider()
st.markdown("### 🏗️ Arquitectura del Sistema")

col_arch1, col_arch2 = st.columns(2)

with col_arch1:
    st.markdown("""
    #### 📦 Base de Datos Relacional (SQL Server)
    
    **Tablas Principales:**
    - `dim_cliente`: Información demográfica de clientes
    - `dim_sexo`, `dim_educacion`, `dim_estado_civil`: Catálogos normalizados
    - `historial_pagos`: Historial transaccional de 6 meses
    - `riesgo_crediticio`: Variable objetivo (target)
    - `auditoria_cambios`: Tabla de auditoría con triggers
    
    **Características:**
    - ✅ Normalización 3NF
    - ✅ Índices clustered/non-clustered
    - ✅ Vistas optimizadas para ML
    - ✅ Triggers de auditoría
    - ✅ Roles diferenciados (analista/admin)
    - ✅ Strategy de backups (Full/Diff/Log)
    """)

with col_arch2:
    st.markdown("""
    #### 📄 Base de Datos Documental (MongoDB)
    
    **Colección:** `experimentos_ml`
    
    **Documentos almacenados:**
    ```json
    {
        "fecha": "ISODate",
        "algoritmo": "XGBoost",
        "hiperparametros": {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1
        },
        "metricas": {
            "accuracy": 0.82,
            "precision": 0.78,
            "recall": 0.75,
            "f1_score": 0.76
        }
    }
    ```
    
    **Propósito:**
    - ✅ Tracking de experimentos
    - ✅ Comparación de modelos
    - ✅ Reproducibilidad
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <h4>CreditFlow Analytics © 2025</h4>
    <p>Proyecto Académico de Machine Learning & Bases de Datos</p>
    <p><small>Arquitectura Híbrida SQL Server + MongoDB | UCI Default of Credit Card Clients Dataset</small></p>
</div>
""", unsafe_allow_html=True)
