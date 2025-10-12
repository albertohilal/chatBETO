import pymysql
import json
import os

# Configuración de la base de datos
DB_CONFIG = {
    "host": "sv46.byethost46.org",
    "user": "iunaorg_b3toh",
    "password": "elgeneral2018",
    "database": "iunaorg_chatBeto",
    "port": 3306
}

# Archivos JSON
JSON_FILES = [
    "./extracted/conversations.json",
    "./extracted/message_feedback.json",
    "./extracted/model_comparisons.json",
    "./extracted/shared_conversations.json"
]

def connect_to_db():
    """Conectar a la base de datos MySQL."""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("[OK] Conectado a la base de datos correctamente.")
        return connection
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        return None

def drop_tables():
    """Eliminar tablas antes de la nueva creación."""
    connection = connect_to_db()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("DROP TABLE IF EXISTS message_relations;")
            cursor.execute("DROP TABLE IF EXISTS messages;")
            cursor.execute("DROP TABLE IF EXISTS conversations;")
            cursor.execute("DROP TABLE IF EXISTS message_feedback;")
            cursor.execute("DROP TABLE IF EXISTS model_comparisons;")
            cursor.execute("DROP TABLE IF EXISTS shared_conversations;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
        print("[OK] Tablas eliminadas correctamente.")
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudieron eliminar las tablas: {e}")
    finally:
        connection.close()

def create_table_from_json(table_name, data):
    """Crear una tabla en MySQL basada en la estructura del JSON."""
    connection = connect_to_db()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            columns = ", ".join([f"{key} TEXT" for key in data[0].keys()])
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, {columns});"
            cursor.execute(sql)
            connection.commit()
        print(f"[OK] Tabla '{table_name}' creada.")
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo crear la tabla {table_name}: {e}")
    finally:
        connection.close()

def insert_data(table_name, data):
    """Insertar datos en la tabla correspondiente."""
    connection = connect_to_db()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            columns = ", ".join(data[0].keys())
            placeholders = ", ".join(["%s"] * len(data[0]))
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
            cursor.executemany(sql, [tuple(d.values()) for d in data])
            connection.commit()
        print(f"[OK] Datos insertados en '{table_name}'.")
    except pymysql.MySQLError as e:
        print(f"[ERROR] No se pudo insertar en {table_name}: {e}")
    finally:
        connection.close()

def load_json(filepath):
    """Cargar datos desde un archivo JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] No se pudo cargar JSON {filepath}: {e}")
        return None

def process_json_files():
    """Procesar archivos JSON y almacenarlos en MySQL."""
    for filepath in JSON_FILES:
        table_name = os.path.basename(filepath).replace(".json", "")
        data = load_json(filepath)

        if data:
            create_table_from_json(table_name, data)
            insert_data(table_name, data)
        else:
            print(f"[INFO] No hay datos en {table_name}, se omite la inserción.")

def main():
    """Función principal."""
    drop_tables()
    process_json_files()
    print("[OK] Datos procesados y almacenados.")

if __name__ == "__main__":
    main()
