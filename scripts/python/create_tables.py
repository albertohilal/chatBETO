import pymysql

# Configuración de la base de datos
DB_CONFIG = {
    "host": "sv46.byethost46.org",
    "user": "iunaorg_b3toh",
    "password": "elgeneral2018",
    "database": "iunaorg_chatBeto",
    "port": 3306
}

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
    """Crea las nuevas tablas conversations y messages."""
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                print("[INFO] Creando tabla 'conversations'...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id VARCHAR(255) PRIMARY KEY,
                        title TEXT
                    );
                """)
                
                print("[INFO] Creando tabla 'messages'...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id VARCHAR(255) PRIMARY KEY,
                        conversation_id VARCHAR(255),
                        role VARCHAR(50),
                        content TEXT,
                        parts TEXT,
                        create_time DATETIME,
                        parent VARCHAR(255),
                        children TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                    );
                """)
            connection.commit()
            print("[OK] ✅ Tablas creadas correctamente.")
            
            # Verificar que las tablas se crearon
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                print("\n[INFO] Tablas en la base de datos:")
                for table in tables:
                    print(f"  - {list(table.values())[0]}")
                    
        except pymysql.MySQLError as e:
            print(f"[ERROR] No se pudieron crear las tablas: {e}")
        finally:
            connection.close()
            print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    print("🚀 Creando tablas en la base de datos chatBeto...")
    create_tables()