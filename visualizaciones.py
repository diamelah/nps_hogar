import streamlit as st
import pandas as pd
import re
import altair as alt
from streamlit_echarts import st_echarts
from dolores_keywords import dolores
from unidecode import unidecode
from dolor_detector import detectar_dolor


# --- Detectar dolor (usa dolores importado globalmente) ---
def detectar_dolores(texto, dolores_dict):
    texto = str(texto).lower()
    palabras = texto.split()
    encontrados = []
    texto = unidecode(str(texto).lower())
    palabras_texto = set(texto.replace(",", "").replace(".", "").split())

    for dolor, tokens in dolores.items():
        for token in tokens:
            token = unidecode(token.lower())
            if "+" in token:
                subpalabras = set(token.split("+"))
                if subpalabras.issubset(palabras_texto):
                    return dolor
            else:
                if token in texto:
                    return dolor
    return None


# --- Mostrar análisis temático de verbatims ---
def mostrar_analisis_tematica(df):
    st.subheader("👉​ Análisis de Verbatims")

    # Detectar doloress si falta la columna
    if "dolor_detectado" not in df.columns:
        df["dolor_detectado"] = df["verbatim"].apply(detectar_dolor)

    # Función para detectar verbatims sin letras (solo símbolos/números)
    import re
    def es_basura(txt: str) -> bool:
        txt = str(txt)
        return not bool(re.search(r"[A-Za-záéíóúüñ]", txt))

    # Selector de filtro para verbatims
    opcion = st.radio(
        "🔀 Tipo de verbatim:",
        ["Todos", "Solo válidos (con letras)", "Solo basura (sin letras)"],
        horizontal=True,
        key="radio_basura"
    )

    # Base de datos según filtro basura/válido
    df_base = df.copy()
    if opcion == "Solo válidos (con letras)":
        df_base = df_base[~df_base["verbatim"].astype(str).apply(es_basura)]
    elif opcion == "Solo basura (sin letras)":
        df_base = df_base[df_base["verbatim"].astype(str).apply(es_basura)]

    # Iniciamos df_dolores con df_base
    df_dolores = df_base.copy()

    # Checkbox para verbatims largos (siempre disponible)
    filtrar_largos = st.checkbox(
        "📝 Mostrar solo verbatims con más de 25 palabras",
        key="chk_largos"
    )
    if filtrar_largos:
        df_dolores = df_dolores[df_dolores["verbatim"].astype(str)
                        .apply(lambda x: len(x.split()) > 25)]

    # Multiselect para doloress detectados (si aplica)
    dolores_disp = [t for t in df_dolores["dolor_detectado"].unique() if t is not None]
    dolores_disp.sort()
    dolor_filtrar = st.multiselect(
        "🌟 Filtrar por dolor detectado",
        dolores_disp,
        key="ms_dolores"
    )
    if dolor_filtrar:
        df_dolores = df_dolores[df_dolores["dolor_detectado"].isin(dolor_filtrar)]
        st.markdown("### 🔠 Frases clave del dolor detectado")
        for dolor in dolor_filtrar:
            frases = dolores.get(dolor, [])
            st.markdown(f"**{dolor.capitalize()}**: {', '.join(frases)}")

    # Búsqueda de palabras exactas (siempre disponible)
    search_dolor = st.text_input(
        "🔎 Búsqueda por palabras (puedes separar con comas)",
        key="txt_buscar"
    )
    if search_dolor:
        palabras = [p.strip().lower() for p in search_dolor.split(",") if p.strip()]
        # construimos un patrón que coincida palabra a palabra
        pattern = "|".join(rf"\b{re.escape(p)}\b" for p in palabras)

        # Mascara sobre verbatim
        mask_verbatim = (
            df_dolores["verbatim"]
            .astype(str)
            .str.lower()
            .str.contains(pattern, regex=True)
        )
        # Mascara sobre no_por_que (llenamos nulos con cadena vacía)
        mask_no_por = (
            df_dolores["no_por_que"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(pattern, regex=True)
        )

        # Filtramos filas donde aparezca en cualquiera de las dos columnas
        df_dolores = df_dolores[mask_verbatim | mask_no_por]

    # Mostrar la tabla final con todos los campos
    columnas = [
        "solo_fecha", "cuenta_codigo", "localidad", "grupo_nps", "nps", "verbatim", "pri_causa_raiz",
        "seg_causa_raiz_Aten.Clientes", "seg_causa_raiz_Serv.Tecn.", "seg_causa_raiz_Fact.Pago", "dolor_detectado", "centro_atencion", 
        "llamados_30D", "canal_atencion", "se_resolvio?", "no_por_que", "app_mipersonal_flow"
    ]
    cols_disp = [c for c in columnas if c in df_dolores.columns]
    st.dataframe(df_dolores[cols_disp], use_container_width=True)

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
    "<h3 style='font-size:22px; margin-bottom:0.5rem'>🎯​ Dolores Detectados en Scores Críticos: 0, 1 y 8</h3>",
    unsafe_allow_html=True
    )

    if "dolor_detectado" in df.columns and not df_dolores.empty:
        df_filtrado = df_dolores.copy()

        resumen = (
            df_filtrado
            .loc[df_filtrado["score"].isin([0, 1, 8])]  # Filtrar solo scores 0, 1, 8
            .groupby("dolor_detectado")
            .agg(
                cantidad=("dolor_detectado", "count"),
                porcentaje=("dolor_detectado", lambda x: 100 * len(x) / len(df_filtrado)),
                score_0=("score", lambda x: (x == 0).sum()),
                score_1=("score", lambda x: (x == 1).sum()),
                score_8=("score", lambda x: (x == 8).sum()),
                FTTH=('tecnologia', lambda x: (x.fillna('').str.strip().str.upper() == "FTTH").sum()),
                HFC=('tecnologia', lambda x: (x.fillna('').str.strip().str.upper() == "HFC").sum())
            )
            .reset_index()
        )

        resumen = resumen.rename(columns={
            "dolor_detectado": "Dolor",
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
        f"<h3 style='font-size:22px; margin-bottom:0.5rem'>🎯 Dolores Detectados: Score → {tec_sel}</h3>",
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
        index="dolor_detectado",
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
        #st.markdown("#### 📊 Verbatims por Dolor y SCORE")
        mostrar_evolucion_score(df)
        

#--- Verbatims por Dolores Detectados y SCORE---
        
def mostrar_evolucion_score(df):
    import streamlit as st
    import altair as alt

    st.markdown(
    "<h3 style='font-size:22px; margin-bottom:0.5rem'>🔠​ Verbatims por Dolores Detectados y SCORE</h3>",
    unsafe_allow_html=True
    )

    df["score"] = pd.to_numeric(df["score"], errors='coerce')
    df_valid = df[df["score"].isin([0, 1, 8]) & df["dolor_detectado"].notna()].copy()

    # 🔢 Obtener todos los dolores detectados disponibles
    dolores_disponibles = sorted(df_valid["dolor_detectado"].dropna().unique())

    # 🎯 Selector interactivo con multiselección
    dolores_seleccionados = st.multiselect(
        "🎯 Seleccioná los Dolores a visualizar",
        options=dolores_disponibles,
        default=dolores_disponibles[:5],  # top 5 por defecto
        key="multiselect_score"
    )

    if not dolores_seleccionados:
        st.info("📌 Seleccioná al menos un dolor para mostrar el gráfico.")
        return

    df_filtrado = df_valid[df_valid["dolor_detectado"].isin(dolores_seleccionados)]

    resumen = (
        df_filtrado.groupby(["dolor_detectado", "score"])
        .size()
        .reset_index(name="cantidad")
    )

    chart = alt.Chart(resumen).mark_bar().encode(
        x=alt.X('dolor_detectado:N', title='Dolor Detectado', axis=alt.Axis(labelAngle=-10, labelLimit=300)),
        xOffset='score:N',
        y=alt.Y('cantidad:Q', title='Cantidad de Verbatims'),
        color=alt.Color('score:N', title='SCORE', scale=alt.Scale(
            domain=[0, 1, 8],
            range=["#007bff", "#ff7f0e", "#2ca02c"]
        )),
        tooltip=['dolor_detectado:N', 'score:N', 'cantidad:Q']
    ).properties(
        width=800,
        height=400,
        title="Verbatims por Dolor y Score"
    )

    st.altair_chart(chart, use_container_width=True)

 

import pandas as pd
from streamlit_echarts import st_echarts

def mostrar_detractores_por_dolor(df):
    import streamlit as st
    from dolores_keywords import dolores

    df_original = df.copy()
    df_original["dolor_detectado"] = df_original["verbatim"].apply(detectar_dolor)
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

    dolores_por_mes = df_detractores.groupby(["dolor_detectado", "mes_nombre"]).size().unstack(fill_value=0)
    orden_meses = ["Enero", "Febrero", "Marzo"]
    dolores_por_mes = dolores_por_mes.reindex(columns=orden_meses, fill_value=0)
    

    

#--- Cantidad de dolores detectados por mes ---
def mostrar_dolores_por_mes(df):
    st.divider() 

    st.subheader("👉​ Dolores Detectados por Mes")
    st.markdown("Dolores de clientes - Contacto / No Contacto")

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

    # Agrupar por dolor y mes
    dolores_por_mes = df.groupby(["dolor_detectado", "mes_nombre"]).size().unstack(fill_value=0)
    dolores_por_mes = dolores_por_mes.reindex(columns=orden_meses, fill_value=0)

    # --- Nueva columna: No se contactan ---
    df["centro_atencion"] = df["centro_atencion"].fillna("").astype(str).str.lower().str.strip()
    df_no_contacto = df[df["centro_atencion"] == "no"]
    no_se_contactan = df_no_contacto.groupby("dolor_detectado").size().rename("No se contactaron")

    # Unir con tabla principal
    tabla_completa = dolores_por_mes.copy()
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
            "data": dolores_por_mes[mes].tolist()
        } for mes in orden_meses if mes in dolores_por_mes.columns
    ]

    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": orden_meses},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": dolores_por_mes.index.tolist()},
        "series": chart_data
    }

    # Capturar clic en barra
    event = {
        "click": "function(params) { return { mes: params.seriesName, dolor: params.name }; }"
    }

    result = st_echarts(options=options, height="500px", events=event)

    # Mostrar verbatims al hacer clic en una barra
    if result and "mes" in result and "dolor" in result:
        mes_click = result["mes"]
        dolor_click = result["dolor"]

        st.subheader(f"📝 Verbatims de «{dolor_click}» en «{mes_click}»")

        if "mes_nombre" not in df.columns:
            df["mes_num"] = df["fecha"].dt.month
            df["mes_nombre"] = df["mes_num"].map({
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            })

        verbatims = df[
            (df["dolor_detectado"] == dolor_click) &
            (df["mes_nombre"] == mes_click)
        ]["verbatim"].dropna()

        if not verbatims.empty:
            st.dataframe(verbatims.to_frame().reset_index(drop=True))
        else:
            st.info("No se encontraron verbatims para esta combinación.")
    
    st.divider()




    # ─────────────────────────────────────────────
    #  BLOQUE: Insights por Dolor Detectado
    # ─────────────────────────────────────────────
    st.subheader("🔍 Insights por Dolor Detectado")
    st.markdown(
        "Búsqueda de palabras y frases clave dentro de los verbatims "
        
    )

    # ── Copia completa y columnas de mes
    df_original = df.copy()
    df_original["mes_num"] = df_original["fecha"].dt.month
    map_meses = {
        1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
        7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
    }
    df_original["mes"] = df_original["mes_num"].map(map_meses)
    df_original["dolor_detectado"] = df_original["verbatim"].apply(detectar_dolor)

    # ── Selector de dolor
    dolores_disponibles = sorted(df_original["dolor_detectado"].dropna().unique())
    dolor_filtrado = st.multiselect("🎯 Seleccioná uno o varios dolores", dolores_disponibles)
    if not dolor_filtrado:
        st.info("📌 Elegí al menos un dolor para continuar.")
        st.stop()

    # ── Construir df_palabras
    registros = []
    for dolor in dolor_filtrado:
        frases = dolores.get(dolor, [])
        st.markdown(f"**{dolor.capitalize()}**: {', '.join(frases)}")
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
            ][["solo_fecha", "localidad", "grupo_nps", "pri_causa_raiz", "verbatim"]]
            .sort_values("solo_fecha")
        )
        st.dataframe(verbatims, use_container_width=True)
    else:
        st.caption("💡 Hacé clic en una barra para ver los verbatims asociados.")
        

