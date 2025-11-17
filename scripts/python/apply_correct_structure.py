#!/usr/bin/env python3
# Aplicar estructura exacta del test.sql a la base de datos remota

import mysql.connector
import json
import os

def apply_correct_structure():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🔧 Aplicando estructura correcta a {config['database']}")
        
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
        
        # 1. RESPALDO completo de las tablas actuales
        print(f"\n💾 Creando respaldo de tablas actuales...")
        
        backup_tables = ['projects', 'conversations', 'messages']
        for table in backup_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}_backup_old")
                cursor.execute(f"CREATE TABLE {table}_backup_old AS SELECT * FROM {table}")
                print(f"  ✅ Respaldo creado: {table}_backup_old")
            except mysql.connector.Error as e:
                print(f"  ⚠️ Error respaldando {table}: {e}")
        
        # 2. ELIMINAR tablas actuales
        print(f"\n🗑️ Eliminando tablas actuales...")
        
        # Eliminar en orden por foreign keys
        for table in ['messages', 'conversations', 'projects']:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  🗑️ Eliminada: {table}")
            except mysql.connector.Error as e:
                print(f"  ⚠️ Error eliminando {table}: {e}")
        
        # 3. CREAR tabla PROJECTS con estructura correcta
        print(f"\n📁 Creando tabla 'projects' con estructura correcta...")
        
        projects_sql = """
        CREATE TABLE `projects` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `name` varchar(255) NOT NULL,
          `description` text DEFAULT NULL,
          `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
          `is_starred` tinyint(1) DEFAULT 0,
          `chatgpt_project_id` varchar(100) DEFAULT NULL,
          `openai_assistant_id` varchar(100) DEFAULT NULL,
          PRIMARY KEY (`id`),
          UNIQUE KEY `name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
        
        cursor.execute(projects_sql)
        print(f"  ✅ Tabla 'projects' creada")
        
        # 4. CREAR tabla CONVERSATIONS con estructura correcta
        print(f"\n💬 Creando tabla 'conversations' con estructura correcta...")
        
        conversations_sql = """
        CREATE TABLE `conversations` (
          `id` varchar(36) NOT NULL,
          `project_id` int(11) DEFAULT NULL,
          `title` varchar(500) NOT NULL,
          `conversation_id` varchar(100) DEFAULT NULL,
          `create_time` decimal(20,6) DEFAULT NULL,
          `update_time` decimal(20,6) DEFAULT NULL,
          `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
          `is_archived` tinyint(1) DEFAULT 0,
          `is_starred` tinyint(1) DEFAULT 0,
          `default_model_slug` varchar(100) DEFAULT NULL,
          `gizmo_id` varchar(100) DEFAULT NULL,
          `conversation_origin` varchar(50) DEFAULT NULL,
          `chatgpt_gizmo_id` varchar(100) DEFAULT NULL,
          `openai_thread_id` varchar(100) DEFAULT NULL,
          PRIMARY KEY (`id`),
          KEY `project_id` (`project_id`),
          CONSTRAINT `conversations_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
        
        cursor.execute(conversations_sql)
        print(f"  ✅ Tabla 'conversations' creada")
        
        # 5. CREAR tabla MESSAGES con estructura correcta
        print(f"\n💌 Creando tabla 'messages' con estructura correcta...")
        
        messages_sql = """
        CREATE TABLE `messages` (
          `id` varchar(36) NOT NULL,
          `conversation_id` varchar(36) NOT NULL,
          `parent_message_id` varchar(36) DEFAULT NULL,
          `content_type` varchar(50) DEFAULT 'text',
          `content_text` longtext DEFAULT NULL,
          `author_role` varchar(50) NOT NULL,
          `author_name` varchar(255) DEFAULT NULL,
          `create_time` decimal(20,6) DEFAULT NULL,
          `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
          `status` varchar(50) DEFAULT 'finished_successfully',
          `end_turn` tinyint(1) DEFAULT 0,
          `weight` decimal(5,2) DEFAULT 1.00,
          `channel` varchar(50) DEFAULT NULL,
          `recipient` varchar(50) DEFAULT 'all',
          `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
          PRIMARY KEY (`id`),
          KEY `conversation_id` (`conversation_id`),
          CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
        
        cursor.execute(messages_sql)
        print(f"  ✅ Tabla 'messages' creada")
        
        # 6. VERIFICAR estructura creada
        print(f"\n📋 Verificando estructura creada...")
        
        for table_name in ['projects', 'conversations', 'messages']:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"\n  Tabla '{table_name}' ({len(columns)} columnas):")
            for col in columns:
                print(f"    {col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]}")
        
        # 7. MIGRAR datos desde respaldos si existen
        print(f"\n🔄 Intentando migrar datos desde respaldos...")
        
        # Migrar projects
        try:
            cursor.execute("""
                INSERT INTO projects (name, description, created_at, is_starred, chatgpt_project_id, openai_assistant_id)
                SELECT 
                    name, 
                    description, 
                    created_at,
                    COALESCE(is_favorite, 0) as is_starred,
                    gizmo_id as chatgpt_project_id,
                    NULL as openai_assistant_id
                FROM projects_backup_old
                WHERE name IS NOT NULL
                ORDER BY id
                LIMIT 66
            """)
            migrated_projects = cursor.rowcount
            print(f"  ✅ Migrados {migrated_projects} proyectos")
        except mysql.connector.Error as e:
            print(f"  ⚠️ Error migrando projects: {e}")
        
        # Migrar conversations
        try:
            cursor.execute("""
                INSERT INTO conversations (
                    id, project_id, title, conversation_id, 
                    create_time, update_time, created_at, 
                    is_archived, is_starred, default_model_slug, 
                    gizmo_id, conversation_origin, chatgpt_gizmo_id, openai_thread_id
                )
                SELECT 
                    conversation_id as id,
                    CAST(project_id AS UNSIGNED) as project_id,
                    title,
                    conversation_id,
                    UNIX_TIMESTAMP(create_time) as create_time,
                    UNIX_TIMESTAMP(update_time) as update_time,
                    NOW() as created_at,
                    0 as is_archived,
                    COALESCE(is_favorite, 0) as is_starred,
                    model as default_model_slug,
                    gizmo_id,
                    'chatgpt' as conversation_origin,
                    gizmo_id as chatgpt_gizmo_id,
                    thread_id as openai_thread_id
                FROM conversations_backup_old 
                WHERE conversation_id IS NOT NULL
            """)
            migrated_conversations = cursor.rowcount
            print(f"  ✅ Migradas {migrated_conversations} conversaciones")
        except mysql.connector.Error as e:
            print(f"  ⚠️ Error migrando conversations: {e}")
        
        # Migrar messages
        try:
            cursor.execute("""
                INSERT INTO messages (
                    id, conversation_id, parent_message_id, content_type,
                    content_text, author_role, author_name, create_time,
                    created_at, status, end_turn, weight, channel, recipient
                )
                SELECT 
                    id,
                    conversation_id,
                    parent as parent_message_id,
                    'text' as content_type,
                    content as content_text,
                    role as author_role,
                    author_name,
                    UNIX_TIMESTAMP(create_time) as create_time,
                    NOW() as created_at,
                    COALESCE(status, 'finished_successfully') as status,
                    1 as end_turn,
                    COALESCE(weight, 1.0) as weight,
                    NULL as channel,
                    'all' as recipient
                FROM messages_backup_old 
                WHERE id IS NOT NULL AND conversation_id IS NOT NULL
            """)
            migrated_messages = cursor.rowcount
            print(f"  ✅ Migrados {migrated_messages} mensajes")
        except mysql.connector.Error as e:
            print(f"  ⚠️ Error migrando messages: {e}")
        
        # 8. ESTADÍSTICAS FINALES
        print(f"\n📊 Estadísticas finales:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE chatgpt_project_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {total_projects:,}")
        print(f"  💬 Conversaciones: {total_conversations:,}")
        print(f"  💌 Mensajes: {total_messages:,}")
        print(f"  🎯 Proyectos con ChatGPT ID: {projects_with_gizmo}")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Estructura correcta aplicada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_correct_structure()