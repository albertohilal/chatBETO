#!/bin/bash

# Diagnóstico directo de la base de datos para identificar el problema del mapeo

echo "🔍 DIAGNÓSTICO: Problema de mapeo Conversación ≈ Mensaje"
echo "================================================="

cd /home/beto/Documentos/Github/chatBeto/chatBETO

# Verificar si tenemos acceso a la API de XAMPP
echo ""
echo "📊 VERIFICANDO MENSAJES EN LA API..."

# Obtener datos de muestra
curl -s "http://localhost/chatBETO/api/get_messages_report.php?project_id=1&limit=5" > /tmp/api_response.json

if [ $? -eq 0 ] && [ -s /tmp/api_response.json ]; then
    echo "✅ API responde correctamente"
    
    # Mostrar los datos problemáticos
    echo ""
    echo "📋 DATOS PROBLEMÁTICOS DETECTADOS:"
    echo "=================================="
    
    # Extraer y mostrar los datos usando Python
    python3 -c "
import json
import sys

try:
    with open('/tmp/api_response.json', 'r') as f:
        data = json.load(f)
    
    if data.get('success') and 'data' in data:
        messages = data['data'][:3]  # Primeros 3 mensajes
        
        print('CONVERSACIÓN | ROL | MENSAJE')
        print('-' * 80)
        
        for msg in messages:
            conv_title = msg['conversationTitle'][:30]
            role = msg['messageRole']
            content = msg['messageContent'][:50]
            
            print(f'{conv_title} | {role} | {content}')
            
            # Detectar si son iguales
            if conv_title.replace('Conversación: ', '') in content:
                print('⚠️  PROBLEMA: Mensaje contiene título de conversación')
            
            print()
    else:
        print('❌ Error en la respuesta de la API')
        print(json.dumps(data, indent=2))
        
except Exception as e:
    print(f'❌ Error procesando JSON: {e}')
    with open('/tmp/api_response.json', 'r') as f:
        print('Respuesta raw:', f.read()[:500])
"

else
    echo "❌ No se pudo conectar a la API XAMPP"
    echo "Verificar que XAMPP esté corriendo y los archivos estén en /opt/lampp/htdocs/chatBETO/"
fi

echo ""
echo "🔧 PRÓXIMOS PASOS SUGERIDOS:"
echo "1. Ejecutar script de corrección mejorado"
echo "2. Verificar que los mensajes realmente tengan contenido único"
echo "3. Actualizar el módulo de inserción para prevenir futuros problemas"