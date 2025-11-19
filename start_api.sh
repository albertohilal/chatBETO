#!/bin/bash
# start_api.sh - Script para iniciar la API de mensajes

cd /home/beto/Documentos/Github/chatBeto/chatBETO
echo "🚀 Iniciando API de Mensajes ChatBETO..."
echo "📁 Directorio de trabajo: $(pwd)"
echo "📄 Verificando archivo API: $(ls -la api/messages_api.js 2>/dev/null || echo 'No encontrado')"
echo ""

node api/messages_api.js