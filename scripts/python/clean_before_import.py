#!/usr/bin/env python3
# Limpiar tablas de conversaciones y mensajes antes de reimportar

import mysql.connector
import json
import os

def clean_conversations_and_messages():
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
        
        if current_conversations == 0 and current_messages == 0:
            print(f"\n✅ Las tablas ya están limpias, no hay nada que eliminar")
            cursor.close()
            connection.close()
            return True
        
        # 2. CREAR RESPALDOS antes de limpiar
        print(f"\n💾 Creando respaldos de seguridad...")
        
        # Respaldo de conversations
        if current_conversations > 0:
            cursor.execute("DROP TABLE IF EXISTS conversations_backup_pre_import")
            cursor.execute("CREATE TABLE conversations_backup_pre_import AS SELECT * FROM conversations")
            print(f"  ✅ conversations_backup_pre_import creado ({current_conversations:,} registros)")
        
        # Respaldo de messages
        if current_messages > 0:
            cursor.execute("DROP TABLE IF EXISTS messages_backup_pre_import")
            cursor.execute("CREATE TABLE messages_backup_pre_import AS SELECT * FROM messages")
            print(f"  ✅ messages_backup_pre_import creado ({current_messages:,} registros)")
        
        # 3. LIMPIAR tabla MESSAGES (primero por foreign key)
        print(f"\n🗑️ Limpiando tabla 'messages'...")
        
        if current_messages > 0:
            cursor.execute("DELETE FROM messages")
            deleted_messages = cursor.rowcount
            print(f"  🗑️ {deleted_messages:,} mensajes eliminados")
            
            # Resetear AUTO_INCREMENT si es necesario
            cursor.execute("ALTER TABLE messages AUTO_INCREMENT = 1")
        else:
            print(f"  ℹ️ Tabla 'messages' ya está vacía")
        
        # 4. LIMPIAR tabla CONVERSATIONS
        print(f"\n🗑️ Limpiando tabla 'conversations'...")
        
        if current_conversations > 0:
            cursor.execute("DELETE FROM conversations")
            deleted_conversations = cursor.rowcount
            print(f"  🗑️ {deleted_conversations:,} conversaciones eliminadas")
            
            # Resetear AUTO_INCREMENT si es necesario
            cursor.execute("ALTER TABLE conversations AUTO_INCREMENT = 1")
        else:
            print(f"  ℹ️ Tabla 'conversations' ya está vacía")
        
        # 5. RESETEAR contadores en PROJECTS
        print(f"\n🔄 Reseteando contadores en proyectos...")
        
        cursor.execute("""
            UPDATE projects 
            SET conversation_count = 0
        """)
        
        updated_projects = cursor.rowcount
        print(f"  🔄 {updated_projects} proyectos actualizados (conversation_count = 0)")
        
        # 6. VERIFICAR limpieza
        print(f"\n✅ Verificando limpieza...")
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        final_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        final_projects = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {final_projects} (sin cambios)")
        print(f"  💬 Conversaciones: {final_conversations} (debe ser 0)")
        print(f"  💌 Mensajes: {final_messages} (debe ser 0)")
        
        # 7. MOSTRAR información de proyectos mantenidos
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
        
        # 8. INFORMACIÓN DE RESPALDOS
        if current_conversations > 0 or current_messages > 0:
            print(f"\n💾 Respaldos disponibles:")
            print(f"  📄 conversations_backup_pre_import: {current_conversations:,} registros")
            print(f"  📄 messages_backup_pre_import: {current_messages:,} registros")
            print(f"\n🔄 Para restaurar en caso de error:")
            print(f"    INSERT INTO conversations SELECT * FROM conversations_backup_pre_import;")
            print(f"    INSERT INTO messages SELECT * FROM messages_backup_pre_import;")
        
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
    clean_conversations_and_messages()