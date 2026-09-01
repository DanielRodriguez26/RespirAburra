# Proyecto Final - Analisis de Datos
# Genera web/datos.js con los datos agregados POR ESTACION para la pagina web interactiva.
# Con estos datos la pagina puede recalcular KPIs y graficas al filtrar, sin backend.
# Se corre despues de limpiar_datos.py

import csv
import json
import os
from collections import defaultdict

os.makedirs("web", exist_ok=True)

# cargo las estaciones
estaciones = []
with open("data/estaciones.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        estaciones.append({
            "c": int(r["codigo"]),
            "e": r["nombre_corto"],
            "n": r["estacion"],
            "m": r["municipio"],
        })

# agrupo por (estacion, dia) y por (estacion, mes, hora)
por_dia = defaultdict(list)
por_mes_hora = defaultdict(list)
with open("data/pm25_horario.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = int(r["codigo"])
        v = float(r["pm25"])
        por_dia[(c, r["fecha"][:10])].append(v)
        por_mes_hora[(c, r["fecha"][:7], int(r["fecha"][11:13]))].append(v)

# con 2 decimales para que los conteos contra los umbrales (15 y 37) den igual que en la app
prom = lambda x: round(sum(x) / len(x), 2)

# listas compactas para que el archivo no quede pesado:
# diario   -> [codigo, "aaaa-mm-dd", promedio_del_dia, num_mediciones]
# mes_hora -> [codigo, "aaaa-mm", hora, promedio, num_mediciones]
# (num_mediciones sirve para calcular promedios ponderados iguales a los de la app)
diario = [[c, d, prom(v), len(v)] for (c, d), v in sorted(por_dia.items(), key=lambda x: (x[0][1], x[0][0]))]
mes_hora = [[c, m, h, prom(v), len(v)] for (c, m, h), v in sorted(por_mes_hora.items())]

datos = {"estaciones": estaciones, "diario": diario, "mes_hora": mes_hora}

with open(os.path.join("web", "datos.js"), "w", encoding="utf-8") as f:
    f.write("// generado por exportar_web.py - no editar a mano\n")
    f.write("const DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n")

peso = os.path.getsize(os.path.join("web", "datos.js")) / 1024
print(f"web/datos.js generado: {len(diario)} filas diarias, {len(mes_hora)} filas mes-hora, {peso:.0f} KB")
