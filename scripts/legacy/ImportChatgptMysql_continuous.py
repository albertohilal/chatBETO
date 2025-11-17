#!/usr/bin/env python3
"""
Script de importación continua optimizada para completar automáticamente
todas las conversaciones restantes del archivo conversations.json
"""
import pymysql
import json
import time
import sys
from datetime import datetime
import signal

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

# Variables globales para estadísticas
total_processed = 0
total_messages = 0
start_time = time.time()

def signal_handler(sig, frame):
    """Manejador para interrupciones elegantes"""
    elapsed = time.time() - start_time
    print(f"\n⏸️  PROCESO INTERRUMPIDO")
    print(f"📊 ESTADÍSTICAS PARCIALES:")
    print(f"   ✅ Conversaciones procesadas: {total_processed}")
    print(f"   💬 Mensajes importados: {total_messages}")
    print(f"   ⏱️  Tiempo: {elapsed/60:.2f} minutos")
    if total_processed > 0:
        print(f"   📈 Promedio: {total_messages/total_processed:.1f} mensajes/conv")
        print(f"   🚀 Velocidad: {total_processed/elapsed:.2f} conv/segundo")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def create_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"❌ Error conexión: {e}")
        time.sleep(5)  # Esperar antes de reintentar
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

def process_conversation_ultra_optimized(conversation_id, title, mapping):
    """Versión ultra-optimizada para procesamiento rápido"""
    global total_processed, total_messages
    
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
            
            # Preparar todos los mensajes de una vez
            messages_batch = []
            for message_id, message_data in mapping.items():
                try:
                    if not message_data or not isinstance(message_data, dict):
                        continue
                    
                    message_obj = message_data.get('message')
                    if not message_obj or not isinstance(message_obj, dict):
                        continue
                    
                    # Procesar contenido rápidamente
                    content = ""
                    parts_json = "[]"
                    
                    if 'content' in message_obj:
                        content_data = message_obj['content']
                        if isinstance(content_data, dict) and 'parts' in content_data:
                            parts = content_data['parts']
                            if isinstance(parts, list):
                                content = '\n'.join(str(part) for part in parts if part)[:65000]
                                parts_json = json.dumps(parts)[:65000]
                        elif isinstance(content_data, str):
                            content = content_data[:65000]
                            parts_json = json.dumps([content_data])[:65000]
                    
                    # Campos básicos
                    author = message_obj.get('author', {})
                    role = author.get('role', 'unknown') if isinstance(author, dict) else 'unknown'
                    
                    create_time = None
                    if message_data.get('create_time'):
                        try:
                            create_time = datetime.fromtimestamp(message_data['create_time'])
                        except:
                            pass
                    
                    parent = message_data.get('parent')
                    children = json.dumps(message_data.get('children', []))[:65000]
                    
                    messages_batch.append((
                        message_id,
                        conversation_id,
                        role,
                        content,
                        parts_json,
                        create_time,
                        parent,
                        children
                    ))
                except:
                    continue
            
            # Insertar todos los mensajes de una vez
            if messages_batch:
                cursor.executemany(
                    """INSERT IGNORE INTO messages 
                       (id, conversation_id, role, content, parts, create_time, parent, children) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    messages_batch
                )
            
            message_count = len(messages_batch)
            total_processed += 1
            total_messages += message_count
            
            return message_count
            
    except Exception as e:
        print(f"❌ Error conv {conversation_id}: {e}")
        return 0
    finally:
        connection.close()

def continuous_import():
    """Proceso de importación continua sin interrupciones"""
    global start_time
    
    print("🚀 IMPORTACIÓN CONTINUA AUTOMÁTICA")
    print("=" * 60)
    
    # Obtener estado inicial
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
    
    # Calcular trabajo pendiente
    remaining = len(conversations) - len(existing)
    print(f"🎯 Conversaciones a procesar: {remaining}")
    print("=" * 60)
    
    if remaining == 0:
        print("✅ ¡Todas las conversaciones ya están importadas!")
        return
    
    # Procesar continuamente
    start_time = time.time()
    last_report_time = start_time
    
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
            msg_count = process_conversation_ultra_optimized(conv_id, title, mapping)
            
            current_time = time.time()
            
            # Reporte cada 25 conversaciones o cada 2 minutos
            if total_processed % 25 == 0 or (current_time - last_report_time) >= 120:
                elapsed = current_time - start_time
                rate = total_processed / elapsed if elapsed > 0 else 0
                eta_minutes = (remaining - total_processed) / rate / 60 if rate > 0 else 0
                
                print(f"📊 {total_processed:3d}/{remaining} | {total_messages:5d} msgs | "
                      f"{rate:.2f}/seg | ETA: {eta_minutes:.1f}min | "
                      f"Tiempo: {elapsed/60:.1f}min")
                last_report_time = current_time
            
            # Pausa mínima para no saturar
            time.sleep(0.05)
                
        except Exception as e:
            print(f"⚠️  Error conv {i+1}: {e}")
            continue
    
    # Resumen final
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("🎉 ¡IMPORTACIÓN COMPLETADA!")
    print(f"📊 RESUMEN FINAL:")
    print(f"   ✅ Conversaciones procesadas: {total_processed}")
    print(f"   💬 Mensajes importados: {total_messages}")
    print(f"   ⏱️  Tiempo total: {elapsed/60:.2f} minutos")
    if total_processed > 0:
        print(f"   📈 Promedio: {total_messages/total_processed:.1f} mensajes/conversación")
        print(f"   🚀 Velocidad: {total_processed/elapsed:.2f} conversaciones/segundo")

if __name__ == "__main__":
    try:
        continuous_import()
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")