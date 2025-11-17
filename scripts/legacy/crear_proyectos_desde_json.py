#!/usr/bin/env python3
"""
Script para crear proyectos correctos basándose en gizmo_id del JSON original
"""

import json
import mysql.connector
from mysql.connector import Error
from collections import Counter
import re

# Lista de proyectos del móvil (los 66 correctos)
PROYECTOS_MOVIL = [
    'VS Code Github', 'ChatBeto', 'Xubuntu', 'Fiverr-Alejandro', 'ChatGPT',
    'Galaxy S7 FE', 'Medios Audiovisuales', 'Profesor Proyectual UNA', 'Contabo',
    'Lenguaje Visual', 'Taller complementario Pintura', 'Experto en Linkedin',
    'Krita', 'Diseño web', 'Bancos', 'Agdiciuna', 'Leonardo.a.i',
    'desarrolloydiseño-api', 'Wordpress', 'salud', 'The Odin Project', 'Linkedin',
    'Fiverr', 'whatsapp-bot-responder', 'whatsapp', 'Photoshop', 'desarrolloydiseño',
    'Dolibarr + Factura Electrónica AFIP', 'Whatsapp-Massive-Sender',
    'Menu Interactivo Elementor', 'Fiverr-Spoken', 'Wix', 'Moodle', 'Windows',
    'Ifastnet', 'wappflow-n8n', 'VGR-Diseño gráfico', 'Tesis', 'VGR-ENARGAS & Metrogas',
    'VGROSAS-SALUD', 'VGR-Dpto Thomas', 'Google', 'Beto Personal',
    'vgrosas-Dpto-Thomas', 'Desarrollo AFIP', 'prospectos dyd', 'GIMP',
    'Haby Supply', 'dolibarr', 'VGR-Cerámica', 'VGR-BcoPcia-xtrabajo',
    'VGR-Vianni', 'gmail', 'Ceramica', 'Agentes IA', 'Facebook', 'Cristina',
    'El Odio del Gorila', 'Mercado Barracas', 'freelancer.com',
    'Actúa como experto en soyfreelancer.com', 'Upwork', 'Experto ChatGPT',
    'MercadoSur', 'chatBeto', 'Freelancer'
]

def extraer_proyectos_del_json():
    """Extraer todos los gizmo_ids y sus conversaciones del JSON"""
    
    print("🔍 1. EXTRAYENDO PROYECTOS DEL JSON...")
    
    with open('extracted/conversations.json', 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    # Agrupar conversaciones por gizmo_id
    gizmo_data = {}
    conversaciones_sin_gizmo = []
    
    for conv in conversations:
        gizmo_id = conv.get('gizmo_id')
        if gizmo_id:
            if gizmo_id not in gizmo_data:
                gizmo_data[gizmo_id] = {
                    'conversations': [],
                    'titles': []
                }
            gizmo_data[gizmo_id]['conversations'].append(conv)
            gizmo_data[gizmo_id]['titles'].append(conv.get('title', ''))
        else:
            conversaciones_sin_gizmo.append(conv)
    
    print(f"   ✅ {len(gizmo_data)} gizmo_ids encontrados")
    print(f"   ✅ {len(conversaciones_sin_gizmo)} conversaciones sin gizmo_id")
    
    return gizmo_data, conversaciones_sin_gizmo

def deducir_nombre_proyecto(gizmo_id, titles, conversations):
    """Intentar deducir el nombre real del proyecto basándose en los títulos"""
    
    # Palabras clave para cada proyecto del móvil
    keywords_map = {
        'VS Code Github': ['vscode', 'github', 'git', 'código', 'repositorio'],
        'ChatBeto': ['chatbeto', 'chat', 'beto'],
        'Xubuntu': ['xubuntu', 'ubuntu', 'linux'],
        'Fiverr-Alejandro': ['alejandro', 'fiverr alejandro'],
        'ChatGPT': ['chatgpt', 'openai', 'gpt'],
        'Galaxy S7 FE': ['galaxy', 's7', 'samsung'],
        'Medios Audiovisuales': ['medios', 'audiovisual', 'video', 'audio'],
        'Profesor Proyectual UNA': ['proyectual', 'una', 'profesor'],
        'Contabo': ['contabo', 'servidor', 'vps'],
        'Lenguaje Visual': ['lenguaje visual', 'visual'],
        'Taller complementario Pintura': ['pintura', 'taller', 'arte'],
        'Experto en Linkedin': ['linkedin experto', 'experto linkedin'],
        'Krita': ['krita', 'digital art'],
        'Diseño web': ['diseño web', 'web design', 'html', 'css'],
        'Bancos': ['banco', 'provincia', 'afip', 'embargo', 'financiero'],
        'Agdiciuna': ['agdic', 'agdiciuna'],
        'Leonardo.a.i': ['leonardo', 'ai art', 'leonardo.ai'],
        'desarrolloydiseño-api': ['desarrolloydiseño api', 'dyd api'],
        'Wordpress': ['wordpress', 'wp'],
        'salud': ['salud', 'medicina', 'médico'],
        'The Odin Project': ['odin project', 'odin'],
        'Linkedin': ['linkedin'],
        'Fiverr': ['fiverr'],
        'whatsapp-bot-responder': ['whatsapp bot', 'bot responder'],
        'whatsapp': ['whatsapp', 'wapp'],
        'Photoshop': ['photoshop', 'ps'],
        'desarrolloydiseño': ['desarrolloydiseño', 'dyd'],
        'Dolibarr + Factura Electrónica AFIP': ['dolibarr', 'factura electrónica'],
        'Whatsapp-Massive-Sender': ['whatsapp massive', 'massive sender'],
        'Menu Interactivo Elementor': ['menu interactivo', 'elementor'],
        'Fiverr-Spoken': ['fiverr spoken', 'spoken'],
        'Wix': ['wix'],
        'Moodle': ['moodle', 'lms'],
        'Windows': ['windows'],
        'Ifastnet': ['ifastnet', 'hosting'],
        'wappflow-n8n': ['wappflow', 'n8n'],
        'VGR-Diseño gráfico': ['vgr diseño', 'diseño gráfico'],
        'Tesis': ['tesis', 'tesina'],
        'VGR-ENARGAS & Metrogas': ['enargas', 'metrogas', 'vgr'],
        'VGROSAS-SALUD': ['vgrosas salud', 'salud vgr'],
        'VGR-Dpto Thomas': ['dpto thomas', 'thomas', 'vgr'],
        'Google': ['google'],
        'Beto Personal': ['beto personal', 'personal'],
        'vgrosas-Dpto-Thomas': ['vgrosas thomas', 'dpto'],
        'Desarrollo AFIP': ['desarrollo afip', 'afip'],
        'prospectos dyd': ['prospectos', 'dyd'],
        'GIMP': ['gimp'],
        'Haby Supply': ['haby supply', 'haby'],
        'dolibarr': ['dolibarr'],
        'VGR-Cerámica': ['cerámica', 'ceramica', 'vgr'],
        'VGR-BcoPcia-xtrabajo': ['banco provincia', 'bcopcia', 'trabajo'],
        'VGR-Vianni': ['vianni', 'vgr'],
        'gmail': ['gmail', 'email'],
        'Ceramica': ['ceramica'],
        'Agentes IA': ['agentes ia', 'ai agents'],
        'Facebook': ['facebook', 'fb'],
        'Cristina': ['cristina'],
        'El Odio del Gorila': ['odio gorila', 'gorila'],
        'Mercado Barracas': ['mercado barracas', 'barracas'],
        'freelancer.com': ['freelancer.com', 'freelancer'],
        'Actúa como experto en soyfreelancer.com': ['soyfreelancer', 'experto'],
        'Upwork': ['upwork'],
        'Experto ChatGPT': ['experto chatgpt', 'chatgpt experto'],
        'MercadoSur': ['mercadosur', 'mercado sur'],
        'chatBeto': ['chatbeto', 'chat beto'],
        'Freelancer': ['freelancer']
    }
    
    # Combinar todos los títulos en un texto
    all_text = ' '.join(titles).lower()
    
    # Buscar coincidencias
    matches = []
    for proyecto, keywords in keywords_map.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in all_text:
                score += all_text.count(keyword.lower())
        
        if score > 0:
            matches.append((proyecto, score))
    
    # Ordenar por puntuación y devolver el mejor match
    if matches:
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]  # Mejor match
    
    # Si no hay match, crear nombre basado en títulos más frecuentes
    words = []
    for title in titles[:5]:  # Primeros 5 títulos
        title_words = re.findall(r'\b[A-Za-z]{3,}\b', title)
        words.extend(title_words)
    
    if words:
        word_count = Counter(words)
        common_words = [w for w, c in word_count.most_common(3)]
        return ' '.join(common_words).title()
    
    return f"Proyecto {gizmo_id[-8:]}"  # Último fragmento del gizmo_id

def crear_proyectos_desde_json():
    """Crear proyectos en la base de datos basándose en el JSON"""
    
    gizmo_data, conversaciones_sin_gizmo = extraer_proyectos_del_json()
    
    print(f"\n🏗️  2. CREANDO PROYECTOS DESDE GIZMO_IDS...")
    
    # Cargar configuración de BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Obtener proyectos existentes
        cursor.execute("SELECT chatgpt_project_id FROM projects WHERE chatgpt_project_id IS NOT NULL")
        existing_gizmos = {row['chatgpt_project_id'] for row in cursor.fetchall()}
        
        nuevos_proyectos = 0
        proyectos_creados = []
        
        # Procesar cada gizmo_id
        for gizmo_id, data in gizmo_data.items():
            if gizmo_id not in existing_gizmos:
                # Deducir nombre del proyecto
                nombre_deducido = deducir_nombre_proyecto(
                    gizmo_id, 
                    data['titles'], 
                    data['conversations']
                )
                
                # Crear proyecto
                cursor.execute("""
                    INSERT INTO projects (name, description, is_starred, chatgpt_project_id) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    nombre_deducido,
                    f'Proyecto con {len(data["conversations"])} conversaciones',
                    0,
                    gizmo_id
                ))
                
                nuevos_proyectos += 1
                proyectos_creados.append({
                    'nombre': nombre_deducido,
                    'gizmo_id': gizmo_id,
                    'conversaciones': len(data['conversations'])
                })
                
                print(f"   ✅ {nuevos_proyectos:2d}. {nombre_deducido} ({len(data['conversations'])} convs)")
        
        # Crear proyecto para conversaciones sin gizmo_id si no existe
        cursor.execute("SELECT id FROM projects WHERE name = 'Conversaciones Generales'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO projects (name, description, is_starred, chatgpt_project_id) 
                VALUES (%s, %s, %s, %s)
            """, (
                'Conversaciones Generales',
                f'Conversaciones sin proyecto específico ({len(conversaciones_sin_gizmo)} conversaciones)',
                0,
                None
            ))
            print(f"   ✅ Conversaciones Generales ({len(conversaciones_sin_gizmo)} convs)")
        
        connection.commit()
        
        print(f"\n✅ PROYECTOS CREADOS: {nuevos_proyectos}")
        
        # Mostrar resumen de proyectos creados
        if proyectos_creados:
            print(f"\n📊 RESUMEN DE PROYECTOS CREADOS:")
            for proyecto in proyectos_creados:
                print(f"   - {proyecto['nombre']} ({proyecto['conversaciones']} convs)")
        
        return proyectos_creados
        
    except Error as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 CREANDO PROYECTOS DESDE JSON (GIZMO_IDS REALES)")
    print("=" * 80)
    
    proyectos_creados = crear_proyectos_desde_json()
    
    print(f"\n✅ Proceso completado.")
    print(f"💡 Próximo paso: Reasignar conversaciones a proyectos correctos")
    print("=" * 80)