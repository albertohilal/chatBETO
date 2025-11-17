# 🔐 Sistema de Variables de Entorno - ChatBETO

## 📋 Descripción

Este sistema permite manejar las credenciales y configuración de forma segura usando archivos `.env`, evitando exponer datos sensibles en el código fuente.

## 🚀 Configuración Inicial

### 1. Crear el archivo de configuración

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales reales
nano .env
```

### 2. Estructura del archivo `.env`

```env
# Configuración de Base de Datos
DB_HOST=tu_host_mysql
DB_NAME=tu_base_de_datos
DB_USERNAME=tu_usuario
DB_PASSWORD=tu_password

# Configuración de la Aplicación
APP_NAME=ChatBETO
APP_ENV=production
APP_DEBUG=false

# Configuración del Servidor Web
WEB_PORT=80
WEB_HOST=localhost
```

## 💻 Uso en PHP

```php
<?php
require_once 'env_loader.php';

// Obtener variables de entorno
$host = env('DB_HOST', 'localhost');
$debug = env('APP_DEBUG', false);

// Usar en conexión de base de datos
$conn = connect_to_db(); // Usa automáticamente las variables del .env
?>
```

## 🐍 Uso en Python

```python
from env_loader import env, get_db_config

# Obtener variables individuales
host = env('DB_HOST', 'localhost')
debug = env('APP_DEBUG', False)

# Obtener configuración completa de DB
db_config = get_db_config()
connection = mysql.connector.connect(**db_config)
```

## 🔒 Seguridad

### Archivos protegidos por `.gitignore`:
- `.env` - Archivo con credenciales reales (NO se sube a Git)
- `.env.local` - Configuración local de desarrollo
- `.env.production` - Configuración de producción

### Archivo público:
- `.env.example` - Plantilla sin credenciales (SÍ se sube a Git)

## 🛠️ Scripts de Prueba

### Verificar configuración PHP:
```bash
php -f test_connection.php
```

### Verificar configuración Python:
```bash
python3 test_env_connection.py
```

## 📝 Migración de Scripts Existentes

### Antes (credenciales hardcodeadas):
```php
$host = "sv46.byethost46.org";
$dbname = "iunaorg_chatBeto";
```

### Después (usando .env):
```php
require_once 'env_loader.php';
$host = env('DB_HOST');
$dbname = env('DB_NAME');
```

## 🚨 Importante

1. **NUNCA** subas el archivo `.env` al repositorio Git
2. **SIEMPRE** mantén actualizado el `.env.example`
3. **REVISA** que `.env` esté en `.gitignore`
4. **COMPARTE** solo el `.env.example` con otros desarrolladores

## 🔧 Troubleshooting

### Error: "Archivo .env no encontrado"
```bash
# Verificar que existe el archivo
ls -la .env

# Si no existe, crear desde la plantilla
cp .env.example .env
```

### Error: "Variables no cargadas"
- Verificar que el archivo `.env` tenga el formato correcto: `KEY=VALUE`
- Sin espacios alrededor del `=`
- Sin caracteres especiales en las claves