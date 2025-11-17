# 🤖 ChatGPT Puppeteer Test Script

Este script de prueba procesa **únicamente el primer proyecto** (ID 1: "VS Code Github") para validar la lógica de scraping antes de ejecutar los 67 proyectos completos.

## 🎯 Qué hace el script:

1. **Conecta a la base de datos** MySQL remota
2. **Abre ChatGPT** en el navegador (modo visible para debugging)
3. **Busca el proyecto "VS Code Github"** 
4. **Extrae las conversaciones** del proyecto
5. **Mapea y actualiza** las conversaciones encontradas (cambia project_id de 67 → 1)

## 🚀 Cómo ejecutar:

```bash
# Método 1: Usar npm script
npm test

# Método 2: Ejecutar directamente
node puppeteer_test.js
```

## 🔧 Configuración:

- **Base de datos:** Configurada para `iunaorg_chatBeto` (remoto)
- **Navegador:** Modo visible (`headless: false`) para debugging
- **Screenshots:** Se guardan automáticamente como `debug_chatgpt_loaded.png`
- **Proyecto objetivo:** ID 1 "VS Code Github"

## 📊 Salida esperada:

```
🚀 Iniciando Puppeteer...
✅ Puppeteer iniciado
🔗 Conectando a la base de datos...
✅ Conexión a BD establecida

🎯 Procesando proyecto: VS Code Github (ID: 1)
🌐 Navegando a ChatGPT...
✅ ChatGPT cargado
🔍 Buscando proyecto: "VS Code Github"
✅ Proyecto encontrado y seleccionado
📝 Extrayendo conversaciones del proyecto...
✅ Extraídas 15 conversaciones

💾 Actualizando conversaciones para proyecto ID 1...
  ✅ Actualizada por ID: "Configurar VS Code con GitHub"
  ✅ Actualizada por título: "Sincronizar repositorios"
  ⚠️ No encontrada en BD: "Nueva conversación"

📊 Resultado: 12 actualizadas, 3 no encontradas

✅ Proceso completado para "VS Code Github"
   - Conversaciones extraídas: 15
   - Actualizadas en BD: 12
   - No encontradas: 3
```

## ⚠️ Importante:

1. **Login manual:** Si ChatGPT pide login, hazlo manualmente en el navegador
2. **Selectores dinámicos:** Los selectores CSS pueden cambiar; el script tiene fallbacks
3. **Rate limiting:** Incluye delays para evitar bloqueos
4. **Solo proyecto 1:** Este script NO procesa todos los proyectos

## 🛠️ Debugging:

- **Screenshot automático:** `debug_chatgpt_loaded.png`
- **Logs detallados:** Cada paso se registra en consola
- **Modo visible:** Puedes ver qué hace el navegador

## 📝 Próximos pasos:

Una vez validado este script, crear la versión completa que:
- Procese los 67 proyectos
- Maneje errores de red
- Implemente retry logic
- Añada rate limiting inteligente

## 🚨 Notas de seguridad:

- Las credenciales de BD están hardcodeadas (solo para testing)
- Usar variables de entorno en producción
- El script no maneja 2FA automáticamente