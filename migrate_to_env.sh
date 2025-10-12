#!/bin/bash

# Script para migrar archivos PHP existentes al nuevo sistema de .env
# Uso: ./migrate_to_env.sh

echo "🔄 Iniciando migración al sistema de variables de entorno..."

# Crear backup de archivos originales
echo "📁 Creando backup de archivos originales..."
mkdir -p backup_migration
cp *.php backup_migration/ 2>/dev/null

# Lista de archivos PHP a actualizar (excluyendo los ya migrados)
php_files=(
    "buscar_chat_enriquecida.php"
    "estadisticas_detalladas.php"
    "test_busqueda.php"
)

# Función para actualizar un archivo PHP
migrate_php_file() {
    local file=$1
    
    if [ ! -f "$file" ]; then
        echo "⚠️  Archivo no encontrado: $file"
        return
    fi
    
    echo "🔧 Migrando: $file"
    
    # Crear archivo temporal
    temp_file="${file}.tmp"
    
    # Agregar require del env_loader al inicio (después de <?php)
    sed '1a\
// Cargar variables de entorno\
require_once __DIR__ . "/env_loader.php";' "$file" > "$temp_file"
    
    # Reemplazar conexiones hardcodeadas (si las encuentra)
    sed -i 's/require_once.*db_connection\.php.*/require_once __DIR__ . "\/db_connection.php";/' "$temp_file"
    
    # Mostrar diferencias
    echo "📋 Cambios en $file:"
    diff -u "$file" "$temp_file" | head -20
    
    # Preguntar si aplicar cambios
    read -p "¿Aplicar cambios a $file? (y/N): " apply
    if [[ $apply == "y" || $apply == "Y" ]]; then
        mv "$temp_file" "$file"
        echo "✅ $file actualizado"
    else
        rm "$temp_file"
        echo "❌ Cambios descartados para $file"
    fi
    
    echo ""
}

# Verificar que existe .env
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no encontrado"
    echo "📝 Creando desde .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Archivo .env creado desde plantilla"
        echo "⚠️  IMPORTANTE: Edita .env con tus credenciales reales"
    else
        echo "❌ Tampoco se encontró .env.example"
        exit 1
    fi
fi

# Migrar cada archivo
for file in "${php_files[@]}"; do
    migrate_php_file "$file"
done

# Verificar .gitignore
echo "🔍 Verificando .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -q "\.env$" .gitignore; then
        echo "✅ .env ya está en .gitignore"
    else
        echo "📝 Agregando .env a .gitignore..."
        echo ".env" >> .gitignore
    fi
else
    echo "📝 Creando .gitignore..."
    echo ".env" > .gitignore
fi

# Copiar a XAMPP si existe
if [ -d "/opt/lampp/htdocs/chatBETO/" ]; then
    echo "🌐 Copiando archivos actualizados a XAMPP..."
    sudo cp .env env_loader.php db_connection.php /opt/lampp/htdocs/chatBETO/
    
    # Copiar archivos migrados
    for file in "${php_files[@]}"; do
        if [ -f "$file" ]; then
            sudo cp "$file" /opt/lampp/htdocs/chatBETO/
        fi
    done
    
    echo "✅ Archivos copiados a XAMPP"
fi

echo ""
echo "🎉 Migración completada!"
echo ""
echo "📋 Pasos siguientes:"
echo "1. Editar .env con las credenciales correctas"
echo "2. Verificar que las APIs funcionen: curl http://localhost/chatBETO/get_projects.php"
echo "3. Probar la aplicación web: http://localhost/chatBETO/index_improved.html"
echo "4. NUNCA subir el archivo .env al repositorio Git"
echo ""
echo "🔐 El sistema ahora usa variables de entorno para mayor seguridad!"