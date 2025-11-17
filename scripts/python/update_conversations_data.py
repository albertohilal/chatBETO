#!/usr/bin/env python3
"""
Script para actualizar las conversaciones existentes con los nuevos campos:
project_id, project_name, create_time, update_time, model
"""
import pymysql
import json
import sys
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

def update_conversations_data():
    """Actualiza las conversaciones con los nuevos campos desde el JSON"""
    connection = create_connection()
    if not connection:
        return
    
    # Cargar datos del JSON
    try:
        with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        print(f"📁 Archivo JSON cargado: {len(conversations)} conversaciones")
    except Exception as e:
        print(f"❌ Error cargando JSON: {e}")
        return
    
    try:
        with connection.cursor() as cursor:
            updated_count = 0
            
            print("🔄 Actualizando conversaciones con nuevos campos...")
            
            for conv in conversations:
                try:
                    conv_id = conv.get('conversation_id') or conv.get('id')
                    if not conv_id:
                        continue
                    
                    # Extraer campos del JSON
                    project_id = conv.get('conversation_template_id') or conv.get('gizmo_id')
                    project_name = conv.get('title', 'Conversación ChatGPT')
                    
                    # Fechas
                    create_time = None
                    update_time = None
                    
                    if conv.get('create_time'):
                        try:
                            create_time = datetime.fromtimestamp(conv['create_time'])
                        except:
                            pass
                    
                    if conv.get('update_time'):
                        try:
                            update_time = datetime.fromtimestamp(conv['update_time'])
                        except:
                            pass
                    
                    # Modelo (buscar en el primer mensaje del assistant)
                    model = conv.get('default_model_slug', 'gpt-4')
                    
                    # También podemos extraer el modelo del primer mensaje assistant
                    mapping = conv.get('mapping', {})
                    for msg_data in mapping.values():
                        if isinstance(msg_data, dict):
                            message = msg_data.get('message')
                            if message and isinstance(message, dict):
                                author = message.get('author', {})
                                if author.get('role') == 'assistant':
                                    metadata = message.get('metadata', {})
                                    if metadata.get('model_slug'):
                                        model = metadata['model_slug']
                                        break
                    
                    # Actualizar la conversación
                    update_query = """
                    UPDATE conversations 
                    SET project_id = %s,
                        project_name = %s,
                        create_time = %s,
                        update_time = %s,
                        model = %s
                    WHERE conversation_id = %s
                    """
                    
                    cursor.execute(update_query, (
                        project_id,
                        project_name[:255] if project_name else None,
                        create_time,
                        update_time,
                        model,
                        conv_id
                    ))
                    
                    updated_count += 1
                    
                    # Progreso cada 50 conversaciones
                    if updated_count % 50 == 0:
                        print(f"📊 Actualizadas: {updated_count} conversaciones")
                
                except Exception as e:
                    print(f"⚠️  Error procesando conversación {conv_id}: {e}")
                    continue
            
            print(f"\n✅ Actualización completada: {updated_count} conversaciones actualizadas")
            
    except Exception as e:
        print(f"❌ Error en actualización: {e}")
    finally:
        connection.close()

def verify_update():
    """Verifica que las conversaciones se hayan actualizado correctamente"""
    connection = create_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) as total FROM conversations")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as with_dates FROM conversations WHERE create_time IS NOT NULL")
            with_dates = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as with_model FROM conversations WHERE model IS NOT NULL")
            with_model = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as with_project FROM conversations WHERE project_id IS NOT NULL")
            with_project = cursor.fetchone()[0]
            
            print(f"\n📊 Estadísticas de actualización:")
            print(f"   Total conversaciones: {total}")
            print(f"   Con fechas: {with_dates}")
            print(f"   Con modelo: {with_model}")
            print(f"   Con project_id: {with_project}")
            
            # Muestra de datos actualizados
            cursor.execute("""
            SELECT conversation_id, project_name, create_time, model 
            FROM conversations 
            WHERE create_time IS NOT NULL 
            LIMIT 5
            """)
            
            sample = cursor.fetchall()
            print(f"\n📝 Muestra de datos actualizados:")
            for row in sample:
                print(f"   ID: {row[0][:20]}... | Título: {row[1][:30]}... | Fecha: {row[2]} | Modelo: {row[3]}")
                
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    print("🚀 ACTUALIZANDO DATOS DE CONVERSACIONES")
    print("=" * 50)
    
    update_conversations_data()
    verify_update()
    
    print("\n🎉 ¡Proceso completado!")