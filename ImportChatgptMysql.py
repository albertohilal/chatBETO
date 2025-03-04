import pymysql
import json
import zipfile
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

# Conectar a MySQL
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
        print("✅ Conectado a la base de datos correctamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None

# Eliminar tablas existentes
def drop_tables():
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS message_relations;")
                cursor.execute("DROP TABLE IF EXISTS messages;")
                cursor.execute("DROP TABLE IF EXISTS conversations;")
            connection.commit()
            print("✅ Tablas eliminadas correctamente.")
        finally:
            connection.close()

# Crear tablas nuevamente
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
                        author_role VARCHAR(20),
                        create_time TIMESTAMP,
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
            print("✅ Tablas creadas correctamente.")
        finally:
            connection.close()

# Extraer el archivo ZIP
def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ Archivo ZIP extraído correctamente en {extract_to}.")
        return True
    except Exception as e:
        print(f"❌ Error al extraer ZIP: {e}")
        return False

# Cargar JSON
def load_json_file(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        print(f"✅ Archivo JSON {json_path} cargado correctamente.")
        return data
    except Exception as e:
        print(f"❌ Error al cargar JSON {json_path}: {e}")
        return None

# Insertar datos en MySQL
def insert_data(conversations):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                print("📌 Insertando conversaciones...")
                for conv in conversations:
                    cursor.execute("""
                        INSERT INTO conversations (conversation_id, default_model_slug, is_archived)
                        VALUES (%s, %s, %s)
                    """, (
                        conv.get("id", ""),
                        conv.get("default_model_slug", ""),
                        int(conv.get("is_archived", False))
                    ))

                print("📌 Insertando mensajes...")
                for conv in conversations:
                    for msg in conv.get("mapping", {}).values():
                        message_id = msg.get("id", "")
                        conversation_id = conv.get("id", "")
                        author_role = msg.get("message", {}).get("author", {}).get("role", "unknown")

                        # Verificar si es imagen o audio
                        content_data = msg.get("message", {}).get("content", "")
                        if isinstance(content_data, list) and len(content_data) > 0:
                            content = content_data[0]
                            if isinstance(content, dict) and content.get("content_type") == "image_asset_pointer":
                                file_url = f"http://diarioiuna12.ar.nf/chatBeto/uploads/{content.get('asset_pointer').replace('file-service://', '')}-image.png"
                                author_role = "image"
                            elif isinstance(content, dict) and content.get("content_type") == "audio_asset_pointer":
                                file_url = f"http://diarioiuna12.ar.nf/chatBeto/uploads/{content.get('asset_pointer').replace('file-service://', '')}-audio.mp3"
                                author_role = "audio"
                            else:
                                file_url = content.get("text", "")
                        else:
                            file_url = content_data if isinstance(content_data, str) else ""

                        create_time = msg.get("message", {}).get("create_time", None)
                        parent_id = msg.get("parent", None)

                        cursor.execute("""
                            INSERT INTO messages (id, conversation_id, author_role, create_time, content, parent_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            message_id, conversation_id, author_role, create_time, file_url, parent_id
                        ))

                print("✅ Datos insertados correctamente en MySQL.")
                connection.commit()
        except Exception as e:
            print(f"❌ Error al insertar datos: {e}")
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
