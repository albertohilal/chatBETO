#!/usr/bin/env python3
"""
Script para limpiar completamente la tabla projects y recrear con datos correctos del JSON
"""

import json
import mysql.connector
from mysql.connector import Error
from collections import Counter
import re

def limpiar_tabla_projects():
    """Eliminar todos los proyectos existentes (excepto conversaciones que quedarán temporalmente sin proyecto)"""
    
    print("🧹 1. LIMPIANDO TABLA PROJECTS...")
    
    # Cargar configuración
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Contar proyectos actuales
        cursor.execute("SELECT COUNT(*) as total FROM projects")
        total_antes = cursor.fetchone()['total']
        
        # Contar conversaciones que quedarán huérfanas temporalmente
        cursor.execute("SELECT COUNT(*) as total FROM conversations WHERE project_id IS NOT NULL")
        conversaciones_afectadas = cursor.fetchone()['total']
        
        print(f"   Proyectos actuales: {total_antes}")
        print(f"   Conversaciones que quedarán temporalmente sin proyecto: {conversaciones_afectadas}")
        
        # Poner conversaciones como huérfanas temporalmente
        print("   ➡️  Desasignando conversaciones de proyectos...")
        cursor.execute("UPDATE conversations SET project_id = NULL")
        
        # Eliminar todos los proyectos
        print("   ➡️  Eliminando todos los proyectos...")
        cursor.execute("DELETE FROM projects")
        
        connection.commit()
        print("   ✅ Tabla projects limpiada completamente")
        
        return True
        
    except Error as e:
        print(f"   ❌ Error limpiando tabla: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def extraer_proyectos_del_json():
    """Extraer todos los gizmo_ids y sus conversaciones del JSON"""
    
    print("\n🔍 2. EXTRAYENDO PROYECTOS DEL JSON...")
    
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
    """Deducir el nombre del proyecto basándose en los títulos más comunes"""
    
    # Obtener palabras clave de los títulos
    words = []
    for title in titles[:10]:  # Primeros 10 títulos
        # Extraer palabras significativas (3+ caracteres)
        title_words = re.findall(r'\b[A-Za-zÀ-ÿ]{3,}\b', title)
        words.extend([w.lower() for w in title_words])
    
    if not words:
        return f"Proyecto {gizmo_id[-8:]}"
    
    # Contar frecuencia de palabras
    word_count = Counter(words)
    
    # Palabras a ignorar (muy comunes y poco descriptivas)
    stop_words = {'para', 'con', 'por', 'the', 'and', 'del', 'las', 'los', 'una', 'que', 'como', 'sobre'}
    
    # Obtener las 3 palabras más comunes (excluyendo stop words)
    common_words = []
    for word, count in word_count.most_common(20):
        if word not in stop_words and len(word) > 3:
            common_words.append(word.title())
            if len(common_words) >= 3:
                break
    
    if common_words:
        return ' '.join(common_words)
    else:
        # Si no hay palabras útiles, usar el primer título limpio
        first_title = titles[0] if titles else f"Proyecto {gizmo_id[-8:]}"
        return first_title[:50]  # Limitar longitud

def crear_proyectos_desde_json_limpio():
    """Crear proyectos en la base de datos basándose en el JSON (después de limpiar)"""
    
    gizmo_data, conversaciones_sin_gizmo = extraer_proyectos_del_json()
    
    print(f"\n🏗️  3. CREANDO PROYECTOS DESDE GIZMO_IDS...")
    
    # Cargar configuración de BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        proyectos_creados = []
        
        # Crear proyecto para conversaciones sin gizmo_id primero
        cursor.execute("""
            INSERT INTO projects (name, description, is_starred, chatgpt_project_id) 
            VALUES (%s, %s, %s, %s)
        """, (
            'Conversaciones Generales',
            f'Conversaciones sin proyecto específico asignado',
            0,
            None
        ))
        
        proyecto_general_id = cursor.lastrowid
        print(f"   ✅ 1. Conversaciones Generales ({len(conversaciones_sin_gizmo)} convs)")
        
        # Procesar cada gizmo_id
        contador = 2
        for gizmo_id, data in sorted(gizmo_data.items(), key=lambda x: len(x[1]['conversations']), reverse=True):
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
            
            proyecto_id = cursor.lastrowid
            
            proyectos_creados.append({
                'id': proyecto_id,
                'nombre': nombre_deducido,
                'gizmo_id': gizmo_id,
                'conversaciones': len(data['conversations']),
                'conversation_ids': [c['id'] for c in data['conversations']]
            })
            
            print(f"   ✅ {contador:2d}. {nombre_deducido} ({len(data['conversations'])} convs)")
            contador += 1
        
        connection.commit()
        
        print(f"\n✅ PROYECTOS CREADOS: {len(proyectos_creados) + 1}")
        
        # Guardar mapeo para el siguiente paso
        mapeo_data = {
            'proyecto_general_id': proyecto_general_id,
            'conversaciones_sin_gizmo': [c['id'] for c in conversaciones_sin_gizmo],
            'proyectos_creados': proyectos_creados
        }
        
        with open('mapeo_proyectos.json', 'w', encoding='utf-8') as f:
            json.dump(mapeo_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Mapeo guardado en mapeo_proyectos.json")
        
        return mapeo_data
        
    except Error as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def reasignar_conversaciones_inmediatamente():
    """Reasignar conversaciones a sus proyectos correctos basándose en el mapeo"""
    
    print(f"\n🔄 4. REASIGNANDO CONVERSACIONES A PROYECTOS...")
    
    # Cargar mapeo
    with open('mapeo_proyectos.json', 'r', encoding='utf-8') as f:
        mapeo = json.load(f)
    
    # Cargar configuración de BD
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        total_reasignadas = 0
        
        # Reasignar conversaciones sin gizmo_id al proyecto general
        if mapeo['conversaciones_sin_gizmo']:
            placeholders = ','.join(['%s'] * len(mapeo['conversaciones_sin_gizmo']))
            cursor.execute(f"""
                UPDATE conversations 
                SET project_id = %s 
                WHERE id IN ({placeholders})
            """, [mapeo['proyecto_general_id']] + mapeo['conversaciones_sin_gizmo'])
            
            reasignadas = cursor.rowcount
            total_reasignadas += reasignadas
            print(f"   ✅ {reasignadas} conversaciones → Conversaciones Generales")
        
        # Reasignar conversaciones con gizmo_id a sus proyectos
        for proyecto in mapeo['proyectos_creados']:
            if proyecto['conversation_ids']:
                placeholders = ','.join(['%s'] * len(proyecto['conversation_ids']))
                cursor.execute(f"""
                    UPDATE conversations 
                    SET project_id = %s 
                    WHERE id IN ({placeholders})
                """, [proyecto['id']] + proyecto['conversation_ids'])
                
                reasignadas = cursor.rowcount
                total_reasignadas += reasignadas
                print(f"   ✅ {reasignadas} conversaciones → {proyecto['nombre']}")
        
        connection.commit()
        print(f"\n✅ TOTAL CONVERSACIONES REASIGNADAS: {total_reasignadas}")
        
        return True
        
    except Error as e:
        print(f"❌ Error reasignando conversaciones: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 LIMPIEZA COMPLETA Y RECREACIÓN DE PROYECTOS")
    print("=" * 80)
    
    # Paso 1: Limpiar tabla
    if not limpiar_tabla_projects():
        print("❌ Error en limpieza. Abortando.")
        exit(1)
    
    # Paso 2: Crear proyectos desde JSON
    mapeo = crear_proyectos_desde_json_limpio()
    if not mapeo:
        print("❌ Error creando proyectos. Abortando.")
        exit(1)
    
    # Paso 3: Reasignar conversaciones inmediatamente
    if not reasignar_conversaciones_inmediatamente():
        print("❌ Error reasignando conversaciones.")
        exit(1)
    
    print(f"\n✅ PROCESO COMPLETADO EXITOSAMENTE")
    print(f"📊 Base de datos reorganizada con proyectos correctos del JSON")
    print("=" * 80)