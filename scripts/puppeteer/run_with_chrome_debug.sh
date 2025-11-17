#!/bin/bash

echo "🚀 PREPARACIÓN CHROME CON DEBUG REMOTO"
echo "======================================"
echo ""
echo "📋 ESTE SCRIPT HARÁ:"
echo "1. Cerrará Chrome actual"
echo "2. Abrirá Chrome con debug remoto"
echo "3. Te permitirá hacer login manual"
echo "4. Ejecutará Puppeteer conectándose al Chrome existente"
echo ""

read -p "¿Continuar? (Enter para sí, Ctrl+C para cancelar): "

echo ""
echo "🔄 Cerrando Chrome actual..."
pkill -f chrome || true
pkill -f google-chrome || true
sleep 3

echo "🚀 Iniciando Chrome con debug remoto..."
echo "👀 Se abrirá Chrome - haz login en ChatGPT manualmente"
echo ""

# Abrir Chrome con debug remoto en background
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile > /dev/null 2>&1 &
CHROME_PID=$!

echo "✅ Chrome iniciado con PID: $CHROME_PID"
echo "🌐 Ve al navegador y:"
echo "   1. Ve a https://chatgpt.com/"
echo "   2. Haz login con tu cuenta de ChatGPT de pago"
echo "   3. Verifica que puedes ver conversaciones"
echo ""

read -p "Presiona Enter cuando hayas terminado el login..."

echo ""
echo "🤖 Ejecutando Puppeteer conectado..."
echo ""

# Ejecutar el script que se conecta a Chrome existente
node puppeteer_connect_existing.js

echo ""
echo "🔄 ¿Cerrar Chrome debug? (Enter para sí, Ctrl+C para mantener)"
read -p ""

echo "🛑 Cerrando Chrome debug..."
kill $CHROME_PID 2>/dev/null || true
pkill -f chrome || true

echo "✅ Completado"