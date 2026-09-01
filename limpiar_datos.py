# Proyecto Final - Analisis de Datos
# Script para limpiar los datos de PM2.5 de SIATA (datos abiertos del Area Metropolitana)
# Descargue el archivo de aca:
# https://datosabiertos.metropol.gov.co/sites/default/files/uploaded_resources/Datos_SIATA_Aire_pm25.json

import json
import csv

# la bandera "calidad" = 1.0 significa dato valido segun SIATA
# el valor -9999 es dato faltante y 99999 es dato invalido, por eso se descartan

with open("data/raw/Datos_SIATA_Aire_pm25.json", encoding="utf-8") as f:
    estaciones_json = json.load(f)

# estas dos estaciones no traen el municipio en el nombre
municipios_especiales = {12: "Medellín", 48: "La Estrella"}

estaciones = []
mediciones = []

for est in estaciones_json:
    nombre = (est.get("nombre") or "").strip()
    codigo = est["codigoSerial"]

    # las estaciones con prefijo _OFF estan fuera de servicio
    if nombre == "" or nombre.startswith("_OFF"):
        print("Excluida (fuera de servicio):", codigo, nombre)
        continue

    # me quedo solo con los datos validos y con valores que tengan sentido fisico
    validos = []
    for d in est["datos"]:
        if float(d["calidad"]) == 1.0 and 0 <= d["valor"] <= 500:
            validos.append((d["fecha"], round(d["valor"], 1)))

    # si la estacion tiene menos del 50% de datos del año, no sirve para el analisis
    cobertura = len(validos) / len(est["datos"])
    if cobertura < 0.5:
        print("Excluida (pocos datos):", codigo, nombre)
        continue

    # saco el municipio del nombre de la estacion, ej: "Bello - I.E. Fernando Velez" -> "Bello"
    if codigo in municipios_especiales:
        municipio = municipios_especiales[codigo]
    else:
        municipio = nombre.split(" - ")[0].split(",")[0].strip()
        if municipio == "Medellin":
            municipio = "Medellín"

    estaciones.append([codigo, nombre, est.get("nombreCorto", ""), municipio, est["latitud"], est["longitud"]])
    for fecha, valor in validos:
        mediciones.append([fecha, codigo, valor])

    print("OK:", codigo, nombre, "->", len(validos), "registros validos")

mediciones.sort()

with open("data/estaciones.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "estacion", "nombre_corto", "municipio", "lat", "lon"])
    w.writerows(estaciones)

with open("data/pm25_horario.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["fecha", "codigo", "pm25"])
    w.writerows(mediciones)

print()
print("Estaciones:", len(estaciones))
print("Mediciones validas:", len(mediciones))
