import streamlit as st

from unidecode import unidecode
from data_loader import cargar_datos, renombrar_columnas
from dolor_detector import detectar_dolor
from filtros import mostrar_filtros
from visualizaciones import (
    mostrar_analisis_tematica,
    mostrar_dolores_por_mes,   
)
from configuracion import configurar_pagina

configurar_pagina()

st.title("📊 NPS Hogar Relacionamiento")
st.divider()

uploaded_file = st.sidebar.file_uploader("📁 Subí el archivo CSV o Excel para analizar", type=["csv", "xlsx"])

if uploaded_file:
    df = cargar_datos(uploaded_file)
    df = renombrar_columnas(df)
    df = mostrar_filtros(df)
    df["dolor_detectado"] = df["verbatim"].apply(detectar_dolor)

    import re
    total_encuestas = len(df)

    def es_basura(txt: str) -> bool:
        txt = str(txt).strip()
        if txt == "" or txt.lower() in {"nan", "none"}:
            return True
        return not bool(re.search(r"[A-Za-z0-9áéíóúüñ]", txt))

    cantidad_vacios = int(df["verbatim"].apply(es_basura).sum())
    cantidad_verbatims = total_encuestas - cantidad_vacios

    
    col1, col2, col3 = st.columns(3)
    col1.metric("Q. Encuestas",        f"{total_encuestas:,}")
    col2.metric("Q. Verbatims",        f"{cantidad_verbatims:,}")
    col3.metric("Q. Verbatims vacíos", f"{cantidad_vacios:,}")

    st.divider()
    mostrar_analisis_tematica(df)
    mostrar_dolores_por_mes(df)
       
        

    