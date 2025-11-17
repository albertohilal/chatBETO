#!/usr/bin/env python3
# Test de las APIs con la base remota

import requests
import json

def test_apis():
    try:
        print(f"🧪 Probando APIs con base de datos remota...")
        
        # Base URL (asumiendo que usas un servidor web local)
        base_url = "http://localhost"
        
        apis = [
            'api_get_projects.php',
            'api_get_stats.php',
            'api_get_conversations.php',
            'api_get_messages.php'
        ]
        
        for api in apis:
            print(f"\n🔍 Probando {api}...")
            
            try:
                url = f"{base_url}/{api}"
                response = requests.get(url, timeout=10)
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        print(f"  ✅ Array con {len(data)} elementos")
                        if len(data) > 0:
                            print(f"  📋 Primer elemento: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                    elif isinstance(data, dict):
                        print(f"  ✅ Objeto con {len(data)} propiedades")
                        print(f"  📋 Contenido: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"  ⚠️ Tipo de dato inesperado: {type(data)}")
                        
                else:
                    print(f"  ❌ Error HTTP: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Error de conexión: {e}")
                
        print(f"\n🔧 Si hay errores de conexión, inicia un servidor web:")
        print(f"   • cd /home/beto/Documentos/Github/chatBeto/chatBETO")
        print(f"   • php -S localhost:8080")
        print(f"   • O configura Apache/Nginx")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_db_connection_directly():
    print(f"\n🔄 Probando conexión directa a base de datos...")
    
    try:
        import mysql.connector
        import os
        
        # Leer configuración
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Test de API projects
        print(f"\n📁 Test API Projects:")
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.description,
                p.is_starred,
                p.chatgpt_project_id,
                COUNT(c.id) as conversation_count
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id
            GROUP BY p.id, p.name, p.description, p.is_starred, p.chatgpt_project_id
            ORDER BY p.is_starred DESC, conversation_count DESC, p.name ASC
            LIMIT 5
        """)
        
        projects = cursor.fetchall()
        print(f"  ✅ {len(projects)} proyectos obtenidos")
        
        for project in projects:
            star = "⭐" if project[3] else "  "
            print(f"    {project[0]:2d}. {star} {project[1][:30]:<30} | {project[5]} conv")
        
        # Test de API stats
        print(f"\n📊 Test API Stats:")
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {total_projects}")
        print(f"  💬 Conversaciones: {total_conversations}")
        print(f"  💌 Mensajes: {total_messages}")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ Conexión directa a BD funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error en conexión directa: {e}")

if __name__ == "__main__":
    test_db_connection_directly()
    test_apis()