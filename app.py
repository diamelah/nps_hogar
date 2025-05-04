import streamlit as st
from unidecode import unidecode
from data_loader import cargar_datos, renombrar_columnas
from tema_detector import detectar_tema
from filtros import mostrar_filtros
from visualizaciones import (
    mostrar_analisis_tematica,
    mostrar_temas_por_mes,
    mostrar_palabras_clave,
)
from configuracion import configurar_pagina

configurar_pagina()
st.title("📊 Dashboard NPS Hogar Relacionamiento")
st.divider()  

uploaded_file = st.sidebar.file_uploader("📁 Subí el archivo CSV o Excel para analizar", type=["csv", "xlsx"])

if uploaded_file:
    df = cargar_datos(uploaded_file)
    df = renombrar_columnas(df)
    df = mostrar_filtros(df)
    df["tema_detectado"] = df["verbatim"].apply(detectar_tema)
    
    # ──────────────────────────────────────────
    #  NUEVAS MÉTRICAS – Encuestas · Verbatims · Verbatims vacíos
    # ──────────────────────────────────────────
    import re

    total_encuestas = len(df)

    # Sólo símbolos/sin contenido alfanumérico → basura
    def es_basura(txt: str) -> bool:
        txt = str(txt).strip()
        if txt == "" or txt.lower() in {"nan", "none"}:
            return True
        # True si NO hay ni letra (áéíóúüñ) ni dígito
        return not bool(re.search(r"[A-Za-z0-9áéíóúüñ]", txt))

    # Cantidad de verbatims vacíos/basura
    cantidad_vacios = int(df["verbatim"].apply(es_basura).sum())

    # Verbatims “válidos” = total menos basura
    cantidad_verbatims = total_encuestas - cantidad_vacios

    col1, col2, col3 = st.columns(3)
    col1.metric("Q. Encuestas",        f"{total_encuestas:,}")
    col2.metric("Q. Verbatims",        f"{cantidad_verbatims:,}")
    col3.metric("Q. Verbatims vacíos", f"{cantidad_vacios:,}")

    st.divider()
    

    mostrar_analisis_tematica(df)
    mostrar_temas_por_mes(df)  # ✅ reemplaza a mostrar_detractores_por_tema
    mostrar_palabras_clave(df)
        
   
        
    
