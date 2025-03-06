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


def create_tables():
    """Crea las tablas necesarias para almacenar conversaciones y mensajes."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title TEXT
                    );
                ""
                )
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        conversation_id INT,
                        role VARCHAR(50),
                        content TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    );
                ""
                )
            connection.commit()
            print("[OK] Tablas creadas correctamente.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudieron crear las tablas: {e}")
        finally:
            connection.close()


def insert_conversation(title, messages):
    """Inserta una conversación y sus mensajes en la base de datos."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO conversations (title) VALUES (%s)", (title,))
                conversation_id = cursor.lastrowid
                
                for msg in messages:
                    cursor.execute(
                        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                        (conversation_id, msg.get("role", ""), msg.get("content", ""))
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
                insert_conversation(conversation.get("title", "Sin título"), conversation.get("mapping", {}).values())
    except Exception as e:
        print(f"[ERROR] No se pudo procesar el JSON: {e}")


def main():
    """Función principal"""
    create_tables()
    process_conversations()
    print("[OK] Datos procesados y almacenados correctamente.")


if __name__ == "__main__":
    main()
