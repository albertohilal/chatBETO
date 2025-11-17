#!/usr/bin/env python3
"""
Script para corregir los nombres de proyecto basándose en el contenido 
y categorías más específicas en lugar de duplicar el título
"""
import pymysql
import json
import re
from datetime import datetime

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

def categorize_conversation(title, model, messages_content):
    """
    Categoriza la conversación basándose en el título, modelo y contenido
    """
    title_lower = title.lower()
    content_lower = messages_content.lower()
    
    # Categorías de desarrollo y programación
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['python', 'javascript', 'php', 'html', 'css', 'sql', 'mysql', 'programming', 'código', 'script', 'desarrollo']):
        return "Desarrollo y Programación"
    
    # Categorías de IA y Machine Learning
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['chatgpt', 'openai', 'ia', 'artificial', 'machine learning', 'gpt']):
        return "Inteligencia Artificial"
    
    # Categorías de negocio y marketing
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['negocio', 'marketing', 'ventas', 'cliente', 'estrategia', 'plan', 'mercadosur']):
        return "Negocios y Marketing"
    
    # Categorías de diseño y creatividad
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['diseño', 'design', 'photoshop', 'imagen', 'creativo', 'brand', 'logo']):
        return "Diseño y Creatividad"
    
    # Categorías de tecnología y herramientas
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['github', 'git', 'vs code', 'linux', 'ubuntu', 'windows', 'servidor', 'hosting']):
        return "Tecnología y Herramientas"
    
    # Categorías de educación y aprendizaje
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['learn', 'tutorial', 'curso', 'enseñar', 'explicar', 'help', 'ayuda']):
        return "Educación y Aprendizaje"
    
    # Categorías de escritura y contenido
    if any(keyword in title_lower or keyword in content_lower for keyword in 
           ['escribir', 'redactar', 'contenido', 'texto', 'artículo', 'blog']):
        return "Escritura y Contenido"
    
    # Basado en el modelo usado
    if model:
        if 'gpt-4' in model:
            return "GPT-4 General"
        elif 'gpt-3' in model:
            return "GPT-3 General"
        elif 'davinci' in model:
            return "Davinci General"
    
    # Categoría por defecto
    return "Conversación General"

def get_conversation_content_sample(conversation_id):
    """
    Obtiene una muestra del contenido de los mensajes para categorización
    """
    connection = create_connection()
    if not connection:
        return ""
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT content 
                FROM messages 
                WHERE conversation_id = %s 
                AND content IS NOT NULL 
                AND content != '' 
                LIMIT 5
            """, (conversation_id,))
            
            results = cursor.fetchall()
            content_sample = " ".join([row[0][:200] for row in results])
            return content_sample
    except Exception as e:
        print(f"⚠️ Error obteniendo contenido: {e}")
        return ""
    finally:
        connection.close()

def update_project_names():
    """
    Actualiza los nombres de proyecto con categorías más específicas
    """
    connection = create_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            # Obtener todas las conversaciones
            cursor.execute("""
                SELECT conversation_id, title, model 
                FROM conversations 
                ORDER BY create_time DESC
            """)
            
            conversations = cursor.fetchall()
            print(f"📊 Procesando {len(conversations)} conversaciones...")
            
            updated_count = 0
            categories_count = {}
            
            for conv in conversations:
                conv_id = conv[0]
                title = conv[1] or "Sin título"
                model = conv[2] or ""
                
                # Obtener muestra del contenido
                content_sample = get_conversation_content_sample(conv_id)
                
                # Categorizar
                project_name = categorize_conversation(title, model, content_sample)
                
                # Contar categorías
                if project_name not in categories_count:
                    categories_count[project_name] = 0
                categories_count[project_name] += 1
                
                # Actualizar en la base de datos
                cursor.execute("""
                    UPDATE conversations 
                    SET project_name = %s 
                    WHERE conversation_id = %s
                """, (project_name, conv_id))
                
                updated_count += 1
                
                if updated_count % 50 == 0:
                    print(f"📊 Actualizadas: {updated_count} conversaciones")
            
            print(f"\n✅ Actualización completada: {updated_count} conversaciones")
            print(f"\n📊 Distribución por categorías:")
            for category, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / updated_count) * 100
                print(f"   {category}: {count} ({percentage:.1f}%)")
                
    except Exception as e:
        print(f"❌ Error en actualización: {e}")
    finally:
        connection.close()

def verify_project_names():
    """
    Verifica los nuevos nombres de proyecto
    """
    connection = create_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            # Verificar que project_name y title sean diferentes
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN project_name = title THEN 1 ELSE 0 END) as duplicados,
                    COUNT(DISTINCT project_name) as categorias_unicas
                FROM conversations
            """)
            
            stats = cursor.fetchone()
            print(f"\n📊 Estadísticas de project_name:")
            print(f"   Total conversaciones: {stats[0]}")
            print(f"   Duplicados (project_name = title): {stats[1]}")
            print(f"   Categorías únicas: {stats[2]}")
            
            # Mostrar muestra de diferentes categorías
            cursor.execute("""
                SELECT project_name, title, model, create_time
                FROM conversations 
                WHERE project_name != title
                ORDER BY project_name, create_time DESC
                LIMIT 10
            """)
            
            samples = cursor.fetchall()
            print(f"\n📝 Muestra de conversaciones categorizadas:")
            for sample in samples:
                print(f"   {sample[0]} | {sample[1][:40]}... | {sample[2]} | {sample[3]}")
                
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    print("🔧 CORRIGIENDO NOMBRES DE PROYECTO")
    print("=" * 50)
    
    update_project_names()
    verify_project_names()
    
    print("\n🎉 ¡Proceso completado!")
    print("Ahora project_name contiene categorías específicas en lugar de duplicar el título.")