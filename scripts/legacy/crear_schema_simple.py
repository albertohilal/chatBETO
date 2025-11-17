#!/usr/bin/env python3
"""
Script simplificado para crear esquema compatible con MariaDB
"""

import json
import mysql.connector
from mysql.connector import Error

def create_simple_schema():
    """Crea el esquema simplificado usando Python"""
    
    # Cargar configuración
    try:
        with open('db_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró db_config.json")
        return False
    
    try:
        # Conectar a MySQL
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("✅ Conectado a MySQL")
        
        # Leer schema simplificado
        with open('schema_simple.sql', 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Ejecutar por bloques separados por punto y coma
        statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"✅ Sentencia {i+1}/{len(statements)} ejecutada")
                except Error as e:
                    if "already exists" in str(e):
                        print(f"⚠️  Tabla ya existe - {i+1}/{len(statements)}")
                    else:
                        print(f"❌ Error en sentencia {i+1}: {e}")
        
        connection.commit()
        print("\n✅ Esquema creado exitosamente!")
        
        # Verificar tablas creadas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\nTablas creadas: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creando esquema simplificado...")
    create_simple_schema()