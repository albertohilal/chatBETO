#!/usr/bin/env python3
"""
Script para mapear gizmo_id de ChatGPT a proyectos y actualizar la base de datos
"""

import json
import mysql.connector
from collections import defaultdict

def mapear_gizmos_a_proyectos():
    """Mapea los gizmo_id de ChatGPT a nuestros proyectos"""
    
    # Cargar configuración DB
    with open('db_config.json', 'r') as f:
        config = json.load(f)
    
    # Cargar datos de conversaciones originales
    with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    # Cargar mapeo de proyectos
    with open('conversation_project_mapping.json', 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    # Crear mapeo conversation_id -> project_name
    conv_to_project = {}
    for conv in mapping_data['mapped_conversations']:
        conv_to_project[conv['conversation_id']] = conv['project_name']
    
    # Analizar gizmo_id por proyecto
    project_gizmos = defaultdict(list)
    
    print("🔍 Analizando gizmo_id por proyecto...")
    
    for conv in conversations:
        conv_id = conv.get('id')
        gizmo_id = conv.get('gizmo_id')
        title = conv.get('title', '')
        
        if not conv_id or not gizmo_id:
            continue
            
        project_name = conv_to_project.get(conv_id)
        if project_name:
            project_gizmos[project_name].append({
                'gizmo_id': gizmo_id,
                'conv_id': conv_id,
                'title': title[:50]
            })
    
    # Mostrar análisis
    print(f"\n📊 MAPEO GIZMO_ID -> PROYECTOS:")
    print(f"Proyectos con gizmo_id identificados: {len(project_gizmos)}")
    
    # Encontrar el gizmo_id más común por proyecto
    project_main_gizmo = {}
    
    for project_name, gizmos in project_gizmos.items():
        # Contar frecuencia de cada gizmo_id
        gizmo_count = defaultdict(int)
        for item in gizmos:
            gizmo_count[item['gizmo_id']] += 1
        
        # El más común
        main_gizmo = max(gizmo_count.items(), key=lambda x: x[1])
        project_main_gizmo[project_name] = {
            'gizmo_id': main_gizmo[0],
            'frequency': main_gizmo[1],
            'total_conversations': len(gizmos)
        }
        
        print(f"\n🎯 {project_name}:")
        print(f"   Gizmo principal: {main_gizmo[0]}")
        print(f"   Frecuencia: {main_gizmo[1]}/{len(gizmos)} conversaciones")
        
        # Mostrar otros gizmos si los hay
        other_gizmos = [(gid, count) for gid, count in gizmo_count.items() if gid != main_gizmo[0]]
        if other_gizmos:
            print(f"   Otros gizmos: {len(other_gizmos)}")
    
    # Actualizar base de datos
    print(f"\n🔄 Actualizando base de datos...")
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Actualizar projects con chatgpt_project_id (usando gizmo_id principal)
    for project_name, gizmo_info in project_main_gizmo.items():
        try:
            cursor.execute(
                "UPDATE projects SET chatgpt_project_id = %s WHERE name = %s",
                (gizmo_info['gizmo_id'], project_name)
            )
            print(f"✅ {project_name} -> {gizmo_info['gizmo_id']}")
        except Exception as e:
            print(f"❌ Error actualizando {project_name}: {e}")
    
    # Actualizar conversations con chatgpt_gizmo_id
    conversations_updated = 0
    for conv in conversations:
        conv_id = conv.get('id')
        gizmo_id = conv.get('gizmo_id')
        
        if conv_id and gizmo_id:
            try:
                cursor.execute(
                    "UPDATE conversations SET chatgpt_gizmo_id = %s WHERE id = %s",
                    (gizmo_id, conv_id)
                )
                conversations_updated += 1
            except Exception as e:
                pass  # Ignorar conversaciones que no están en nuestra DB
    
    conn.commit()
    
    print(f"\n✅ ACTUALIZACIÓN COMPLETADA:")
    print(f"   Proyectos actualizados: {len(project_main_gizmo)}")
    print(f"   Conversaciones actualizadas: {conversations_updated}")
    
    # Mostrar estadísticas finales
    cursor.execute("""
        SELECT p.name, p.chatgpt_project_id, COUNT(c.id) as conversations
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id AND c.chatgpt_gizmo_id = p.chatgpt_project_id
        WHERE p.chatgpt_project_id IS NOT NULL
        GROUP BY p.id, p.name, p.chatgpt_project_id
        ORDER BY conversations DESC
    """)
    
    print(f"\n📈 PROYECTOS CON CHATGPT PROJECT ID:")
    results = cursor.fetchall()
    for row in results:
        print(f"   {row[0]}: {row[2]} conversaciones (ID: {row[1][:20]}...)")
    
    cursor.close()
    conn.close()
    
    return project_main_gizmo

if __name__ == "__main__":
    print("🚀 Iniciando mapeo de gizmo_id a proyectos...")
    mapear_gizmos_a_proyectos()
    print("\n🎉 Mapeo completado!")