#!/bin/bash

# Script para limpiar credenciales del historial de Git
# ⚠️  ADVERTENCIA: Este script reescribe la historia de Git

echo "🚨 LIMPIEZA DE CREDENCIALES EN HISTORIAL DE GIT"
echo "=============================================="
echo ""
echo "⚠️  ADVERTENCIA: Este proceso reescribirá la historia de Git"
echo "   Esto afectará a todos los colaboradores del repositorio"
echo ""
echo "🔍 Credenciales encontradas en commits anteriores:"
echo "   - Host: sv46.byethost46.org"
echo "   - Database: iunaorg_chatBeto" 
echo "   - Username: iunaorg_b3toh"
echo "   - Password: elgeneral2018"
echo ""

read -p "¿Continuar con la limpieza? (y/N): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

# Crear backup del repositorio actual
echo "📁 Creando backup del repositorio..."
cd ..
cp -r chatBETO chatBETO_backup_$(date +%Y%m%d_%H%M%S)
cd chatBETO

echo "🔧 Iniciando limpieza del historial..."

# Usar git filter-branch para reescribir el historial
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch db_connection.php' \
--prune-empty --tag-name-filter cat -- --all

# Alternativa más agresiva con BFG (si está disponible)
# bfg --delete-files db_connection.php
# git reflog expire --expire=now --all && git gc --prune=now --aggressive

echo "🧹 Limpiando referencias..."
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "📝 Verificando limpieza..."
# Verificar que las credenciales ya no están en el historial
if git log --all --grep="elgeneral2018" --grep="sv46.byethost46.org" --grep="iunaorg" > /dev/null 2>&1; then
    echo "⚠️  Aún se encontraron referencias a credenciales"
else
    echo "✅ No se encontraron credenciales en el historial"
fi

echo ""
echo "🚀 Siguiente paso: FORZAR PUSH al repositorio remoto"
echo "   git push --force-with-lease origin main"
echo ""
echo "⚠️  IMPORTANTE: Informa a todos los colaboradores que deben:"
echo "   1. git fetch origin"
echo "   2. git reset --hard origin/main"
echo ""
read -p "¿Realizar el force push ahora? (y/N): " push_confirm

if [[ $push_confirm == "y" || $push_confirm == "Y" ]]; then
    echo "🚀 Realizando force push..."
    git push --force-with-lease origin main
    echo "✅ Historial limpiado y subido al repositorio remoto"
else
    echo "⏸️  Force push pendiente. Ejecutar manualmente:"
    echo "   git push --force-with-lease origin main"
fi

echo ""
echo "🎉 Proceso completado!"
echo "📋 Pasos adicionales recomendados:"
echo "1. Cambiar las credenciales del servidor de base de datos"
echo "2. Verificar que .env está en .gitignore (✅ ya está)"
echo "3. Informar a colaboradores sobre la reescritura del historial"