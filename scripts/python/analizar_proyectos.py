#!/usr/bin/env python3
import re
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Leer proyectos del listado
with open('proyectos_nombres.txt', 'r', encoding='utf-8') as f:
    proyectos = [line.strip() for line in f if line.strip()]

# Leer títulos de conversaciones  
with open('extracted/titulos_conversaciones.txt', 'r', encoding='utf-8') as f:
    titulos = [line.strip() for line in f if line.strip()]

print(f"Total de proyectos en listado: {len(proyectos)}")
print(f"Total de conversaciones: {len(titulos)}")
print("\n=== ANÁLISIS DE COINCIDENCIAS ===\n")

encontrados = []
no_encontrados = []

for proyecto in proyectos:
    mejor_coincidencia = None
    mejor_score = 0
    
    # Buscar coincidencias exactas o parciales
    coincidencias_exactas = []
    coincidencias_parciales = []
    
    for titulo in titulos:
        # Coincidencia exacta (ignorando case)
        if proyecto.lower() == titulo.lower():
            coincidencias_exactas.append(titulo)
        # Coincidencia parcial (proyecto contenido en título)
        elif proyecto.lower() in titulo.lower():
            coincidencias_parciales.append(titulo)
        # Similarity score alto
        score = similarity(proyecto, titulo)
        if score > mejor_score:
            mejor_score = score
            mejor_coincidencia = titulo
    
    if coincidencias_exactas:
        print(f"✅ EXACTA - '{proyecto}' → {coincidencias_exactas}")
        encontrados.append(proyecto)
    elif coincidencias_parciales:
        print(f"🔍 PARCIAL - '{proyecto}' → {coincidencias_parciales[:3]}")  # Solo mostrar primeras 3
        encontrados.append(proyecto)
    elif mejor_score > 0.6:  # Similarity alta
        print(f"🤔 SIMILAR - '{proyecto}' → '{mejor_coincidencia}' (score: {mejor_score:.2f})")
        encontrados.append(proyecto)
    else:
        print(f"❌ NO ENCONTRADO - '{proyecto}' (mejor: '{mejor_coincidencia}' score: {mejor_score:.2f})")
        no_encontrados.append(proyecto)

print(f"\n=== RESUMEN ===")
print(f"Proyectos encontrados: {len(encontrados)}/{len(proyectos)}")
print(f"Proyectos no encontrados: {len(no_encontrados)}")

if no_encontrados:
    print(f"\nProyectos no encontrados:")
    for p in no_encontrados:
        print(f"  - {p}")
