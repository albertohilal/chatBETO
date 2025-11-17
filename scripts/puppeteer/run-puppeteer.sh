#!/bin/bash

echo "🚀 CHATBETO - INSTALADOR Y EJECUTOR PUPPETEER"
echo "=============================================="

# 1. Verificar Node.js
echo "🔍 Verificando Node.js..."
if command -v node >/dev/null 2>&1; then
    echo "✅ Node.js encontrado: $(node --version)"
else
    echo "❌ Node.js no encontrado. Instala Node.js primero:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
fi

# 2. Instalar dependencias
echo -e "\n📦 Instalando dependencias..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "❌ Error instalando dependencias"
    exit 1
fi

# 3. Crear directorio para screenshots
mkdir -p screenshots
echo "📁 Directorio screenshots creado"

# 4. Mostrar instrucciones
echo -e "\n🤖 INSTRUCCIONES DE USO:"
echo "========================"
echo "1. El script abrirá Chrome/Chromium"
echo "2. Inicia sesión en ChatGPT manualmente"
echo "3. Navega a la página principal de ChatGPT"
echo "4. Regresa a esta consola y presiona ENTER"
echo "5. El script comenzará a extraer gizmo_ids automáticamente"

echo -e "\n📊 CONFIGURACIÓN ACTUAL:"
echo "- Máximo conversaciones: 50 (modo prueba)"
echo "- Screenshots habilitados: Sí"
echo "- Modo headless: No (verás el browser)"
echo "- Base de datos: $(grep -o '"host": "[^"]*"' db_config.json | cut -d'"' -f4)"

echo -e "\n🚀 ¿Ejecutar el scraper ahora? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "\n🔄 Ejecutando scraper..."
    node puppeteer-scraper.js
else
    echo "📝 Para ejecutar manualmente: npm start"
    echo "📝 O directamente: node puppeteer-scraper.js"
fi

echo -e "\n✅ Script completado"