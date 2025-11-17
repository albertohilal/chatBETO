#!/usr/bin/env python3
"""
Script para corregir el mapeo de proyectos en ChatBETO
Crear los 66 proyectos correctos de la lista móvil y reasignar conversaciones
"""

import json
import mysql.connector
from mysql.connector import Error

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

def crear_proyectos_faltantes():
    """Crear los proyectos de la lista móvil que no existen en la BD"""
    
    # Cargar configuración
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        print("🔍 1. Analizando proyectos existentes...")
        
        # Obtener proyectos existentes
        cursor.execute("""
            SELECT name FROM projects 
            WHERE name != 'Conversaciones Generales'
        """)
        
        proyectos_existentes = {row['name'] for row in cursor.fetchall()}
        print(f"   Proyectos existentes: {len(proyectos_existentes)}")
        
        # Encontrar faltantes
        faltantes = [p for p in PROYECTOS_MOVIL if p not in proyectos_existentes]
        print(f"   Proyectos faltantes: {len(faltantes)}")
        
        # Crear proyectos faltantes
        if faltantes:
            print(f"\n🏗️  2. Creando {len(faltantes)} proyectos faltantes...")
            
            for i, proyecto in enumerate(faltantes, 1):
                cursor.execute("""
                    INSERT INTO projects (name, description, is_starred, chatgpt_project_id) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    proyecto,
                    f'Proyecto: {proyecto}',
                    0,
                    f'g-p-manual-{i:03d}'  # ID temporal hasta tener los reales
                ))
                
                print(f"   ✅ {i:2d}/63: {proyecto}")
            
            connection.commit()
            print(f"\n✅ Todos los proyectos creados exitosamente")
        else:
            print("\n✅ Todos los proyectos ya existen")
        
        # Mostrar resumen final
        cursor.execute("SELECT COUNT(*) as total FROM projects WHERE name != 'Conversaciones Generales'")
        total = cursor.fetchone()['total']
        
        print(f"\n📊 RESUMEN:")
        print(f"   Total proyectos (sin 'Conversaciones Generales'): {total}")
        print(f"   Proyectos del móvil: {len(PROYECTOS_MOVIL)}")
        print(f"   Estado: {'✅ Completo' if total >= len(PROYECTOS_MOVIL) else '❌ Faltan proyectos'}")
        
    except Error as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def mostrar_proyectos_extras():
    """Mostrar proyectos que no están en la lista móvil"""
    
    with open('db_config.json', 'r') as f:
        db_config = json.load(f)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Obtener proyectos que no están en la lista móvil
        cursor.execute("""
            SELECT p.name, COUNT(c.id) as conversations
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id
            WHERE p.name != 'Conversaciones Generales'
            GROUP BY p.id, p.name
            ORDER BY conversations DESC
        """)
        
        todos_proyectos = cursor.fetchall()
        extras = [p for p in todos_proyectos if p['name'] not in PROYECTOS_MOVIL]
        
        print(f"\n🔍 PROYECTOS EXTRAS (no están en tu móvil): {len(extras)}")
        print("   Estos fueron creados incorrectamente durante la importación:")
        
        for i, proyecto in enumerate(extras, 1):
            print(f"   {i:2d}. '{proyecto['name']}' ({proyecto['conversations']} conversaciones)")
        
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 CORRECCIÓN DE PROYECTOS CHATBETO")
    print("=" * 80)
    
    crear_proyectos_faltantes()
    mostrar_proyectos_extras()
    
    print("\n" + "=" * 80)
    print("✅ Proceso completado. Los proyectos faltantes han sido creados.")
    print("💡 Próximo paso: Reasignar conversaciones a proyectos correctos")
    print("=" * 80)