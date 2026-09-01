# Proyecto Final - Analisis de Datos
# RespirAburra: monitor de calidad del aire (PM2.5) del Valle de Aburra
# Datos abiertos de SIATA / Area Metropolitana del Valle de Aburra
# https://datosabiertos.metropol.gov.co/node/99

import os

import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq

# para que los CSV se encuentren sin importar desde donde se ejecute la app
os.chdir(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="RespirAburrá", page_icon="🌬️", layout="wide")

# umbrales de referencia para PM2.5 promedio en 24 horas (µg/m3)
GUIA_OMS = 15   # guia de la Organizacion Mundial de la Salud (2021)
NORMA_COL = 37  # norma colombiana (Resolucion 2254 de 2017)

COLORES_ICA = {
    "Buena": "#4caf50",
    "Aceptable": "#ffc107",
    "Dañina para grupos sensibles": "#ff9800",
    "Dañina para la salud": "#f44336",
}


# categorias del Indice de Calidad del Aire (ICA) para PM2.5 en 24 horas
# segun la Resolucion 2254 de 2017 del Ministerio de Ambiente
def categoria_ica(valor):
    if valor <= 12.5:
        return "Buena"
    elif valor <= 37.5:
        return "Aceptable"
    elif valor <= 55.4:
        return "Dañina para grupos sensibles"
    else:
        return "Dañina para la salud"


@st.cache_data
def cargar_datos():
    mediciones = pd.read_csv("data/pm25_horario.csv", parse_dates=["fecha"])
    estaciones = pd.read_csv("data/estaciones.csv")
    df = mediciones.merge(estaciones, on="codigo")
    return df, estaciones


df, estaciones = cargar_datos()

# ------------------- barra lateral: filtros -------------------
st.sidebar.title("🔍 Filtros")

municipios = sorted(df["municipio"].unique())
municipios_sel = st.sidebar.multiselect("Municipio", municipios, default=municipios)

estaciones_disp = sorted(df[df["municipio"].isin(municipios_sel)]["nombre_corto"].unique())
estaciones_sel = st.sidebar.multiselect("Estación", estaciones_disp, default=estaciones_disp)

dia_min = df["fecha"].min().date()
dia_max = df["fecha"].max().date()
rango = st.sidebar.date_input("Rango de fechas", (dia_min, dia_max),
                              min_value=dia_min, max_value=dia_max)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Análisis con IA")
api_key = st.sidebar.text_input("API Key de Groq", type="password",
                                help="Se consigue gratis en https://console.groq.com")

if len(rango) != 2:
    st.info("Selecciona la fecha final del rango en la barra lateral.")
    st.stop()

datos = df[(df["municipio"].isin(municipios_sel))
           & (df["nombre_corto"].isin(estaciones_sel))
           & (df["fecha"].dt.date >= rango[0])
           & (df["fecha"].dt.date <= rango[1])]

if datos.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# promedio diario por estacion (el ICA de PM2.5 se calcula sobre 24 horas)
diario = (datos.assign(dia=datos["fecha"].dt.date)
          .groupby(["dia", "nombre_corto", "municipio"], as_index=False)["pm25"].mean())
diario["categoria"] = diario["pm25"].apply(categoria_ica)

# promedio diario de toda la zona seleccionada (para la serie de tiempo)
diario_general = diario.groupby("dia", as_index=False)["pm25"].mean()

# ------------------- titulo y KPIs -------------------
st.title("🌬️ RespirAburrá")
st.markdown("**¿Qué aire respiramos en el Valle de Aburrá?** Análisis de material particulado "
            "PM2.5 con datos abiertos de la red de monitoreo de SIATA "
            f"({dia_min.strftime('%b %Y')} – {dia_max.strftime('%b %Y')}).")

promedio = datos["pm25"].mean()
dias_sobre_oms = (diario_general["pm25"] > GUIA_OMS).sum()
pct_oms = dias_sobre_oms / len(diario_general) * 100
dias_sobre_norma = (diario["pm25"] > NORMA_COL).groupby(diario["dia"]).any().sum()
prom_estacion = diario.groupby("nombre_corto")["pm25"].mean()
peor_estacion = prom_estacion.idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Promedio PM2.5", f"{promedio:.1f} µg/m³",
          f"{promedio - GUIA_OMS:+.1f} vs guía OMS", delta_color="inverse")
c2.metric("Días sobre la guía OMS (15)", f"{dias_sobre_oms} días", f"{pct_oms:.0f}% del periodo",
          delta_color="off")
c3.metric("Días con alguna estación sobre la norma (37)", f"{dias_sobre_norma} días")
c4.metric("Estación más contaminada", peor_estacion, f"{prom_estacion.max():.1f} µg/m³",
          delta_color="off")

# ------------------- pestañas -------------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencia", "📍 Estaciones", "🕐 Patrones", "🤖 Informe con IA"])

# --- pestaña 1: serie de tiempo
with tab1:
    st.subheader("Evolución diaria del PM2.5")
    fig = px.line(diario_general, x="dia", y="pm25",
                  labels={"dia": "Fecha", "pm25": "PM2.5 (µg/m³)"})
    fig.add_hline(y=GUIA_OMS, line_dash="dash", line_color="orange",
                  annotation_text="Guía OMS (15)")
    fig.add_hline(y=NORMA_COL, line_dash="dash", line_color="red",
                  annotation_text="Norma colombiana (37)")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("¿Cómo se reparten los días según el ICA?")
    conteo = diario["categoria"].value_counts().reset_index()
    conteo.columns = ["categoria", "dias"]
    fig2 = px.pie(conteo, names="categoria", values="dias",
                  color="categoria", color_discrete_map=COLORES_ICA, hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Cada porción cuenta días-estación clasificados con el Índice de Calidad "
               "del Aire (Resolución 2254 de 2017).")

# --- pestaña 2: comparacion de estaciones
with tab2:
    st.subheader("Promedio de PM2.5 por estación")
    ranking = diario.groupby(["nombre_corto", "municipio"], as_index=False)["pm25"].mean()
    ranking["categoria"] = ranking["pm25"].apply(categoria_ica)
    ranking = ranking.sort_values("pm25", ascending=True)
    fig3 = px.bar(ranking, x="pm25", y="nombre_corto", orientation="h",
                  color="categoria", color_discrete_map=COLORES_ICA,
                  hover_data=["municipio"],
                  labels={"pm25": "PM2.5 promedio (µg/m³)", "nombre_corto": "Estación"})
    st.plotly_chart(fig3, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Ubicación de las estaciones")
        mapa = estaciones[estaciones["nombre_corto"].isin(estaciones_sel)]
        st.map(mapa[["lat", "lon"]])
    with col_b:
        st.subheader("Semáforo por estación")
        tabla = ranking.sort_values("pm25", ascending=False).copy()
        tabla["pm25"] = tabla["pm25"].round(1)
        tabla.columns = ["Estación", "Municipio", "PM2.5 promedio", "Categoría ICA"]
        st.dataframe(tabla, use_container_width=True, hide_index=True)

# --- pestaña 3: patrones por hora y por mes
with tab3:
    st.subheader("¿A qué horas se contamina más el aire?")
    por_hora = datos.groupby(datos["fecha"].dt.hour)["pm25"].mean().reset_index()
    por_hora.columns = ["hora", "pm25"]
    fig4 = px.area(por_hora, x="hora", y="pm25",
                   labels={"hora": "Hora del día", "pm25": "PM2.5 promedio (µg/m³)"})
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("El pico de la mañana coincide con la hora pico vehicular.")

    st.subheader("¿Qué meses son los más críticos?")
    por_mes = datos.groupby(datos["fecha"].dt.strftime("%Y-%m"))["pm25"].mean().reset_index()
    por_mes.columns = ["mes", "pm25"]
    fig5 = px.bar(por_mes, x="mes", y="pm25",
                  labels={"mes": "Mes", "pm25": "PM2.5 promedio (µg/m³)"})
    fig5.add_hline(y=GUIA_OMS, line_dash="dash", line_color="orange")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("En este periodo los meses más críticos fueron febrero y marzo, que coinciden con "
               "la temporada de menor dispersión atmosférica en el Valle de Aburrá.")

# --- pestaña 4: informe generado con IA + chat
with tab4:
    # resumen de los datos filtrados que se le envia al modelo (datos agregados, no crudos)
    resumen_datos = f"""
Periodo analizado: {rango[0]} a {rango[1]}
Municipios: {", ".join(municipios_sel)}
Numero de estaciones: {len(estaciones_sel)}
Promedio general de PM2.5: {promedio:.1f} µg/m3
Dias con promedio sobre la guia OMS de 15 µg/m3: {dias_sobre_oms} de {len(diario_general)} ({pct_oms:.0f}%)
Dias con alguna estacion sobre la norma colombiana de 37 µg/m3: {dias_sobre_norma}
Top 5 estaciones mas contaminadas (promedio diario en µg/m3):
{prom_estacion.sort_values(ascending=False).head(5).round(1).to_string()}
Top 3 estaciones menos contaminadas:
{prom_estacion.sort_values().head(3).round(1).to_string()}
Promedio por hora del dia (µg/m3):
{por_hora.round(1).to_string(index=False)}
Promedio por mes (µg/m3):
{por_mes.round(1).to_string(index=False)}
"""

    st.subheader("Informe ejecutivo generado con IA")
    st.write("El botón envía los **indicadores agregados** del periodo filtrado al modelo "
             "`openai/gpt-oss-120b` (vía Groq) y este redacta un informe en español.")

    if st.button("✨ Generar informe con IA"):
        if not api_key:
            st.warning("Primero ingresa tu API Key de Groq en la barra lateral.")
        else:
            try:
                client = Groq(api_key=api_key)
                with st.spinner("Analizando los datos..."):
                    respuesta = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {"role": "system",
                             "content": "Eres un analista ambiental. Redacta en español un informe "
                                        "ejecutivo breve (maximo 400 palabras) sobre la calidad del aire "
                                        "del Valle de Aburra con los datos que te entregan: hallazgos "
                                        "principales, comparacion con la guia OMS y la norma colombiana, "
                                        "zonas y horarios criticos, y 3 recomendaciones practicas."},
                            {"role": "user", "content": resumen_datos},
                        ],
                    )
                st.session_state["informe"] = respuesta.choices[0].message.content
            except Exception as e:
                st.error(f"Error llamando a la API de Groq: {e}")

    if "informe" in st.session_state:
        st.markdown(st.session_state["informe"])
        st.download_button("⬇️ Descargar informe (.txt)", st.session_state["informe"],
                           file_name="informe_calidad_aire.txt")

    # chat para hacerle preguntas a los datos
    st.markdown("---")
    st.subheader("💬 Pregúntale a los datos")

    if "mensajes" not in st.session_state:
        st.session_state["mensajes"] = []

    for m in st.session_state["mensajes"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    pregunta = st.chat_input("Ej: ¿por qué Tráfico Sur es la estación más contaminada?")
    if pregunta:
        if not api_key:
            st.warning("Primero ingresa tu API Key de Groq en la barra lateral.")
        else:
            st.session_state["mensajes"].append({"role": "user", "content": pregunta})
            with st.chat_message("user"):
                st.markdown(pregunta)
            try:
                client = Groq(api_key=api_key)
                with st.spinner("Pensando..."):
                    respuesta = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {"role": "system",
                             "content": "Eres un asistente que responde preguntas sobre la calidad del "
                                        "aire del Valle de Aburra usando UNICAMENTE este resumen de datos. "
                                        "Si la pregunta no se puede responder con los datos, dilo con "
                                        "honestidad. Responde en español y de forma corta.\n"
                                        + resumen_datos},
                        ] + st.session_state["mensajes"][-6:],
                    )
                texto = respuesta.choices[0].message.content
                st.session_state["mensajes"].append({"role": "assistant", "content": texto})
                with st.chat_message("assistant"):
                    st.markdown(texto)
            except Exception as e:
                st.error(f"Error llamando a la API de Groq: {e}")

# ------------------- pie de pagina -------------------
st.markdown("---")
st.caption("Fuente: red de monitoreo de calidad del aire de SIATA — Portal de Datos Abiertos "
           "del Área Metropolitana del Valle de Aburrá. Datos limpiados con `limpiar_datos.py` "
           "(solo registros con bandera de calidad válida).")
