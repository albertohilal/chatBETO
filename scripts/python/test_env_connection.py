"""
Ejemplo de script actualizado para usar variables de entorno
Basado en los scripts de importación existentes
"""
import mysql.connector
from env_loader import get_db_config, get_app_config
import logging

def connect_to_db():
    """Conectar a la base de datos usando configuración del .env"""
    config = get_db_config()
    app_config = get_app_config()
    
    try:
        connection = mysql.connector.connect(**config)
        
        if app_config['debug']:
            print(f"✅ Conectado a la base de datos: {config['database']} en {config['host']}")
        
        return connection
        
    except mysql.connector.Error as e:
        if app_config['debug']:
            print(f"❌ Error detallado: {e}")
        else:
            print("❌ Error de conexión a la base de datos")
        raise

def verify_connection():
    """Verificar que la conexión funciona correctamente"""
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Test básico
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✅ Conexión a la base de datos exitosa")
            
            # Mostrar información de configuración (sin credenciales)
            config = get_db_config()
            app_config = get_app_config()
            
            print(f"📊 Aplicación: {app_config['name']}")
            print(f"🌍 Entorno: {app_config['environment']}")
            print(f"🗄️  Base de datos: {config['database']}")
            print(f"🖥️  Host: {config['host']}")
            
            return True
        else:
            print("❌ La conexión no respondió correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error en la verificación: {str(e)}")
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔐 Verificando conexión con credenciales desde .env")
    verify_connection()