import streamlit as st
import pandas as pd
import re
import altair as alt
from streamlit_echarts import st_echarts
from temas_keywords import temas
from unidecode import unidecode

from tema_detector import detectar_tema

# --- Detectar tema (usa temas importado globalmente) ---
def detectar_temas(texto, temas_dict):
    texto = str(texto).lower()
    palabras = texto.split()
    encontrados = []
    texto = unidecode(str(texto).lower())
    palabras_texto = set(texto.replace(",", "").replace(".", "").split())

    for tema, tokens in temas.items():
        for token in tokens:
            token = unidecode(token.lower())
            if "+" in token:
                subpalabras = set(token.split("+"))
                if subpalabras.issubset(palabras_texto):
                    return tema
            else:
                if token in texto:
                    return tema
    return None


# --- Mostrar análisis temático de verbatims ---
def mostrar_analisis_tematica(df):
    st.subheader("👉​ Análisis de Verbatims")

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
        # Normalizamos y separamos por comas
        palabras = [p.strip().lower() for p in search_tema.split(",") if p.strip()]

        # Patrón regex:  \bpalabra\b  (coincidencia exacta, no sub-string)
        pattern = "|".join(rf"\b{re.escape(p)}\b" for p in palabras)

        df_temas = df_temas[
            df_temas["verbatim"]
                .astype(str)
                .str.lower()
                .str.contains(pattern, regex=True)
        ]

    columnas_tema = [
        "solo_fecha", "codigo_cuenta", "localidad", "grupo_nps", "categoria",
        "verbatim", "tema_detectado", "centro_atencion", "canal_atencion",
        "no_por_que", "app_mipersonal_flow"
    ]
    columnas_tema_disponibles = [col for col in columnas_tema if col in df_temas.columns]
    st.dataframe(df_temas[columnas_tema_disponibles])

    st.divider()  
    
    # --- Uso de app y detractores ---
    st.subheader("👉​ Uso de Aplicaciones")
    
    if "app_mipersonal_flow" in df.columns:
        with st.container():  # 🔁 Agrupamos las columnas + gráfico en el mismo bloque
            col1, col2 = st.columns(2)
        with col1:
            st.markdown(
            "<h3 style='font-size:22px; margin-bottom:0.5rem'>📱 App Mi Personal Flow</h3>",
            unsafe_allow_html=True
        )
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
            st.markdown(
                "<h3 style='font-size:22px; margin-bottom:0.5rem'>📉 Detractores vs. App</h3>",
                unsafe_allow_html=True
            )
            df_detractores = df[df["grupo_nps"].astype(str).str.lower() == "detractor"].copy()
            conteo_det_app = df_detractores["app_mipersonal_flow"].fillna("No informado").astype(str).str.strip().str.lower().value_counts()
            porcentaje_det_app = (conteo_det_app / len(df_detractores) * 100).rename("Porcentaje")
            resumen_det_app = pd.DataFrame({
                "Usa App": porcentaje_det_app.index.str.capitalize(),
                "Porcentaje": porcentaje_det_app.values
            })
            st.dataframe(resumen_det_app.style.format({"Porcentaje": "{:.2f}%"}))
            
    st.divider() 

# --- Tabla  Detractores Score, Segmento ---
    st.subheader("👉​ SCORE")
    st.markdown(
    "<h3 style='font-size:22px; margin-bottom:0.5rem'>🎯​ Temas Detectados en Scores Críticos: 0, 1 y 8</h3>",
    unsafe_allow_html=True
    )

    if "tema_detectado" in df.columns and not df_temas.empty:
        df_filtrado = df_temas.copy()

        resumen = (
            df_filtrado
            .loc[df_filtrado["score"].isin([0, 1, 8])]  # Filtrar solo scores 0, 1, 8
            .groupby("tema_detectado")
            .agg(
                cantidad=("tema_detectado", "count"),
                porcentaje=("tema_detectado", lambda x: 100 * len(x) / len(df_filtrado)),
                score_0=("score", lambda x: (x == 0).sum()),
                score_1=("score", lambda x: (x == 1).sum()),
                score_8=("score", lambda x: (x == 8).sum()),
                FTTH=('tecnologia', lambda x: (x.fillna('').str.strip().str.upper() == "FTTH").sum()),
                HFC=('tecnologia', lambda x: (x.fillna('').str.strip().str.upper() == "HFC").sum())
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
            "FTTH": "FTTH",
            "HFC": "HFC"
        })

        resumen["Porcentaje %"] = resumen["Porcentaje %"].round(2)

        st.dataframe(resumen.style.format({
            "Porcentaje %": "{:.2f}%",
            "Cantidad": "{:,.0f}"
        }))
        
    # ────────────────────────────────────────────────────────────────────────────
    # Tabla dinámica por tecnología (FTTH, HFC, …)
    # ────────────────────────────────────────────────────────────────────────────

    # 1) Selector de tecnología
    tecnologias_disp = sorted(df["tecnologia"].dropna().str.upper().unique())
    tec_sel = st.radio(
        "Seleccioná la tecnología",
        options=tecnologias_disp,
        index=0,            # FTTH por defecto (o el que quede primero)
        horizontal=True,
        key="tec_selector"
    )

    # 2) Encabezado dinámico
    st.markdown(
        f"<h3 style='font-size:22px; margin-bottom:0.5rem'>🎯 Temas Detectados: Score → {tec_sel}</h3>",
        unsafe_allow_html=True
    )

    # 3) Filtrado de la tech elegida
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df_tec = df[df["tecnologia"].astype(str).str.upper() == tec_sel].copy()

    # 4) Tabla pivote
    todos_scores = sorted(df["score"].dropna().unique())
    tabla_tec = pd.pivot_table(
        df_tec,
        values="verbatim",
        index="tema_detectado",
        columns="score",
        aggfunc="count",
        fill_value=0
    )

    # Asegurar que estén todos los scores
    for s in todos_scores:
        if s not in tabla_tec.columns:
            tabla_tec[s] = 0
    tabla_tec = tabla_tec[sorted(tabla_tec.columns)]
    tabla_tec.columns = [f"SCORE {s}" for s in tabla_tec.columns]
    tabla_tec.index.name = tec_sel

    # 5) Mostrar o advertir
    if tabla_tec.empty:
        st.warning(f"No hay verbatims con tecnología {tec_sel}.")
    else:
        st.dataframe(tabla_tec)


    
            
# 🔽 Gráfico justo después de las columnas
        #st.markdown("#### 📊 Verbatims por Tema y SCORE")
        mostrar_evolucion_score(df)
        

#--- Verbatims por Temas Detectados y SCORE---
        
def mostrar_evolucion_score(df):
    import streamlit as st
    import altair as alt

    st.markdown(
    "<h3 style='font-size:22px; margin-bottom:0.5rem'>🔠​ Verbatims por Temas Detectados y SCORE</h3>",
    unsafe_allow_html=True
    )

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
    df_original["tema_detectado"] = df_original["verbatim"].apply(detectar_tema)
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
    

    

#--- Cantidad de temas detectados por mes ---
def mostrar_temas_por_mes(df):
    import streamlit as st
    from streamlit_echarts import st_echarts
    
    st.divider() 

    st.subheader("👉​ Temas Detectados por Mes")
    st.markdown("Q. de Dolores y Q. de No se contactaron por nuestro Centros de Atención")

    # Convertir fechas por si vinieran en string
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # Crear columna mes con nombres en español
    df["mes_num"] = df["fecha"].dt.month
    df["mes_nombre"] = df["mes_num"].map({
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    })

    # Generar orden dinámico de los meses que efectivamente existen en el dataframe filtrado
    orden_meses = df["mes_nombre"].dropna().unique().tolist()
    orden_meses = sorted(orden_meses, key=lambda x: [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ].index(x))

    # Agrupar por tema y mes
    temas_por_mes = df.groupby(["tema_detectado", "mes_nombre"]).size().unstack(fill_value=0)
    temas_por_mes = temas_por_mes.reindex(columns=orden_meses, fill_value=0)

    # --- Nueva columna: No se contactan ---
    df["centro_atencion"] = df["centro_atencion"].fillna("").astype(str).str.lower().str.strip()
    df_no_contacto = df[df["centro_atencion"] == "no"]
    no_se_contactan = df_no_contacto.groupby("tema_detectado").size().rename("No se contactaron")

    # Unir con tabla principal
    tabla_completa = temas_por_mes.copy()
    tabla_completa["No se contactaron"] = no_se_contactan
    tabla_completa["No se contactaron"] = tabla_completa["No se contactaron"].fillna(0).astype(int)

    # Mostrar tabla final
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

#--- Palabras clave por tema detectado ---
def mostrar_palabras_clave(df):
    import streamlit as st
    from streamlit_echarts import st_echarts
    from temas_keywords import temas
    import pandas as pd

    df_original = df.copy()
    df_original["tema_detectado"] = df_original["verbatim"].apply(detectar_tema)
    df_detractores = df_original[df_original["grupo_nps"].astype(str).str.lower() == "detractor"]

    # ✅ Agregar columna de mes en texto (español)
    df_detractores["mes_num"] = df_detractores["fecha"].dt.month
    df_detractores["mes"] = df_detractores["mes_num"].map({
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    })

    st.divider() 

    # ─────────────────────────────────────────────
    #  BLOQUE: Insights por Tema Detectado
    # ─────────────────────────────────────────────
    st.subheader("🔍 Insights por Tema Detectado")
    st.markdown(
        "Búsqueda de palabras y frases clave dentro de los verbatims "
        "(clicá en la barra para ver el detalle)."
    )

    # ── Copia completa y columnas de mes
    df_original = df.copy()
    df_original["mes_num"] = df_original["fecha"].dt.month
    map_meses = {
        1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
        7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
    }
    df_original["mes"] = df_original["mes_num"].map(map_meses)
    df_original["tema_detectado"] = df_original["verbatim"].apply(detectar_tema)

    # ── Selector de tema
    temas_disponibles = sorted(df_original["tema_detectado"].dropna().unique())
    tema_filtrado = st.multiselect("🎯 Seleccioná uno o varios temas", temas_disponibles)
    if not tema_filtrado:
        st.info("📌 Elegí al menos un tema para continuar.")
        st.stop()

    # ── Construir df_palabras
    registros = []
    for tema in tema_filtrado:
        frases = temas.get(tema, [])
        st.markdown(f"**{tema.capitalize()}**: {', '.join(frases)}")
        for palabra in frases:
            subset = df_original[
                df_original["verbatim"]
                .astype(str)
                .str.lower()
                .str.contains(rf"\b{re.escape(palabra)}\b", regex=True)
            ]
            for _, fila in subset.iterrows():
                registros.append({"palabra": palabra, "mes": fila["mes"]})

    df_palabras = pd.DataFrame(registros)
    if df_palabras.empty:
        st.warning("⚠️ No se encontraron ocurrencias para las palabras clave.")
        st.stop()

    # ── Meses presentes (orden calendario)
    meses_presentes = df_palabras["mes"].unique().tolist()
    meses_orden = [map_meses[m] for m in sorted(
        [k for k,v in map_meses.items() if v in meses_presentes]
    )]

    # ── Pivot y top-N
    pivot_top = (
        df_palabras.assign(conteo=1)
        .groupby(["palabra", "mes"])["conteo"].sum()
        .reset_index()
        .pivot_table(index="palabra", columns="mes", values="conteo",
                    aggfunc="sum", fill_value=0)
        .reindex(columns=meses_orden, fill_value=0)
    )
    top_n = st.slider("🔢 Top N palabras", 3, 30, 10)
    pivot_top = pivot_top.loc[
        pivot_top.sum(axis=1).sort_values(ascending=False).head(top_n).index
    ]

    st.dataframe(pivot_top)

    # ── Gráfico con evento click
    chart_data = [
        {
            "name": mes,
            "type": "bar",
            "stack": "total",
            "label": {"show": True},
            "emphasis": {"focus": "series"},
            "data": pivot_top[mes].tolist(),
        }
        for mes in meses_orden
    ]

    options_kw = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": meses_orden},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": pivot_top.index.tolist()},
        "series": chart_data,
    }

    clicked_word = st_echarts(
        options_kw,
        events={"click": "function(params){ return params.name; }"},
        height="500px",
    )

    # ── Tabla de verbatims filtrada
    if clicked_word:
        st.subheader(f"📝 Verbatims con «{clicked_word}»")
        verbatims = (
            df_original[
                df_original["verbatim"]
                .astype(str)
                .str.lower()
                .str.contains(rf"\b{re.escape(clicked_word.lower())}\b", regex=True)
            ][["solo_fecha", "localidad", "grupo_nps", "categoria", "verbatim"]]
            .sort_values("solo_fecha")
        )
        st.dataframe(verbatims, use_container_width=True)
    else:
        st.caption("💡 Hacé clic en una barra para ver los verbatims asociados.")



