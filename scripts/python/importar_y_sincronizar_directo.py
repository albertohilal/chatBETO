#!/usr/bin/env python3
"""
Importador directo de mensajes desde conversations.json
"""

import json
import mysql.connector
from datetime import datetime
import uuid

def importar_mensajes_conversacion(conversation_id, limit_messages=None):
    """Importar mensajes de una conversación específica"""
    
    print(f"📥 Importando mensajes para conversación: {conversation_id}")
    
    # Cargar conversations.json
    with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
        all_conversations = json.load(f)
    
    # Encontrar la conversación
    target_conversation = None
    for conv in all_conversations:
        if conv.get('id') == conversation_id:
            target_conversation = conv
            break
    
    if not target_conversation:
        print(f"❌ Conversación {conversation_id} no encontrada en JSON")
        return 0
    
    # Extraer mensajes del mapping
    mapping = target_conversation.get('mapping', {})
    if not mapping:
        print("❌ No hay mapping de mensajes")
        return 0
    
    print(f"📊 Mapping encontrado con {len(mapping)} nodos")
    
    # Conectar a BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Verificar si la conversación existe
    cursor.execute("SELECT id FROM conversations WHERE id = %s", (conversation_id,))
    if not cursor.fetchone():
        print(f"❌ Conversación {conversation_id} no existe en BD")
        cursor.close()
        conn.close()
        return 0
    
    imported_count = 0
    
    # Procesar cada nodo del mapping
    for node_id, node_data in mapping.items():
        try:
            if not isinstance(node_data, dict):
                continue
                
            message = node_data.get('message')
            if not message:
                continue
            
            # Extraer datos del mensaje
            message_id = message.get('id')
            if not message_id:
                message_id = str(uuid.uuid4())
            
            author = message.get('author', {})
            role = author.get('role', 'unknown')
            
            # Extraer contenido
            content = message.get('content', {})
            if isinstance(content, dict):
                parts = content.get('parts', [])
                if parts and isinstance(parts, list):
                    content_text = ' '.join(str(part) for part in parts if part)
                else:
                    content_text = str(content.get('text', '')) if content.get('text') else ''
            else:
                content_text = str(content) if content else ''
            
            if not content_text.strip():
                continue  # Saltar mensajes vacíos
            
            # Timestamps
            create_time = message.get('create_time')
            update_time = message.get('update_time')
            
            created_at = None
            if create_time:
                try:
                    created_at = datetime.fromtimestamp(create_time)
                except:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()
            
            # Verificar si el mensaje ya existe
            cursor.execute("SELECT id FROM messages WHERE id = %s", (message_id,))
            if cursor.fetchone():
                continue  # Saltar si ya existe
            
            # Insertar mensaje
            cursor.execute("""
                INSERT INTO messages (
                    id, conversation_id, author_role, content_text,
                    created_at, create_time
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                message_id, conversation_id, role, content_text[:10000],  # Limitar contenido
                created_at, create_time
            ))
            
            imported_count += 1
            
            # Limitar si se especifica
            if limit_messages and imported_count >= limit_messages:
                break
                
        except Exception as e:
            print(f"⚠️  Error procesando nodo {node_id}: {str(e)[:50]}...")
            continue
    
    # Confirmar cambios
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Importados {imported_count} mensajes para conversación {conversation_id}")
    return imported_count

def sincronizar_conversacion_completa(conv_id, max_messages=50):
    """Importar mensajes y sincronizar con OpenAI en un solo paso"""
    
    print(f"\n🚀 PROCESO COMPLETO PARA: {conv_id}")
    
    # 1. Importar mensajes
    imported_count = importar_mensajes_conversacion(conv_id, max_messages)
    
    if imported_count == 0:
        print("❌ No se importaron mensajes, cancelando sincronización")
        return False
    
    # 2. Obtener datos de la conversación
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            c.id, c.title, 
            p.name as project_name, 
            p.chatgpt_project_id
        FROM conversations c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE c.id = %s
    """, (conv_id,))
    
    conv_data = cursor.fetchone()
    
    if not conv_data or not conv_data['chatgpt_project_id']:
        print("❌ Conversación no mapeada a proyecto válido")
        cursor.close()
        conn.close()
        return False
    
    # 3. Obtener mensajes
    cursor.execute("""
        SELECT * FROM messages 
        WHERE conversation_id = %s 
        ORDER BY create_time ASC, created_at ASC
    """, (conv_id,))
    
    messages = cursor.fetchall()
    print(f"📨 Mensajes listos para sincronizar: {len(messages)}")
    
    if len(messages) == 0:
        print("❌ No hay mensajes para sincronizar")
        cursor.close()
        conn.close()
        return False
    
    # 4. Sincronizar con OpenAI
    try:
        import os
        from openai import OpenAI
        import time
        
        # Configurar API
        with open('openai_key.txt', 'r') as f:
            api_key = f.read().strip()
        
        os.environ['OPENAI_API_KEY'] = api_key
        openai_client = OpenAI(api_key=api_key)
        
        print("🔗 Creando thread en OpenAI...")
        
        # Crear thread
        thread = openai_client.beta.threads.create(
            metadata={
                "chatbeto_conversation_id": conv_id,
                "chatbeto_project_name": conv_data['project_name'],
                "conversation_title": conv_data['title'][:100] if conv_data['title'] else 'Sin título',
                "message_count": str(len(messages)),
                "sync_timestamp": str(time.time())
            }
        )
        
        thread_id = thread.id
        print(f"✅ Thread creado: {thread_id}")
        
        # Enviar mensajes
        print(f"📤 Enviando {len(messages)} mensajes...")
        
        messages_sent = 0
        for i, message in enumerate(messages):
            try:
                role = "user" if message['author_role'] == 'user' else "assistant"
                content = message['content_text'] or ''
                
                if content.strip() and len(content.strip()) > 5:  # Solo mensajes con contenido útil
                    openai_client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role=role,
                        content=content[:30000]  # Limitar longitud
                    )
                    messages_sent += 1
                    
                    if i % 5 == 0:  # Progreso cada 5 mensajes
                        print(f"   Enviados: {messages_sent}/{len(messages)}")
                    
                    time.sleep(0.2)  # Pausa para evitar rate limits
                
            except Exception as e:
                print(f"   ⚠️  Error mensaje {i}: {str(e)[:30]}...")
        
        # Actualizar BD
        cursor.execute(
            "UPDATE conversations SET openai_thread_id = %s WHERE id = %s",
            (thread_id, conv_id)
        )
        conn.commit()
        
        print(f"🎉 SINCRONIZACIÓN EXITOSA:")
        print(f"   📥 Mensajes importados: {imported_count}")
        print(f"   📤 Mensajes enviados: {messages_sent}")
        print(f"   🔗 Thread ID: {thread_id}")
        print(f"   📋 Título: {conv_data['title'][:50] if conv_data['title'] else 'Sin título'}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en sincronización OpenAI: {e}")
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    # Conversaciones prioritarias identificadas anteriormente
    priority_conversations = [
        "6880f866-5740-8330-9748-562fbe224adc",  # Navegar y analizar (1828 msgs)
        "68c69d90-3664-832a-9d31-2ce69536a4fa",  # 43 Análisis de endpoints API (1083 msgs)
        "68ce826d-d420-8333-8412-01c929ece8bc"   # 48 Crear filtros WebAPI V6 (926 msgs)
    ]
    
    print("🚀 SINCRONIZACIÓN DIRECTA DE CONVERSACIONES PRIORITARIAS")
    
    success_count = 0
    
    for i, conv_id in enumerate(priority_conversations, 1):
        print(f"\n{'='*70}")
        print(f"CONVERSACIÓN {i}/{len(priority_conversations)}: {conv_id}")
        
        if sincronizar_conversacion_completa(conv_id, max_messages=30):  # Limitar a 30 mensajes por conversación
            success_count += 1
            print("✅ Éxito")
        else:
            print("❌ Falló")
    
    print(f"\n🎉 PROCESO COMPLETADO:")
    print(f"   ✅ Conversaciones sincronizadas: {success_count}/{len(priority_conversations)}")
    print(f"   📈 Tasa de éxito: {(success_count/len(priority_conversations))*100:.1f}%")