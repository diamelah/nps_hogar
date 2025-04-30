import pandas as pd
import io
import streamlit as st


@st.cache_data
def cargar_datos(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        df_excel = pd.read_excel(uploaded_file)
        csv_buffer = io.StringIO()
        df_excel.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        df = pd.read_csv(csv_buffer)
    else:
        df = pd.DataFrame()
    return df

@st.cache_data
def renombrar_columnas(df):
    return df.rename(columns={
        "Q2 - ¿Cuál es el motivo de tu calificación?": "verbatim",
        "Q15_2_TEXT - No, ¿por qué?": "no_por_que",
        "Q12 - ¿Cuál fue tu inconveniente?": "inconveniente",
        "Grupo NPS": "grupo_nps",
        "NPS": "nps",
        "Q3 - ¿Cuál fue el factor que más influyó en tu nota?": "categoria",
        "Fecha registrada (+00:00 GMT)": "fecha",
        "Q125- A tráves de que canal te contactaste:": "canal_atencion",
        "Q14 - En el último mes, ¿Te contactaste con nuestro centro de atención al cliente...": "centro_atencion",
        "¿Tu problema fue resuelto?": "resuelto",
        "CUENTA_CODIGO": "cuenta_codigo",
        "SCORE": "score",
        "SEGMENTO1": "segmento",
        "TECNOLOGIA": "tecnologia",
        "BASE_OPERATIVA": "localidad",
        "Q104 - ¿Utilizas la APP Mi Personal Flow?": "app_mipersonal_flow"
    })