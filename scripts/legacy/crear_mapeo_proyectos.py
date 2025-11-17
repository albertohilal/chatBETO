#!/usr/bin/env python3
"""
Script para mapear conversaciones de ChatGPT a proyectos identificados
Utiliza el análisis de similitud previo para asignar conversaciones a proyectos
"""

import json
import re
from difflib import SequenceMatcher
from datetime import datetime

def similarity(a, b):
    """Calcula similitud entre dos strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def load_projects():
    """Carga la lista de proyectos desde el archivo"""
    projects = []
    try:
        with open('proyectos_nombres.txt', 'r', encoding='utf-8') as f:
            for line in f:
                project_name = line.strip()
                if project_name:
                    projects.append(project_name)
    except FileNotFoundError:
        print("Error: No se encontró proyectos_nombres.txt")
        return []
    
    return projects

def load_conversations():
    """Carga las conversaciones del archivo JSON"""
    try:
        with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        return conversations
    except Exception as e:
        print(f"Error cargando conversations.json: {e}")
        return []

def map_conversation_to_project(conversation_title, projects):
    """
    Mapea una conversación a un proyecto basándose en similitud
    Retorna: (project_name, confidence_score, mapping_type)
    """
    title_lower = conversation_title.lower()
    
    # Buscar coincidencias exactas
    for project in projects:
        if project.lower() == title_lower:
            return (project, 1.0, 'exact')
    
    # Buscar coincidencias parciales (proyecto contenido en título)
    partial_matches = []
    for project in projects:
        if project.lower() in title_lower:
            partial_matches.append((project, 0.8, 'partial'))
    
    if partial_matches:
        # Retornar la coincidencia parcial más larga (más específica)
        best_match = max(partial_matches, key=lambda x: len(x[0]))
        return best_match
    
    # Buscar por similitud alta
    best_similarity = 0
    best_project = None
    
    for project in projects:
        score = similarity(project, conversation_title)
        if score > best_similarity:
            best_similarity = score
            best_project = project
    
    # Solo considerar similitudes altas como válidas
    if best_similarity > 0.7:
        return (best_project, best_similarity, 'similar')
    
    return (None, 0.0, 'none')

def create_project_mapping():
    """Crea el mapeo completo de conversaciones a proyectos"""
    
    print("Cargando proyectos...")
    projects = load_projects()
    if not projects:
        return
    
    print(f"Proyectos cargados: {len(projects)}")
    
    print("Cargando conversaciones...")
    conversations = load_conversations()
    if not conversations:
        return
    
    print(f"Conversaciones cargadas: {len(conversations)}")
    
    # Crear mapeo
    mapping_results = {
        'mapped_conversations': [],
        'unmapped_conversations': [],
        'projects_with_conversations': {},
        'statistics': {
            'total_conversations': len(conversations),
            'total_projects': len(projects),
            'mapped_count': 0,
            'unmapped_count': 0,
            'exact_matches': 0,
            'partial_matches': 0,
            'similar_matches': 0
        }
    }
    
    print("\nAnalizando mapeos...")
    
    for i, conv in enumerate(conversations):
        if i % 100 == 0:
            print(f"Procesando conversación {i+1}/{len(conversations)}")
        
        conv_id = conv.get('id')
        title = conv.get('title', '')
        
        if not title or not conv_id:
            continue
        
        # Mapear conversación a proyecto
        project_name, confidence, mapping_type = map_conversation_to_project(title, projects)
        
        conversation_data = {
            'conversation_id': conv_id,
            'title': title,
            'create_time': conv.get('create_time'),
            'update_time': conv.get('update_time'),
            'project_name': project_name,
            'confidence_score': confidence,
            'mapping_type': mapping_type,
            'is_archived': conv.get('is_archived', False),
            'is_starred': conv.get('is_starred', False),
            'default_model_slug': conv.get('default_model_slug'),
            'gizmo_id': conv.get('gizmo_id'),
            'conversation_origin': conv.get('conversation_origin')
        }
        
        if project_name:
            mapping_results['mapped_conversations'].append(conversation_data)
            mapping_results['statistics']['mapped_count'] += 1
            
            # Actualizar estadísticas por tipo de mapeo
            mapping_results['statistics'][f'{mapping_type}_matches'] += 1
            
            # Agregar a proyectos con conversaciones
            if project_name not in mapping_results['projects_with_conversations']:
                mapping_results['projects_with_conversations'][project_name] = []
            mapping_results['projects_with_conversations'][project_name].append({
                'conversation_id': conv_id,
                'title': title,
                'confidence': confidence,
                'mapping_type': mapping_type
            })
        else:
            mapping_results['unmapped_conversations'].append(conversation_data)
            mapping_results['statistics']['unmapped_count'] += 1
    
    # Guardar resultados
    output_file = 'conversation_project_mapping.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Mapeo completado y guardado en {output_file}")
    
    # Mostrar estadísticas
    stats = mapping_results['statistics']
    print("\n" + "="*50)
    print("ESTADÍSTICAS DEL MAPEO")
    print("="*50)
    print(f"Total de conversaciones: {stats['total_conversations']:,}")
    print(f"Total de proyectos: {stats['total_projects']}")
    print(f"Conversaciones mapeadas: {stats['mapped_count']:,} ({stats['mapped_count']/stats['total_conversations']*100:.1f}%)")
    print(f"Conversaciones sin mapear: {stats['unmapped_count']:,} ({stats['unmapped_count']/stats['total_conversations']*100:.1f}%)")
    print()
    print("TIPOS DE COINCIDENCIAS:")
    print(f"  Exactas: {stats['exact_matches']}")
    print(f"  Parciales: {stats['partial_matches']}")
    print(f"  Similares: {stats['similar_matches']}")
    print()
    print("PROYECTOS CON MÁS CONVERSACIONES:")
    project_counts = [(name, len(convs)) for name, convs in mapping_results['projects_with_conversations'].items()]
    project_counts.sort(key=lambda x: x[1], reverse=True)
    
    for project_name, count in project_counts[:10]:
        print(f"  {project_name}: {count} conversaciones")
    
    return mapping_results

def generate_sql_inserts(mapping_results):
    """Genera sentencias SQL para insertar los datos en la base de datos"""
    
    sql_statements = []
    
    # 1. Insertar proyectos
    sql_statements.append("-- Insertar proyectos")
    sql_statements.append("INSERT INTO projects (name, original_name, is_starred, created_at) VALUES")
    
    project_inserts = []
    projects_with_conversations = set(mapping_results['projects_with_conversations'].keys())
    
    # Leer el listado original con fechas y estrellas
    starred_projects = set()
    try:
        with open('Auxiliar/ListadoProyectos.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '⭐' in line:
                    project_name = line.split('(')[0].strip().replace('⭐', '').strip()
                    starred_projects.add(project_name)
    except:
        pass
    
    for project_name in projects_with_conversations:
        is_starred = 'TRUE' if project_name in starred_projects else 'FALSE'
        project_inserts.append(f"('{project_name}', '{project_name}', {is_starred}, NOW())")
    
    sql_statements.append(',\n'.join(project_inserts) + ';')
    sql_statements.append("")
    
    # 2. Insertar conversaciones
    sql_statements.append("-- Insertar conversaciones")
    
    # Primero conversaciones con proyecto
    if mapping_results['mapped_conversations']:
        sql_statements.append("INSERT INTO conversations (id, project_id, title, create_time, update_time, is_archived, is_starred, default_model_slug, gizmo_id, conversation_origin) VALUES")
        
        conv_inserts = []
        for conv in mapping_results['mapped_conversations'][:100]:  # Limitar para ejemplo
            project_id = f"(SELECT id FROM projects WHERE name = '{conv['project_name']}')"
            create_time = conv['create_time'] if conv['create_time'] else 'NULL'
            update_time = conv['update_time'] if conv['update_time'] else 'NULL'
            title_escaped = conv['title'].replace("'", "\\'")
            
            conv_inserts.append(
                f"('{conv['conversation_id']}', {project_id}, '{title_escaped}', "
                f"{create_time}, {update_time}, {conv['is_archived']}, {conv['is_starred']}, "
                f"'{conv['default_model_slug'] or ''}', '{conv['gizmo_id'] or ''}', '{conv['conversation_origin'] or ''}')"
            )
        
        sql_statements.append(',\n'.join(conv_inserts) + ';')
        sql_statements.append("")
    
    # Guardar SQL
    with open('migration_inserts.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    print("✅ Sentencias SQL generadas en migration_inserts.sql")

if __name__ == "__main__":
    print("🚀 Iniciando mapeo de conversaciones a proyectos...")
    
    mapping_results = create_project_mapping()
    
    if mapping_results:
        print("\n📝 Generando sentencias SQL...")
        generate_sql_inserts(mapping_results)
        
        print("\n✅ Proceso completado exitosamente!")
        print(f"📊 Revisa el archivo 'conversation_project_mapping.json' para ver los resultados detallados")
        print(f"📄 Revisa el archivo 'migration_inserts.sql' para las sentencias de inserción")
    else:
        print("❌ Error en el proceso de mapeo")