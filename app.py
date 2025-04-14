import streamlit as st
from data_loader import cargar_datos, renombrar_columnas
from tema_detector import detectar_tema
from filtros import mostrar_filtros
from visualizaciones import (
    mostrar_analisis_tematica,
    mostrar_detractores_por_tema,
    mostrar_palabras_clave,
    
)
from configuracion import configurar_pagina

configurar_pagina()
st.title("📊 Dashboard de Verbatims NPS")

uploaded_file = st.sidebar.file_uploader("📁 Subí el archivo CSV o Excel para analizar", type=["csv", "xlsx"])

if uploaded_file:
    df = cargar_datos(uploaded_file)
    df = renombrar_columnas(df)
    df = mostrar_filtros(df)
    df["tema_detectado"] = df["verbatim"].apply(detectar_tema)

    mostrar_analisis_tematica(df)
    mostrar_detractores_por_tema(df)
    mostrar_palabras_clave(df)

