import json
import os
import pymysql
import zipfile

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
        print("[OK] Conectado a la base de datos correctamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        return None


def drop_tables():
    """Elimina las tablas si existen."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                cursor.execute("DROP TABLE IF EXISTS messages;")
                cursor.execute("DROP TABLE IF EXISTS conversations;")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
            print("[OK] Tablas eliminadas correctamente.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudieron eliminar las tablas: {e}")
        finally:
            connection.close()


def create_tables():
    """Crea las nuevas tablas conversations y messages."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id VARCHAR(255) PRIMARY KEY,
                        title TEXT
                    );
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id VARCHAR(255) PRIMARY KEY,
                        conversation_id VARCHAR(255),
                        role VARCHAR(50),
                        content TEXT,
                        parts TEXT,
                        create_time FLOAT,
                        parent VARCHAR(255),
                        children TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                    );
                """)
            connection.commit()
            print("[OK] Tablas creadas correctamente.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudieron crear las tablas: {e}")
        finally:
            connection.close()


def insert_conversation(conversation_id, title, messages):
    """Inserta una conversación y sus mensajes en la base de datos."""
    if not conversation_id:
        print("[WARNING] Saltando conversación sin ID válido.")
        return

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO conversations (conversation_id, title) VALUES (%s, %s) ON DUPLICATE KEY UPDATE title=%s",
                               (conversation_id, title, title))
                
                for msg_id, msg_data in (messages or {}).items():
                    if not msg_data:
                        continue
                    
                    message = msg_data.get("message", {}) or {}
                    role = message.get("author", {}).get("role", "unknown")
                    parts_list = message.get("content", {}).get("parts", [])
                    
                    # Convertir cada parte a string si es un diccionario
                    parts = [json.dumps(part) if isinstance(part, dict) else str(part) for part in parts_list]
                    content = " ".join(parts)  # Unir en una sola cadena legible
                    
                    create_time = message.get("create_time", 0) or 0
                    parent = msg_data.get("parent", None)
                    children = json.dumps(msg_data.get("children", []) or [])
                    
                    cursor.execute(
                        """
                        INSERT INTO messages (id, conversation_id, role, content, parts, create_time, parent, children)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (msg_id, conversation_id, role, content, json.dumps(parts), create_time, parent, children)
                    )
            connection.commit()
            print(f"[OK] Conversación '{title}' y sus mensajes insertados.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudo insertar la conversación: {e}")
        finally:
            connection.close()


def process_conversations():
    """Carga y procesa el archivo JSON de conversaciones."""
    file_path = os.path.join(EXTRACT_PATH, "conversations.json")
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encontró el archivo {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for conversation in data:
                if not isinstance(conversation, dict):
                    print("[WARNING] Conversación inválida encontrada y omitida.")
                    continue
                
                conversation_id = conversation.get("conversation_id") or "unknown"
                title = conversation.get("title", "Sin título")
                messages = conversation.get("mapping", {})
                
                insert_conversation(conversation_id, title, messages)
    except Exception as e:
        print(f"[ERROR] No se pudo procesar el JSON: {e}")


def main():
    """Función principal"""
    drop_tables()
    create_tables()
    process_conversations()
    print("[OK] Datos procesados y almacenados correctamente.")


if __name__ == "__main__":
    main()
