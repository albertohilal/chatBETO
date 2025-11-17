#!/bin/bash

echo "🚀 SINCRONIZACIÓN COMPLETA CHATGPT ↔ BASE DE DATOS"
echo "=================================================="
echo ""
echo "📋 ESTE SCRIPT:"
echo "• Procesará automáticamente los 67 proyectos"
echo "• Extraerá conversaciones de cada proyecto específico"
echo "• Mapeará conversaciones del proyecto 67 'General' a su proyecto correcto"
echo "• Generará un reporte completo del proceso"
echo ""
echo "⚠️  REQUISITOS:"
echo "• Chrome debe estar ejecutándose con debug port 9222"
echo "• Debes estar logueado en ChatGPT en ese Chrome"
echo "• La base de datos debe estar accesible"
echo ""

# Verificar que Chrome debug esté corriendo
echo "🔍 Verificando Chrome debug..."
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✅ Chrome debug detectado en puerto 9222"
else
    echo "❌ Chrome debug no encontrado"
    echo ""
    echo "💡 Para iniciar Chrome debug:"
    echo "   google-chrome --remote-debugging-port=9222"
    echo "   Luego haz login en ChatGPT y vuelve a ejecutar este script"
    echo ""
    exit 1
fi

echo ""
echo "⏰ ESTIMACIÓN DE TIEMPO:"
echo "• ~67 proyectos × 30 segundos = ~35 minutos"
echo "• El progreso se mostrará en tiempo real"
echo ""

read -p "¿Continuar con la sincronización completa? (Enter para sí, Ctrl+C para cancelar): "

echo ""
echo "🚀 Iniciando sincronización completa..."
echo "   Puedes seguir el progreso detallado abajo"
echo "   El reporte final se guardará en sync_report.json"
echo ""
echo "=" $(date) "="
echo ""

# Ejecutar la sincronización completa
node puppeteer_full_sync.js

echo ""
echo "=" $(date) "="
echo "✅ Proceso completado. Revisa sync_report.json para detalles."