#!/usr/bin/env python3
# Limpiar tabla messages e importar mensajes desde conversations.json

import mysql.connector
import json
import os
import uuid
from datetime import datetime

def clean_and_import_messages():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🧹 Limpiando tabla messages e importando desde conversations.json...")
        
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4',
            autocommit=False
        )
        
        cursor = connection.cursor()
        
        # 1. VERIFICAR estado actual
        print(f"\n📊 Estado actual:")
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        existing_messages = cursor.fetchone()[0]
        
        print(f"  💬 Conversaciones: {total_conversations:,}")
        print(f"  💌 Mensajes existentes: {existing_messages:,}")
        
        # 2. LIMPIAR tabla messages
        if existing_messages > 0:
            print(f"\n🗑️ Limpiando tabla 'messages'...")
            
            # Crear respaldo antes de limpiar
            cursor.execute("DROP TABLE IF EXISTS messages_backup_before_reimport")
            cursor.execute("CREATE TABLE messages_backup_before_reimport AS SELECT * FROM messages")
            print(f"  💾 Respaldo creado: messages_backup_before_reimport ({existing_messages:,} registros)")
            
            # Limpiar tabla
            cursor.execute("DELETE FROM messages")
            deleted_count = cursor.rowcount
            connection.commit()
            print(f"  🗑️ {deleted_count:,} mensajes eliminados")
        else:
            print(f"\n✅ Tabla 'messages' ya está vacía")
        
        # 3. CARGAR conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"\n📋 Cargando mensajes desde {conversations_file}...")
        
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        print(f"✅ Cargadas {len(conversations_data)} conversaciones del JSON")
        
        # 4. OBTENER conversation_ids válidos
        cursor.execute("SELECT id FROM conversations")
        valid_conversation_ids = set(row[0] for row in cursor.fetchall())
        print(f"  📋 {len(valid_conversation_ids):,} conversation_ids válidos en BD")
        
        # 5. CONTAR mensajes a importar
        print(f"\n📊 Analizando mensajes en JSON...")
        
        total_messages_to_import = 0
        conversations_with_messages = 0
        
        for conv in conversations_data:
            mapping = conv.get('mapping', {})
            if mapping:
                conversations_with_messages += 1
                # Solo contar mensajes válidos (con contenido)
                for msg_data in mapping.values():
                    message = msg_data.get('message')
                    if message and message.get('content', {}).get('parts'):
                        total_messages_to_import += 1
        
        print(f"  💬 Conversaciones con mensajes: {conversations_with_messages:,}")
        print(f"  💌 Mensajes estimados a importar: {total_messages_to_import:,}")
        
        # 6. IMPORTAR mensajes
        print(f"\n💌 Importando mensajes...")
        
        imported_count = 0
        skipped_count = 0
        batch_size = 500
        batch_data = []
        
        for conv_idx, conv in enumerate(conversations_data):
            conv_id = conv.get('id')
            
            # Solo procesar conversaciones que existen en BD
            if not conv_id or conv_id not in valid_conversation_ids:
                continue
            
            mapping = conv.get('mapping', {})
            
            for msg_id, msg_data in mapping.items():
                try:
                    message = msg_data.get('message')
                    if not message:
                        continue
                    
                    # Extraer datos del autor
                    author = message.get('author', {})
                    author_role = author.get('role', 'user')
                    author_name = author.get('name', '') or None
                    
                    # Extraer contenido
                    content = message.get('content', {})
                    content_type = content.get('content_type', 'text')
                    
                    # Extraer texto del contenido
                    content_text = ""
                    if content_type == 'text':
                        parts = content.get('parts', [])
                        if parts and isinstance(parts, list):
                            valid_parts = []
                            for part in parts:
                                if part and str(part).strip():
                                    valid_parts.append(str(part).strip())
                            content_text = '\n'.join(valid_parts)
                    
                    # Solo importar mensajes con contenido válido
                    if not content_text:
                        skipped_count += 1
                        continue
                    
                    # Limitar tamaño del contenido
                    if len(content_text) > 50000:
                        content_text = content_text[:50000] + "... [contenido truncado]"
                    
                    # Otros campos
                    create_time = message.get('create_time', 0)
                    status = message.get('status', 'finished_successfully')
                    weight = message.get('weight', 1.0)
                    
                    # Parent message
                    parent_id = msg_data.get('parent')
                    if parent_id == msg_id:  # Evitar auto-referencia
                        parent_id = None
                    
                    # Agregar al batch
                    batch_data.append((
                        msg_id,               # id
                        conv_id,             # conversation_id
                        parent_id,           # parent_message_id
                        content_type,        # content_type
                        content_text,        # content_text
                        author_role,         # author_role
                        author_name,         # author_name
                        create_time,         # create_time
                        status,              # status
                        1,                   # end_turn
                        weight,              # weight
                        None,                # channel
                        'all'                # recipient
                    ))
                    
                    # Ejecutar batch
                    if len(batch_data) >= batch_size:
                        cursor.executemany("""
                            INSERT INTO messages (
                                id, conversation_id, parent_message_id, content_type,
                                content_text, author_role, author_name, create_time,
                                created_at, status, end_turn, weight, channel, recipient
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
                        """, batch_data)
                        
                        imported_count += len(batch_data)
                        batch_data = []
                        
                        # Commit y progreso cada 5000 mensajes
                        if imported_count % 5000 == 0:
                            connection.commit()
                            progress = (conv_idx + 1) / len(conversations_data) * 100
                            print(f"    💌 {imported_count:,} mensajes importados... ({progress:.1f}%)")
                
                except Exception as e:
                    skipped_count += 1
                    if skipped_count <= 5:
                        print(f"    ⚠️ Error en mensaje {msg_id}: {str(e)[:80]}")
        
        # Ejecutar batch final
        if batch_data:
            cursor.executemany("""
                INSERT INTO messages (
                    id, conversation_id, parent_message_id, content_type,
                    content_text, author_role, author_name, create_time,
                    created_at, status, end_turn, weight, channel, recipient
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            """, batch_data)
            imported_count += len(batch_data)
        
        # Commit final
        connection.commit()
        
        print(f"\n✅ Importación completada:")
        print(f"  💌 Mensajes importados: {imported_count:,}")
        print(f"  ⚠️ Mensajes omitidos: {skipped_count:,}")
        
        # 7. ESTADÍSTICAS FINALES
        print(f"\n📊 Estadísticas finales:")
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT conversation_id) FROM messages")
        conversations_with_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT author_role) FROM messages")
        unique_roles = cursor.fetchone()[0]
        
        print(f"  💌 Total mensajes en BD: {final_messages:,}")
        print(f"  🔗 Conversaciones con mensajes: {conversations_with_messages:,}")
        print(f"  👥 Tipos de autor únicos: {unique_roles}")
        
        # Distribución por autor
        cursor.execute("""
            SELECT author_role, COUNT(*) as count
            FROM messages 
            GROUP BY author_role 
            ORDER BY count DESC
        """)
        
        role_stats = cursor.fetchall()
        print(f"\n👥 Distribución de mensajes por autor:")
        for role, count in role_stats:
            percentage = (count / final_messages) * 100 if final_messages > 0 else 0
            print(f"  {role:<15}: {count:8,} mensajes ({percentage:5.1f}%)")
        
        # Tamaño promedio de mensajes
        cursor.execute("SELECT AVG(LENGTH(content_text)) FROM messages WHERE content_text IS NOT NULL")
        avg_length = cursor.fetchone()[0] or 0
        
        print(f"\n📏 Tamaño promedio de mensaje: {avg_length:.0f} caracteres")
        
        # Top conversaciones con más mensajes
        cursor.execute("""
            SELECT c.title, COUNT(m.id) as msg_count
            FROM conversations c
            INNER JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id, c.title
            ORDER BY msg_count DESC
            LIMIT 5
        """)
        
        top_conversations = cursor.fetchall()
        print(f"\n🏆 Top 5 conversaciones por mensajes:")
        for i, (title, msg_count) in enumerate(top_conversations, 1):
            title_short = title[:45] + "..." if len(title) > 45 else title
            print(f"  {i}. {title_short:<48} | {msg_count:4,d} msgs")
        
        cursor.close()
        connection.close()
        
        print(f"\n🎉 ¡Base de datos iunaorg_chatBeto completamente actualizada!")
        print(f"   📁 67 proyectos")
        print(f"   💬 {total_conversations:,} conversaciones")
        print(f"   💌 {final_messages:,} mensajes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clean_and_import_messages()