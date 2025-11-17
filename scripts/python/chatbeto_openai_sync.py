#!/usr/bin/env python3
"""
Integración ChatBETO con API de OpenAI usando Project IDs reales
Permite sincronizar conversaciones y mantener memoria externa por proyecto
"""

import mysql.connector
import json
import os
from openai import OpenAI
from datetime import datetime
import time

class ChatBETOSync:
    def __init__(self, config_file='db_config.json', openai_key=None):
        self.config_file = config_file
        self.connection = None
        self.openai_client = None
        
        # Cargar configuración
        self.load_db_config()
        self.setup_openai_client(openai_key)
    
    def load_db_config(self):
        """Cargar configuración de base de datos"""
        try:
            with open(self.config_file, 'r') as f:
                self.db_config = json.load(f)
        except FileNotFoundError:
            print(f"❌ No se encontró {self.config_file}")
            return False
        return True
    
    def setup_openai_client(self, api_key=None):
        """Configurar cliente de OpenAI"""
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  OPENAI_API_KEY no encontrada. Funcionalidad limitada.")
            print("   Configura: export OPENAI_API_KEY='tu_clave_aqui'")
            return False
        
        try:
            self.openai_client = OpenAI(api_key=api_key)
            print("✅ Cliente OpenAI configurado")
            return True
        except Exception as e:
            print(f"❌ Error configurando OpenAI: {e}")
            return False
    
    def connect_to_db(self):
        """Conectar a la base de datos"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"❌ Error conectando a DB: {e}")
            return False
    
    def get_projects_with_chatgpt_ids(self):
        """Obtener proyectos que tienen ChatGPT Project IDs"""
        if not self.connect_to_db():
            return []
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, COUNT(c.id) as conversation_count
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id
            WHERE p.chatgpt_project_id IS NOT NULL
            GROUP BY p.id
            ORDER BY conversation_count DESC
        """)
        
        projects = cursor.fetchall()
        cursor.close()
        return projects
    
    def get_conversation_messages(self, conversation_id):
        """Obtener mensajes de una conversación específica"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM messages 
            WHERE conversation_id = %s 
            ORDER BY create_time ASC, created_at ASC
        """, (conversation_id,))
        
        messages = cursor.fetchall()
        cursor.close()
        return messages
    
    def create_openai_thread(self, project_id, conversation_title=""):
        """Crear un thread en OpenAI para un proyecto específico"""
        if not self.openai_client:
            print("❌ Cliente OpenAI no disponible")
            return None
        
        try:
            # Crear thread con metadata del proyecto
            thread = self.openai_client.beta.threads.create(
                metadata={
                    "chatbeto_project_id": project_id,
                    "conversation_title": conversation_title[:100],  # Limitar longitud
                    "created_by": "chatBETO_sync",
                    "sync_timestamp": str(datetime.now())
                }
            )
            
            return thread.id
        except Exception as e:
            print(f"❌ Error creando thread: {e}")
            return None
    
    def sync_conversation_to_openai(self, conversation_id, project_chatgpt_id, dry_run=True):
        """
        Sincronizar una conversación específica con OpenAI
        
        Args:
            conversation_id: ID de la conversación en nuestra DB
            project_chatgpt_id: Project ID de ChatGPT
            dry_run: Si es True, solo muestra lo que haría sin ejecutar
        """
        print(f"\n🔄 {'[DRY RUN] ' if dry_run else ''}Sincronizando conversación {conversation_id}")
        
        if not self.connect_to_db():
            return False
        
        # Obtener datos de la conversación
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
        conversation = cursor.fetchone()
        
        if not conversation:
            print(f"❌ Conversación {conversation_id} no encontrada")
            return False
        
        # Verificar si ya tiene thread_id
        if conversation.get('openai_thread_id'):
            print(f"✅ Conversación ya sincronizada (Thread: {conversation['openai_thread_id']})")
            return True
        
        # Obtener mensajes
        messages = self.get_conversation_messages(conversation_id)
        print(f"📝 {len(messages)} mensajes encontrados")
        
        if dry_run:
            print(f"   [DRY RUN] Crearía thread para proyecto {project_chatgpt_id}")
            print(f"   [DRY RUN] Enviaría {len(messages)} mensajes")
            for i, msg in enumerate(messages[:3]):  # Mostrar solo los primeros 3
                preview = msg['content_text'][:50] if msg['content_text'] else ''
                print(f"   [DRY RUN] Mensaje {i+1}: [{msg['author_role']}] {preview}...")
            if len(messages) > 3:
                print(f"   [DRY RUN] ... y {len(messages) - 3} mensajes más")
            return True
        
        # Crear thread en OpenAI
        thread_id = self.create_openai_thread(
            project_chatgpt_id, 
            conversation.get('title', '')
        )
        
        if not thread_id:
            return False
        
        print(f"✅ Thread creado: {thread_id}")
        
        # Enviar mensajes al thread
        messages_sent = 0
        for message in messages:
            try:
                # Convertir rol del mensaje
                role = "user" if message['author_role'] == 'user' else "assistant"
                content = message['content_text'] or ''
                
                if content.strip():  # Solo enviar mensajes con contenido
                    self.openai_client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role=role,
                        content=content[:32000]  # Limitar longitud para API
                    )
                    messages_sent += 1
            
            except Exception as e:
                print(f"⚠️  Error enviando mensaje: {e}")
        
        print(f"✅ {messages_sent}/{len(messages)} mensajes enviados")
        
        # Actualizar conversation con thread_id
        cursor.execute(
            "UPDATE conversations SET openai_thread_id = %s WHERE id = %s",
            (thread_id, conversation_id)
        )
        self.connection.commit()
        
        cursor.close()
        return True
    
    def sync_project_conversations(self, project_name, limit=None, dry_run=True):
        """Sincronizar todas las conversaciones de un proyecto"""
        if not self.connect_to_db():
            return False
        
        cursor = self.connection.cursor(dictionary=True)
        
        # Obtener proyecto y sus conversaciones
        cursor.execute("""
            SELECT p.*, c.id as conversation_id, c.title, c.openai_thread_id
            FROM projects p
            JOIN conversations c ON p.id = c.project_id
            WHERE p.name = %s AND p.chatgpt_project_id IS NOT NULL
            ORDER BY c.create_time DESC
            {} 
        """.format(f"LIMIT {limit}" if limit else ""), (project_name,))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"❌ No se encontraron conversaciones para el proyecto '{project_name}'")
            return False
        
        project = results[0]
        project_chatgpt_id = project['chatgpt_project_id']
        
        print(f"\n🎯 {'[DRY RUN] ' if dry_run else ''}Sincronizando proyecto: {project_name}")
        print(f"   ChatGPT Project ID: {project_chatgpt_id}")
        print(f"   Conversaciones a sincronizar: {len(results)}")
        
        success_count = 0
        for result in results:
            if self.sync_conversation_to_openai(
                result['conversation_id'], 
                project_chatgpt_id, 
                dry_run=dry_run
            ):
                success_count += 1
            
            if not dry_run:
                time.sleep(1)  # Pausa para evitar rate limits
        
        print(f"\n✅ {success_count}/{len(results)} conversaciones sincronizadas")
        cursor.close()
        return True
    
    def query_openai_thread(self, conversation_id, user_message):
        """Enviar un mensaje a un thread existente y obtener respuesta"""
        if not self.openai_client:
            print("❌ Cliente OpenAI no disponible")
            return None
        
        if not self.connect_to_db():
            return None
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT openai_thread_id FROM conversations WHERE id = %s", 
            (conversation_id,)
        )
        
        result = cursor.fetchone()
        if not result or not result['openai_thread_id']:
            print(f"❌ Conversación {conversation_id} no tiene thread asociado")
            return None
        
        thread_id = result['openai_thread_id']
        
        try:
            # Enviar mensaje del usuario
            self.openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            
            # Crear run (esto activa el asistente)
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id="asst_default"  # Usar asistente por defecto o crear uno específico
            )
            
            # Esperar respuesta
            while run.status in ['queued', 'in_progress']:
                time.sleep(2)
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Obtener mensajes del thread
                messages = self.openai_client.beta.threads.messages.list(thread_id=thread_id)
                
                # Encontrar la última respuesta del asistente
                for message in messages.data:
                    if message.role == "assistant":
                        response_content = message.content[0].text.value
                        
                        # Guardar respuesta en la base de datos
                        cursor.execute("""
                            INSERT INTO messages 
                            (id, conversation_id, content_text, author_role, created_at)
                            VALUES (UUID(), %s, %s, 'assistant', NOW())
                        """, (conversation_id, response_content))
                        
                        self.connection.commit()
                        cursor.close()
                        
                        return response_content
            
            else:
                print(f"❌ Run falló con estado: {run.status}")
                
        except Exception as e:
            print(f"❌ Error consultando thread: {e}")
        
        cursor.close()
        return None
    
    def show_project_status(self):
        """Mostrar estado de sincronización de proyectos"""
        projects = self.get_projects_with_chatgpt_ids()
        
        print(f"\n📊 ESTADO DE PROYECTOS CON CHATGPT IDS:")
        print(f"{'Proyecto':<30} {'Conversaciones':<15} {'ChatGPT Project ID':<20}")
        print("-" * 80)
        
        for project in projects[:10]:  # Mostrar top 10
            name = project['name'][:29]
            conv_count = project['conversation_count']
            chatgpt_id = project['chatgpt_project_id'][:20] + "..." if len(project['chatgpt_project_id']) > 20 else project['chatgpt_project_id']
            
            print(f"{name:<30} {conv_count:<15} {chatgpt_id:<20}")
        
        if len(projects) > 10:
            print(f"... y {len(projects) - 10} proyectos más")
    
    def close_connection(self):
        """Cerrar conexión a la base de datos"""
        if self.connection:
            self.connection.close()


def main():
    """Función principal de ejemplo"""
    print("🚀 ChatBETO - Sincronización con OpenAI API")
    
    # Inicializar
    sync = ChatBETOSync()
    
    # Mostrar estado de proyectos
    sync.show_project_status()
    
    # Ejemplo de uso:
    print(f"\n💡 EJEMPLOS DE USO:")
    print(f"# Sincronizar proyecto específico (dry run):")
    print(f"sync.sync_project_conversations('ChatGPT', limit=2, dry_run=True)")
    
    print(f"\n# Sincronizar proyecto real:")
    print(f"sync.sync_project_conversations('ChatGPT', limit=1, dry_run=False)")
    
    print(f"\n# Consultar thread existente:")
    print(f"response = sync.query_openai_thread('conversation_id', '¿Puedes resumir esta conversación?')")
    
    # Ejemplo de sincronización (dry run)
    print(f"\n🧪 Ejecutando ejemplo (dry run)...")
    sync.sync_project_conversations('ChatGPT', limit=1, dry_run=True)
    
    sync.close_connection()

if __name__ == "__main__":
    main()