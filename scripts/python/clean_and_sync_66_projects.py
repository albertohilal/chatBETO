#!/usr/bin/env python3
# Limpiar y sincronizar correctamente los 66 proyectos reales

import mysql.connector
import json
import os
import re
from datetime import datetime

def clean_and_sync_projects():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Cargar listado real de 66 proyectos
        projects_file = os.path.join(os.path.dirname(__file__), 'Auxiliar', 'ListadoProyectos.txt')
        print(f"📋 Cargando proyectos reales desde {projects_file}")
        
        real_projects = []
        with open(projects_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line and not line.startswith('TOTAL:') and line:
                # Extraer nombre del proyecto y fecha
                is_favorite = '⭐' in line
                clean_line = line.replace('⭐', '').strip()
                
                # Separar nombre y fecha (entre paréntesis)
                match = re.match(r'^(.+?)\s*\((.+?)\)$', clean_line)
                if match:
                    name = match.group(1).strip()
                    date_str = match.group(2).strip()
                    
                    real_projects.append({
                        'name': name,
                        'date_str': date_str,
                        'is_favorite': is_favorite
                    })
                elif clean_line:  # Línea sin fecha
                    real_projects.append({
                        'name': clean_line,
                        'date_str': 'fecha desconocida',
                        'is_favorite': is_favorite
                    })
        
        print(f"✅ Detectados {len(real_projects)} proyectos reales")
        
        # Conectar a base remota
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
        
        # 1. RESPALDO de proyectos actuales
        print("\n💾 Creando respaldo de proyectos actuales...")
        cursor.execute("CREATE TABLE IF NOT EXISTS projects_backup AS SELECT * FROM projects")
        
        # 2. LIMPIAR tabla projects actual
        print("\n🧹 Limpiando tabla projects...")
        cursor.execute("DELETE FROM projects")
        cursor.execute("ALTER TABLE projects AUTO_INCREMENT = 1")
        
        # 3. INSERTAR los 66 proyectos reales
        print("\n📥 Insertando los 66 proyectos reales...")
        
        for i, project in enumerate(real_projects, 1):
            cursor.execute("""
                INSERT INTO projects (
                    id, name, description, is_favorite, 
                    created_at, updated_at, conversation_count, 
                    message_count, last_activity
                ) VALUES (%s, %s, %s, %s, NOW(), NOW(), 0, 0, NULL)
            """, (
                i,  # ID secuencial 1-66
                project['name'],
                f"Proyecto: {project['name']} ({project['date_str']})",
                project['is_favorite']
            ))
            
            print(f"  {i:2d}. {'⭐' if project['is_favorite'] else '  '} {project['name']}")
        
        # 4. CARGAR conversations.json para mapear gizmo_ids
        print(f"\n🔄 Mapeando conversaciones con gizmo_ids...")
        
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        # Crear mapa de gizmo_id -> project_name
        gizmo_to_conversations = {}
        
        for conv in conversations_data:
            if 'gizmo_id' in conv and conv['gizmo_id']:
                gizmo_id = conv['gizmo_id']
                if gizmo_id not in gizmo_to_conversations:
                    gizmo_to_conversations[gizmo_id] = []
                gizmo_to_conversations[gizmo_id].append({
                    'id': conv.get('id', ''),
                    'title': conv.get('title', '')
                })
        
        print(f"📊 Encontrados {len(gizmo_to_conversations)} gizmo_ids únicos")
        
        # 5. ASIGNAR gizmo_ids a proyectos basado en nombres similares
        print(f"\n🎯 Asignando gizmo_ids a proyectos...")
        
        cursor.execute("SELECT id, name FROM projects ORDER BY id")
        projects_in_db = cursor.fetchall()
        
        gizmo_assignments = 0
        
        for project_id, project_name in projects_in_db:
            project_lower = project_name.lower()
            
            # Buscar gizmo_id que mejor coincida
            best_gizmo = None
            best_score = 0
            
            for gizmo_id, conversations in gizmo_to_conversations.items():
                # Calcular score basado en títulos de conversaciones
                score = 0
                for conv in conversations:
                    title_lower = conv['title'].lower()
                    # Coincidencias exactas
                    if project_lower in title_lower or title_lower in project_lower:
                        score += 10
                    # Coincidencias parciales
                    words = project_lower.split()
                    for word in words:
                        if len(word) > 2 and word in title_lower:
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_gizmo = gizmo_id
            
            # Asignar gizmo_id si encontramos buena coincidencia
            if best_gizmo and best_score > 0:
                cursor.execute("""
                    UPDATE projects 
                    SET gizmo_id = %s 
                    WHERE id = %s
                """, (best_gizmo, project_id))
                
                print(f"  🎯 {project_name} -> {best_gizmo} (score: {best_score})")
                gizmo_assignments += 1
            else:
                print(f"  ❓ {project_name} -> Sin gizmo_id")
        
        # 6. ACTUALIZAR conversations con project_id correcto
        print(f"\n🔗 Vinculando conversaciones a proyectos...")
        
        cursor.execute("SELECT id, gizmo_id FROM projects WHERE gizmo_id IS NOT NULL")
        project_gizmos = cursor.fetchall()
        
        conversations_linked = 0
        
        for project_id, gizmo_id in project_gizmos:
            cursor.execute("""
                UPDATE conversations 
                SET project_id = %s, gizmo_id = %s 
                WHERE gizmo_id = %s OR conversation_id IN (
                    SELECT id FROM (
                        SELECT DISTINCT conv.id 
                        FROM conversations conv
                        INNER JOIN messages msg ON msg.conversation_id = conv.conversation_id
                        WHERE msg.content LIKE %s
                    ) temp
                )
            """, (str(project_id), gizmo_id, gizmo_id, f'%{gizmo_id}%'))
            
            linked = cursor.rowcount
            conversations_linked += linked
            
            if linked > 0:
                print(f"    📁 Proyecto {project_id}: {linked} conversaciones vinculadas")
        
        # 7. RECALCULAR contadores
        print(f"\n📊 Recalculando contadores...")
        
        cursor.execute("""
            UPDATE projects p 
            SET 
                conversation_count = (
                    SELECT COUNT(*) FROM conversations c 
                    WHERE c.project_id = p.id
                ),
                message_count = (
                    SELECT COUNT(*) FROM messages m 
                    INNER JOIN conversations c ON m.conversation_id = c.conversation_id
                    WHERE c.project_id = p.id
                ),
                last_activity = (
                    SELECT MAX(c.update_time) FROM conversations c 
                    WHERE c.project_id = p.id
                )
        """)
        
        # 8. ESTADÍSTICAS FINALES
        print(f"\n✅ Sincronización completada:")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE gizmo_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(conversation_count) FROM projects")
        total_conversations = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(message_count) FROM projects")
        total_messages = cursor.fetchone()[0] or 0
        
        print(f"  📁 Total de proyectos: {total_projects}")
        print(f"  🎯 Proyectos con gizmo_id: {projects_with_gizmo}")
        print(f"  💬 Conversaciones vinculadas: {total_conversations}")
        print(f"  💌 Mensajes vinculados: {total_messages}")
        
        # Mostrar top proyectos por actividad
        cursor.execute("""
            SELECT name, conversation_count, message_count, is_favorite
            FROM projects 
            WHERE conversation_count > 0
            ORDER BY message_count DESC 
            LIMIT 10
        """)
        
        top_projects = cursor.fetchall()
        print(f"\n🏆 Top 10 proyectos por actividad:")
        for i, (name, conv_count, msg_count, is_fav) in enumerate(top_projects, 1):
            star = "⭐" if is_fav else "  "
            print(f"  {i:2d}. {star} {name}: {conv_count} conv, {msg_count:,} msgs")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clean_and_sync_projects()