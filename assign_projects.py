#!/usr/bin/env python3
"""
Script para asignar proyectos a conversaciones basándose en sus títulos
"""
import pymysql
import re
from env_loader import EnvLoader

def get_db_config():
    """Obtiene la configuración de base de datos desde variables de entorno"""
    EnvLoader.load()
    
    return {
        'host': EnvLoader.get('DB_HOST'),
        'user': EnvLoader.get('DB_USERNAME'), 
        'password': EnvLoader.get('DB_PASSWORD'),
        'database': EnvLoader.get('DB_NAME'),
        'charset': 'utf8mb4',
        'autocommit': True
    }

def create_connection():
    """Crea una conexión robusta a la base de datos"""
    try:
        config = get_db_config()
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return None

def extract_project_from_title(title):
    """Extrae el nombre del proyecto del título de la conversación"""
    if not title:
        return "General"
    
    title = title.strip()
    
    # Patrones específicos para identificar proyectos
    patterns = {
        # Desarrollo y herramientas
        'VS Code': ['vs code', 'vscode', 'visual studio code'],
        'GitHub': ['github', 'git hub'],
        'ChatGPT': ['chatgpt', 'chat gpt', 'openai'],
        'Xubuntu': ['xubuntu', 'ubuntu'],
        'Python': ['python', 'py', 'django', 'flask'],
        'JavaScript': ['javascript', 'js', 'node', 'react', 'vue'],
        'PHP': ['php', 'laravel', 'symfony'],
        'MySQL': ['mysql', 'mariadb', 'base de datos'],
        'Docker': ['docker', 'contenedor'],
        
        # Diseño y creatividad
        'Photoshop': ['photoshop', 'ps', 'adobe'],
        'GIMP': ['gimp'],
        'Diseño Web': ['diseño web', 'web design', 'css', 'html'],
        'WordPress': ['wordpress', 'wp'],
        'Elementor': ['elementor'],
        'Wix': ['wix'],
        
        # Freelancing y negocios
        'Fiverr': ['fiverr'],
        'Upwork': ['upwork'],
        'Freelancer': ['freelancer'],
        'LinkedIn': ['linkedin'],
        'Facebook': ['facebook'],
        
        # Proyectos específicos
        'AFIP': ['afip', 'factura electronica', 'dolibarr'],
        'WhatsApp': ['whatsapp', 'wa', 'bot'],
        'VGR': ['vgr-', 'vgr '],
        'ENARGAS': ['enargas', 'metrogas'],
        'Cerámica': ['ceramica', 'ceramic'],
        'Salud': ['salud', 'health', 'medicina'],
        'IA': ['inteligencia artificial', 'ia', 'ai', 'machine learning'],
        
        # Herramientas
        'XAMPP': ['xampp', 'lampp'],
        'Moodle': ['moodle'],
        'Google': ['google', 'gmail'],
        'Windows': ['windows'],
        'Android': ['android'],
    }
    
    title_lower = title.lower()
    
    # Buscar coincidencias
    for project, keywords in patterns.items():
        for keyword in keywords:
            if keyword in title_lower:
                return project
    
    # Si contiene números al inicio, podría ser un proyecto numerado
    if re.match(r'^\d+\s+', title):
        # Extraer la parte después del número
        project_part = re.sub(r'^\d+\s+', '', title)
        if len(project_part) > 3:
            return project_part[:30]  # Limitar longitud
    
    # Si no encuentra patrones específicos, usar las primeras 2-3 palabras
    words = title.split()
    if len(words) >= 2:
        return ' '.join(words[:2])
    elif len(words) == 1:
        return words[0]
    
    return "General"

def get_or_create_project(cursor, project_name):
    """Obtiene el ID del proyecto o lo crea si no existe"""
    try:
        # Buscar proyecto existente
        cursor.execute("SELECT id FROM projects WHERE name = %s", (project_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Crear nuevo proyecto
        cursor.execute(
            "INSERT INTO projects (name, description, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
            (project_name, f"Proyecto: {project_name}")
        )
        
        # Obtener el ID del proyecto recién creado
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]
        
    except Exception as e:
        print(f"❌ Error con proyecto {project_name}: {e}")
        return None

def assign_projects_to_conversations():
    """Función principal para asignar proyectos a conversaciones"""
    print("🚀 Iniciando asignación de proyectos a conversaciones...")
    
    connection = create_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Obtener conversaciones sin proyecto
        print("📋 Obteniendo conversaciones sin proyecto asignado...")
        cursor.execute(
            "SELECT conversation_id, title FROM conversations WHERE project_id IS NULL ORDER BY create_time DESC"
        )
        conversations = cursor.fetchall()
        
        print(f"📊 Conversaciones a procesar: {len(conversations)}")
        
        processed = 0
        projects_created = {}
        
        for conversation_id, title in conversations:
            processed += 1
            
            # Extraer proyecto del título
            project_name = extract_project_from_title(title)
            
            # Obtener o crear proyecto
            if project_name not in projects_created:
                project_id = get_or_create_project(cursor, project_name)
                projects_created[project_name] = project_id
            else:
                project_id = projects_created[project_name]
            
            if project_id:
                # Asignar proyecto a la conversación
                cursor.execute(
                    "UPDATE conversations SET project_id = %s WHERE conversation_id = %s",
                    (project_id, conversation_id)
                )
            
            # Mostrar progreso cada 50 conversaciones
            if processed % 50 == 0:
                progress = (processed / len(conversations)) * 100
                print(f"📈 Progreso: {processed}/{len(conversations)} ({progress:.1f}%)")
        
        print(f"\n🎉 ASIGNACIÓN COMPLETADA!")
        print(f"📊 Conversaciones procesadas: {processed}")
        print(f"📊 Proyectos creados: {len(projects_created)}")
        print(f"\n📋 Proyectos creados:")
        for project_name, project_id in projects_created.items():
            print(f"  - {project_name} (ID: {project_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en asignación: {e}")
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    assign_projects_to_conversations()