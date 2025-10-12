#!/usr/bin/env python3
import pymysql
import json
import time
import sys
from datetime import datetime

# Configuración de conexión a la base de datos
DB_CONFIG = {
    'host': 'sv46.byethost46.org',
    'user': 'iunaorg_b3toh',
    'password': 'elgeneral2018',
    'database': 'iunaorg_chatBeto',
    'charset': 'utf8mb4',
    'connect_timeout': 30,
    'read_timeout': 30,
    'write_timeout': 30,
    'autocommit': True
}

def create_connection():
    """Crea una conexión robusta a la base de datos"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

def get_existing_conversations():
    """Obtiene las conversaciones ya importadas"""
    connection = create_connection()
    if not connection:
        return set()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM conversations")
            result = cursor.fetchall()
            return set(row[0] for row in result)
    except Exception as e:
        print(f"❌ Error al obtener conversaciones existentes: {e}")
        return set()
    finally:
        connection.close()

def insert_conversation_safe(conversation_id, title, messages):
    """Inserta una conversación de manera segura con manejo de errores"""
    connection = create_connection()
    if not connection:
        return 0
    
    try:
        with connection.cursor() as cursor:
            # Insertar conversación
            cursor.execute(
                "INSERT IGNORE INTO conversations (conversation_id, title) VALUES (%s, %s)",
                (conversation_id, title)
            )
            
            # Contador de mensajes insertados
            message_count = 0
            
            # Insertar mensajes en lotes pequeños
            batch_size = 10  # Reducido para mayor estabilidad
            message_batch = []
            
            for message_id, message_data in messages.items():
                try:
                    # Procesar contenido del mensaje
                    if isinstance(message_data.get('message'), dict) and 'content' in message_data['message']:
                        content_data = message_data['message']['content']
                        if isinstance(content_data, dict) and 'parts' in content_data:
                            content = '\n'.join(str(part) for part in content_data['parts'] if part)
                            parts_json = json.dumps(content_data['parts'])
                        else:
                            content = str(content_data) if content_data else ""
                            parts_json = json.dumps([content_data])
                    else:
                        content = ""
                        parts_json = "[]"
                    
                    # Obtener otros campos
                    role = message_data.get('message', {}).get('author', {}).get('role', 'unknown')
                    create_time_timestamp = message_data.get('create_time')
                    create_time = None
                    if create_time_timestamp:
                        try:
                            create_time = datetime.fromtimestamp(create_time_timestamp)
                        except:
                            pass
                    
                    parent = message_data.get('parent')
                    children = json.dumps(message_data.get('children', []))
                    
                    message_batch.append((
                        message_id,
                        conversation_id,
                        role,
                        content[:65000],  # Limitar tamaño del contenido
                        parts_json[:65000],  # Limitar tamaño de parts
                        create_time,
                        parent,
                        children[:65000]  # Limitar tamaño de children
                    ))
                    
                    # Insertar batch cuando alcance el tamaño
                    if len(message_batch) >= batch_size:
                        cursor.executemany(
                            """INSERT IGNORE INTO messages 
                               (id, conversation_id, role, content, parts, create_time, parent, children) 
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                            message_batch
                        )
                        message_count += len(message_batch)
                        message_batch = []
                        time.sleep(0.1)  # Pequeña pausa para no saturar
                
                except Exception as e:
                    print(f"⚠️  Error procesando mensaje {message_id}: {e}")
                    continue
            
            # Insertar mensajes restantes
            if message_batch:
                cursor.executemany(
                    """INSERT IGNORE INTO messages 
                       (id, conversation_id, role, content, parts, create_time, parent, children) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    message_batch
                )
                message_count += len(message_batch)
            
            return message_count
            
    except Exception as e:
        print(f"❌ Error insertando conversación {conversation_id}: {e}")
        return 0
    finally:
        connection.close()

def process_conversations_robust():
    """Procesa las conversaciones de manera robusta"""
    print("🚀 Iniciando importación robusta...")
    
    # Obtener conversaciones existentes
    print("[INFO] Obteniendo conversaciones existentes...")
    existing_conversations = get_existing_conversations()
    print(f"[INFO] Conversaciones ya existentes: {len(existing_conversations)}")
    
    # Cargar archivo JSON
    try:
        with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando archivo JSON: {e}")
        return
    
    # Verificar si data es una lista o contiene conversaciones
    if isinstance(data, list):
        conversations = data
    else:
        conversations = data.get('conversations', [])
    
    print(f"[INFO] Total de conversaciones en archivo: {len(conversations)}")
    
    # Procesar conversaciones
    processed_count = 0
    total_messages = 0
    start_time = time.time()
    
    for i, conversation in enumerate(conversations):
        try:
            conversation_id = conversation.get('id')
            if not conversation_id:
                continue
            
            # Saltar si ya existe
            if conversation_id in existing_conversations:
                continue
            
            title = conversation.get('title', 'Sin título')[:500]  # Limitar título
            mapping = conversation.get('conversation_template', {}).get('mapping', {})
            
            # Insertar conversación
            message_count = insert_conversation_safe(conversation_id, title, mapping)
            
            if message_count > 0:
                processed_count += 1
                total_messages += message_count
                
                # Mostrar progreso cada 10 conversaciones
                if processed_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    remaining = len(conversations) - len(existing_conversations) - processed_count
                    eta = remaining / rate if rate > 0 else 0
                    
                    print(f"📊 Progreso: {processed_count} conversaciones | "
                          f"{total_messages} mensajes | "
                          f"{rate:.2f} conv/seg | "
                          f"ETA: {eta/60:.1f} min")
                
                # Pausa para no saturar el servidor
                time.sleep(0.5)
            else:
                print(f"⚠️  Error procesando conversación {i+1}: {conversation_id}")
                
        except KeyboardInterrupt:
            print("\n⏹️  Importación interrumpida por el usuario")
            break
        except Exception as e:
            print(f"❌ Error procesando conversación {i+1}: {e}")
            continue
    
    elapsed = time.time() - start_time
    print(f"\n✅ Importación completada!")
    print(f"📊 Estadísticas:")
    print(f"   • Conversaciones procesadas: {processed_count}")
    print(f"   • Mensajes totales: {total_messages}")
    print(f"   • Tiempo transcurrido: {elapsed/60:.2f} minutos")
    print(f"   • Velocidad promedio: {processed_count/elapsed:.2f} conversaciones/segundo")

if __name__ == "__main__":
    try:
        process_conversations_robust()
    except KeyboardInterrupt:
        print("\n⏹️  Proceso interrumpido")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)