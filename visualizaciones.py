import streamlit as st
import pandas as pd
from temas_keywords import temas
from streamlit_echarts import st_echarts
import altair as alt

# --- Detectar tema (usa temas importado globalmente) ---
def detectar_tema(texto):
    texto = str(texto).lower()
    for tema, palabras in temas.items():
        if any(p in texto for p in palabras):
            return tema
    return None

# --- Mostrar análisis temático de verbatims ---
def mostrar_analisis_tematica(df):
    st.subheader("🔠 Análisis de Verbatims")

    # Detectar temas solo si no está la columna
    if "tema_detectado" not in df.columns:
        df["tema_detectado"] = df["verbatim"].apply(detectar_tema)

    df_temas = df[df["tema_detectado"].notna()]

    # Checkbox para activar filtro por verbatims largos
    filtrar_largos = st.checkbox("📝 Mostrar solo verbatims con más de 25 palabras")
    if filtrar_largos:
        df_temas = df_temas[df_temas["verbatim"].astype(str).apply(lambda x: len(x.split()) > 25)]

    # Filtros interactivos
    tema_filtrar = st.multiselect("🌟 Filtrar por tema detectado", options=sorted(df_temas["tema_detectado"].unique()))
    if tema_filtrar:
        df_temas = df_temas[df_temas["tema_detectado"].isin(tema_filtrar)]
        st.markdown("### 🔠 Frases clave del tema detectado")
        for tema in tema_filtrar:
            frases = temas.get(tema, [])
            st.markdown(f"**{tema.capitalize()}**: {', '.join(frases)}")

    search_tema = st.text_input("🔎 Buscar palabras en verbatim (temas):", "")
    if search_tema:
        palabras = [p.strip().lower() for p in search_tema.split(",") if p.strip()]
        df_temas = df_temas[df_temas["verbatim"].astype(str).str.lower().apply(lambda x: any(p in x for p in palabras))]

    columnas_tema = [
        "solo_fecha", "dni", "localidad", "grupo_nps", "categoria",
        "verbatim", "tema_detectado", "centro_atencion", "canal_atencion",
        "no_por_que", "app_mipersonal_flow"
    ]
    columnas_tema_disponibles = [col for col in columnas_tema if col in df_temas.columns]
    st.dataframe(df_temas[columnas_tema_disponibles])



    # --- Tabla  Detractores Score, Segmento ---
    st.subheader("📋 Temas Detectados - Score/Tecnlogía - Centros de Atención")

    if "tema_detectado" in df.columns and not df_temas.empty:
        df_filtrado = df_temas.copy()

        resumen = (
            df_filtrado
            .groupby("tema_detectado")
            .agg(
                cantidad=("tema_detectado", "count"),
                porcentaje=("tema_detectado", lambda x: 100 * len(x) / len(df)),
                score_0=("score", lambda x: (x == 0).sum()),
                score_1=("score", lambda x: (x == 1).sum()),
                score_8=("score", lambda x: (x == 8).sum()),
                tecnologia=('tecnologia', lambda x: "FTTH" if (x.fillna('').str.strip().str.upper() == "FTTH").sum() >= (x.fillna('').str.strip().str.upper() == "HFC").sum() else "HFC"),
                centro_no_pct=("centro_atencion", lambda x: 100 * (x.fillna('').str.lower() == "no").sum() / len(x))
            )
            .reset_index()
        )

        resumen = resumen.rename(columns={
            "tema_detectado": "Tema",
            "cantidad": "Cantidad",
            "porcentaje": "Porcentaje %",
            "score_0": "SCORE 0",
            "score_1": "SCORE 1",
            "score_8": "SCORE 8",
            "tecnologia": "Tecnología",
            "centro_no_pct": "Centro Atención"
        })

        resumen["Porcentaje %"] = resumen["Porcentaje %"].round(2)
        resumen["Centro Atención"] = resumen["Centro Atención"].round(2)

        st.dataframe(resumen.style.format({
            "Porcentaje %": "{:.2f}%",
            "Centro Atención": "{:.2f}%",
            "Cantidad": "{:,.0f}"
        }))
        
        # ⬇️ Agregamos la tabla específica solo para FTTH debajo de la general
        st.subheader("📋 Temas detectados vs SCORE - Tecnología FTTH")

        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df_ftth = df[df["tecnologia"].astype(str).str.upper() == "FTTH"].copy()
        todos_los_scores = sorted(df["score"].dropna().unique())

        tabla_ftth = pd.pivot_table(
            df_ftth,
            values="verbatim",
            index="tema_detectado",
            columns="score",
            aggfunc="count",
            fill_value=0
        )

        for score in todos_los_scores:
            if score not in tabla_ftth.columns:
                tabla_ftth[score] = 0

        tabla_ftth = tabla_ftth[sorted(tabla_ftth.columns)]
        tabla_ftth.columns = [f"SCORE {col}" for col in tabla_ftth.columns]
        tabla_ftth.index.name = "FTTH"

        st.dataframe(tabla_ftth)


    # --- Uso de app y detractores ---
    if "app_mipersonal_flow" in df.columns:
        with st.container():  # 🔁 Agrupamos las columnas + gráfico en el mismo bloque
            col1, col2 = st.columns(2)
        with col1:
            st.subheader("📱 App Mi Personal Flow")
            total = len(df)
            conteo_app = df["app_mipersonal_flow"].fillna("No informado").astype(str).str.strip().str.lower().value_counts()
            porcentaje_app = (conteo_app / total * 100).rename("Porcentaje")
            resumen_app = pd.DataFrame({
                "Respuesta": porcentaje_app.index.str.capitalize(),
                "Cantidad": conteo_app.values,
                "Porcentaje": porcentaje_app.values
            })
            st.dataframe(resumen_app.style.format({"Porcentaje": "{:.2f}%", "Cantidad": "{:,.0f}"}))

        with col2:
            st.subheader("📉 Detractores que usan la App")
            df_detractores = df[df["grupo_nps"].astype(str).str.lower() == "detractor"].copy()
            conteo_det_app = df_detractores["app_mipersonal_flow"].fillna("No informado").astype(str).str.strip().str.lower().value_counts()
            porcentaje_det_app = (conteo_det_app / len(df_detractores) * 100).rename("Porcentaje")
            resumen_det_app = pd.DataFrame({
                "Usa App": porcentaje_det_app.index.str.capitalize(),
                "Porcentaje": porcentaje_det_app.values
            })
            st.dataframe(resumen_det_app.style.format({"Porcentaje": "{:.2f}%"}))
            
# 🔽 Gráfico justo después de las columnas
        #st.markdown("#### 📊 Verbatims por Tema y SCORE")
        mostrar_evolucion_score(df)
        
def mostrar_evolucion_score(df):
    import streamlit as st
    import altair as alt

    st.subheader("📊 Verbatims por Temas Detectados y SCORE")

    df["score"] = pd.to_numeric(df["score"], errors='coerce')
    df_valid = df[df["score"].isin([0, 1, 8]) & df["tema_detectado"].notna()].copy()

    # 🔢 Obtener todos los temas detectados disponibles
    temas_disponibles = sorted(df_valid["tema_detectado"].dropna().unique())

    # 🎯 Selector interactivo con multiselección
    temas_seleccionados = st.multiselect(
        "🎯 Seleccioná los temas a visualizar",
        options=temas_disponibles,
        default=temas_disponibles[:5],  # top 5 por defecto
        key="multiselect_score"
    )

    if not temas_seleccionados:
        st.info("📌 Seleccioná al menos un tema para mostrar el gráfico.")
        return

    df_filtrado = df_valid[df_valid["tema_detectado"].isin(temas_seleccionados)]

    resumen = (
        df_filtrado.groupby(["tema_detectado", "score"])
        .size()
        .reset_index(name="cantidad")
    )

    chart = alt.Chart(resumen).mark_bar().encode(
        x=alt.X('tema_detectado:N', title='Tema Detectado', axis=alt.Axis(labelAngle=-10, labelLimit=300)),
        xOffset='score:N',
        y=alt.Y('cantidad:Q', title='Cantidad de Verbatims'),
        color=alt.Color('score:N', title='SCORE', scale=alt.Scale(
            domain=[0, 1, 8],
            range=["#007bff", "#ff7f0e", "#2ca02c"]
        )),
        tooltip=['tema_detectado:N', 'score:N', 'cantidad:Q']
    ).properties(
        width=800,
        height=400,
        title="Verbatims por Tema y Score"
    )

    st.altair_chart(chart, use_container_width=True)



import pandas as pd
from streamlit_echarts import st_echarts

def mostrar_detractores_por_tema(df):
    import streamlit as st
    from temas_keywords import temas

    df_original = df.copy()
    df_original["tema_detectado"] = df_original["verbatim"].apply(lambda x: detectar_tema(x, temas))
    df_detractores = df_original.copy()
    df_detractores["mes_num"] = df_detractores["fecha"].dt.month

    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df_detractores["mes_nombre"] = df_detractores["mes_num"].map(meses_es)
    df_detractores = df_detractores[
        (df_detractores["grupo_nps"].astype(str).str.lower() == "detractor") &
        (df_detractores["mes_num"].isin([1, 2, 3]))
    ]

    if df_detractores.empty:
        st.info("📌 No hay detractores disponibles para enero, febrero o marzo.")
        return

    temas_por_mes = df_detractores.groupby(["tema_detectado", "mes_nombre"]).size().unstack(fill_value=0)
    orden_meses = ["Enero", "Febrero", "Marzo"]
    temas_por_mes = temas_por_mes.reindex(columns=orden_meses, fill_value=0)

def mostrar_temas_por_mes(df):
    import streamlit as st
    from streamlit_echarts import st_echarts

    st.subheader("📋 Cantidad de temas detectados por mes")

    # Asegurarse de que las fechas estén bien y crear columna mes
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["mes_num"] = df["fecha"].dt.month
    df["mes_nombre"] = df["mes_num"].map({
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    })

    # Agrupar por tema y mes
    temas_por_mes = df.groupby(["tema_detectado", "mes_nombre"]).size().unstack(fill_value=0)

    # Reordenar columnas (meses)
    orden_meses = ["Enero", "Febrero", "Marzo"]
    temas_por_mes = temas_por_mes.reindex(columns=orden_meses, fill_value=0)

    # --- Nueva columna: No se contactan ---
    df["centro_atencion"] = df["centro_atencion"].fillna("").astype(str).str.lower().str.strip()
    df_no_contacto = df[df["centro_atencion"] == "no"]
    no_se_contactan = df_no_contacto.groupby("tema_detectado").size().rename("No se contactaron")

    # Unir con tabla
    tabla_completa = temas_por_mes.copy()
    tabla_completa["No se contactaron"] = no_se_contactan
    tabla_completa["No se contactaron"] = tabla_completa["No se contactaron"].fillna(0).astype(int)

    # Mostrar tabla
    st.dataframe(tabla_completa)

    # Gráfico de barras apiladas horizontales
    chart_data = [
        {
            "name": mes,
            "type": "bar",
            "stack": "total",
            "label": {"show": True},
            "emphasis": {"focus": "series"},
            "data": temas_por_mes[mes].tolist()
        } for mes in orden_meses if mes in temas_por_mes.columns
    ]

    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": orden_meses},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": temas_por_mes.index.tolist()},
        "series": chart_data
    }

    st_echarts(options=options, height="500px")






def mostrar_palabras_clave(df):
    import streamlit as st
    from temas_keywords import temas

    df_original = df.copy()
    df_original["tema_detectado"] = df_original["verbatim"].apply(lambda x: detectar_tema(x, temas))
    df_detractores = df_original[
        df_original["grupo_nps"].astype(str).str.lower() == "detractor"
    ]
    df_detractores["mes_num"] = df_detractores["fecha"].dt.month
    df_detractores["mes_nombre"] = df_detractores["mes_num"].map({1: "Enero", 2: "Febrero", 3: "Marzo"})

    st.subheader("🔍 Palabras clave por tema detectado")
    temas_disponibles = sorted(df_original["tema_detectado"].dropna().unique())
    tema_filtrado = st.multiselect("🎯 Seleccioná un tema para analizar palabras clave", options=temas_disponibles)

    if not tema_filtrado:
        st.info("📌 Seleccioná al menos un tema detectado para ver el gráfico de palabras clave.")
        return

    registros = []
    for tema in tema_filtrado:
        frases = temas.get(tema, [])
        st.markdown(f"**{tema.capitalize()}**: {', '.join(frases)}")
        for palabra in frases:
            subset = df_detractores[df_detractores["verbatim"].astype(str).str.lower().str.contains(palabra, regex=False)]
            for _, fila in subset.iterrows():
                registros.append({"palabra": palabra, "mes": fila["mes_nombre"]})

    df_palabras = pd.DataFrame(registros)
    if df_palabras.empty:
        st.warning("⚠️ No se encontraron ocurrencias para las palabras clave del tema seleccionado.")
        return

    df_palabras["conteo"] = 1
    pivot_ocurrencias = (
        df_palabras
        .groupby(["palabra", "mes"])["conteo"]
        .sum()
        .reset_index()
        .pivot_table(index="palabra", columns="mes", values="conteo", aggfunc="sum", fill_value=0)
        .reindex(columns=["Enero", "Febrero", "Marzo"], fill_value=0)
    )

    top_n = st.slider("🔢 Mostrar top N palabras más frecuentes", min_value=3, max_value=30, value=10)
    palabras_top = pivot_ocurrencias.sum(axis=1).sort_values(ascending=False).head(top_n).index
    pivot_ocurrencias = pivot_ocurrencias.loc[palabras_top]

    st.dataframe(pivot_ocurrencias)

    chart_data = [
        {
            "name": mes,
            "type": "bar",
            "stack": "total",
            "label": {"show": True},
            "emphasis": {"focus": "series"},
            "data": pivot_ocurrencias[mes].tolist()
        } for mes in ["Enero", "Febrero", "Marzo"]
    ]

    options_keywords = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": ["Enero", "Febrero", "Marzo"]},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": pivot_ocurrencias.index.tolist()},
        "series": chart_data
    }

    st_echarts(options=options_keywords, height="500px")

def detectar_tema(texto, temas):
    texto = str(texto).lower()
    for tema, palabras in temas.items():
        if any(p in texto for p in palabras):
            return tema
    return None