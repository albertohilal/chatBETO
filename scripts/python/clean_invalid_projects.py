#!/usr/bin/env python3
# Limpiar proyectos incorrectos y mantener solo los 66 válidos

import mysql.connector
import json
import os

def clean_invalid_projects():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🧹 Limpiando proyectos incorrectos en {config['database']}")
        
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
        print(f"\n📊 Estado actual de la base de datos:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE id <= 66")
        valid_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE id > 66")
        invalid_projects = cursor.fetchone()[0]
        
        print(f"  📁 Total proyectos: {total_projects}")
        print(f"  ✅ Proyectos válidos (ID 1-66): {valid_projects}")
        print(f"  ❌ Proyectos inválidos (ID > 66): {invalid_projects}")
        
        # Mostrar algunos proyectos inválidos
        if invalid_projects > 0:
            print(f"\n🔍 Proyectos inválidos detectados:")
            cursor.execute("""
                SELECT id, name, chatgpt_project_id 
                FROM projects 
                WHERE id > 66 
                ORDER BY id 
                LIMIT 10
            """)
            invalid_list = cursor.fetchall()
            
            for project_id, name, gizmo_id in invalid_list:
                print(f"  ❌ ID {project_id}: {name} | {gizmo_id or 'Sin gizmo_id'}")
            
            if invalid_projects > 10:
                print(f"  ... y {invalid_projects - 10} más")
        
        # 2. ELIMINAR conversaciones vinculadas a proyectos inválidos
        print(f"\n🗑️ Eliminando conversaciones de proyectos inválidos...")
        
        cursor.execute("""
            SELECT COUNT(*) FROM conversations 
            WHERE project_id > 66
        """)
        invalid_conversations = cursor.fetchone()[0]
        
        if invalid_conversations > 0:
            # Primero eliminar mensajes de esas conversaciones
            cursor.execute("""
                DELETE m FROM messages m
                INNER JOIN conversations c ON m.conversation_id = c.id
                WHERE c.project_id > 66
            """)
            deleted_messages = cursor.rowcount
            
            # Luego eliminar las conversaciones
            cursor.execute("DELETE FROM conversations WHERE project_id > 66")
            deleted_conversations = cursor.rowcount
            
            print(f"  🗑️ {deleted_messages:,} mensajes eliminados")
            print(f"  🗑️ {deleted_conversations:,} conversaciones eliminadas")
        else:
            print(f"  ℹ️ No hay conversaciones vinculadas a proyectos inválidos")
        
        # 3. ELIMINAR proyectos inválidos (ID > 66)
        print(f"\n🗑️ Eliminando proyectos inválidos...")
        
        cursor.execute("DELETE FROM projects WHERE id > 66")
        deleted_projects = cursor.rowcount
        
        print(f"  🗑️ {deleted_projects} proyectos inválidos eliminados")
        
        # 4. RESETEAR AUTO_INCREMENT a 67 para evitar futuros conflictos
        cursor.execute("ALTER TABLE projects AUTO_INCREMENT = 67")
        print(f"  🔧 AUTO_INCREMENT configurado a 67")
        
        # 5. VERIFICAR los 66 proyectos válidos
        print(f"\n✅ Verificando proyectos válidos restantes...")
        
        cursor.execute("""
            SELECT id, name, chatgpt_project_id, is_starred
            FROM projects 
            WHERE id <= 66
            ORDER BY id
        """)
        
        valid_projects_list = cursor.fetchall()
        
        print(f"  📁 {len(valid_projects_list)} proyectos válidos confirmados (ID 1-66)")
        
        # Mostrar algunos ejemplos
        print(f"\n📋 Primeros 10 proyectos válidos:")
        for i, (project_id, name, gizmo_id, is_starred) in enumerate(valid_projects_list[:10]):
            star = "⭐" if is_starred else "  "
            gizmo_display = gizmo_id[:15] + "..." if gizmo_id and len(gizmo_id) > 15 else gizmo_id or "Sin gizmo_id"
            print(f"  {project_id:2d}. {star} {name[:25]:<25} | {gizmo_display}")
        
        if len(valid_projects_list) > 10:
            print(f"  ... y {len(valid_projects_list) - 10} más")
        
        # Proyectos favoritos (con estrella)
        starred_projects = [p for p in valid_projects_list if p[3]]
        if starred_projects:
            print(f"\n⭐ Proyectos favoritos ({len(starred_projects)}):")
            for project_id, name, gizmo_id, _ in starred_projects:
                print(f"    {project_id:2d}. {name}")
        
        # 6. ESTADÍSTICAS FINALES
        print(f"\n📊 Estado final de la base de datos:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        final_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        final_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE chatgpt_project_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"  📁 Proyectos: {final_projects} (debe ser 66 o menos)")
        print(f"  💬 Conversaciones: {final_conversations:,}")
        print(f"  💌 Mensajes: {final_messages:,}")
        print(f"  🎯 Proyectos con ChatGPT ID: {projects_with_gizmo}")
        
        # Verificar integridad
        if final_projects <= 66:
            print(f"\n✅ ¡Base de datos limpia! Solo proyectos válidos (ID 1-{final_projects})")
        else:
            print(f"\n⚠️ Advertencia: Aún hay {final_projects} proyectos, debería ser máximo 66")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clean_invalid_projects()