#!/usr/bin/env python3
"""
Importar TODAS las conversaciones del archivo conversations.json
"""

import json
import mysql.connector
from datetime import datetime

def importar_todas_las_conversaciones():
    """Importar todas las 1,532 conversaciones del archivo original"""
    
    print("🚀 IMPORTACIÓN COMPLETA DE CONVERSACIONES")
    
    # Conectar a BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Leer archivo conversations.json completo
    print("📂 Cargando conversations.json...")
    with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
        all_conversations = json.load(f)
    
    print(f"📊 Total conversaciones en archivo: {len(all_conversations)}")
    
    # Obtener conversaciones existentes
    cursor.execute("SELECT id FROM conversations")
    existing_conversations = {row['id'] for row in cursor.fetchall()}
    print(f"✅ Conversaciones ya importadas: {len(existing_conversations)}")
    
    # Obtener mapeo de gizmo_id a project_id
    cursor.execute("SELECT id, chatgpt_project_id FROM projects WHERE chatgpt_project_id IS NOT NULL")
    gizmo_to_project = {}
    for row in cursor.fetchall():
        gizmo_to_project[row['chatgpt_project_id']] = row['id']
    
    print(f"🗺️  Proyectos mapeables: {len(gizmo_to_project)}")
    
    # Estadísticas
    imported_count = 0
    skipped_count = 0
    mapped_count = 0
    orphan_count = 0
    error_count = 0
    
    print(f"\n🔄 PROCESANDO CONVERSACIONES...")
    
    for i, conv_data in enumerate(all_conversations):
        try:
            conv_id = conv_data.get('id')
            if not conv_id:
                error_count += 1
                continue
                
            # Saltar si ya existe
            if conv_id in existing_conversations:
                skipped_count += 1
                continue
            
            # Extraer datos
            title = conv_data.get('title', 'Sin título')[:500]  # Limitar longitud
            create_time = conv_data.get('create_time')
            update_time = conv_data.get('update_time') 
            gizmo_id = conv_data.get('gizmo_id')
            
            # Convertir timestamps
            created_at = None
            updated_at = None
            
            if create_time:
                try:
                    created_at = datetime.fromtimestamp(create_time)
                except:
                    pass
                    
            if update_time:
                try:
                    updated_at = datetime.fromtimestamp(update_time)
                except:
                    pass
            
            # Mapear proyecto
            project_id = None
            if gizmo_id and gizmo_id in gizmo_to_project:
                project_id = gizmo_to_project[gizmo_id]
                mapped_count += 1
            else:
                orphan_count += 1
            
            # Insertar conversación
            cursor.execute("""
                INSERT INTO conversations (
                    id, title, project_id, chatgpt_gizmo_id,
                    created_at, create_time, update_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                conv_id, title, project_id, gizmo_id,
                created_at, create_time, update_time
            ))
            
            imported_count += 1
            
            # Progreso cada 100
            if i % 100 == 0:
                percent = (i/len(all_conversations))*100
                print(f"   Procesadas: {i}/{len(all_conversations)} ({percent:.1f}%)")
                
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Mostrar solo los primeros errores
                error_msg = str(e)[:50]
                print(f"   ❌ Error en conversación {i}: {error_msg}...")
    
    # Confirmar cambios
    conn.commit()
    
    # Verificar resultado final
    cursor.execute("SELECT COUNT(*) as count FROM conversations")
    total_final = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE project_id IS NOT NULL")
    mapped_final = cursor.fetchone()['count']
    
    print(f"\n🎉 IMPORTACIÓN COMPLETADA:")
    print(f"   ✅ Conversaciones importadas: {imported_count}")
    print(f"   ⏭️  Conversaciones omitidas: {skipped_count}")
    print(f"   🎯 Conversaciones mapeadas: {mapped_count}")
    print(f"   🔄 Conversaciones huérfanas: {orphan_count}")
    print(f"   ❌ Errores: {error_count}")
    print(f"   📊 Total final en BD: {total_final}")
    print(f"   🗺️  Total mapeadas: {mapped_final}")
    
    if total_final > 0:
        percent_mapped = (mapped_final/total_final)*100
        print(f"   📈 Porcentaje mapeado: {percent_mapped:.1f}%")
    
    # Mostrar estadísticas de proyectos
    cursor.execute("""
        SELECT p.name, COUNT(c.id) as conv_count
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        WHERE p.chatgpt_project_id IS NOT NULL
        GROUP BY p.id, p.name
        ORDER BY conv_count DESC
        LIMIT 10
    """)
    
    top_projects = cursor.fetchall()
    print(f"\n📋 TOP 10 PROYECTOS CON MÁS CONVERSACIONES:")
    for project in top_projects:
        project_name = project['name'][:40]
        conv_count = project['conv_count']
        print(f"   - {project_name:40}: {conv_count} conversaciones")
    
    cursor.close()
    conn.close()
    
    return imported_count > 0

if __name__ == "__main__":
    importar_todas_las_conversaciones()