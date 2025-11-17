#!/usr/bin/env python3
"""
Mapear todos los gizmo_ids disponibles con proyectos existentes
"""

import mysql.connector
import json
import subprocess
from collections import defaultdict

def mapear_todos_los_gizmos():
    """Mapear todos los gizmo_ids disponibles con proyectos"""
    
    print("🚀 MAPEANDO TODOS LOS GIZMO_IDS DISPONIBLES")
    
    # Conectar a BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Obtener todos los gizmo_ids y sus frecuencias
    print("🔍 Analizando conversations.json...")
    
    try:
        # Obtener gizmo_ids con frecuencias usando jq
        result = subprocess.run([
            'jq', '-r', 
            '.[] | select(.gizmo_id != null) | .gizmo_id', 
            'extracted/conversations.json'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Error al leer conversations.json")
            return False
            
        all_gizmos = result.stdout.strip().split('\n')
        all_gizmos = [g.strip() for g in all_gizmos if g.strip()]
        
        # Contar frecuencias
        gizmo_counts = defaultdict(int)
        for gizmo in all_gizmos:
            gizmo_counts[gizmo] += 1
            
        # Filtrar solo proyectos (g-p-*)
        project_gizmos = {gid: count for gid, count in gizmo_counts.items() 
                         if gid.startswith('g-p-')}
        
        print(f"📊 Gizmo_ids de proyectos encontrados: {len(project_gizmos)}")
        
        # Obtener gizmo_ids ya mapeados
        cursor.execute("SELECT chatgpt_project_id FROM projects WHERE chatgpt_project_id IS NOT NULL")
        existing_gizmos = {row['chatgpt_project_id'] for row in cursor.fetchall()}
        
        print(f"✅ Gizmo_ids ya mapeados: {len(existing_gizmos)}")
        
        # Gizmo_ids disponibles para mapear
        available_gizmos = {gid: count for gid, count in project_gizmos.items() 
                           if gid not in existing_gizmos}
        
        print(f"🎯 Gizmo_ids disponibles para mapear: {len(available_gizmos)}")
        
        # Obtener proyectos sin gizmo_id
        cursor.execute("""
            SELECT id, name 
            FROM projects 
            WHERE chatgpt_project_id IS NULL 
            ORDER BY id
        """)
        
        projects_without_gizmo = cursor.fetchall()
        print(f"📋 Proyectos sin gizmo_id: {len(projects_without_gizmo)}")
        
        if not available_gizmos or not projects_without_gizmo:
            print("ℹ️  No hay mapeos pendientes")
            return True
            
        # Ordenar gizmos por frecuencia (más usados primero)
        sorted_gizmos = sorted(available_gizmos.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n🔄 INICIANDO MAPEO AUTOMÁTICO:")
        print(f"   Gizmos disponibles: {len(sorted_gizmos)}")
        print(f"   Proyectos sin mapear: {len(projects_without_gizmo)}")
        
        mapped_count = 0
        max_mappings = min(len(sorted_gizmos), len(projects_without_gizmo))
        
        for i in range(max_mappings):
            project = projects_without_gizmo[i]
            gizmo_id, conversation_count = sorted_gizmos[i]
            
            try:
                cursor.execute("""
                    UPDATE projects 
                    SET chatgpt_project_id = %s 
                    WHERE id = %s
                """, (gizmo_id, project['id']))
                
                mapped_count += 1
                print(f"   {mapped_count:2d}. {project['name'][:40]:40} → {gizmo_id} ({conversation_count} conv)")
                
            except Exception as e:
                print(f"   ❌ Error mapeando {project['name']}: {e}")
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar resultado final
        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE chatgpt_project_id IS NOT NULL")
        total_mapped = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM projects")
        total_projects = cursor.fetchone()['count']
        
        print(f"\n🎉 MAPEO COMPLETADO:")
        print(f"   ✅ Proyectos mapeados: {mapped_count}")
        print(f"   📊 Total con gizmo_id: {total_mapped}/{total_projects}")
        print(f"   🎯 Porcentaje completado: {(total_mapped/total_projects)*100:.1f}%")
        
        # Mostrar algunos ejemplos de mapeos nuevos
        if mapped_count > 0:
            cursor.execute("""
                SELECT p.name, p.chatgpt_project_id,
                       (SELECT COUNT(*) FROM conversations c WHERE c.chatgpt_gizmo_id = p.chatgpt_project_id) as conv_count
                FROM projects p 
                WHERE p.chatgpt_project_id IS NOT NULL 
                ORDER BY p.id DESC 
                LIMIT 5
            """)
            
            recent_mappings = cursor.fetchall()
            print(f"\n📋 ÚLTIMOS MAPEOS REALIZADOS:")
            for mapping in recent_mappings:
                print(f"   - {mapping['name'][:40]:40} → {mapping['conv_count']} conversaciones")
        
    except Exception as e:
        print(f"❌ Error durante el mapeo: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    mapear_todos_los_gizmos()