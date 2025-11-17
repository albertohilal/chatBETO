#!/usr/bin/env python3
# Migrar conversations y messages desde conversations.json con estructura correcta

import mysql.connector
import json
import os
import uuid
from datetime import datetime
from collections import defaultdict

def migrate_from_conversations_json():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Cargar conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"📋 Cargando {conversations_file}...")
        
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        print(f"✅ Cargadas {len(conversations_data)} conversaciones del JSON")
        
        # Conectar a base remota
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
        
        # 1. OBTENER proyectos existentes
        print(f"\n📁 Obteniendo proyectos existentes...")
        
        cursor.execute("SELECT id, name, chatgpt_project_id FROM projects ORDER BY id")
        projects = cursor.fetchall()
        
        # Crear mapeos
        gizmo_to_project_id = {}
        project_names = {}
        
        for project_id, name, gizmo_id in projects:
            project_names[project_id] = name
            if gizmo_id:
                gizmo_to_project_id[gizmo_id] = project_id
        
        print(f"  📊 {len(projects)} proyectos encontrados")
        print(f"  🎯 {len(gizmo_to_project_id)} con gizmo_id mapeado")
        
        # 2. AGRUPAR conversaciones por gizmo_id
        print(f"\n🔄 Agrupando conversaciones por gizmo_id...")
        
        gizmo_conversations = defaultdict(list)
        no_gizmo_conversations = []
        
        for conv in conversations_data:
            gizmo_id = conv.get('gizmo_id')
            if gizmo_id:
                gizmo_conversations[gizmo_id].append(conv)
            else:
                no_gizmo_conversations.append(conv)
        
        print(f"  🎯 {len(gizmo_conversations)} gizmo_ids únicos")
        print(f"  ❓ {len(no_gizmo_conversations)} conversaciones sin gizmo_id")
        
        # 3. MAPEAR gizmo_ids a project_ids y actualizar projects
        print(f"\n🎯 Mapeando gizmo_ids a proyectos...")
        
        gizmo_project_mapping = {}
        new_projects_created = 0
        
        for gizmo_id, conversations in gizmo_conversations.items():
            if gizmo_id in gizmo_to_project_id:
                # Ya existe el mapeo
                project_id = gizmo_to_project_id[gizmo_id]
                gizmo_project_mapping[gizmo_id] = project_id
                print(f"  ✅ {gizmo_id} -> Proyecto {project_id} ({project_names[project_id]})")
            else:
                # Crear nuevo proyecto o asignar a uno sin gizmo_id
                cursor.execute("SELECT id, name FROM projects WHERE chatgpt_project_id IS NULL LIMIT 1")
                available_project = cursor.fetchone()
                
                if available_project:
                    project_id = available_project[0]
                    project_name = available_project[1]
                    
                    # Asignar gizmo_id a este proyecto
                    cursor.execute("""
                        UPDATE projects 
                        SET chatgpt_project_id = %s 
                        WHERE id = %s
                    """, (gizmo_id, project_id))
                    
                    gizmo_project_mapping[gizmo_id] = project_id
                    print(f"  🔗 {gizmo_id} -> Asignado a proyecto {project_id} ({project_name})")
                else:
                    # Crear nuevo proyecto
                    first_conv = conversations[0]
                    project_name = f"Proyecto {gizmo_id[:8]}"
                    if first_conv.get('title'):
                        title_words = first_conv['title'].split()[:3]
                        project_name = ' '.join(title_words)[:50]
                    
                    cursor.execute("""
                        INSERT INTO projects (name, description, chatgpt_project_id, created_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (project_name, f"Proyecto para gizmo {gizmo_id}", gizmo_id))
                    
                    project_id = cursor.lastrowid
                    gizmo_project_mapping[gizmo_id] = project_id
                    new_projects_created += 1
                    print(f"  ✨ {gizmo_id} -> Nuevo proyecto {project_id} ({project_name})")
        
        if new_projects_created > 0:
            print(f"  📈 {new_projects_created} nuevos proyectos creados")
        
        # 4. INSERTAR conversaciones
        print(f"\n💬 Insertando conversaciones...")
        
        conversations_inserted = 0
        conversations_skipped = 0
        
        for conv in conversations_data:
            try:
                # Generar ID único si no existe
                conv_id = conv.get('id') or str(uuid.uuid4())
                
                # Determinar project_id
                gizmo_id = conv.get('gizmo_id')
                project_id = None
                
                if gizmo_id and gizmo_id in gizmo_project_mapping:
                    project_id = gizmo_project_mapping[gizmo_id]
                elif no_gizmo_conversations and conv in no_gizmo_conversations:
                    # Asignar a proyecto por defecto (primer proyecto sin gizmo)
                    cursor.execute("SELECT id FROM projects WHERE chatgpt_project_id IS NULL LIMIT 1")
                    default_project = cursor.fetchone()
                    if default_project:
                        project_id = default_project[0]
                
                # Preparar datos
                title = conv.get('title', 'Sin título')[:500]
                conversation_id = conv.get('conversation_id') or conv_id
                create_time = conv.get('create_time', 0)
                update_time = conv.get('update_time', 0)
                
                cursor.execute("""
                    INSERT INTO conversations (
                        id, project_id, title, conversation_id,
                        create_time, update_time, created_at,
                        is_archived, is_starred, default_model_slug,
                        gizmo_id, conversation_origin, chatgpt_gizmo_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
                """, (
                    conv_id, project_id, title, conversation_id,
                    create_time, update_time,
                    0, 0, conv.get('default_model_slug', 'gpt-4'),
                    gizmo_id, 'chatgpt', gizmo_id
                ))
                
                conversations_inserted += 1
                
                if conversations_inserted % 100 == 0:
                    print(f"    💬 {conversations_inserted} conversaciones insertadas...")
                
            except mysql.connector.Error as e:
                conversations_skipped += 1
                if conversations_skipped <= 5:  # Solo mostrar los primeros errores
                    print(f"    ⚠️ Error en conversación {conv.get('id', 'unknown')}: {e}")
        
        print(f"  ✅ {conversations_inserted} conversaciones insertadas")
        print(f"  ⚠️ {conversations_skipped} conversaciones omitidas")
        
        # 5. INSERTAR mensajes
        print(f"\n💌 Insertando mensajes...")
        
        messages_inserted = 0
        messages_skipped = 0
        
        for conv in conversations_data:
            conv_id = conv.get('id') or str(uuid.uuid4())
            
            # Verificar que la conversación existe
            cursor.execute("SELECT id FROM conversations WHERE id = %s", (conv_id,))
            if not cursor.fetchone():
                continue
            
            # Insertar mensajes de esta conversación
            mapping = conv.get('mapping', {})
            
            for msg_id, msg_data in mapping.items():
                try:
                    message = msg_data.get('message')
                    if not message:
                        continue
                    
                    # Extraer datos del mensaje
                    author = message.get('author', {})
                    author_role = author.get('role', 'user')
                    author_name = author.get('name')
                    
                    content = message.get('content', {})
                    content_type = content.get('content_type', 'text')
                    
                    # Extraer texto del contenido
                    content_text = ""
                    if content_type == 'text':
                        parts = content.get('parts', [])
                        if parts and isinstance(parts, list):
                            content_text = '\n'.join(str(part) for part in parts if part)
                    
                    create_time = message.get('create_time', 0)
                    status = message.get('status', 'finished_successfully')
                    weight = message.get('weight', 1.0)
                    
                    # Parent message
                    parent_id = msg_data.get('parent')
                    
                    cursor.execute("""
                        INSERT INTO messages (
                            id, conversation_id, parent_message_id, content_type,
                            content_text, author_role, author_name, create_time,
                            created_at, status, end_turn, weight, recipient
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s)
                    """, (
                        msg_id, conv_id, parent_id, content_type,
                        content_text, author_role, author_name, create_time,
                        status, 1, weight, 'all'
                    ))
                    
                    messages_inserted += 1
                    
                    if messages_inserted % 1000 == 0:
                        print(f"    💌 {messages_inserted} mensajes insertados...")
                
                except mysql.connector.Error as e:
                    messages_skipped += 1
                    if messages_skipped <= 5:
                        print(f"    ⚠️ Error en mensaje {msg_id}: {e}")
        
        print(f"  ✅ {messages_inserted} mensajes insertados")
        print(f"  ⚠️ {messages_skipped} mensajes omitidos")
        
        # 6. ESTADÍSTICAS FINALES
        print(f"\n📊 Estadísticas finales:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE chatgpt_project_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {total_projects:,}")
        print(f"  💬 Conversaciones: {total_conversations:,}")
        print(f"  💌 Mensajes: {total_messages:,}")
        print(f"  🎯 Proyectos con ChatGPT ID: {projects_with_gizmo}")
        
        # Top proyectos por actividad
        cursor.execute("""
            SELECT p.name, COUNT(c.id) as conv_count, COUNT(m.id) as msg_count
            FROM projects p
            LEFT JOIN conversations c ON c.project_id = p.id
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY p.id, p.name
            HAVING conv_count > 0
            ORDER BY msg_count DESC
            LIMIT 10
        """)
        
        top_projects = cursor.fetchall()
        print(f"\n🏆 Top 10 proyectos por actividad:")
        for i, (name, conv_count, msg_count) in enumerate(top_projects, 1):
            print(f"  {i:2d}. {name[:30]:<30} | {conv_count:3d} conv | {msg_count:5,d} msgs")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Migración desde conversations.json completada!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_from_conversations_json()