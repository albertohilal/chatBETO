#!/usr/bin/env python3
"""
Agregar los 26 proyectos faltantes a la base de datos
"""

import mysql.connector
import json
import re
from datetime import datetime

def agregar_proyectos_faltantes():
    """Agregar todos los proyectos faltantes de la lista completa"""
    
    print("🚀 AGREGANDO PROYECTOS FALTANTES")
    
    # Leer lista completa de proyectos
    with open('Auxiliar/ListadoProyectos.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraer nombres de proyectos (sin fechas) y guardar fechas
    projects_from_list = []
    lines = content.strip().split('\n')
    
    for line in lines:
        if line.strip() and not line.startswith('TOTAL:'):
            # Extraer fecha si existe
            date_match = re.search(r'\(([^)]+)\)', line)
            date_info = date_match.group(1) if date_match else 'Sin fecha'
            
            # Remover fecha y símbolos para obtener nombre limpio
            name = re.sub(r'\s*\([^)]+\)\s*⭐?', '', line.strip())
            name = name.replace('⭐', '').strip()
            
            if name:
                projects_from_list.append({
                    'name': name,
                    'date_info': date_info,
                    'is_starred': '⭐' in line
                })

    print(f"📋 Total proyectos en lista: {len(projects_from_list)}")

    # Conectar a BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Obtener proyectos existentes
    cursor.execute('SELECT name FROM projects')
    existing_projects = {row[0] for row in cursor.fetchall()}
    
    print(f"🗄️ Proyectos existentes en BD: {len(existing_projects)}")

    # Identificar proyectos faltantes
    missing_projects = []
    for project in projects_from_list:
        if project['name'] not in existing_projects:
            missing_projects.append(project)

    print(f"❌ Proyectos a agregar: {len(missing_projects)}")

    if not missing_projects:
        print("✅ Todos los proyectos ya están en la BD")
        return

    # Insertar proyectos faltantes
    print(f"\n📝 INSERTANDO {len(missing_projects)} PROYECTOS:")
    
    inserted_count = 0
    for i, project in enumerate(missing_projects, 1):
        try:
            # Crear descripción basada en la información disponible
            description = f"Proyecto desde lista móvil ({project['date_info']})"
            if project['is_starred']:
                description += " ⭐ Destacado"
            
            # Insertar proyecto
            cursor.execute("""
                INSERT INTO projects (name, description, is_starred) 
                VALUES (%s, %s, %s)
            """, (project['name'], description, 1 if project['is_starred'] else 0))
            
            inserted_count += 1
            print(f"   {i:2d}. ✅ {project['name']} ({project['date_info']})")
            
        except mysql.connector.Error as e:
            print(f"   {i:2d}. ❌ {project['name']} - Error: {e}")

    # Confirmar cambios
    conn.commit()
    
    # Verificar resultado final
    cursor.execute('SELECT COUNT(*) FROM projects')
    total_projects = cursor.fetchone()[0]
    
    print(f"\n🎉 RESULTADO:")
    print(f"   ✅ Proyectos insertados: {inserted_count}")
    print(f"   📊 Total proyectos en BD: {total_projects}")
    print(f"   🎯 Objetivo (66 proyectos): {'✅ ALCANZADO' if total_projects >= 66 else '⚠️ Faltan ' + str(66 - total_projects)}")

    # Mostrar algunos de los proyectos recién agregados
    if inserted_count > 0:
        print(f"\n📋 ÚLTIMOS PROYECTOS AGREGADOS:")
        cursor.execute("""
            SELECT id, name, description, created_at 
            FROM projects 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        for project in cursor.fetchall():
            print(f"   ID: {project[0]} | {project[1]} | {project[2]}")

    cursor.close()
    conn.close()
    
    return inserted_count

if __name__ == "__main__":
    agregar_proyectos_faltantes()