#!/bin/bash

# Script para generar releases de chatBETO
# Uso: ./build_release.sh [version]

set -e

# Configuración
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$PROJECT_DIR/deploy"
RELEASES_DIR="$PROJECT_DIR/releases"
VERSION="${1:-$(date +%Y%m%d_%H%M)}"

echo "🏗️  Generando release de chatBETO..."
echo "📁 Directorio: $PROJECT_DIR"
echo "🏷️  Versión: $VERSION"

# Crear directorio releases si no existe
mkdir -p "$RELEASES_DIR"

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
RELEASE_NAME="chatBeto_v${VERSION}"
RELEASE_PATH="$TEMP_DIR/$RELEASE_NAME"

echo "📦 Creando estructura de release..."

# Copiar archivos de deploy
mkdir -p "$RELEASE_PATH"
cp -r "$DEPLOY_DIR"/* "$RELEASE_PATH/"

# Limpiar archivos innecesarios para producción
echo "🧹 Limpiando archivos innecesarios..."
find "$RELEASE_PATH" -name "*.md" -delete
find "$RELEASE_PATH" -name "*.txt" -delete
find "$RELEASE_PATH" -name "schema_*.sql" -delete
find "$RELEASE_PATH" -name "backup_*.sql" -delete
rm -f "$RELEASE_PATH/database/db_connection_ifastnet.php"

# Crear ZIP
ZIP_NAME="chatBETO_v${VERSION}.zip"
ZIP_PATH="$RELEASES_DIR/$ZIP_NAME"

echo "📦 Creando ZIP: $ZIP_NAME"
cd "$TEMP_DIR"
zip -r "$ZIP_PATH" "$RELEASE_NAME/" > /dev/null

# Limpiar temporal
rm -rf "$TEMP_DIR"

# Información del ZIP
ZIP_SIZE=$(ls -lh "$ZIP_PATH" | awk '{print $5}')
FILE_COUNT=$(unzip -l "$ZIP_PATH" | tail -1 | awk '{print $2}')

echo ""
echo "✅ Release generado exitosamente:"
echo "📦 Archivo: $ZIP_NAME"
echo "📏 Tamaño: $ZIP_SIZE"
echo "📄 Archivos: $FILE_COUNT"
echo "📍 Ubicación: $ZIP_PATH"
echo ""
echo "🚀 Listo para subir a iFastNet!"

# Crear enlace simbólico al último release
cd "$RELEASES_DIR"
rm -f latest.zip
ln -s "$ZIP_NAME" latest.zip

echo "🔗 Enlace 'latest.zip' actualizado"