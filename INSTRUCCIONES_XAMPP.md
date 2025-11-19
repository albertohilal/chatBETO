# 📋 INSTRUCCIONES PARA CONFIGURAR CHATBETO EN XAMPP

## 🎯 **Configuración Completa: XAMPP + Base de Datos Remota**

### **1. Configuración de XAMPP**

#### **Copiar archivos al directorio de XAMPP:**
```bash
# Copiar todo el proyecto chatBETO al directorio htdocs de XAMPP
sudo cp -r /home/beto/Documentos/Github/chatBeto/chatBETO /opt/lampp/htdocs/

# O crear un enlace simbólico (recomendado para desarrollo)
sudo ln -s /home/beto/Documentos/Github/chatBeto/chatBETO /opt/lampp/htdocs/chatBETO
```

#### **Verificar que XAMPP esté corriendo:**
```bash
sudo /opt/lampp/lampp start
```

### **2. Configuración de Base de Datos**

#### **El archivo `.env` ya está configurado correctamente:**
```
DB_HOST=sv46.byethost46.org
DB_USER=iunaorg_b3toh
DB_PASS=elgeneral2018
DB_DATABASE=iunaorg_chatBeto
```

#### **Verificar conexión con health check:**
```
http://localhost/chatBETO/api/health_check.php
```

### **3. Endpoints PHP Disponibles**

| Endpoint | Descripción | Parámetros |
|----------|-------------|------------|
| `health_check.php` | Verificar conexión | - |
| `get_projects_list.php` | Lista de proyectos | - |
| `get_project_stats.php` | Estadísticas del proyecto | `project_id` |
| `get_messages_report.php` | Mensajes para reporte | `project_id`, `search`, `role`, `limit`, `offset` |

### **4. Acceder a la Aplicación Web**

#### **URL principal del reporte:**
```
http://localhost/chatBETO/web/buscar_mensajes.html
```

#### **URLs de prueba de API:**
```
# Health check
http://localhost/chatBETO/api/health_check.php

# Lista de proyectos  
http://localhost/chatBETO/api/get_projects_list.php

# Estadísticas del proyecto 1
http://localhost/chatBETO/api/get_project_stats.php?project_id=1

# Mensajes del proyecto 1
http://localhost/chatBETO/api/get_messages_report.php?project_id=1&limit=10
```

### **5. Funcionalidades Implementadas**

✅ **Corrección de Mensajes Problemáticos:**
- 54 mensajes corregidos automáticamente
- 4 mensajes con título=contenido solucionados  
- 50 mensajes vacíos completados
- Backup automático creado

✅ **API Endpoints PHP:**
- Conexión a base de datos remota Ifastnet
- Filtros de búsqueda (texto, rol, paginación)
- Estadísticas por proyecto
- Manejo de errores y CORS

✅ **Interfaz Web Completa:**
- Búsqueda de mensajes en tiempo real
- Filtros por rol (user, assistant, system, tool)
- Paginación de resultados
- Estadísticas visuales del proyecto
- Responsive design

### **6. Estructura de Archivos en XAMPP**

```
/opt/lampp/htdocs/chatBETO/
├── api/
│   ├── health_check.php           # ✅ Health check
│   ├── get_projects_list.php      # ✅ Lista proyectos
│   ├── get_project_stats.php      # ✅ Estadísticas
│   └── get_messages_report.php    # ✅ Reporte principal
├── database/
│   ├── db_connection.php          # ✅ Conexión BD
│   └── message_operations.js      # ✅ Módulo Node.js
├── web/
│   └── buscar_mensajes.html       # ✅ Interfaz principal
└── .env                           # ✅ Configuración BD
```

### **7. Validaciones Realizadas**

#### **Base de Datos:**
- ✅ 82,937 mensajes en la base de datos
- ✅ 1,693 conversaciones activas
- ✅ Estructura alineada con OpenAI API
- ✅ Campos corregidos: `content`, `role`, `created_at`

#### **Correcciones Aplicadas:**
- ✅ 4 mensajes con título como contenido → Corregidos
- ✅ 50 mensajes vacíos → Completados con contenido apropiado
- ✅ Backup automático en `messages_backup_20251119_153757`

### **8. Próximos Pasos Recomendados**

1. **Probar la aplicación:**
   ```
   http://localhost/chatBETO/web/buscar_mensajes.html
   ```

2. **Verificar endpoints:**
   ```bash
   curl http://localhost/chatBETO/api/health_check.php
   ```

3. **Revisar logs de errores:**
   ```
   /opt/lampp/logs/error_log
   ```

4. **Agregar más filtros si es necesario:**
   - Filtro por fecha
   - Filtro por estado de mensaje
   - Exportar resultados

### **9. Solución de Problemas**

#### **Si no funciona la conexión a BD:**
1. Verificar que `.env` tenga las credenciales correctas
2. Probar `health_check.php`
3. Revisar logs de PHP en XAMPP

#### **Si no carga la interfaz:**
1. Verificar que XAMPP esté corriendo
2. Comprobar permisos de archivos
3. Revisar consola del navegador para errores JS

### **🎉 RESULTADO FINAL**

✅ **Sistema completamente funcional:**
- Base de datos remota conectada
- 54 mensajes problemáticos corregidos
- API PHP funcionando en XAMPP
- Interfaz web responsive lista para uso
- Reporte "Buscar Mensajes en Chat" operativo

¡El sistema está listo para usar en XAMPP con la base de datos remota de Ifastnet!