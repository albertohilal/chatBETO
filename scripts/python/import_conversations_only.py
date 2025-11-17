#!/usr/bin/env python3
# Importar conversaciones desde conversations.json a la base remota

import mysql.connector
import json
import os
import uuid
from datetime import datetime
from collections import defaultdict

def import_conversations_from_json():
    try:
        # Leer credenciales
        config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Cargar conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"📋 Cargando conversaciones desde {conversations_file}...")
        
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        print(f"✅ Cargadas {len(conversations_data)} conversaciones del JSON")
        
        # Conectar a base remota
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4',
            autocommit=False  # Usar transacciones para mejor rendimiento
        )
        
        cursor = connection.cursor()
        
        # 1. OBTENER mapeo de gizmo_ids a project_ids
        print(f"\n🎯 Obteniendo mapeo de gizmo_ids a proyectos...")
        
        cursor.execute("SELECT id, name, chatgpt_project_id FROM projects WHERE chatgpt_project_id IS NOT NULL")
        projects_with_gizmo = cursor.fetchall()
        
        gizmo_to_project = {}
        project_names = {}
        
        for project_id, name, gizmo_id in projects_with_gizmo:
            gizmo_to_project[gizmo_id] = project_id
            project_names[project_id] = name
        
        print(f"  📊 {len(gizmo_to_project)} proyectos con gizmo_id mapeados")
        
        # Mostrar algunos mapeos
        print(f"  🔗 Primeros 5 mapeos:")
        for i, (gizmo_id, project_id) in enumerate(list(gizmo_to_project.items())[:5]):
            project_name = project_names[project_id]
            print(f"    {i+1}. {gizmo_id[:20]}... -> Proyecto {project_id} ({project_name})")
        
        # 2. ANALIZAR conversaciones por gizmo_id
        print(f"\n📈 Analizando distribución de conversaciones...")
        
        gizmo_stats = defaultdict(int)
        no_gizmo_count = 0
        
        for conv in conversations_data:
            gizmo_id = conv.get('gizmo_id')
            if gizmo_id:
                gizmo_stats[gizmo_id] += 1
            else:
                no_gizmo_count += 1
        
        print(f"  🎯 Conversaciones con gizmo_id: {len(conversations_data) - no_gizmo_count:,}")
        print(f"  ❓ Conversaciones sin gizmo_id: {no_gizmo_count:,}")
        print(f"  📊 Gizmo_ids únicos: {len(gizmo_stats)}")
        
        # Top 10 gizmos por cantidad de conversaciones
        top_gizmos = sorted(gizmo_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"\n🏆 Top 10 gizmo_ids por conversaciones:")
        for i, (gizmo_id, count) in enumerate(top_gizmos, 1):
            project_id = gizmo_to_project.get(gizmo_id, 'Sin proyecto')
            project_name = project_names.get(project_id, 'Desconocido') if isinstance(project_id, int) else 'Sin mapear'
            print(f"    {i:2d}. {gizmo_id[:25]:<25} | {count:4d} conv | {project_name}")
        
        # 3. CREAR proyecto por defecto para conversaciones sin gizmo_id
        default_project_id = None
        if no_gizmo_count > 0:
            print(f"\n📁 Creando proyecto por defecto para conversaciones sin gizmo_id...")
            
            cursor.execute("""
                INSERT INTO projects (name, description, is_starred, created_at)
                VALUES (%s, %s, %s, NOW())
            """, ('Conversaciones Generales', 'Conversaciones sin proyecto específico asignado', 0))
            
            default_project_id = cursor.lastrowid
            print(f"  ✨ Proyecto por defecto creado: ID {default_project_id}")
        
        # 4. IMPORTAR conversaciones
        print(f"\n💬 Importando conversaciones...")
        
        imported_count = 0
        skipped_count = 0
        batch_size = 100
        batch_data = []
        
        for i, conv in enumerate(conversations_data):
            try:
                # Generar ID único
                conv_id = conv.get('id') or str(uuid.uuid4())
                
                # Determinar project_id
                gizmo_id = conv.get('gizmo_id')
                project_id = None
                
                if gizmo_id and gizmo_id in gizmo_to_project:
                    project_id = gizmo_to_project[gizmo_id]
                else:
                    project_id = default_project_id
                
                # Preparar datos de la conversación
                title = (conv.get('title') or 'Sin título')[:500]
                conversation_id = conv.get('conversation_id') or conv_id
                create_time = conv.get('create_time', 0)
                update_time = conv.get('update_time', 0)
                
                # Datos adicionales
                is_archived = 1 if conv.get('is_archived', False) else 0
                default_model = conv.get('default_model_slug', 'gpt-4')
                
                # Agregar al batch
                batch_data.append((
                    conv_id, project_id, title, conversation_id,
                    create_time, update_time,
                    is_archived, 0, default_model,  # is_starred = 0 por defecto
                    gizmo_id, 'chatgpt', gizmo_id, None  # conversation_origin, chatgpt_gizmo_id, openai_thread_id
                ))
                
                # Ejecutar batch cuando esté lleno
                if len(batch_data) >= batch_size:
                    cursor.executemany("""
                        INSERT INTO conversations (
                            id, project_id, title, conversation_id,
                            create_time, update_time, created_at,
                            is_archived, is_starred, default_model_slug,
                            gizmo_id, conversation_origin, chatgpt_gizmo_id, openai_thread_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
                    """, batch_data)
                    
                    imported_count += len(batch_data)
                    batch_data = []
                    
                    # Commit periódico para evitar locks largos
                    if imported_count % 1000 == 0:
                        connection.commit()
                        print(f"    💬 {imported_count:,} conversaciones importadas...")
                
            except Exception as e:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"    ⚠️ Error en conversación {i+1}: {e}")
        
        # Ejecutar batch final
        if batch_data:
            cursor.executemany("""
                INSERT INTO conversations (
                    id, project_id, title, conversation_id,
                    create_time, update_time, created_at,
                    is_archived, is_starred, default_model_slug,
                    gizmo_id, conversation_origin, chatgpt_gizmo_id, openai_thread_id
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
            """, batch_data)
            imported_count += len(batch_data)
        
        # Commit final
        connection.commit()
        
        print(f"\n✅ Importación de conversaciones completada:")
        print(f"  💬 Conversaciones importadas: {imported_count:,}")
        print(f"  ⚠️ Conversaciones omitidas: {skipped_count:,}")
        
        # 5. ACTUALIZAR contadores en proyectos
        print(f"\n🔄 Actualizando contadores de proyectos...")
        
        cursor.execute("""
            UPDATE projects p 
            SET conversation_count = (
                SELECT COUNT(*) FROM conversations c 
                WHERE c.project_id = p.id
            )
        """)
        
        affected_projects = cursor.rowcount
        connection.commit()
        
        print(f"  ✅ {affected_projects} proyectos actualizados")
        
        # 6. ESTADÍSTICAS FINALES
        print(f"\n📊 Estadísticas finales:")
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT project_id) FROM conversations WHERE project_id IS NOT NULL")
        projects_with_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE gizmo_id IS NOT NULL")
        conversations_with_gizmo = cursor.fetchone()[0]
        
        print(f"  💬 Total conversaciones en BD: {total_conversations:,}")
        print(f"  📁 Proyectos con conversaciones: {projects_with_conversations}")
        print(f"  🎯 Conversaciones con gizmo_id: {conversations_with_gizmo:,}")
        
        # Top proyectos por conversaciones
        cursor.execute("""
            SELECT p.name, COUNT(c.id) as conv_count, p.is_starred
            FROM projects p
            LEFT JOIN conversations c ON c.project_id = p.id
            GROUP BY p.id, p.name, p.is_starred
            HAVING conv_count > 0
            ORDER BY conv_count DESC
            LIMIT 10
        """)
        
        top_projects = cursor.fetchall()
        print(f"\n🏆 Top 10 proyectos por conversaciones:")
        for i, (name, conv_count, is_starred) in enumerate(top_projects, 1):
            star = "⭐" if is_starred else "  "
            print(f"  {i:2d}. {star} {name[:35]:<35} | {conv_count:4,d} conversaciones")
        
        cursor.close()
        connection.close()
        
        print(f"\n✅ ¡Conversaciones importadas exitosamente!")
        print(f"\n🔜 Siguiente paso: Importar mensajes con script separado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import_conversations_from_json()