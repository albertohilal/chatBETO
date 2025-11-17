#!/usr/bin/env python3
"""
Importar mensajes desde conversations.json e identificar conversaciones prioritarias para sincronizar
"""

import json
import mysql.connector
import subprocess
from datetime import datetime

def importar_mensajes_prioritarios():
    """Importar mensajes de las conversaciones más importantes y sincronizar con OpenAI"""
    
    print("🚀 IMPORTANDO MENSAJES Y PREPARANDO SINCRONIZACIÓN")
    
    # Conectar a BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    print("🔍 ANALIZANDO CONVERSATIONS.JSON PARA MENSAJES...")
    
    # Usar jq para obtener conversaciones con más mensajes
    result = subprocess.run([
        'jq', '-r',
        '.[] | select(.mapping != null and (.mapping | length) > 5) | "\\(.id),\\(.title // "Sin título"),\\(.mapping | length)"',
        'extracted/conversations.json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Error al analizar conversations.json")
        return False
    
    # Procesar resultados
    lines = result.stdout.strip().split('\n')
    priority_conversations = []
    
    for line in lines:
        if line.strip():
            parts = line.split(',', 2)
            if len(parts) >= 3:
                conv_id, title, mapping_count = parts
                try:
                    mapping_count = int(mapping_count)
                    priority_conversations.append({
                        'id': conv_id,
                        'title': title,
                        'mapping_count': mapping_count
                    })
                except:
                    pass
    
    # Ordenar por cantidad de mensajes
    priority_conversations.sort(key=lambda x: x['mapping_count'], reverse=True)
    
    print(f"📊 Conversaciones con 5+ mensajes: {len(priority_conversations)}")
    
    # Mostrar top 10 candidatas
    print(f"\n🎯 TOP 10 CONVERSACIONES PARA SINCRONIZAR:")
    for i, conv in enumerate(priority_conversations[:10], 1):
        title_short = conv['title'][:50]
        print(f"   {i:2d}. {conv['id']} | {title_short:50} | {conv['mapping_count']} msgs")
    
    # Verificar cuáles están en BD y tienen proyecto mapeado
    print(f"\n🔍 VERIFICANDO MAPEO EN BASE DE DATOS...")
    
    available_for_sync = []
    
    for conv in priority_conversations[:20]:  # Top 20
        cursor.execute("""
            SELECT 
                c.id, c.title, 
                p.name as project_name, 
                p.chatgpt_project_id,
                c.openai_thread_id,
                (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as current_messages
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE c.id = %s
        """, (conv['id'],))
        
        db_conv = cursor.fetchone()
        
        if db_conv and db_conv['project_name'] and db_conv['chatgpt_project_id']:
            available_for_sync.append({
                'conv_id': conv['id'],
                'title': conv['title'],
                'project_name': db_conv['project_name'],
                'chatgpt_project_id': db_conv['chatgpt_project_id'],
                'mapping_count': conv['mapping_count'],
                'current_messages': db_conv['current_messages'],
                'has_thread': db_conv['openai_thread_id'] is not None
            })
    
    print(f"✅ Conversaciones mapeables: {len(available_for_sync)}")
    
    # Mostrar conversaciones listas para sincronizar
    print(f"\n📋 CONVERSACIONES LISTAS PARA SINCRONIZACIÓN:")
    sync_candidates = []
    
    for i, conv in enumerate(available_for_sync[:10], 1):
        title_short = conv['title'][:40]
        project_short = conv['project_name'][:15]
        status = "🔗 Sincronizada" if conv['has_thread'] else "⚪ Pendiente"
        need_import = conv['current_messages'] == 0 and conv['mapping_count'] > 0
        import_note = " (necesita import)" if need_import else ""
        
        print(f"   {i:2d}. [{project_short:15}] {title_short:40} | {conv['mapping_count']:3d} msgs | {status}{import_note}")
        
        if not conv['has_thread']:
            sync_candidates.append(conv)
    
    if not sync_candidates:
        print("ℹ️  No hay conversaciones pendientes de sincronizar")
        cursor.close()
        conn.close()
        return True
    
    # Preguntar cuántas sincronizar
    print(f"\n🚀 LISTO PARA SINCRONIZAR {len(sync_candidates)} CONVERSACIONES")
    
    try:
        count = int(input(f"¿Cuántas conversaciones sincronizar? (1-{min(5, len(sync_candidates))}): ") or "3")
        count = max(1, min(count, len(sync_candidates), 5))
    except:
        count = 3
    
    selected_conversations = sync_candidates[:count]
    
    print(f"\n🎯 SINCRONIZANDO {count} CONVERSACIONES:")
    for i, conv in enumerate(selected_conversations, 1):
        print(f"   {i}. {conv['title'][:50]} ({conv['mapping_count']} mensajes)")
    
    cursor.close()
    conn.close()
    
    return selected_conversations

def sincronizar_conversacion_con_openai(conv_data):
    """Sincronizar una conversación específica con OpenAI"""
    
    print(f"\n🔄 SINCRONIZANDO: {conv_data['title'][:50]}...")
    
    try:
        # Configurar OpenAI
        import os
        from openai import OpenAI
        
        # Leer API key
        with open('openai_key.txt', 'r') as f:
            api_key = f.read().strip()
        
        os.environ['OPENAI_API_KEY'] = api_key
        openai_client = OpenAI(api_key=api_key)
        
        # Conectar a BD
        with open('db_config.json', 'r') as f:
            db_config = json.load(f)
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 1. Importar mensajes si es necesario
        if conv_data['current_messages'] == 0:
            print("   📥 Importando mensajes desde JSON...")
            
            # Usar el importador de mensajes existente para esta conversación específica
            result = subprocess.run([
                'python3', 'ImportChatgptMysql_final.py', 
                '--conversation-id', conv_data['conv_id']
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Mensajes importados correctamente")
            else:
                print(f"   ⚠️  Import con warnings: {result.stderr[:100]}...")
        
        # 2. Obtener mensajes de la BD
        cursor.execute("""
            SELECT * FROM messages 
            WHERE conversation_id = %s 
            ORDER BY create_time ASC, created_at ASC
        """, (conv_data['conv_id'],))
        
        messages = cursor.fetchall()
        print(f"   📨 Mensajes disponibles: {len(messages)}")
        
        if len(messages) == 0:
            print("   ❌ No se encontraron mensajes para sincronizar")
            cursor.close()
            conn.close()
            return False
        
        # 3. Crear thread en OpenAI
        print("   🔗 Creando thread en OpenAI...")
        
        thread = openai_client.beta.threads.create(
            metadata={
                "chatbeto_conversation_id": conv_data['conv_id'],
                "chatbeto_project_name": conv_data['project_name'],
                "conversation_title": conv_data['title'][:100],
                "message_count": str(len(messages)),
                "sync_timestamp": str(datetime.now().timestamp())
            }
        )
        
        thread_id = thread.id
        print(f"   ✅ Thread creado: {thread_id}")
        
        # 4. Enviar mensajes
        print(f"   📤 Enviando {len(messages)} mensajes...")
        
        messages_sent = 0
        for i, message in enumerate(messages):
            try:
                role = "user" if message['author_role'] == 'user' else "assistant"
                content = message['content_text'] or ''
                
                if content.strip():
                    openai_client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role=role,
                        content=content[:30000]  # Limitar longitud
                    )
                    messages_sent += 1
                
                if i % 10 == 0:
                    print(f"      Enviados: {messages_sent}/{len(messages)}")
                
            except Exception as e:
                print(f"      ⚠️  Error mensaje {i}: {str(e)[:30]}...")
        
        # 5. Actualizar BD
        cursor.execute(
            "UPDATE conversations SET openai_thread_id = %s WHERE id = %s",
            (thread_id, conv_data['conv_id'])
        )
        conn.commit()
        
        print(f"   🎉 Sincronización completada: {messages_sent}/{len(messages)} mensajes")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error durante sincronización: {e}")
        return False

if __name__ == "__main__":
    # Paso 1: Identificar conversaciones prioritarias
    selected_conversations = importar_mensajes_prioritarios()
    
    if isinstance(selected_conversations, list) and selected_conversations:
        print(f"\n🚀 INICIANDO SINCRONIZACIÓN MASIVA...")
        
        success_count = 0
        for i, conv in enumerate(selected_conversations, 1):
            print(f"\n{'='*60}")
            print(f"CONVERSACIÓN {i}/{len(selected_conversations)}")
            
            if sincronizar_conversacion_con_openai(conv):
                success_count += 1
        
        print(f"\n🎉 SINCRONIZACIÓN MASIVA COMPLETADA:")
        print(f"   ✅ Éxitos: {success_count}/{len(selected_conversations)}")
        print(f"   📈 Tasa de éxito: {(success_count/len(selected_conversations))*100:.1f}%")
    else:
        print("ℹ️  Proceso cancelado o no hay conversaciones para sincronizar")