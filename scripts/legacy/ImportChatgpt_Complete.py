#!/usr/bin/env python3
"""
Importador completo de ChatGPT a MySQL
Versión robusta con configuración de entorno y manejo completo de errores
"""
import pymysql
import json
import time
import sys
import os
from datetime import datetime
from env_loader import EnvLoader

def get_db_config():
    """Obtiene la configuración de base de datos desde variables de entorno"""
    EnvLoader.load()
    
    return {
        'host': EnvLoader.get('DB_HOST'),
        'user': EnvLoader.get('DB_USERNAME'), 
        'password': EnvLoader.get('DB_PASSWORD'),
        'database': EnvLoader.get('DB_NAME'),
        'charset': 'utf8mb4',
        'connect_timeout': 60,
        'read_timeout': 60,
        'write_timeout': 60,
        'autocommit': True
    }

def create_connection():
    """Crea una conexión robusta a la base de datos"""
    try:
        config = get_db_config()
        connection = pymysql.connect(**config)
        print(f"✅ Conectado a la base de datos: {config['database']}")
        return connection
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

def get_existing_conversations():
    """Obtiene las conversaciones ya importadas para evitar duplicados"""
    connection = create_connection()
    if not connection:
        return set()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM conversations")
            result = cursor.fetchall()
            existing = set(row[0] for row in result)
            print(f"📊 Conversaciones existentes en BD: {len(existing)}")
            return existing
    except Exception as e:
        print(f"❌ Error al obtener conversaciones existentes: {e}")
        return set()
    finally:
        connection.close()

def get_existing_messages():
    """Obtiene los mensajes ya importados para evitar duplicados"""
    connection = create_connection()
    if not connection:
        return set()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM messages")
            result = cursor.fetchall()
            existing = set(row[0] for row in result)
            print(f"📊 Mensajes existentes en BD: {len(existing)}")
            return existing
    except Exception as e:
        print(f"❌ Error al obtener mensajes existentes: {e}")
        return set()
    finally:
        connection.close()

def insert_batch_messages(cursor, messages_batch):
    """Inserta mensajes en lotes para mejor rendimiento"""
    if not messages_batch:
        return 0
    
    try:
        cursor.executemany(
            """INSERT IGNORE INTO messages 
               (id, conversation_id, role, content, parts, create_time, parent, children) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            messages_batch
        )
        return cursor.rowcount
    except Exception as e:
        print(f"❌ Error insertando lote de mensajes: {e}")
        return 0

def process_conversation(conversation_id, conversation_data, existing_conversations, existing_messages):
    """Procesa una conversación individual"""
    
    # Skip si ya existe
    if conversation_id in existing_conversations:
        print(f"⏭️  Conversación {conversation_id} ya existe, omitiendo...")
        return 0, 0
    
    try:
        title = conversation_data.get('title', 'Sin título')
        create_time = conversation_data.get('create_time', time.time())
        update_time = conversation_data.get('update_time', time.time())
        
        # Convertir timestamps
        if isinstance(create_time, (int, float)):
            create_time = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(update_time, (int, float)):
            update_time = datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # Insertar conversación
        connection = create_connection()
        if not connection:
            return 0, 0
        
        messages_inserted = 0
        
        try:
            with connection.cursor() as cursor:
                # Insertar conversación (estructura exacta de la BD)
                cursor.execute(
                    """INSERT IGNORE INTO conversations 
                       (conversation_id, project_id, project_name, title, create_time, update_time, model) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (conversation_id, None, None, title, create_time, update_time, None)
                )
                conversation_inserted = cursor.rowcount
                
                # Procesar mensajes
                mapping = conversation_data.get('mapping', {})
                messages_batch = []
                
                for message_id, message_data in mapping.items():
                    # Skip si ya existe
                    if message_id in existing_messages:
                        continue
                    
                    message_info = message_data.get('message')
                    if not message_info:
                        continue
                    
                    # Extraer datos del mensaje
                    author = message_info.get('author', {})
                    role = author.get('role', 'unknown')
                    
                    content = message_info.get('content', {})
                    parts = content.get('parts', [])
                    content_text = ' '.join(str(part) for part in parts) if parts else ''
                    
                    # Timestamp del mensaje
                    msg_create_time = message_info.get('create_time')
                    if msg_create_time:
                        if isinstance(msg_create_time, (int, float)):
                            msg_create_time = datetime.fromtimestamp(msg_create_time).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        msg_create_time = create_time
                    
                    # Relaciones familiares
                    parent = message_data.get('parent')
                    children = json.dumps(message_data.get('children', []))
                    parts_json = json.dumps(parts) if parts else '[]'
                    
                    messages_batch.append((
                        message_id,
                        conversation_id, 
                        role,
                        content_text,
                        parts_json,
                        msg_create_time,
                        parent,
                        children
                    ))
                
                # Insertar mensajes en lotes
                if messages_batch:
                    messages_inserted = insert_batch_messages(cursor, messages_batch)
                
                print(f"✅ Procesada: {title[:50]}... | Msgs: {messages_inserted}")
                return conversation_inserted, messages_inserted
                
        finally:
            connection.close()
            
    except Exception as e:
        print(f"❌ Error procesando conversación {conversation_id}: {e}")
        return 0, 0

def import_conversations_from_json(json_file_path):
    """Función principal de importación"""
    print(f"🚀 Iniciando importación desde: {json_file_path}")
    
    # Verificar archivo
    if not os.path.exists(json_file_path):
        print(f"❌ Archivo no encontrado: {json_file_path}")
        return False
    
    # Obtener datos existentes
    print("📋 Obteniendo datos existentes...")
    existing_conversations = get_existing_conversations()
    existing_messages = get_existing_messages()
    
    # Cargar JSON
    print("📖 Cargando archivo JSON...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            conversations_data = json.load(file)
    except Exception as e:
        print(f"❌ Error leyendo JSON: {e}")
        return False
    
    print(f"📊 Conversaciones en archivo: {len(conversations_data)}")
    
    # Procesar conversaciones
    total_conversations = 0
    total_messages = 0
    processed = 0
    
    start_time = time.time()
    
    for conversation_data in conversations_data:
        # Generar ID si no existe
        conversation_id = conversation_data.get('id', f"conv_{processed}")
        if not conversation_id or conversation_id == 'conv_':
            # Usar el hash del título y timestamp como ID
            title = conversation_data.get('title', 'Sin título')
            create_time = conversation_data.get('create_time', time.time())
            conversation_id = f"conv_{hash(f'{title}_{create_time}')}"
        processed += 1
        conv_inserted, msg_inserted = process_conversation(
            conversation_id, 
            conversation_data, 
            existing_conversations, 
            existing_messages
        )
        
        total_conversations += conv_inserted
        total_messages += msg_inserted
        
        # Progreso cada 10 conversaciones
        if processed % 10 == 0:
            elapsed = time.time() - start_time
            progress = (processed / len(conversations_data)) * 100
            print(f"📈 Progreso: {processed}/{len(conversations_data)} ({progress:.1f}%) | Tiempo: {elapsed:.1f}s")
    
    # Resumen final
    elapsed = time.time() - start_time
    print(f"\n🎉 IMPORTACIÓN COMPLETADA!")
    print(f"📊 Conversaciones procesadas: {processed}")
    print(f"📊 Conversaciones nuevas: {total_conversations}")
    print(f"📊 Mensajes nuevos: {total_messages}")
    print(f"⏱️  Tiempo total: {elapsed:.2f} segundos")
    
    return True

def import_user_data(json_file_path):
    """Importa datos del usuario desde user.json (tabla no existe en estructura actual, solo log)"""
    print(f"👤 Procesando datos de usuario desde: {json_file_path}")
    
    if not os.path.exists(json_file_path):
        print(f"❌ Archivo de usuario no encontrado: {json_file_path}")
        return False
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            user_data = json.load(file)
        
        # Solo mostrar información del usuario (no hay tabla users en la estructura actual)
        print(f"📋 Usuario: {user_data.get('name', 'Sin nombre')}")
        print(f"📧 Email: {user_data.get('email', 'Sin email')}")
        print(f"🆔 ID: {user_data.get('id', 'Sin ID')}")
        
        return True
                
    except Exception as e:
        print(f"❌ Error procesando datos de usuario: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🤖 IMPORTADOR COMPLETO DE CHATGPT")
    print("=" * 60)
    
    # Directorio de archivos extraídos
    extracted_dir = "./extracted"
    
    if not os.path.exists(extracted_dir):
        print(f"❌ Directorio {extracted_dir} no existe")
        return
    
    # Archivos a importar
    conversations_file = os.path.join(extracted_dir, "conversations.json")
    user_file = os.path.join(extracted_dir, "user.json")
    
    # Importar datos del usuario
    if os.path.exists(user_file):
        import_user_data(user_file)
    
    # Importar conversaciones
    if os.path.exists(conversations_file):
        success = import_conversations_from_json(conversations_file)
        if success:
            print("\n🎉 ¡Importación completada exitosamente!")
        else:
            print("\n❌ Error en la importación")
    else:
        print(f"❌ Archivo de conversaciones no encontrado: {conversations_file}")

if __name__ == "__main__":
    main()