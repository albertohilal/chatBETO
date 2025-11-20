#!/bin/bash

# 🚀 Script para iniciar el servidor PHP de desarrollo
# Ahora usa el servidor estable con auto-restart

echo "🚀 Usando servidor PHP estable..."
echo "📂 Directorio: $(pwd)"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "web" ] || [ ! -d "api" ]; then
    echo "❌ ERROR: No se encontraron los directorios 'web' y 'api'"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

# Usar el servidor estable
if [ -f "start_stable_server.sh" ]; then
    echo "✅ Iniciando servidor estable..."
    ./start_stable_server.sh start
else
    echo "⚠️  Servidor estable no encontrado, usando servidor básico..."
    echo "🌐 URL: http://localhost:8002/web/buscar_mensajes.html"
    echo "🔗 API: http://localhost:8002/api/messages_simple_working.php"
    echo ""
    php -S localhost:8002
fi
php -S localhost:8002