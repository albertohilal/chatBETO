#!/bin/bash

# 🧹 Script de limpieza del proyecto chatBETO
# Elimina archivos redundantes y temporales

echo "🧹 Iniciando limpieza del proyecto chatBETO..."
echo "📂 Directorio: $(pwd)"
echo ""

# Función para eliminar archivo/directorio con confirmación
remove_if_exists() {
    if [ -e "$1" ]; then
        echo "🗑️  Eliminando: $1"
        rm -rf "$1"
        echo "    ✅ Eliminado"
    else
        echo "    ⚠️  No existe: $1"
    fi
}

echo "=== 1. Eliminando archivos de debug/testing ==="
remove_if_exists "debug_simple.php"
remove_if_exists "test_js.html" 
remove_if_exists "get_projects.php"
remove_if_exists "get_projects_fixed.php"

echo ""
echo "=== 2. Eliminando entornos virtuales redundantes ==="
remove_if_exists ".venv-1"
remove_if_exists ".venv-chatBETO"

echo ""
echo "=== 3. Eliminando scripts de importación (ya ejecutados) ==="
remove_if_exists "ImportChatgptMysql-02.PY"
remove_if_exists "ImportChatgptMysql-03.PY"

echo ""
echo "=== 4. Eliminando APIs duplicadas/viejas ==="
remove_if_exists "api/buscar_chat.php"
remove_if_exists "api/buscar_chat-02.php"
remove_if_exists "api/buscar_chat_enriquecida.php" 
remove_if_exists "api/buscar_chat_fixed.php"
remove_if_exists "api/messages_diverse.php"

echo ""
echo "=== 5. Eliminando documentación temporal ==="
remove_if_exists "SOLUCION_DEFINITIVA.txt"
remove_if_exists "SOLUCION_ERROR_JSON.txt"

echo ""
echo "=== 6. Eliminando cachés Python ==="
remove_if_exists "__pycache__"

echo ""
echo "✅ Limpieza completada!"
echo ""
echo "📋 Archivos importantes mantenidos:"
echo "   - web/buscar_mensajes.html (interfaz principal)"
echo "   - api/messages_simple_working.php (API principal)"
echo "   - api/update_conversation_project.php (proyectos)" 
echo "   - api/get_projects_list.php (lista proyectos)"
echo "   - config/ (configuración)"
echo "   - database/ (conexión BD)"
echo "   - start_php_server.sh (desarrollo)"
echo "   - .env (variables de entorno)"
echo ""

# Mostrar estado final
echo "📊 Archivos restantes en directorio raíz:"
ls -la | grep -v "^d" | wc -l
echo ""
echo "🎯 Proyecto limpio y organizado!"