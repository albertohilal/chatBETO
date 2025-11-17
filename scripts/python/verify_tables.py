import pymysql

# Configuración de la base de datos
DB_CONFIG = {
    "host": "sv46.byethost46.org",
    "user": "iunaorg_b3toh",
    "password": "elgeneral2018",
    "database": "iunaorg_chatBeto",
    "port": 3306
}

def verify_tables():
    """Verifica que las tablas estén creadas correctamente"""
    try:
        connection = pymysql.connect(**DB_CONFIG, charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
        
        with connection.cursor() as cursor:
            # Mostrar todas las tablas
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print("📋 Tablas en la base de datos:")
            for table in tables:
                print(f"  ✅ {list(table.values())[0]}")
            
            print("\n" + "="*50)
            
            # Mostrar estructura de conversations
            cursor.execute("DESCRIBE conversations;")
            conv_structure = cursor.fetchall()
            print("\n🗂️  Estructura de tabla 'conversations':")
            for field in conv_structure:
                print(f"  - {field['Field']}: {field['Type']} ({field['Key']})")
            
            # Mostrar estructura de messages
            cursor.execute("DESCRIBE messages;")
            msg_structure = cursor.fetchall()
            print("\n💬 Estructura de tabla 'messages':")
            for field in msg_structure:
                print(f"  - {field['Field']}: {field['Type']} ({field['Key']})")
                
            # Contar registros (debería ser 0 inicialmente)
            cursor.execute("SELECT COUNT(*) as count FROM conversations;")
            conv_count = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) as count FROM messages;")
            msg_count = cursor.fetchone()
            
            print(f"\n📊 Registros actuales:")
            print(f"  - Conversaciones: {conv_count['count']}")
            print(f"  - Mensajes: {msg_count['count']}")
            
        connection.close()
        print("\n✅ Verificación completada. Las tablas están listas para la importación!")
        
    except pymysql.MySQLError as e:
        print(f"❌ Error verificando tablas: {e}")

if __name__ == "__main__":
    verify_tables()