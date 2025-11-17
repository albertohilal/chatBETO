#!/usr/bin/env python3
# Actualizar estructura de tablas en iunaorg_chatBeto con mejoras

import mysql.connector
import json
import os

def update_remote_structure():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"Actualizando estructura en {config['database']}...")
        
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
        
        # Mejoras para la tabla projects
        print("\n🔧 Actualizando tabla 'projects'...")
        
        # Agregar campos faltantes si no existen
        try:
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN gizmo_id VARCHAR(100) NULL,
                ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE,
                ADD COLUMN last_activity DATETIME NULL,
                ADD COLUMN message_count INT DEFAULT 0,
                ADD INDEX idx_gizmo_id (gizmo_id),
                ADD INDEX idx_last_activity (last_activity)
            """)
            print("  ✅ Campos añadidos: gizmo_id, is_favorite, last_activity, message_count")
        except mysql.connector.Error as e:
            if "Duplicate column name" in str(e):
                print("  ℹ️ Los campos ya existen, continuando...")
            else:
                print(f"  ⚠️ Error al modificar projects: {e}")
        
        # Mejoras para la tabla conversations
        print("\n🔧 Actualizando tabla 'conversations'...")
        
        try:
            cursor.execute("""
                ALTER TABLE conversations
                ADD COLUMN gizmo_id VARCHAR(100) NULL,
                ADD COLUMN thread_id VARCHAR(100) NULL,
                ADD COLUMN message_count INT DEFAULT 0,
                ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE,
                ADD INDEX idx_gizmo_id (gizmo_id),
                ADD INDEX idx_thread_id (thread_id),
                ADD INDEX idx_create_time (create_time),
                ADD INDEX idx_project_id (project_id)
            """)
            print("  ✅ Campos añadidos: gizmo_id, thread_id, message_count, is_favorite")
        except mysql.connector.Error as e:
            if "Duplicate column name" in str(e):
                print("  ℹ️ Los campos ya existen, continuando...")
            else:
                print(f"  ⚠️ Error al modificar conversations: {e}")
        
        # Mejoras para la tabla messages
        print("\n🔧 Actualizando tabla 'messages'...")
        
        try:
            cursor.execute("""
                ALTER TABLE messages
                ADD COLUMN author_name VARCHAR(100) NULL,
                ADD COLUMN author_role VARCHAR(50) NULL,
                ADD COLUMN weight FLOAT DEFAULT 1.0,
                ADD COLUMN status VARCHAR(50) DEFAULT 'finished_successfully',
                ADD INDEX idx_conversation_id (conversation_id),
                ADD INDEX idx_create_time (create_time),
                ADD INDEX idx_role (role)
            """)
            print("  ✅ Campos añadidos: author_name, author_role, weight, status")
        except mysql.connector.Error as e:
            if "Duplicate column name" in str(e):
                print("  ℹ️ Los campos ya existen, continuando...")
            else:
                print(f"  ⚠️ Error al modificar messages: {e}")
        
        # Verificar estructura actualizada
        print("\n📋 Verificando estructura actualizada...")
        
        for table in ['projects', 'conversations', 'messages']:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            print(f"\n  Tabla '{table}' ({len(columns)} columnas):")
            for col in columns:
                print(f"    {col[0]} | {col[1]}")
        
        # Actualizar contadores
        print("\n📊 Actualizando contadores...")
        
        # Actualizar message_count en conversations
        cursor.execute("""
            UPDATE conversations c 
            SET message_count = (
                SELECT COUNT(*) FROM messages m 
                WHERE m.conversation_id = c.conversation_id
            )
        """)
        print("  ✅ Actualizado message_count en conversations")
        
        # Actualizar conversation_count y message_count en projects
        cursor.execute("""
            UPDATE projects p 
            SET conversation_count = (
                SELECT COUNT(*) FROM conversations c 
                WHERE c.project_id = p.id
            ),
            message_count = (
                SELECT COUNT(*) FROM messages m 
                INNER JOIN conversations c ON m.conversation_id = c.conversation_id
                WHERE c.project_id = p.id
            )
        """)
        print("  ✅ Actualizado contadores en projects")
        
        # Mostrar estadísticas finales
        print("\n📈 Estadísticas actualizadas:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversation_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE gizmo_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {project_count:,}")
        print(f"  💬 Conversaciones: {conversation_count:,}")
        print(f"  💌 Mensajes: {message_count:,}")
        print(f"  🎯 Proyectos con gizmo_id: {projects_with_gizmo:,}")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Estructura actualizada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    update_remote_structure()