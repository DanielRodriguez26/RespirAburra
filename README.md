# 🌬️ RespirAburrá

Proyecto final del curso de Análisis de Datos.

Dashboard interactivo para analizar la calidad del aire (material particulado PM2.5)
del Valle de Aburrá, usando un año de datos abiertos de la red de monitoreo de SIATA
(18 estaciones, más de 147.000 mediciones horarias). Incluye un informe ejecutivo
generado con IA (Groq) y un chat para hacerle preguntas a los datos.

## 📊 ¿Qué se puede hacer?

- Filtrar por municipio, estación y rango de fechas
- Ver KPIs: promedio de PM2.5, días sobre la guía OMS y la norma colombiana
- Tendencia diaria, ranking de estaciones, semáforo ICA, mapa
- Patrones por hora del día y por mes
- 🤖 Generar un informe ejecutivo con IA y chatear con los datos

## 📁 Archivos

- `app.py` — la aplicación (Streamlit)
- `limpiar_datos.py` — limpieza del dataset original de SIATA
- `exportar_web.py` — genera los datos agregados para la página web
- `data/estaciones.csv` y `data/pm25_horario.csv` — datos ya limpios
- `web/` — página web interactiva (HTML + Plotly.js, se despliega en Vercel)
- `requirements.txt` — dependencias

## 🚀 Cómo correrla local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para el informe con IA se necesita una API Key gratuita de https://console.groq.com
(se ingresa en la barra lateral de la app).

## ☁️ Cómo desplegarla

1. Subir el repo a GitHub
2. Entrar a https://share.streamlit.io con la cuenta de GitHub
3. New app → elegir el repo → archivo principal `app.py` → Deploy

## 📚 Fuente de los datos

Portal de Datos Abiertos del Área Metropolitana del Valle de Aburrá:
"Mediciones estaciones calidad del aire" (red SIATA).
https://datosabiertos.metropol.gov.co/node/99

La limpieza descarta los datos con bandera de calidad inválida y los valores
centinela (-9999 y 99999). El detalle está en `limpiar_datos.py`.
