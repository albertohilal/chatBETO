#!/bin/bash

# 🚀 Iniciar servidor PHP integrado para ChatBETO
# Puerto: 8002
# Directorio: chatBETO (donde están los archivos web y api)

# Asegurar que estamos en el directorio correcto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Iniciando servidor PHP en puerto 8002..."
echo "📂 Directorio: $(pwd)"
echo "🌐 URL: http://localhost:8002"
echo ""
echo "Endpoints disponibles:"
echo "  - http://localhost:8002/web/buscar_mensajes.html"
echo "  - http://localhost:8002/api/messages_simple_working.php"
echo ""
echo "Archivos en web/:"
ls web/ | sed 's/^/    - /'
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "============================================="

# Iniciar servidor PHP
php -S localhost:8002