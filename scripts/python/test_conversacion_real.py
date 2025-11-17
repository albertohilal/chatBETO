#!/usr/bin/env python3
"""
Test específico de sincronización real con conversación que tiene mensajes
"""

import os
import mysql.connector
import json
from openai import OpenAI
import time

def test_conversacion_especifica():
    """Probar sincronización con la conversación que tiene 57 mensajes"""
    
    print("🚀 TEST ESPECÍFICO - Conversación con 57 mensajes")
    
    # Configurar API key
    api_key_file = 'openai_key.txt'
    try:
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()
        os.environ['OPENAI_API_KEY'] = api_key
        print("✅ API Key configurada")
    except FileNotFoundError:
        print("❌ API Key no encontrada")
        return False
    
    # Configurar clientes
    openai_client = OpenAI(api_key=api_key)
    
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # ID de la conversación con 57 mensajes
    conversation_id = "68e32ec9-37a4-8321-aa91-87bf4038eede"
    
    print(f"\n📝 Analizando conversación: {conversation_id}")
    
    # Obtener datos de la conversación
    cursor.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
    conversation = cursor.fetchone()
    
    if not conversation:
        print("❌ Conversación no encontrada")
        return False
    
    print(f"   Título: {conversation['title']}")
    print(f"   Proyecto ID: {conversation['project_id']}")
    
    # Obtener proyecto asociado
    cursor.execute("""
        SELECT * FROM projects 
        WHERE id = %s AND chatgpt_project_id IS NOT NULL
    """, (conversation['project_id'],))
    
    project = cursor.fetchone()
    if not project:
        print("❌ Proyecto no encontrado o sin ChatGPT Project ID")
        return False
    
    print(f"   Proyecto: {project['name']}")
    print(f"   ChatGPT Project ID: {project['chatgpt_project_id']}")
    
    # Obtener mensajes
    cursor.execute("""
        SELECT * FROM messages 
        WHERE conversation_id = %s 
        ORDER BY create_time ASC, created_at ASC
    """, (conversation_id,))
    
    messages = cursor.fetchall()
    print(f"   Mensajes encontrados: {len(messages)}")
    
    if not messages:
        print("❌ No hay mensajes para sincronizar")
        return False
    
    # Mostrar muestra de mensajes
    print(f"\n📋 MUESTRA DE MENSAJES:")
    for i, msg in enumerate(messages[:3]):
        role = msg['author_role']
        content_preview = (msg['content_text'] or '')[:60]
        print(f"   {i+1}. [{role}] {content_preview}...")
    
    if len(messages) > 3:
        print(f"   ... y {len(messages) - 3} mensajes más")
    
    # Verificar si ya tiene thread
    if conversation.get('openai_thread_id'):
        print(f"\n⚠️  Esta conversación ya tiene thread: {conversation['openai_thread_id']}")
        return True
    
    # Confirmar sincronización
    print(f"\n🔄 PREPARADO PARA SINCRONIZACIÓN REAL:")
    print(f"   - Crear thread en proyecto ChatGPT")
    print(f"   - Enviar {len(messages)} mensajes")
    print(f"   - Actualizar base de datos")
    
    confirm = input(f"\n¿Proceder con la sincronización real? (y/N): ")
    
    if confirm.lower() != 'y':
        print("ℹ️  Sincronización cancelada")
        return True
    
    try:
        print("\n🚀 INICIANDO SINCRONIZACIÓN REAL...")
        
        # 1. Crear thread
        print("1️⃣ Creando thread en OpenAI...")
        thread = openai_client.beta.threads.create(
            metadata={
                "chatbeto_conversation_id": conversation_id,
                "chatbeto_project_name": project['name'],
                "conversation_title": conversation['title'][:100],
                "sync_timestamp": str(time.time())
            }
        )
        
        thread_id = thread.id
        print(f"✅ Thread creado: {thread_id}")
        
        # 2. Enviar mensajes
        print(f"2️⃣ Enviando {len(messages)} mensajes...")
        
        messages_sent = 0
        for i, message in enumerate(messages):
            try:
                # Convertir rol
                role = "user" if message['author_role'] == 'user' else "assistant"
                content = message['content_text'] or ''
                
                if content.strip():  # Solo mensajes con contenido
                    openai_client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role=role,
                        content=content[:30000]  # Limitar longitud
                    )
                    messages_sent += 1
                    
                    if i % 10 == 0:  # Progreso cada 10 mensajes
                        print(f"   Enviados: {messages_sent}/{len(messages)}")
                    
                    time.sleep(0.1)  # Pausa para evitar rate limits
                
            except Exception as e:
                print(f"   ⚠️  Error enviando mensaje {i+1}: {str(e)[:50]}...")
        
        print(f"✅ {messages_sent}/{len(messages)} mensajes enviados correctamente")
        
        # 3. Actualizar base de datos
        print("3️⃣ Actualizando base de datos...")
        cursor.execute(
            "UPDATE conversations SET openai_thread_id = %s WHERE id = %s",
            (thread_id, conversation_id)
        )
        conn.commit()
        print("✅ Base de datos actualizada")
        
        print(f"\n🎉 SINCRONIZACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"   Thread ID: {thread_id}")
        print(f"   Mensajes sincronizados: {messages_sent}")
        print(f"   Conversación: {conversation['title']}")
        
        # Opcional: Probar consulta
        print(f"\n💡 PROBANDO CONSULTA AL THREAD...")
        try:
            # Agregar un mensaje de prueba
            openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content="Por favor, proporciona un breve resumen de esta conversación."
            )
            
            # Crear run (esto necesita un assistant_id válido)
            print("   Nota: Para consultas completas necesitas configurar un assistant_id")
            
        except Exception as e:
            print(f"   ⚠️  Error en consulta de prueba: {e}")
        
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
        return False
    
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    test_conversacion_especifica()