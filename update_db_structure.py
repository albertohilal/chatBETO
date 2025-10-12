#!/usr/bin/env python3
"""
Script para actualizar la estructura de la tabla conversations
agregando los campos recomendados
"""
import pymysql
import sys

# Configuración de conexión
DB_CONFIG = {
    'host': 'sv46.byethost46.org',
    'user': 'iunaorg_b3toh',
    'password': 'elgeneral2018',
    'database': 'iunaorg_chatBeto',
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
    'autocommit': True
}

def create_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"❌ Error conexión: {e}")
        return None

def update_conversations_structure():
    """Actualiza la estructura de la tabla conversations"""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            print("🔧 Actualizando estructura de tabla 'conversations'...")
            
            # ALTER TABLE para agregar los nuevos campos
            alter_query = """
            ALTER TABLE conversations
            ADD COLUMN project_id VARCHAR(100) NULL AFTER conversation_id,
            ADD COLUMN project_name VARCHAR(255) NULL AFTER project_id,
            ADD COLUMN create_time DATETIME NULL AFTER title,
            ADD COLUMN update_time DATETIME NULL AFTER create_time,
            ADD COLUMN model VARCHAR(100) NULL AFTER update_time
            """
            
            cursor.execute(alter_query)
            print("✅ Estructura actualizada exitosamente!")
            
            # Verificar la nueva estructura
            cursor.execute("DESCRIBE conversations")
            columns = cursor.fetchall()
            
            print("\n📋 Nueva estructura de la tabla 'conversations':")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} ({column[3]})")
            
            return True
            
    except pymysql.MySQLError as e:
        if "Duplicate column name" in str(e):
            print("⚠️  Los campos ya existen en la tabla")
            return True
        else:
            print(f"❌ Error al actualizar estructura: {e}")
            return False
    finally:
        connection.close()

def verify_structure():
    """Verifica que la estructura se haya actualizado correctamente"""
    connection = create_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE conversations")
            columns = cursor.fetchall()
            
            expected_fields = ['conversation_id', 'project_id', 'project_name', 'title', 'create_time', 'update_time', 'model']
            existing_fields = [col[0] for col in columns]
            
            print("\n🔍 Verificación de campos:")
            for field in expected_fields:
                if field in existing_fields:
                    print(f"  ✅ {field}")
                else:
                    print(f"  ❌ {field} (faltante)")
                    
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    print("🚀 ACTUALIZANDO ESTRUCTURA DE BASE DE DATOS")
    print("=" * 50)
    
    if update_conversations_structure():
        verify_structure()
        print("\n🎉 ¡Actualización completada!")
    else:
        print("\n❌ Falló la actualización")
        sys.exit(1)