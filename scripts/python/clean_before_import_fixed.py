#!/usr/bin/env python3
# Limpiar tablas (versión corregida)

import mysql.connector
import json
import os

def clean_conversations_and_messages_fixed():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🧹 Limpiando tablas de conversaciones y mensajes en {config['database']}")
        
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
        
        # 1. VERIFICAR estado actual
        print(f"\n📊 Estado actual de las tablas:")
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        current_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        current_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        current_projects = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {current_projects}")
        print(f"  💬 Conversaciones: {current_conversations:,}")
        print(f"  💌 Mensajes: {current_messages:,}")
        
        # 2. LIMPIAR tabla MESSAGES (primero por foreign key)
        print(f"\n🗑️ Limpiando tabla 'messages'...")
        
        if current_messages > 0:
            cursor.execute("DELETE FROM messages")
            deleted_messages = cursor.rowcount
            print(f"  🗑️ {deleted_messages:,} mensajes eliminados")
        else:
            print(f"  ℹ️ Tabla 'messages' ya está vacía")
        
        # 3. LIMPIAR tabla CONVERSATIONS
        print(f"\n🗑️ Limpiando tabla 'conversations'...")
        
        if current_conversations > 0:
            cursor.execute("DELETE FROM conversations")
            deleted_conversations = cursor.rowcount
            print(f"  🗑️ {deleted_conversations:,} conversaciones eliminadas")
        else:
            print(f"  ℹ️ Tabla 'conversations' ya está vacía")
        
        # 4. VERIFICAR estructura de projects
        print(f"\n🔍 Verificando estructura de tabla 'projects'...")
        
        cursor.execute("DESCRIBE projects")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        print(f"  📋 Columnas en projects: {', '.join(column_names)}")
        
        # Solo intentar actualizar si la columna existe
        if 'conversation_count' in column_names:
            cursor.execute("UPDATE projects SET conversation_count = 0")
            updated_projects = cursor.rowcount
            print(f"  🔄 {updated_projects} proyectos actualizados (conversation_count = 0)")
        else:
            print(f"  ℹ️ Columna 'conversation_count' no existe, omitiendo actualización")
        
        # 5. VERIFICAR limpieza
        print(f"\n✅ Verificando limpieza...")
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        final_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        final_projects = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {final_projects} (mantenidos)")
        print(f"  💬 Conversaciones: {final_conversations} (debe ser 0)")
        print(f"  💌 Mensajes: {final_messages} (debe ser 0)")
        
        # 6. MOSTRAR información de proyectos mantenidos
        print(f"\n📋 Proyectos mantenidos (primeros 10):")
        cursor.execute("""
            SELECT id, name, chatgpt_project_id, is_starred
            FROM projects 
            ORDER BY id 
            LIMIT 10
        """)
        
        projects = cursor.fetchall()
        for project_id, name, gizmo_id, is_starred in projects:
            star = "⭐" if is_starred else "  "
            gizmo_display = (gizmo_id[:20] + "...") if gizmo_id and len(gizmo_id) > 20 else gizmo_id or "Sin gizmo_id"
            print(f"    {project_id:2d}. {star} {name[:25]:<25} | {gizmo_display}")
        
        if final_projects > 10:
            print(f"    ... y {final_projects - 10} proyectos más")
        
        # 7. VERIFICAR gizmo_ids mapeados
        cursor.execute("SELECT COUNT(*) FROM projects WHERE chatgpt_project_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"\n🎯 Proyectos con gizmo_id mapeado: {projects_with_gizmo} de {final_projects}")
        
        cursor.close()
        connection.close()
        
        if final_conversations == 0 and final_messages == 0:
            print(f"\n✅ ¡Limpieza completada exitosamente!")
            print(f"📤 Listo para importar conversaciones desde conversations.json")
            return True
        else:
            print(f"\n⚠️ Advertencia: La limpieza no fue completa")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clean_conversations_and_messages_fixed()