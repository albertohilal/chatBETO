#!/usr/bin/env python3
"""
Test de sincronización real con OpenAI API
"""

import os
from chatbeto_openai_sync import ChatBETOSync

def test_sincronizacion_real():
    """Probar sincronización real con la API de OpenAI"""
    
    print("🚀 TEST REAL DE SINCRONIZACIÓN ChatBETO ↔ OpenAI")
    
    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Leer de archivo si no está en variable de entorno
        try:
            with open('openai_key.txt', 'r') as f:
                api_key = f.read().strip()
            os.environ['OPENAI_API_KEY'] = api_key
            print("✅ API Key cargada desde archivo")
        except FileNotFoundError:
            print("❌ API Key no encontrada")
            return False
    
    # Inicializar sistema
    sync = ChatBETOSync()
    
    # Mostrar proyectos disponibles
    print("\n📊 PROYECTOS DISPONIBLES PARA SINCRONIZACIÓN:")
    projects = sync.get_projects_with_chatgpt_ids()
    
    for i, project in enumerate(projects[:10], 1):
        print(f"{i:2d}. {project['name']:<30} ({project['conversation_count']} conversaciones)")
        print(f"    ID: {project['chatgpt_project_id'][:40]}...")
    
    # Probar con el proyecto que tenga más conversaciones
    if projects:
        top_project = projects[0]
        project_name = top_project['name']
        
        print(f"\n🎯 PROBANDO CON PROYECTO: {project_name}")
        
        # Dry run primero
        print("\n1️⃣ DRY RUN (simulación):")
        success = sync.sync_project_conversations(project_name, limit=1, dry_run=True)
        
        if success and sync.openai_client:
            print(f"\n2️⃣ SINCRONIZACIÓN REAL:")
            confirm = input(f"¿Sincronizar 1 conversación de '{project_name}' con OpenAI? (y/N): ")
            
            if confirm.lower() == 'y':
                try:
                    success = sync.sync_project_conversations(project_name, limit=1, dry_run=False)
                    if success:
                        print("🎉 ¡SINCRONIZACIÓN EXITOSA!")
                        print("   - Thread creado en OpenAI")
                        print("   - Mensajes enviados")
                        print("   - Base de datos actualizada")
                    else:
                        print("❌ Error en la sincronización")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("ℹ️  Sincronización cancelada por el usuario")
        else:
            print("⚠️  No se puede hacer sincronización real sin API key válida")
    
    # Cerrar conexión
    try:
        sync.close_connection()
    except:
        pass
    
    return True

if __name__ == "__main__":
    test_sincronizacion_real()