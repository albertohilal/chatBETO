#!/usr/bin/env python3
"""
Script para crear el esquema de base de datos usando Python
"""

import json
import mysql.connector
from mysql.connector import Error

def create_schema_python():
    """Crea el esquema usando Python/MySQL connector"""
    
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
        
        # Leer y ejecutar schema
        with open('schema_chatbeto.sql', 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Dividir en sentencias individuales
        statements = []
        current_statement = ""
        
        for line in schema_content.split('\n'):
            line = line.strip()
            
            # Saltar comentarios y líneas vacías
            if line.startswith('--') or not line:
                continue
            
            current_statement += line + " "
            
            # Si termina en ;, es una sentencia completa
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Ejecutar cada sentencia
        for statement in statements:
            if statement and len(statement.strip()) > 5:  # Evitar sentencias vacías
                try:
                    cursor.execute(statement)
                    print(f"✅ Ejecutado: {statement[:60]}...")
                except Error as e:
                    if "already exists" in str(e) or "Duplicate key name" in str(e):
                        print(f"⚠️  Ya existe: {statement[:60]}...")
                    else:
                        print(f"❌ Error: {e}")
                        print(f"Sentencia: {statement[:100]}...")
        
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
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creando esquema de base de datos...")
    create_schema_python()