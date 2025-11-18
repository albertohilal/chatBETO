# 📥 Guía para Futuras Exportaciones de ChatGPT

## 📂 **DIRECTORIO RECOMENDADO:**
```
data/exports/raw/
```

## 📋 **FLUJO DE TRABAJO RECOMENDADO:**

### 1. 🔽 Descargar Nueva Exportación
```bash
# Descargar el ZIP desde ChatGPT a:
/home/beto/Documentos/Github/chatBeto/chatBETO/data/exports/raw/

# Ejemplo de nombre:
# exportacion_chatgpt_2025-12-01.zip
```

### 2. ⚡ Ejecutar Importación Incremental
```bash
cd /home/beto/Documentos/Github/chatBeto/chatBETO
node scripts/node/update_chatgpt_incremental.js
```

### 3. 🧹 Completar con Mensajes (si es necesario)
```bash
node scripts/node/import_complete_conversations_messages.js
```

## 🗂️ **ESTRUCTURA DE DIRECTORIOS:**

```
data/exports/
├── raw/                    # ← AQUÍ van los ZIPs nuevos
│   ├── export_2025-11-17.zip
│   ├── export_2025-12-01.zip
│   └── export_2026-01-15.zip
├── extracted/              # Archivos JSON extraídos
├── temp_complete_*/        # Procesamiento temporal
└── processed/             # Archivos ya procesados (opcional)
```

## 🎯 **VENTAJAS DE ESTE SISTEMA:**

✅ **Organización**: Exports separados por fecha  
✅ **Seguridad**: Carpeta protegida por .gitignore  
✅ **Automatización**: Scripts detectan automáticamente  
✅ **Trazabilidad**: Historial de todas las importaciones  
✅ **Limpieza**: Fácil eliminar archivos antiguos  

## 📋 **COMANDOS ÚTILES:**

### Verificar última importación:
```bash
ls -lt data/exports/raw/ | head -5
```

### Limpiar archivos antiguos (opcional):
```bash
# Remover exports de más de 30 días
find data/exports/raw/ -name "*.zip" -mtime +30 -delete
```

### Ver estado de la base de datos:
```bash
node scripts/node/investigar_problema.js
```

## 🔔 **RECORDATORIO:**

1. **Siempre** descarga en `data/exports/raw/`
2. **Ejecuta** el script incremental primero
3. **Verifica** que no hay errores antes de continuar
4. **Mantén** máximo 3-4 exports (para ahorrar espacio)

¡Con este flujo tendrás tus conversaciones ChatGPT siempre actualizadas y organizadas! 🚀