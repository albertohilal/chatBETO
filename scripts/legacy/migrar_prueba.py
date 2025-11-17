#!/usr/bin/env python3
"""
Script de migración simplificado para pruebas
"""

import json
import mysql.connector
from mysql.connector import Error

def migrar_prueba():
    """Migración de prueba simplificada"""
    
    # Cargar configuración
    try:
        with open('db_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró db_config.json")
        return False
    
    # Cargar mapping
    try:
        with open('conversation_project_mapping.json', 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró conversation_project_mapping.json")
        return False
    
    try:
        # Conectar
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        print("✅ Conexión exitosa")
        
        # 1. Insertar proyectos únicos
        projects = set()
        for conv in mapping_data['mapped_conversations']:
            if conv['project_name']:
                projects.add(conv['project_name'])
        
        print(f"📁 Insertando {len(projects)} proyectos...")
        
        for project_name in projects:
            try:
                cursor.execute(
                    "INSERT IGNORE INTO projects (name, is_starred) VALUES (%s, %s)",
                    (project_name, False)
                )
            except Error as e:
                print(f"Error insertando proyecto {project_name}: {e}")
        
        connection.commit()
        print(f"✅ {len(projects)} proyectos insertados")
        
        # 2. Insertar conversaciones (primeras 20)
        print("💬 Insertando conversaciones...")
        
        # Conversaciones con proyecto (primeras 10)
        conv_count = 0
        for conv in mapping_data['mapped_conversations'][:10]:
            try:
                cursor.execute(
                    """INSERT IGNORE INTO conversations 
                    (id, project_id, title, create_time, update_time, is_archived, is_starred) 
                    VALUES (%s, (SELECT id FROM projects WHERE name = %s), %s, %s, %s, %s, %s)""",
                    (
                        conv['conversation_id'],
                        conv['project_name'],
                        conv['title'][:500],
                        conv.get('create_time'),
                        conv.get('update_time'),
                        conv.get('is_archived', False),
                        conv.get('is_starred', False)
                    )
                )
                conv_count += 1
            except Error as e:
                print(f"Error insertando conversación: {e}")
        
        # Conversaciones sin proyecto (primeras 10)
        for conv in mapping_data['unmapped_conversations'][:10]:
            try:
                cursor.execute(
                    """INSERT IGNORE INTO conversations 
                    (id, project_id, title, create_time, update_time, is_archived, is_starred) 
                    VALUES (%s, NULL, %s, %s, %s, %s, %s)""",
                    (
                        conv['conversation_id'],
                        conv['title'][:500],
                        conv.get('create_time'),
                        conv.get('update_time'),
                        conv.get('is_archived', False),
                        conv.get('is_starred', False)
                    )
                )
                conv_count += 1
            except Error as e:
                print(f"Error insertando conversación huérfana: {e}")
        
        connection.commit()
        print(f"✅ {conv_count} conversaciones insertadas")
        
        # 3. Insertar algunos mensajes de muestra
        print("📝 Insertando mensajes de muestra...")
        
        try:
            with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
                conversations = json.load(f)
        except Exception as e:
            print(f"Error cargando conversations.json: {e}")
            return False
        
        message_count = 0
        processed_convs = 0
        
        for conv in conversations[:5]:  # Solo primeras 5 conversaciones
            conv_id = conv.get('id')
            if not conv_id:
                continue
                
            mapping = conv.get('mapping', {})
            if not mapping:
                continue
            
            processed_convs += 1
            
            # Insertar mensajes de esta conversación
            for msg_id, msg_node in mapping.items():
                if not msg_node or not msg_node.get('message'):
                    continue
                
                message = msg_node['message']
                
                # Extraer contenido
                content_parts = message.get('content', {})
                if isinstance(content_parts, dict):
                    parts = content_parts.get('parts', [])
                    if parts and isinstance(parts, list):
                        content_text = str(parts[0]) if parts[0] else ''
                    else:
                        content_text = str(content_parts)
                else:
                    content_text = str(content_parts) if content_parts else ''
                
                # Truncar si es muy largo
                if len(content_text) > 10000:
                    content_text = content_text[:10000] + "... [TRUNCATED]"
                
                # Datos del autor
                author = message.get('author', {})
                author_role = author.get('role', 'unknown')
                author_name = author.get('name', '')
                
                try:
                    cursor.execute(
                        """INSERT IGNORE INTO messages 
                        (id, conversation_id, parent_message_id, content_text, 
                         author_role, author_name, create_time) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (
                            msg_node.get('id', msg_id),
                            conv_id,
                            msg_node.get('parent'),
                            content_text,
                            author_role,
                            author_name,
                            message.get('create_time')
                        )
                    )
                    message_count += 1
                except Error as e:
                    print(f"Error insertando mensaje: {e}")
            
            if message_count > 50:  # Limitar mensajes para prueba
                break
        
        connection.commit()
        print(f"✅ {message_count} mensajes insertados de {processed_convs} conversaciones")
        
        # Mostrar estadísticas finales
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversations_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE project_id IS NOT NULL")
        mapped_conversations = cursor.fetchone()[0]
        
        print("\n" + "="*50)
        print("ESTADÍSTICAS DE LA MIGRACIÓN DE PRUEBA")
        print("="*50)
        print(f"Proyectos: {projects_count}")
        print(f"Conversaciones totales: {conversations_count}")
        print(f"  - Con proyecto asignado: {mapped_conversations}")
        print(f"  - Sin proyecto: {conversations_count - mapped_conversations}")
        print(f"Mensajes: {messages_count}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de prueba...")
    success = migrar_prueba()
    
    if success:
        print("\n🎉 ¡Migración de prueba exitosa!")
        print("Puedes verificar los datos en phpMyAdmin")
    else:
        print("\n❌ La migración de prueba falló")