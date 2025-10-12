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

def insert_conversation_corrected(conversation_id, title, mapping):
    """Inserta una conversación con la estructura correcta del JSON"""
    connection = create_connection()
    if not connection:
        return 0
    
    try:
        with connection.cursor() as cursor:
            # Insertar conversación
            cursor.execute(
                "INSERT IGNORE INTO conversations (conversation_id, title) VALUES (%s, %s)",
                (conversation_id, title[:500])  # Limitar título
            )
            
            # Contador de mensajes insertados
            message_count = 0
            
            # Procesar mensajes del mapping
            for message_id, message_data in mapping.items():
                try:
                    # Verificar que el mensaje tiene datos válidos
                    if not message_data or not isinstance(message_data, dict):
                        continue
                    
                    message_obj = message_data.get('message')
                    if not message_obj or not isinstance(message_obj, dict):
                        continue
                    
                    # Extraer contenido
                    content = ""
                    parts_json = "[]"
                    
                    if 'content' in message_obj:
                        content_data = message_obj['content']
                        if isinstance(content_data, dict) and 'parts' in content_data:
                            parts = content_data['parts']
                            if isinstance(parts, list):
                                content = '\n'.join(str(part) for part in parts if part)
                                parts_json = json.dumps(parts)
                        elif isinstance(content_data, str):
                            content = content_data
                            parts_json = json.dumps([content_data])
                    
                    # Obtener otros campos
                    author = message_obj.get('author', {})
                    role = author.get('role', 'unknown') if isinstance(author, dict) else 'unknown'
                    
                    # Create time
                    create_time_timestamp = message_data.get('create_time')
                    create_time = None
                    if create_time_timestamp:
                        try:
                            create_time = datetime.fromtimestamp(create_time_timestamp)
                        except:
                            pass
                    
                    parent = message_data.get('parent')
                    children = json.dumps(message_data.get('children', []))
                    
                    # Insertar mensaje
                    cursor.execute(
                        """INSERT IGNORE INTO messages 
                           (id, conversation_id, role, content, parts, create_time, parent, children) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            message_id,
                            conversation_id,
                            role,
                            content[:65000],  # Limitar contenido
                            parts_json[:65000],
                            create_time,
                            parent,
                            children[:65000]
                        )
                    )
                    
                    message_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error procesando mensaje {message_id}: {e}")
                    continue
            
            return message_count
            
    except Exception as e:
        print(f"❌ Error insertando conversación {conversation_id}: {e}")
        return 0
    finally:
        connection.close()

def process_conversations_fixed():
    """Procesa las conversaciones con la estructura JSON correcta"""
    print("🚀 Iniciando importación con estructura JSON corregida...")
    
    # Obtener conversaciones existentes
    print("[INFO] Obteniendo conversaciones existentes...")
    existing_conversations = get_existing_conversations()
    print(f"[INFO] Conversaciones ya existentes: {len(existing_conversations)}")
    
    # Cargar archivo JSON
    try:
        with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
            conversations = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando archivo JSON: {e}")
        return
    
    print(f"[INFO] Total de conversaciones en archivo: {len(conversations)}")
    
    # Procesar conversaciones
    processed_count = 0
    total_messages = 0
    start_time = time.time()
    
    for i, conversation in enumerate(conversations):
        try:
            # Obtener ID de conversación
            conversation_id = conversation.get('conversation_id') or conversation.get('id')
            if not conversation_id:
                print(f"⚠️  Conversación {i+1} sin ID válido")
                continue
            
            # Saltar si ya existe
            if conversation_id in existing_conversations:
                continue
            
            title = conversation.get('title', 'Sin título')
            mapping = conversation.get('mapping', {})
            
            if not mapping:
                print(f"⚠️  Conversación {conversation_id} sin mensajes")
                continue
            
            # Insertar conversación
            message_count = insert_conversation_corrected(conversation_id, title, mapping)
            
            if message_count > 0:
                processed_count += 1
                total_messages += message_count
                
                print(f"✅ Conversación {processed_count}: {title[:50]}... ({message_count} mensajes)")
                
                # Mostrar progreso cada 25 conversaciones
                if processed_count % 25 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    remaining = len(conversations) - len(existing_conversations) - processed_count
                    eta = remaining / rate if rate > 0 else 0
                    
                    print(f"📊 Progreso: {processed_count} conversaciones | "
                          f"{total_messages} mensajes | "
                          f"{rate:.2f} conv/seg | "
                          f"ETA: {eta/60:.1f} min")
                
                # Pausa pequeña para no saturar
                time.sleep(0.2)
            else:
                print(f"⚠️  Sin mensajes válidos en conversación: {conversation_id}")
                
        except KeyboardInterrupt:
            print("\n⏹️  Importación interrumpida por el usuario")
            break
        except Exception as e:
            print(f"❌ Error procesando conversación {i+1}: {e}")
            continue
    
    elapsed = time.time() - start_time
    print(f"\n✅ Importación completada!")
    print(f"📊 Estadísticas finales:")
    print(f"   • Conversaciones procesadas: {processed_count}")
    print(f"   • Mensajes totales importados: {total_messages}")
    print(f"   • Tiempo transcurrido: {elapsed/60:.2f} minutos")
    if processed_count > 0:
        print(f"   • Promedio mensajes por conversación: {total_messages/processed_count:.1f}")
        print(f"   • Velocidad: {processed_count/elapsed:.2f} conversaciones/segundo")

if __name__ == "__main__":
    try:
        process_conversations_fixed()
    except KeyboardInterrupt:
        print("\n⏹️  Proceso interrumpido")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)