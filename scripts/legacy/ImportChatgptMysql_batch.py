import json
import os
import pymysql
from datetime import datetime
import time

# Configuración de la base de datos
DB_CONFIG = {
    "host": "sv46.byethost46.org",
    "user": "iunaorg_b3toh",
    "password": "elgeneral2018",
    "database": "iunaorg_chatBeto",
    "port": 3306
}

ZIP_FILE = "conversations.zip"
EXTRACT_PATH = "./extracted"

def connect_to_db():
    """Conecta a la base de datos MySQL"""
    try:
        connection = pymysql.connect(**DB_CONFIG, charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        return None

def get_existing_conversations():
    """Obtiene IDs de conversaciones que ya existen en la DB"""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT conversation_id FROM conversations")
                result = cursor.fetchall()
                return set(row['conversation_id'] for row in result)
        except pymysql.MySQLError as e:
            print(f"[ERROR] Error al obtener conversaciones existentes: {e}")
            return set()
        finally:
            connection.close()
    return set()

def insert_conversation(conversation_id, title, messages):
    """Inserta una conversación y sus mensajes en la base de datos."""
    if not conversation_id:
        return False

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Insertar conversación
                cursor.execute("INSERT INTO conversations (conversation_id, title) VALUES (%s, %s)",
                               (conversation_id, title))
                
                message_count = 0
                for msg_id, msg_data in (messages or {}).items():
                    if not msg_data:
                        continue
                    
                    message = msg_data.get("message", {}) or {}
                    role = message.get("author", {}).get("role", "unknown")
                    parts_list = message.get("content", {}).get("parts", [])

                    # Filtrar partes vacías y limpiar espacios
                    parts = [json.dumps(part, ensure_ascii=False) if isinstance(part, dict) else str(part).strip() for part in parts_list]
                    content = " ".join(parts).strip()

                    # Si el mensaje está vacío, no se inserta
                    if not content:
                        continue

                    create_time = message.get("create_time", 0) or 0
                    formatted_time = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                    
                    parent = msg_data.get("parent", None)
                    children = json.dumps(msg_data.get("children", []) or [], ensure_ascii=False)
                    
                    cursor.execute(
                        """
                        INSERT INTO messages (id, conversation_id, role, content, parts, create_time, parent, children)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (msg_id, conversation_id, role, content, json.dumps(parts, ensure_ascii=False), formatted_time, parent, children)
                    )
                    message_count += 1
            
            connection.commit()
            return message_count
        except pymysql.MySQLError as e:
            print(f"[ERROR] Error insertando conversación {conversation_id}: {e}")
            return False
        finally:
            connection.close()
    return False

def process_conversations_batch():
    """Procesa conversaciones por lotes para mejor rendimiento"""
    file_path = os.path.join(EXTRACT_PATH, "conversations.json")
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encontró el archivo {file_path}")
        return
    
    print("[INFO] Obteniendo conversaciones existentes...")
    existing_conversations = get_existing_conversations()
    print(f"[INFO] Conversaciones ya existentes: {len(existing_conversations)}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            total_conversations = len(data)
            processed = 0
            imported = 0
            skipped = 0
            
            print(f"[INFO] Total de conversaciones en archivo: {total_conversations}")
            
            for conversation in data:
                processed += 1
                
                if not isinstance(conversation, dict):
                    continue
                
                conversation_id = conversation.get("conversation_id") or "unknown"
                title = conversation.get("title", "Sin título")
                messages = conversation.get("mapping", {})
                
                # Skip if already exists
                if conversation_id in existing_conversations:
                    skipped += 1
                    if processed % 100 == 0:
                        print(f"[INFO] Progreso: {processed}/{total_conversations} | Importadas: {imported} | Saltadas: {skipped}")
                    continue
                
                # Import new conversation
                message_count = insert_conversation(conversation_id, title, messages)
                if message_count:
                    imported += 1
                    print(f"[OK] Importada: '{title}' ({message_count} mensajes)")
                
                # Progress update
                if processed % 50 == 0:
                    print(f"[INFO] Progreso: {processed}/{total_conversations} | Importadas: {imported} | Saltadas: {skipped}")
                    time.sleep(0.1)  # Small delay to prevent overwhelming the server
            
            print(f"\n[RESUMEN FINAL]")
            print(f"  - Total procesadas: {processed}")
            print(f"  - Nuevas importadas: {imported}")
            print(f"  - Ya existían: {skipped}")
            
    except Exception as e:
        print(f"[ERROR] No se pudo procesar el JSON: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando importación por lotes...")
    process_conversations_batch()
    print("[OK] Importación completada.")