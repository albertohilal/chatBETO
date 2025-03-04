import zipfile
import json
import pymysql
import os

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

# Conectar a la base de datos
def connect_to_db():
    try:
        connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"],
            charset="utf8mb4"
        )
        print("Conectado a la base de datos correctamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# Extraer archivo ZIP
def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Archivo ZIP extraído correctamente en {extract_to}.")
        return True
    except Exception as e:
        print(f"Error al extraer ZIP: {e}")
        return False

# Leer archivo JSON
def load_json_file(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"Archivo JSON {json_path} cargado correctamente.")
        return data
    except Exception as e:
        print(f"Error al cargar JSON {json_path}: {e}")
        return None

# Eliminar tablas
def drop_tables():
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS message_relations;")
                cursor.execute("DROP TABLE IF EXISTS messages;")
                cursor.execute("DROP TABLE IF EXISTS conversations;")
            connection.commit()
            print("Tablas eliminadas correctamente.")
        finally:
            connection.close()

# Crear tablas
def create_tables():
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                CREATE TABLE conversations (
                    conversation_id VARCHAR(50) PRIMARY KEY,
                    default_model_slug VARCHAR(50),
                    is_archived TINYINT(1)
                );
                """)
                cursor.execute("""
                CREATE TABLE messages (
                    id VARCHAR(50) PRIMARY KEY,
                    conversation_id VARCHAR(50),
                    author_role VARCHAR(50),
                    create_time FLOAT,
                    content TEXT,
                    parent_id VARCHAR(50),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE message_relations (
                    parent_id VARCHAR(50),
                    child_id VARCHAR(50),
                    PRIMARY KEY (parent_id, child_id),
                    FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE,
                    FOREIGN KEY (child_id) REFERENCES messages(id) ON DELETE CASCADE
                );
                """)
            connection.commit()
            print("Tablas creadas correctamente.")
        finally:
            connection.close()

# Insertar datos en la base de datos
def insert_data(data):
    connection = connect_to_db()
    if connection is None:
        return
    try:
        with connection.cursor() as cursor:
            # Insertar conversaciones
            print("Insertando conversaciones...")
            for conv in data:
                sql = "INSERT INTO conversations (conversation_id, default_model_slug, is_archived) VALUES (%s, %s, %s)"
                cursor.execute(sql, (conv["id"], conv.get("default_model_slug", None), conv.get("is_archived", 0)))
            connection.commit()
            
            # Insertar mensajes
            print("Insertando mensajes...")
            for conv in data:
                for msg in conv.get("mapping", {}).values():
                    message = msg.get("message", {})
                    if not message or "id" not in message:
                        continue
                    
                    # Convertir contenido a string
                    content = message.get("content", "")
                    if isinstance(content, (dict, list)):  # Si es dict o lista, convertirlo a string
                        content = json.dumps(content, ensure_ascii=False)

                    sql = "INSERT INTO messages (id, conversation_id, author_role, create_time, content, parent_id) VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (
                        message["id"],
                        conv["id"],
                        message.get("author", {}).get("role", ""),
                        message.get("create_time", 0),
                        content,  # Ahora convertido a string
                        msg.get("parent", None)
                    ))
            connection.commit()
            
            # Insertar relaciones entre mensajes
            print("Insertando relaciones entre mensajes...")
            for conv in data:
                for msg in conv.get("mapping", {}).values():
                    if "parent" in msg and msg["parent"]:
                        sql = "INSERT INTO message_relations (parent_id, child_id) VALUES (%s, %s)"
                        cursor.execute(sql, (msg["parent"], msg["message"]["id"]))
            connection.commit()
        print("Datos insertados correctamente en MySQL.")
    except pymysql.MySQLError as e:
        print(f"Error al insertar datos: {e}")
    finally:
        connection.close()

# Proceso principal
def main():
    drop_tables()  # Elimina las tablas antes de crearlas
    create_tables()  # Vuelve a crearlas desde cero

    if extract_zip(ZIP_FILE, EXTRACT_PATH):
        json_path = os.path.join(EXTRACT_PATH, JSON_FILENAME)
        data = load_json_file(json_path)
        if data:
            insert_data(data)  # Inserta los datos en la base

if __name__ == "__main__":
    main()
