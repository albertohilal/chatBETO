# 🚀 GUÍA DE DESPLIEGUE IFASTNET - chatBETO

## ⚡ PASOS PARA DESPLEGAR EN IFASTNET

### 📁 Paso 1: Subir archivos al hosting

1. **Accede a tu panel de iFastNet** (byethost o ifastnet)
2. **Ve al File Manager** o usa FTP
3. **Sube SOLO estos archivos/carpetas del directorio `deploy/`:**

```
📂 htdocs/ (carpeta raíz de tu sitio)
├── 📄 index.html
├── 📄 styles.css  
├── 📄 estadisticas.html
├── 📄 index_chatgpt_style.html
├── 📄 index_fixed.html
└── 📂 api/
    ├── 📄 api_get_conversations.php
    ├── 📄 api_get_messages.php
    ├── 📄 api_get_projects.php
    ├── 📄 api_get_stats.php
    ├── 📄 buscar_chat_enriquecida.php
    ├── 📄 buscar_chat_fixed.php
    ├── 📄 buscar_chat_with_filters.php
    └── 📂 database/
        └── 📄 db_connection.php
```

### ✅ Paso 2: Verificar configuración

**¡IMPORTANTE!** ✋ 
- **NO subas el directorio `database/` completo**
- **NO ejecutes scripts de esquema** 
- **La base de datos YA EXISTE y tiene datos**

**La configuración está lista para:**
- 🔗 Host: `sv46.byethost46.org`  
- 🗄️ Base de datos: `iunaorg_chatBeto`
- 👤 Usuario: `iunaorg_b3toh`
- 🔑 Password: `elgeneral2018`

### 🌐 Paso 3: Probar el sitio

1. **Visita tu URL de iFastNet** (ej: `tudominio.byethost46.org`)
2. **Deberías ver la interfaz de chatBETO**
3. **Prueba buscar algo para verificar conexión con la BD**

### 🔧 Paso 4: Solución de problemas

Si hay errores:

1. **Revisa los logs de error del hosting**
2. **Verifica que PHP esté habilitado** 
3. **Comprueba que la BD siga activa:**
   - Ve a tu panel de iFastNet
   - Sección "MySQL Databases"
   - Verifica que `iunaorg_chatBeto` esté listada

### 📋 Estructura de archivos en el servidor

```
htdocs/
├── index.html              ← Página principal
├── styles.css              ← Estilos
├── estadisticas.html       ← Dashboard stats
├── index_chatgpt_style.html ← Alternativa UI
├── index_fixed.html        ← Versión fija
└── api/
    ├── buscar_chat.php     ← API principal búsqueda
    ├── api_get_*.php       ← APIs datos
    └── database/
        └── db_connection.php ← Conexión BD (configurada)
```

## ⚠️ NOTAS IMPORTANTES

1. **Base de datos:** Ya existe y contiene tus conversaciones
2. **Credenciales:** Están hardcodeadas en `db_connection.php` 
3. **Seguridad:** Asegúrate de que solo tú tengas acceso al FTP
4. **Backup:** Considera hacer backup de la BD antes de cambios

## 🎯 ¿Listo para subir?

Solo necesitas:
1. ✅ Subir archivos del directorio `deploy/` 
2. ✅ Probar que funcione la búsqueda
3. ✅ ¡Disfrutar tu chatBETO en línea! 🎉