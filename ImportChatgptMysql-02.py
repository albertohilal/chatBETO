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
JSON_FILES = [
   # "user.json",
    "conversations.json",
    "message_feedback.json",
    "model_comparisons.json",
    "shared_conversations.json"
]

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
    """Elimina las tablas en el orden correcto para evitar errores de claves foráneas"""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                tables_to_delete = ["message_feedback", "shared_conversations", "model_comparisons", "message_relations", "messages", "conversations"]
                for table in tables_to_delete:
                    cursor.execute(f"DROP TABLE IF EXISTS {table};")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
            print("[OK] Tablas eliminadas correctamente.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudieron eliminar las tablas: {e}")
        finally:
            connection.close()

# def extract_zip(zip_path, extract_to):
#     """Extrae el archivo ZIP que contiene los JSON"""
#     try:
#         with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#             zip_ref.extractall(extract_to)
#         print(f"[OK] Archivo ZIP extraído en {extract_to}.")
#         return True
#     except Exception as e:
#         print(f"[ERROR] No se pudo extraer ZIP: {e}")
#         return False

def load_json(file_path):
    """Carga un archivo JSON"""
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encontró el archivo JSON: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"[OK] JSON cargado: {file_path}.")
        return data
    except Exception as e:
        print(f"[ERROR] No se pudo cargar JSON {file_path}: {e}")
        return None

def create_table_from_json(table_name, data):
    """Crea una tabla basada en la estructura del JSON"""
    if not isinstance(data, list) or len(data) == 0:
        print(f"[INFO] No hay datos en {table_name}, se omite la creación.")
        return

    sample_record = data[0]
    columns = []

    for key, value in sample_record.items():
        if key.lower() == "id":  
            continue
        if isinstance(value, int):
            column_type = "INT"
        elif isinstance(value, float):
            column_type = "FLOAT"
        elif isinstance(value, bool):
            column_type = "TINYINT(1)"
        else:
            column_type = "TEXT"

        columns.append(f"`{key}` {column_type}")

    column_definitions = ", ".join(columns)

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS `{table_name}` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        {column_definitions}
                    );
                """)
            connection.commit()
            print(f"[OK] Tabla '{table_name}' creada.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudo crear la tabla {table_name}: {e}")
        finally:
            connection.close()

def insert_data(table_name, data):
    """Inserta datos en la tabla correspondiente"""
    if not isinstance(data, list) or len(data) == 0:
        print(f"[INFO] No hay datos en {table_name}, omitiendo la inserción.")
        return

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sample_record = data[0]
                columns = [col for col in sample_record.keys() if col.lower() != "id"]
                column_names = ", ".join([f"`{col}`" for col in columns])
                placeholders = ", ".join(["%s"] * len(columns))

                sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
                values = []

                for item in data:
                    row_values = []
                    for col in columns:
                        val = item.get(col, None)
                        if isinstance(val, dict):  
                            val = json.dumps(val)  
                        elif isinstance(val, list):
                            val = json.dumps(val)  
                        row_values.append(val)
                    values.append(tuple(row_values))

                cursor.executemany(sql, values)
            connection.commit()
            print(f"[OK] Datos insertados en '{table_name}'.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudo insertar en {table_name}: {e}")
        finally:
            connection.close()

def process_json_files():
    """Procesa los archivos JSON, crea tablas y almacena los datos"""
    for json_file in JSON_FILES:
        file_path = os.path.join(EXTRACT_PATH, json_file)
        data = load_json(file_path)
        if data:
            table_name = json_file.replace(".json", "")
            create_table_from_json(table_name, data)
            insert_data(table_name, data)

def main():
    """Función principal"""
    drop_tables()
  #  extract_zip(ZIP_FILE, EXTRACT_PATH)
    process_json_files()
    print("[OK] Datos procesados y almacenados.")

if __name__ == "__main__":
    main()
