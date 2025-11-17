#!/usr/bin/env python3
import pymysql
import json
import time
import sys
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    'host': 'sv46.byethost46.org',
    'user': 'iunaorg_b3toh',
    'password': 'elgeneral2018',
    'database': 'iunaorg_chatBeto',
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
    'autocommit': True
}

def create_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"❌ Error conexión: {e}")
        return None

def get_existing_conversations():
    connection = create_connection()
    if not connection:
        return set()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM conversations")
            return set(row[0] for row in cursor.fetchall())
    except:
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
        return len(messages_batch)
    except Exception as e:
        print(f"⚠️  Error batch: {e}")
        return 0

def process_conversation_optimized(conversation_id, title, mapping):
    """Procesa una conversación de manera optimizada"""
    connection = create_connection()
    if not connection:
        return 0
    
    try:
        with connection.cursor() as cursor:
            # Insertar conversación
            cursor.execute(
                "INSERT IGNORE INTO conversations (conversation_id, title) VALUES (%s, %s)",
                (conversation_id, title[:500])
            )
            
            # Preparar mensajes en lote
            messages_batch = []
            batch_size = 50  # Tamaño de lote optimizado
            
            for message_id, message_data in mapping.items():
                try:
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
                    
                    # Campos adicionales
                    author = message_obj.get('author', {})
                    role = author.get('role', 'unknown') if isinstance(author, dict) else 'unknown'
                    
                    create_time = None
                    if message_data.get('create_time'):
                        try:
                            create_time = datetime.fromtimestamp(message_data['create_time'])
                        except:
                            pass
                    
                    parent = message_data.get('parent')
                    children = json.dumps(message_data.get('children', []))
                    
                    messages_batch.append((
                        message_id,
                        conversation_id,
                        role,
                        content[:65000],
                        parts_json[:65000],
                        create_time,
                        parent,
                        children[:65000]
                    ))
                    
                    # Insertar cuando el lote esté completo
                    if len(messages_batch) >= batch_size:
                        insert_batch_messages(cursor, messages_batch)
                        messages_batch = []
                        
                except Exception:
                    continue
            
            # Insertar mensajes restantes
            message_count = insert_batch_messages(cursor, messages_batch)
            return message_count + len(messages_batch)
            
    except Exception as e:
        print(f"❌ Error conversación {conversation_id}: {e}")
        return 0
    finally:
        connection.close()

def main_import_process():
    """Proceso principal de importación optimizado"""
    print("🚀 IMPORTACIÓN MASIVA AUTOMÁTICA")
    print("=" * 50)
    
    # Estado inicial
    existing = get_existing_conversations()
    print(f"📊 Conversaciones existentes: {len(existing)}")
    
    # Cargar datos
    try:
        with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        print(f"📁 Conversaciones en archivo: {len(conversations)}")
    except Exception as e:
        print(f"❌ Error cargando JSON: {e}")
        return
    
    # Procesar
    processed = 0
    total_messages = 0
    start_time = time.time()
    remaining = len(conversations) - len(existing)
    
    print(f"🎯 Conversaciones a procesar: {remaining}")
    print("=" * 50)
    
    for i, conv in enumerate(conversations):
        try:
            conv_id = conv.get('conversation_id') or conv.get('id')
            if not conv_id or conv_id in existing:
                continue
            
            title = conv.get('title', 'Sin título')
            mapping = conv.get('mapping', {})
            
            if not mapping:
                continue
            
            # Procesar conversación
            msg_count = process_conversation_optimized(conv_id, title, mapping)
            
            if msg_count > 0:
                processed += 1
                total_messages += msg_count
                
                # Reporte de progreso cada 10 conversaciones
                if processed % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta_minutes = (remaining - processed) / rate / 60 if rate > 0 else 0
                    
                    print(f"✅ {processed:3d}/{remaining} | {total_messages:5d} msgs | "
                          f"{rate:.2f}/seg | ETA: {eta_minutes:.1f}min")
                
                # Pausa mínima para no saturar servidor
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⏸️  Proceso interrumpido")
            break
        except Exception as e:
            continue
    
    # Estadísticas finales
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL:")
    print(f"   ✅ Conversaciones procesadas: {processed}")
    print(f"   💬 Mensajes importados: {total_messages}")
    print(f"   ⏱️  Tiempo total: {elapsed/60:.2f} minutos")
    if processed > 0:
        print(f"   📈 Promedio: {total_messages/processed:.1f} mensajes/conversación")
        print(f"   🚀 Velocidad: {processed/elapsed:.2f} conversaciones/segundo")

if __name__ == "__main__":
    try:
        main_import_process()
        print("\n🎉 IMPORTACIÓN COMPLETADA!")
    except KeyboardInterrupt:
        print("\n⏸️  Proceso terminado por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")