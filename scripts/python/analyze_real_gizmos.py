#!/usr/bin/env python3
# Analizar los gizmo_ids reales y sus nombres en OpenAI

import json
import os
from collections import defaultdict, Counter

def analyze_real_gizmo_projects():
    try:
        # Cargar conversations.json
        conversations_file = os.path.join(os.path.dirname(__file__), 'extracted', 'conversations.json')
        print(f"📋 Analizando {conversations_file}...")
        
        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        
        print(f"✅ Cargadas {len(conversations_data)} conversaciones")
        
        # Agrupar por gizmo_id
        gizmo_projects = defaultdict(list)
        
        for conv in conversations_data:
            gizmo_id = conv.get('gizmo_id')
            if gizmo_id:
                gizmo_projects[gizmo_id].append({
                    'id': conv.get('id', ''),
                    'title': conv.get('title', ''),
                    'create_time': conv.get('create_time', ''),
                    'update_time': conv.get('update_time', '')
                })
        
        print(f"\n🎯 Encontrados {len(gizmo_projects)} gizmo_ids únicos:")
        
        # Mostrar cada gizmo_id con sus conversaciones
        for i, (gizmo_id, conversations) in enumerate(sorted(gizmo_projects.items()), 1):
            print(f"\n{i:2d}. gizmo_id: {gizmo_id}")
            print(f"    📊 {len(conversations)} conversaciones")
            
            # Mostrar títulos más frecuentes para identificar el proyecto
            titles = [conv['title'] for conv in conversations if conv['title']]
            
            # Analizar palabras clave en los títulos
            all_words = []
            for title in titles:
                words = title.lower().split()
                all_words.extend(words)
            
            common_words = Counter(all_words).most_common(5)
            print(f"    🔤 Palabras frecuentes: {[w[0] for w in common_words]}")
            
            # Mostrar primeras 3 conversaciones como ejemplo
            print(f"    💬 Ejemplos de conversaciones:")
            for j, conv in enumerate(conversations[:3], 1):
                title = conv['title'][:60] + "..." if len(conv['title']) > 60 else conv['title']
                print(f"      {j}. {title}")
            
            if len(conversations) > 3:
                print(f"      ... y {len(conversations) - 3} más")
        
        print(f"\n" + "="*80)
        print(f"RESUMEN:")
        print(f"- Total gizmo_ids únicos: {len(gizmo_projects)}")
        print(f"- Total conversaciones con gizmo_id: {sum(len(convs) for convs in gizmo_projects.values())}")
        
        # Mostrar conversaciones sin gizmo_id
        no_gizmo = [conv for conv in conversations_data if not conv.get('gizmo_id')]
        print(f"- Conversaciones sin gizmo_id: {len(no_gizmo)}")
        
        return gizmo_projects
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    analyze_real_gizmo_projects()