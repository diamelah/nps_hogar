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
    #  MÉTRICAS – Total + tres categorías
    # ──────────────────────────────────────────
    from unidecode import unidecode

    def norm(txt):
        """Minúsculas + sin tildes + strip."""
        return unidecode(str(txt)).lower().strip()

    total_encuestas = len(df)

    # Filas con tema_detectado
    df_tema = df[df["tema_detectado"].notna()].copy()
    df_tema["categoria_norm"] = df_tema["categoria"].apply(norm)

    # ---- Claves normalizadas (lo que aparece en value_counts) ----
    cat1_key = "atencion a clientes"
    cat2_key = "facturacion y pago"
    cat3_key = "atencion del servicio tecnico"

    cnt_cat1 = (df_tema["categoria_norm"] == cat1_key).sum()
    cnt_cat2 = (df_tema["categoria_norm"] == cat2_key).sum()
    cnt_cat3 = (df_tema["categoria_norm"] == cat3_key).sum()

    # ---- Etiquetas bonitas para mostrar ----
    cat1_label = "Atención a Clientes"
    cat2_label = "Facturación y Pago"
    cat3_label = "Atención del Servicio Técnico"

    # Fila de 4 KPI
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Encuestas", f"{total_encuestas:,}")
    col2.metric(cat1_label, f"{cnt_cat1:,}")
    col3.metric(cat2_label, f"{cnt_cat2:,}")
    col4.metric(cat3_label, f"{cnt_cat3:,}")

    st.divider()
      # línea separadora antes de tus análisis

    

    mostrar_analisis_tematica(df)
    mostrar_temas_por_mes(df)  # ✅ reemplaza a mostrar_detractores_por_tema
    mostrar_palabras_clave(df)
        
   
        
    
