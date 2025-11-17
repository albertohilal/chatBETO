#!/usr/bin/env python3
# Test de conexión a la base de datos remota iunaorg_chatBeto

import mysql.connector
import json
import sys
import os

def test_remote_connection():
    try:
        # Leer credenciales desde db_config.json
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"Conectando a: {config['host']}:{config['port']}")
        print(f"Base de datos: {config['database']}")
        print(f"Usuario: {config['user']}")
        
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4',
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Verificar conexión
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa!")
        print(f"MySQL Version: {version[0]}")
        
        # Verificar tablas existentes
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n📋 Tablas existentes ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar estructura de cada tabla
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"\n🔧 Estructura de '{table_name}':")
            for col in columns:
                print(f"  {col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]}")
        
        # Contar registros en cada tabla
        print(f"\n📊 Conteo de registros:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} registros")
        
        cursor.close()
        connection.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error de conexión MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    success = test_remote_connection()
    sys.exit(0 if success else 1)