# 🚀 Guía de Instalación chatBETO en iFastNet

## 📋 **PASOS PARA CONFIGURAR EN TU HOSTING:**

### 1. 🌐 **Subir Archivos via FTP/Administrador de Archivos**
```
Subir todos los archivos de la carpeta deploy/ a:
/public_html/chatbeto/
```

### 2. 🗄️ **Configurar Base de Datos**

#### A. Crear Base de Datos en cPanel:
- Ve a **MySQL Databases**
- Crea una nueva base de datos: `tu_usuario_chatbeto`
- Crea un usuario y asígnalo a la base de datos
- **¡Guarda estos datos!**

#### B. Ejecutar Schema SQL:
- Abre **phpMyAdmin** 
- Selecciona tu base de datos
- Importa el archivo `schema_ifastnet.sql`

### 3. ⚙️ **Configurar Conexión BD**

Edita `database/db_connection.php` con tus datos reales:

```php
$host = 'sql110.infinityfree.com';        // Tu host MySQL
$dbname = 'if0_XXXXXX_chatbeto';          // Tu base de datos  
$username = 'if0_XXXXXX';                 // Tu usuario BD
$password = 'tu_password_real';           // Tu password real
```

### 4. 🔍 **Probar la Instalación**

Visita: `https://tu-dominio.com/chatbeto/`

### 5. 📊 **Importar Datos (Opcional)**

Para importar tus conversaciones de ChatGPT:

1. **Sube** el script `import_to_remote.php` (lo crearemos)
2. **Exporta** datos desde tu BD local
3. **Importa** via script web

## 🔧 **ARCHIVOS INCLUIDOS:**

```
chatbeto/
├── index.html              # Interfaz principal
├── styles.css              # Estilos
├── estadisticas.html       # Página de estadísticas  
├── api/                    # APIs PHP
│   ├── buscar_chat.php     # API búsqueda
│   ├── api_get_projects.php # API proyectos
│   └── ...
├── database/
│   └── db_connection.php   # Conexión BD
└── schema_ifastnet.sql     # Script BD
```

## 🎯 **URLs DE ACCESO:**

- **Interfaz Principal**: `https://tu-dominio.com/chatbeto/`
- **API Búsqueda**: `https://tu-dominio.com/chatbeto/api/buscar_chat.php`
- **Estadísticas**: `https://tu-dominio.com/chatbeto/estadisticas.html`

## ⚠️ **IMPORTANTE:**

1. **Cambia las credenciales** de la base de datos
2. **Prueba la conexión** antes de usar
3. **Mantén backups** de tu configuración
4. **Protege** el acceso si contiene datos sensibles

¡Tu chatBETO estará listo en tu hosting! 🎊