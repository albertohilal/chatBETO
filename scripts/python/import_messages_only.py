#!/usr/bin/env python3
# Importar mensajes desde conversations.json (Segunda etapa)

import mysql.connector
import json
import os
import uuid
from datetime import datetime

def import_messages_from_json():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Cargar conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"📋 Cargando mensajes desde {conversations_file}...")
        
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
            autocommit=False  # Usar transacciones para mejor rendimiento
        )
        
        cursor = connection.cursor()
        
        # 1. VERIFICAR conversaciones existentes en BD
        print(f"\n🔍 Verificando conversaciones existentes en BD...")
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations_db = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        existing_messages = cursor.fetchone()[0]
        
        print(f"  💬 Conversaciones en BD: {total_conversations_db:,}")
        print(f"  💌 Mensajes existentes: {existing_messages:,}")
        
        if existing_messages > 0:
            print(f"  ⚠️ Ya existen mensajes, se agregarán a los existentes")
        
        # Crear set de conversation_ids válidos
        cursor.execute("SELECT id FROM conversations")
        valid_conversation_ids = set(row[0] for row in cursor.fetchall())
        print(f"  📋 {len(valid_conversation_ids):,} conversation_ids válidos")
        
        # 2. CONTAR mensajes totales a importar
        print(f"\n📊 Analizando mensajes en conversations.json...")
        
        total_messages_to_import = 0
        conversations_with_messages = 0
        
        for conv in conversations_data:
            mapping = conv.get('mapping', {})
            if mapping:
                conversations_with_messages += 1
                total_messages_to_import += len(mapping)
        
        print(f"  💬 Conversaciones con mensajes: {conversations_with_messages:,}")
        print(f"  💌 Total mensajes a importar: {total_messages_to_import:,}")
        
        # 3. IMPORTAR mensajes por lotes
        print(f"\n💌 Importando mensajes por lotes...")
        
        imported_count = 0
        skipped_count = 0
        batch_size = 500
        batch_data = []
        
        for conv_idx, conv in enumerate(conversations_data):
            conv_id = conv.get('id')
            
            # Verificar que la conversación existe en BD
            if not conv_id or conv_id not in valid_conversation_ids:
                continue
            
            # Procesar mensajes de esta conversación
            mapping = conv.get('mapping', {})
            
            for msg_id, msg_data in mapping.items():
                try:
                    message = msg_data.get('message')
                    if not message:
                        continue
                    
                    # Extraer datos del mensaje
                    author = message.get('author', {})
                    author_role = author.get('role', 'user')
                    author_name = author.get('name', '')
                    
                    content = message.get('content', {})
                    content_type = content.get('content_type', 'text')
                    
                    # Extraer texto del contenido
                    content_text = ""
                    if content_type == 'text':
                        parts = content.get('parts', [])
                        if parts and isinstance(parts, list):
                            # Filtrar partes válidas y unir
                            valid_parts = [str(part).strip() for part in parts if part and str(part).strip()]
                            content_text = '\n'.join(valid_parts)
                    
                    # Solo importar mensajes con contenido
                    if not content_text:
                        continue
                    
                    # Otros datos
                    create_time = message.get('create_time', 0)
                    status = message.get('status', 'finished_successfully')
                    weight = message.get('weight', 1.0)
                    
                    # Parent message (puede ser None)
                    parent_id = msg_data.get('parent')
                    if parent_id == msg_id:  # Evitar auto-referencia
                        parent_id = None
                    
                    # Agregar al batch
                    batch_data.append((
                        msg_id,                 # id
                        conv_id,               # conversation_id
                        parent_id,             # parent_message_id
                        content_type,          # content_type
                        content_text[:50000],  # content_text (limitar tamaño)
                        author_role,           # author_role
                        author_name,           # author_name
                        create_time,           # create_time
                        status,                # status
                        1,                     # end_turn
                        weight,                # weight
                        None,                  # channel
                        'all'                  # recipient
                    ))
                    
                    # Ejecutar batch cuando esté lleno
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
                        
                        # Commit periódico y progreso
                        if imported_count % 5000 == 0:
                            connection.commit()
                            progress = (conv_idx + 1) / len(conversations_data) * 100
                            print(f"    💌 {imported_count:,} mensajes importados... ({progress:.1f}%)")
                
                except Exception as e:
                    skipped_count += 1
                    if skipped_count <= 5:
                        print(f"    ⚠️ Error en mensaje {msg_id}: {str(e)[:100]}")
        
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
        
        print(f"\n✅ Importación de mensajes completada:")
        print(f"  💌 Mensajes importados: {imported_count:,}")
        print(f"  ⚠️ Mensajes omitidos: {skipped_count:,}")
        
        # 4. ESTADÍSTICAS FINALES
        print(f"\n📊 Estadísticas finales:")
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        final_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT conversation_id) FROM messages")
        conversations_with_messages = cursor.fetchone()[0]
        
        print(f"  💬 Total conversaciones: {final_conversations:,}")
        print(f"  💌 Total mensajes: {final_messages:,}")
        print(f"  🔗 Conversaciones con mensajes: {conversations_with_messages:,}")
        
        # Distribución de mensajes por tipo de autor
        cursor.execute("""
            SELECT author_role, COUNT(*) as count
            FROM messages 
            GROUP BY author_role 
            ORDER BY count DESC
        """)
        
        role_stats = cursor.fetchall()
        print(f"\n👥 Mensajes por tipo de autor:")
        for role, count in role_stats:
            print(f"  {role}: {count:,} mensajes")
        
        # Top conversaciones por mensajes
        cursor.execute("""
            SELECT c.title, COUNT(m.id) as msg_count
            FROM conversations c
            INNER JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id, c.title
            ORDER BY msg_count DESC
            LIMIT 10
        """)
        
        top_conversations = cursor.fetchall()
        print(f"\n🏆 Top 10 conversaciones por mensajes:")
        for i, (title, msg_count) in enumerate(top_conversations, 1):
            title_short = title[:50] + "..." if len(title) > 50 else title
            print(f"  {i:2d}. {title_short:<53} | {msg_count:4,d} msgs")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Mensajes importados exitosamente!")
        print(f"🎉 Base de datos chatBETO completamente actualizada:")
        print(f"   📁 67 proyectos (66 + 1 por defecto)")
        print(f"   💬 {final_conversations:,} conversaciones")
        print(f"   💌 {final_messages:,} mensajes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import_messages_from_json()