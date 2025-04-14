import streamlit as st
import pandas as pd

def mostrar_filtros(df):
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["solo_fecha"] = df["fecha"].dt.date

    fecha_min = df["solo_fecha"].min()
    fecha_max = df["solo_fecha"].max()

    fecha_inicio = st.sidebar.date_input(
        "Fecha inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max
    )

    df = df[(df["solo_fecha"] >= fecha_inicio) & (df["solo_fecha"] <= fecha_fin)]

    grupo_nps_filtrar = st.sidebar.multiselect(
        "Grupo NPS", options=df["grupo_nps"].dropna().unique()
    )
    canal_filtrar = st.sidebar.multiselect(
        "Canal de Atención", options=df["canal_atencion"].dropna().unique()
    )
    categoria_filtrar = st.sidebar.multiselect(
        "Categorias", options=df["categoria"].dropna().unique()
    )

    if grupo_nps_filtrar:
        df = df[df["grupo_nps"].isin(grupo_nps_filtrar)]
    if canal_filtrar:
        df = df[df["canal_atencion"].isin(canal_filtrar)]
    if categoria_filtrar:
        df = df[df["categoria"].isin(categoria_filtrar)]

    return df
