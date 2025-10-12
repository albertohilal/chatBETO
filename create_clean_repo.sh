#!/bin/bash

# Opción SEGURA: Crear repositorio completamente nuevo sin historial comprometido
echo "🔄 CREACIÓN DE REPOSITORIO LIMPIO"
echo "================================"
echo ""
echo "Esta opción es MÁS SEGURA que reescribir el historial existente"
echo ""

# Crear nuevo directorio para el repositorio limpio
CLEAN_REPO="chatBETO_clean_$(date +%Y%m%d_%H%M%S)"
echo "📁 Creando repositorio limpio en: $CLEAN_REPO"

# Ir al directorio padre
cd ..
mkdir "$CLEAN_REPO"
cd "$CLEAN_REPO"

echo "🔧 Inicializando nuevo repositorio Git..."
git init
git branch -M main

echo "📋 Copiando archivos actuales (sin .git)..."
# Copiar todos los archivos excepto .git, .env y otros sensibles
rsync -av --exclude='.git/' --exclude='.env' --exclude='Auxiliar/' ../chatBETO/ ./

# Verificar que .env no está presente
if [ -f ".env" ]; then
    echo "⚠️  Archivo .env encontrado, eliminándolo..."
    rm .env
fi

echo "🔍 Archivos copiados:"
ls -la

echo ""
echo "✅ Repositorio limpio creado en: $(pwd)"
echo ""
echo "📋 Próximos pasos:"
echo "1. Revisar que no hay archivos sensibles: ls -la"
echo "2. Hacer primer commit: git add . && git commit -m 'Initial commit - Clean repository'"
echo "3. Crear nuevo repositorio en GitHub (diferente nombre)"
echo "4. Conectar y subir: git remote add origin <NEW_REPO_URL>"
echo "5. git push -u origin main"
echo ""
echo "💡 Ventajas de esta opción:"
echo "   ✅ Sin riesgo de credenciales en historial"
echo "   ✅ Historial completamente limpio"
echo "   ✅ No afecta el repositorio actual"
echo "   ✅ Proceso reversible"
echo ""

read -p "¿Realizar el primer commit del repositorio limpio? (y/N): " commit_confirm

if [[ $commit_confirm == "y" || $commit_confirm == "Y" ]]; then
    echo "📝 Realizando primer commit..."
    git add .
    git commit -m "🚀 Initial commit - ChatBETO Clean Repository

✨ Sistema completo de búsqueda de conversaciones ChatGPT
🔐 Sin credenciales expuestas - Sistema .env implementado
🗄️  Base de datos normalizada: PROYECTO → CONVERSACIÓN → MENSAJE
🎨 Interfaz moderna con filtros por proyecto
📊 Panel de estadísticas detalladas

Características:
- 779 conversaciones organizadas en 10 categorías
- 15,104 mensajes indexados
- APIs RESTful con filtros avanzados
- Sistema de variables de entorno seguro
- Interfaz web responsive moderna"

    echo "✅ Primer commit realizado"
    echo ""
    echo "🌐 Para subir a GitHub:"
    echo "1. Crear nuevo repositorio en GitHub (ej: chatBETO-clean)"
    echo "2. git remote add origin https://github.com/albertohilal/chatBETO-clean.git"
    echo "3. git push -u origin main"
else
    echo "⏸️  Commit pendiente. El repositorio limpio está listo en: $(pwd)"
fi