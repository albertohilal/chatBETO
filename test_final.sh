#!/bin/bash
echo "🔍 Probando chatBETO - index.html actualizado"
echo "================================================="

echo "📊 1. Probando API con búsqueda 'python' (ordenado por fecha):"
curl -s "http://localhost/chatBETO/buscar_chat.php?query=python" | head -5

echo ""
echo "📊 2. Probando API sin query (mostrar todo):"  
curl -s "http://localhost/chatBETO/buscar_chat.php?query=" | head -3

echo ""
echo "📊 3. Verificando que index.html carga:"
curl -s "http://localhost/chatBETO/index.html" | grep -E "(title|h1)" | head -3

echo ""
echo "✅ Tests completados!"
echo ""
echo "🌐 Accede a la aplicación en:"
echo "   http://localhost/chatBETO/index.html"