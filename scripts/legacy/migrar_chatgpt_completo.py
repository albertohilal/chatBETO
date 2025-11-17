#!/usr/bin/env python3
"""
Script completo de migración de datos ChatGPT a MySQL
Importa: Proyectos -> Conversaciones -> Mensajes
"""

import json
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import sys

class ChatGPTMigrator:
    def __init__(self, config_file='db_config.json'):
        self.config_file = config_file
        self.connection = None
        self.mapping_data = None
        
    def load_db_config(self):
        """Carga configuración de base de datos"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ No se encontró {self.config_file}")
            print("Creando archivo de configuración de ejemplo...")
            
            example_config = {
                "host": "localhost",
                "database": "chatbeto",
                "user": "tu_usuario",
                "password": "tu_password",
                "port": 3306,
                "charset": "utf8mb4"
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(example_config, f, indent=2)
            
            print(f"✏️  Edita {self.config_file} con tus credenciales de MySQL")
            return None
    
    def connect_to_db(self):
        """Conecta a la base de datos MySQL"""
        config = self.load_db_config()
        if not config:
            return False
        
        try:
            self.connection = mysql.connector.connect(**config)
            if self.connection.is_connected():
                print("✅ Conexión exitosa a MySQL")
                return True
        except Error as e:
            print(f"❌ Error conectando a MySQL: {e}")
            return False
    
    def create_database_schema(self):
        """Crea el esquema de base de datos"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Leer y ejecutar el schema
            with open('schema_chatbeto.sql', 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Dividir en sentencias individuales
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'ALTER', 'DROP')):
                    try:
                        cursor.execute(statement)
                        print(f"✅ Ejecutado: {statement[:50]}...")
                    except Error as e:
                        if "already exists" in str(e):
                            print(f"⚠️  Ya existe: {statement[:50]}...")
                        else:
                            print(f"❌ Error: {e}")
            
            self.connection.commit()
            print("✅ Esquema de base de datos creado/actualizado")
            return True
            
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            return False
    
    def load_mapping_data(self):
        """Carga los datos de mapeo generados previamente"""
        try:
            with open('conversation_project_mapping.json', 'r', encoding='utf-8') as f:
                self.mapping_data = json.load(f)
            print("✅ Datos de mapeo cargados")
            return True
        except FileNotFoundError:
            print("❌ No se encontró conversation_project_mapping.json")
            print("Ejecuta primero: python3 crear_mapeo_proyectos.py")
            return False
    
    def import_projects(self):
        """Importa los proyectos a la base de datos"""
        if not self.mapping_data:
            return False
        
        cursor = self.connection.cursor()
        
        try:
            # Obtener proyectos únicos
            projects = set()
            for conv in self.mapping_data['mapped_conversations']:
                if conv['project_name']:
                    projects.add(conv['project_name'])
            
            # Leer proyectos destacados
            starred_projects = set()
            try:
                with open('Auxiliar/ListadoProyectos.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if '⭐' in line:
                            project_name = line.split('(')[0].strip().replace('⭐', '').strip()
                            starred_projects.add(project_name)
            except:
                pass
            
            # Insertar proyectos
            insert_project_sql = """
                INSERT IGNORE INTO projects (name, original_name, is_starred, created_at) 
                VALUES (%s, %s, %s, NOW())
            """
            
            project_data = []
            for project_name in projects:
                is_starred = project_name in starred_projects
                project_data.append((project_name, project_name, is_starred))
            
            cursor.executemany(insert_project_sql, project_data)
            self.connection.commit()
            
            print(f"✅ {len(project_data)} proyectos importados")
            return True
            
        except Error as e:
            print(f"❌ Error importando proyectos: {e}")
            return False
    
    def import_conversations(self):
        """Importa las conversaciones a la base de datos"""
        if not self.mapping_data:
            return False
        
        cursor = self.connection.cursor()
        
        try:
            # Insertar conversaciones con proyecto
            insert_conv_sql = """
                INSERT IGNORE INTO conversations 
                (id, project_id, title, conversation_id, create_time, update_time, 
                 is_archived, is_starred, default_model_slug, gizmo_id, conversation_origin)
                VALUES (%s, (SELECT id FROM projects WHERE name = %s), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            mapped_data = []
            for conv in self.mapping_data['mapped_conversations']:
                mapped_data.append((
                    conv['conversation_id'],
                    conv['project_name'],
                    conv['title'][:500],  # Truncar título si es muy largo
                    conv.get('conversation_id'),
                    conv.get('create_time'),
                    conv.get('update_time'),
                    conv.get('is_archived', False),
                    conv.get('is_starred', False),
                    conv.get('default_model_slug', ''),
                    conv.get('gizmo_id', ''),
                    conv.get('conversation_origin', '')
                ))
            
            cursor.executemany(insert_conv_sql, mapped_data)
            
            # Insertar conversaciones sin proyecto
            insert_orphan_sql = """
                INSERT IGNORE INTO conversations 
                (id, project_id, title, conversation_id, create_time, update_time, 
                 is_archived, is_starred, default_model_slug, gizmo_id, conversation_origin)
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            orphan_data = []
            for conv in self.mapping_data['unmapped_conversations']:
                orphan_data.append((
                    conv['conversation_id'],
                    conv['title'][:500],
                    conv.get('conversation_id'),
                    conv.get('create_time'),
                    conv.get('update_time'),
                    conv.get('is_archived', False),
                    conv.get('is_starred', False),
                    conv.get('default_model_slug', ''),
                    conv.get('gizmo_id', ''),
                    conv.get('conversation_origin', '')
                ))
            
            cursor.executemany(insert_orphan_sql, orphan_data)
            
            self.connection.commit()
            
            print(f"✅ {len(mapped_data)} conversaciones con proyecto importadas")
            print(f"✅ {len(orphan_data)} conversaciones huérfanas importadas")
            return True
            
        except Error as e:
            print(f"❌ Error importando conversaciones: {e}")
            return False
    
    def import_messages(self, limit=None):
        """Importa los mensajes de las conversaciones"""
        try:
            with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
                conversations = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando conversations.json: {e}")
            return False
        
        cursor = self.connection.cursor()
        
        insert_message_sql = """
            INSERT IGNORE INTO messages 
            (id, conversation_id, parent_message_id, content_type, content_text, 
             author_role, author_name, create_time, status, end_turn, weight, 
             channel, recipient, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        total_messages = 0
        processed_conversations = 0
        
        for i, conv in enumerate(conversations):
            if limit and i >= limit:
                break
                
            conv_id = conv.get('id')
            if not conv_id:
                continue
                
            mapping = conv.get('mapping', {})
            if not mapping:
                continue
            
            processed_conversations += 1
            
            # Procesar cada mensaje en la conversación
            message_data = []
            
            for msg_id, msg_node in mapping.items():
                if not msg_node or not msg_node.get('message'):
                    continue
                
                message = msg_node['message']
                
                # Extraer contenido del mensaje
                content_parts = message.get('content', {})
                if isinstance(content_parts, dict):
                    parts = content_parts.get('parts', [])
                    if parts and isinstance(parts, list):
                        content_text = str(parts[0]) if parts[0] else ''
                    else:
                        content_text = str(content_parts)
                else:
                    content_text = str(content_parts) if content_parts else ''
                
                # Truncar contenido muy largo
                if len(content_text) > 65000:  # Dejar espacio para el límite de TEXT
                    content_text = content_text[:65000] + "... [TRUNCATED]"
                
                # Datos del autor
                author = message.get('author', {})
                author_role = author.get('role', 'unknown')
                author_name = author.get('name', '')
                
                # Metadata del mensaje
                metadata = {
                    'original_message': {key: value for key, value in message.items() 
                                      if key not in ['content', 'author', 'create_time']}
                }
                
                message_data.append((
                    msg_node.get('id', msg_id),
                    conv_id,
                    msg_node.get('parent'),
                    'text',  # content_type por defecto
                    content_text,
                    author_role,
                    author_name,
                    message.get('create_time'),
                    message.get('status', {}).get('status', 'finished_successfully'),
                    message.get('end_turn', False),
                    message.get('weight', 1.0),
                    message.get('channel'),
                    message.get('recipient', 'all'),
                    json.dumps(metadata, ensure_ascii=False)
                ))
            
            if message_data:
                cursor.executemany(insert_message_sql, message_data)
                total_messages += len(message_data)
            
            if processed_conversations % 50 == 0:
                print(f"Procesadas {processed_conversations} conversaciones, {total_messages} mensajes")
                self.connection.commit()
        
        self.connection.commit()
        
        print(f"✅ {total_messages} mensajes importados de {processed_conversations} conversaciones")
        return True
    
    def run_migration(self, messages_limit=None):
        """Ejecuta la migración completa"""
        print("🚀 Iniciando migración completa de ChatGPT a MySQL...")
        
        # 1. Conectar a base de datos
        if not self.connect_to_db():
            return False
        
        # 2. Crear esquema
        if not self.create_database_schema():
            return False
        
        # 3. Cargar datos de mapeo
        if not self.load_mapping_data():
            return False
        
        # 4. Importar proyectos
        if not self.import_projects():
            return False
        
        # 5. Importar conversaciones
        if not self.import_conversations():
            return False
        
        # 6. Importar mensajes
        print("⚠️  Importando mensajes (puede tomar varios minutos)...")
        if not self.import_messages(messages_limit):
            return False
        
        print("✅ Migración completada exitosamente!")
        
        # Mostrar estadísticas finales
        self.show_final_stats()
        
        return True
    
    def show_final_stats(self):
        """Muestra estadísticas finales de la base de datos"""
        cursor = self.connection.cursor()
        
        try:
            # Contar proyectos
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_count = cursor.fetchone()[0]
            
            # Contar conversaciones
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversations_count = cursor.fetchone()[0]
            
            # Contar mensajes
            cursor.execute("SELECT COUNT(*) FROM messages")
            messages_count = cursor.fetchone()[0]
            
            # Conversaciones por proyecto
            cursor.execute("""
                SELECT COUNT(*) FROM conversations WHERE project_id IS NOT NULL
            """)
            mapped_conversations = cursor.fetchone()[0]
            
            print("\n" + "="*50)
            print("ESTADÍSTICAS FINALES DE LA BASE DE DATOS")
            print("="*50)
            print(f"Proyectos: {projects_count:,}")
            print(f"Conversaciones totales: {conversations_count:,}")
            print(f"  - Con proyecto asignado: {mapped_conversations:,}")
            print(f"  - Sin proyecto: {conversations_count - mapped_conversations:,}")
            print(f"Mensajes: {messages_count:,}")
            
        except Error as e:
            print(f"Error obteniendo estadísticas: {e}")

def main():
    """Función principal"""
    migrator = ChatGPTMigrator()
    
    # Permitir limitar mensajes para pruebas
    messages_limit = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        messages_limit = int(sys.argv[1])
        print(f"⚠️  Limitando a {messages_limit} conversaciones para mensajes")
    
    success = migrator.run_migration(messages_limit)
    
    if success:
        print("\n🎉 ¡Migración exitosa!")
        print("Ahora puedes consultar tus datos con:")
        print("  - SELECT * FROM project_stats;")
        print("  - SELECT * FROM orphan_conversations LIMIT 10;")
        print("  - SELECT * FROM conversations_with_projects LIMIT 10;")
    else:
        print("\n❌ La migración falló")
        sys.exit(1)

if __name__ == "__main__":
    main()