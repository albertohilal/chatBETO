#!/usr/bin/env python3
# Sincronizar gizmo_ids desde conversations.json a la base remota

import mysql.connector
import json
import os
from collections import defaultdict

def sync_gizmo_ids():
    try:
        # Leer credenciales de la base remota
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Cargar conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"Cargando {conversations_file}...")
        
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        print(f"✅ Cargadas {len(conversations_data)} conversaciones del JSON")
        
        # Conectar a la base remota
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4',
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Mapear gizmo_ids por conversation_id
        gizmo_mapping = {}
        project_gizmos = defaultdict(set)
        
        for conv in conversations_data:
            conv_id = conv.get('id', '')
            if conv_id and 'gizmo_id' in conv and conv['gizmo_id']:
                gizmo_id = conv['gizmo_id']
                gizmo_mapping[conv_id] = gizmo_id
                project_gizmos[gizmo_id].add(conv_id)
        
        print(f"📋 Encontrados {len(gizmo_mapping)} conversation_ids con gizmo_id")
        print(f"🎯 Detectados {len(project_gizmos)} gizmo_ids únicos")
        
        # Actualizar gizmo_ids en conversations
        print("\n🔄 Actualizando gizmo_ids en conversations...")
        updated_conversations = 0
        
        for conv_id, gizmo_id in gizmo_mapping.items():
            cursor.execute("""
                UPDATE conversations 
                SET gizmo_id = %s 
                WHERE conversation_id = %s
            """, (gizmo_id, conv_id))
            
            if cursor.rowcount > 0:
                updated_conversations += 1
        
        print(f"  ✅ Actualizadas {updated_conversations} conversaciones con gizmo_id")
        
        # Actualizar o crear proyectos por gizmo_id
        print("\n🎯 Sincronizando proyectos por gizmo_id...")
        
        for gizmo_id, conv_ids in project_gizmos.items():
            # Buscar si ya existe un proyecto con este gizmo_id
            cursor.execute("SELECT id, name FROM projects WHERE gizmo_id = %s", (gizmo_id,))
            existing_project = cursor.fetchone()
            
            if existing_project:
                project_id = existing_project[0]
                print(f"  📁 Proyecto existente: {existing_project[1]} ({gizmo_id})")
            else:
                # Crear nuevo proyecto para este gizmo_id
                # Obtener info del primer conversation
                first_conv = conversations_data[0]  # Simplificado, deberíamos buscar por ID
                for conv in conversations_data:
                    if conv.get('id') in conv_ids:
                        first_conv = conv
                        break
                
                project_name = f"Proyecto {gizmo_id[:8]}"
                if 'title' in first_conv:
                    project_name = first_conv['title'][:50]
                
                cursor.execute("""
                    INSERT INTO projects (name, gizmo_id, description, created_at) 
                    VALUES (%s, %s, %s, NOW())
                """, (project_name, gizmo_id, f"Proyecto para gizmo {gizmo_id}"))
                
                project_id = cursor.lastrowid
                print(f"  ✨ Nuevo proyecto creado: {project_name} (ID: {project_id})")
            
            # Actualizar project_id en todas las conversaciones de este gizmo
            cursor.execute("""
                UPDATE conversations 
                SET project_id = %s 
                WHERE gizmo_id = %s
            """, (str(project_id), gizmo_id))
            
            updated_count = cursor.rowcount
            if updated_count > 0:
                print(f"    🔗 {updated_count} conversaciones vinculadas al proyecto")
        
        # Actualizar contadores finales
        print("\n📊 Recalculando contadores...")
        
        # Actualizar message_count en conversations
        cursor.execute("""
            UPDATE conversations c 
            SET message_count = (
                SELECT COUNT(*) FROM messages m 
                WHERE m.conversation_id = c.conversation_id
            )
        """)
        
        # Actualizar contadores en projects
        cursor.execute("""
            UPDATE projects p 
            SET conversation_count = (
                SELECT COUNT(*) FROM conversations c 
                WHERE c.project_id = p.id
            ),
            message_count = (
                SELECT COUNT(*) FROM messages m 
                INNER JOIN conversations c ON m.conversation_id = c.conversation_id
                WHERE c.project_id = p.id
            ),
            last_activity = (
                SELECT MAX(c.update_time) FROM conversations c 
                WHERE c.project_id = p.id
            )
        """)
        
        # Estadísticas finales
        cursor.execute("SELECT COUNT(*) FROM projects WHERE gizmo_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE gizmo_id IS NOT NULL")
        conversations_with_gizmo = cursor.fetchone()[0]
        
        print(f"\n✅ Sincronización completada:")
        print(f"  🎯 Proyectos con gizmo_id: {projects_with_gizmo}")
        print(f"  💬 Conversaciones con gizmo_id: {conversations_with_gizmo}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sync_gizmo_ids()