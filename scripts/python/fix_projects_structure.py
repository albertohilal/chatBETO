#!/usr/bin/env python3
# Actualizar estructura de la tabla projects según lo mostrado en phpMyAdmin

import mysql.connector
import json
import os

def fix_projects_structure():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🔧 Actualizando estructura de tabla 'projects' en {config['database']}")
        
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
        
        # Verificar estructura actual
        print("\n📋 Estructura actual de 'projects':")
        cursor.execute("DESCRIBE projects")
        current_structure = cursor.fetchall()
        
        for col in current_structure:
            print(f"  {col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]}")
        
        # Verificar qué campos necesitamos agregar/modificar
        existing_columns = [col[0] for col in current_structure]
        
        # Campos requeridos según phpMyAdmin
        required_fields = [
            ('gizmo_id', 'VARCHAR(100)', 'Gizmo ID del proyecto ChatGPT'),
            ('is_favorite', 'BOOLEAN DEFAULT FALSE', 'Proyecto marcado como favorito'),
            ('conversation_count', 'INT DEFAULT 0', 'Número de conversaciones'),
            ('message_count', 'INT DEFAULT 0', 'Número total de mensajes'),
            ('last_activity', 'DATETIME', 'Última actividad del proyecto'),
            ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', 'Fecha de actualización')
        ]
        
        print(f"\n🔧 Aplicando actualizaciones necesarias...")
        
        for field_name, field_type, description in required_fields:
            if field_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE projects ADD COLUMN {field_name} {field_type}"
                    cursor.execute(sql)
                    print(f"  ✅ Agregado: {field_name} ({description})")
                except mysql.connector.Error as e:
                    print(f"  ⚠️ Error agregando {field_name}: {e}")
        
        # Renombrar chatgpt_project_id a gizmo_id si existe
        if 'chatgpt_project_id' in existing_columns and 'gizmo_id' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE projects CHANGE chatgpt_project_id gizmo_id VARCHAR(100)")
                print(f"  🔄 Renombrado: chatgpt_project_id -> gizmo_id")
            except mysql.connector.Error as e:
                print(f"  ⚠️ Error renombrando chatgpt_project_id: {e}")
        
        # Agregar índices importantes
        print(f"\n📇 Creando índices...")
        
        indexes = [
            ('idx_gizmo_id', 'gizmo_id'),
            ('idx_name', 'name'),
            ('idx_is_favorite', 'is_favorite'),
            ('idx_last_activity', 'last_activity'),
            ('idx_created_at', 'created_at')
        ]
        
        for index_name, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX {index_name} ON projects ({column})")
                print(f"  ✅ Índice creado: {index_name}")
            except mysql.connector.Error as e:
                if "Duplicate key name" in str(e):
                    print(f"  ℹ️ Índice ya existe: {index_name}")
                else:
                    print(f"  ⚠️ Error creando índice {index_name}: {e}")
        
        # Verificar estructura final
        print(f"\n📋 Estructura final de 'projects':")
        cursor.execute("DESCRIBE projects")
        final_structure = cursor.fetchall()
        
        for col in final_structure:
            print(f"  {col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE gizmo_id IS NOT NULL AND gizmo_id != ''")
        projects_with_gizmo = cursor.fetchone()[0]
        
        print(f"\n📊 Estado actual:")
        print(f"  📁 Total proyectos: {project_count}")
        print(f"  🎯 Proyectos con gizmo_id: {projects_with_gizmo}")
        
        # Mostrar algunos ejemplos
        print(f"\n💼 Primeros 10 proyectos:")
        cursor.execute("SELECT id, name, gizmo_id, is_favorite FROM projects ORDER BY id LIMIT 10")
        sample_projects = cursor.fetchall()
        
        for project in sample_projects:
            star = "⭐" if project[3] else "  "
            gizmo = project[2] if project[2] else "Sin gizmo_id"
            print(f"  {project[0]:2d}. {star} {project[1][:30]:<30} | {gizmo}")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Estructura de 'projects' actualizada correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_projects_structure()