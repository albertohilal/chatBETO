import zipfile
import json
import pymysql
import os
import sys

# Asegurar compatibilidad de codificación en Windows
sys.stdout.reconfigure(encoding="utf-8")

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
JSON_FILENAME = "conversations.json"


def connect_to_db():
    """Establece la conexión con la base de datos."""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        print("[OK] Conectado a la base de datos correctamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        return None


def execute_query(query, params=None):
    """Ejecuta una consulta SQL en la base de datos."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
            connection.commit()
            return True
        except pymysql.MySQLError as e:
            print(f"[ERROR] Falló la consulta: {e}\nConsulta: {query}")
            return False
        finally:
            connection.close()
    return False


def drop_tables():
    """Elimina las tablas antes de volver a crearlas desde cero."""
    queries = [
        "SET FOREIGN_KEY_CHECKS = 0;",
        "DROP TABLE IF EXISTS message_relations;",
        "DROP TABLE IF EXISTS messages;",
        "DROP TABLE IF EXISTS conversations;",
        "SET FOREIGN_KEY_CHECKS = 1;"
    ]
    for query in queries:
        execute_query(query)
    print("[OK] Tablas eliminadas correctamente.")


def create_tables():
    """Crea las tablas en la base de datos."""
    queries = [
        """CREATE TABLE conversations (
            conversation_id VARCHAR(50) PRIMARY KEY,
            default_model_slug VARCHAR(50),
            is_archived TINYINT(1)
        );""",
        """CREATE TABLE messages (
            id VARCHAR(50) PRIMARY KEY,
            conversation_id VARCHAR(50),
            author_role VARCHAR(50),
            create_time BIGINT,
            content TEXT,
            parent_id VARCHAR(50),
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
        );""",
        """CREATE TABLE message_relations (
            parent_id VARCHAR(50),
            child_id VARCHAR(50),
            PRIMARY KEY (parent_id, child_id),
            FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES messages(id) ON DELETE CASCADE
        );"""
    ]
    for query in queries:
        execute_query(query)
    print("[OK] Tablas creadas correctamente.")


def extract_zip(zip_path, extract_to):
    """Extrae el archivo ZIP."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[OK] Archivo ZIP extraído en {extract_to}.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo extraer el ZIP: {e}")
        return False


def load_json_file(json_path):
    """Carga el archivo JSON y devuelve los datos."""
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        print(f"[OK] Archivo JSON {json_path} cargado correctamente.")
        return data
    except Exception as e:
        print(f"[ERROR] No se pudo cargar JSON {json_path}: {e}")
        return None


def insert_data(conversations):
    """Inserta los datos en MySQL."""
    connection = connect_to_db()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            # Insertar las conversaciones
            print("[INFO] Insertando conversaciones...")
            for conv in conversations:
                conversation_id = conv.get("id", "")
                if not conversation_id:
                    continue
                default_model_slug = conv.get("default_model_slug", "")
                is_archived = conv.get("is_archived", 0)

                sql_conv = """INSERT IGNORE INTO conversations 
                              (conversation_id, default_model_slug, is_archived) 
                              VALUES (%s, %s, %s)"""
                cursor.execute(sql_conv, (conversation_id, default_model_slug, is_archived))

            connection.commit()

            # Insertar los mensajes
            print("[INFO] Insertando mensajes...")
            message_ids = set()
            for conv in conversations:
                conversation_id = conv.get("id", "")
                if not conversation_id:
                    continue

                for msg_id, msg in conv.get("mapping", {}).items():
                    if not isinstance(msg, dict):
                        continue

                    message_data = msg.get("message")
                    if not message_data:
                        continue

                    message_id = msg.get("id", "")
                    author_role = message_data.get("author", {}).get("role", "")
                    create_time = message_data.get("create_time", 0)
                    content_parts = message_data.get("content", {}).get("parts", [])

                    content = " ".join(str(part) if isinstance(part, str) else json.dumps(part) for part in content_parts)

                    parent_id = msg.get("parent", "")

                    sql_msg = """INSERT IGNORE INTO messages 
                                 (id, conversation_id, author_role, create_time, content, parent_id) 
                                 VALUES (%s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql_msg, (message_id, conversation_id, author_role, create_time, content, parent_id))
                    message_ids.add(message_id)

            connection.commit()

            # Insertar relaciones
            print("[INFO] Insertando relaciones...")
            for conv in conversations:
                for msg_id, msg in conv.get("mapping", {}).items():
                    if not isinstance(msg, dict):
                        continue

                    parent_id = msg.get("parent", "")
                    child_id = msg.get("id", "")

                    if parent_id and child_id and parent_id in message_ids:
                        sql_rel = """INSERT IGNORE INTO message_relations 
                                     (parent_id, child_id) 
                                     VALUES (%s, %s)"""
                        cursor.execute(sql_rel, (parent_id, child_id))

            connection.commit()
            print("[OK] Datos insertados correctamente en MySQL.")

    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudieron insertar datos: {e}")

    finally:
        connection.close()


def main():
    """Función principal para gestionar la importación de datos."""
    drop_tables()  # Elimina las tablas antes de crearlas
    create_tables()  # Vuelve a crearlas desde cero

    if extract_zip(ZIP_FILE, EXTRACT_PATH):
        json_path = os.path.join(EXTRACT_PATH, JSON_FILENAME)
        data = load_json_file(json_path)

        if data:
            insert_data(data)  # Inserta los datos en la base


if __name__ == "__main__":
    main()
