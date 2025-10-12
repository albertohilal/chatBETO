# ChatBETO 🤖💬

Una aplicación web para importar, almacenar y buscar conversaciones de ChatGPT de manera eficiente.

## 📋 Descripción

ChatBETO es una herramienta que permite importar conversaciones exportadas desde ChatGPT a una base de datos MySQL y proporciona una interfaz web intuitiva para buscar específicamente dentro del contenido de esos mensajes. Ideal para mantener un archivo personal searchable de todas tus interacciones con ChatGPT.

## ✨ Características

- 📤 **Importación automática** de archivos JSON exportados desde ChatGPT
- 🔍 **Búsqueda de texto completo** en todas las conversaciones
- 🎨 **Renderizado Markdown** para formateo de código y texto
- 🖼️ **Soporte para imágenes** con visualización modal ampliada
- 📱 **Interfaz responsiva** y fácil de usar
- 🌐 **Soporte UTF-8 completo** para múltiples idiomas
- ⚡ **Búsqueda rápida** con resultados en tiempo real

## 🏗️ Arquitectura

### Frontend
- **HTML5** con interfaz limpia y moderna
- **CSS3** con estilos responsivos
- **JavaScript** para interacciones dinámicas
- **Marked.js** para renderizado de Markdown

### Backend
- **PHP** para APIs y lógica de servidor
- **MySQL** para almacenamiento de datos
- **Python** para scripts de importación

## 📦 Estructura del Proyecto

```
chatBETO/
├── index.html              # Interfaz principal
├── styles.css              # Estilos de la aplicación
├── db_connection.php       # Configuración de base de datos
├── buscar_chat.php         # API de búsqueda principal
├── buscar_chat-02.php      # API de búsqueda alternativa
├── ImportChatgptMysql.py   # Script de importación principal
├── ImportChatgptMysql-02.PY # Script de importación v2
├── ImportChatgptMysql-03.PY # Script de importación v3
├── conversation-messages.sql # Query de ejemplo
├── test_error.php          # Script de pruebas
├── error_log.txt           # Log de errores
└── extracted/
    └── conversations.json  # Datos importados (Git LFS)
```

## 🛠️ Instalación

### Prerrequisitos

- **PHP 7.4+** con extensiones PDO y MySQL
- **MySQL 5.7+** o MariaDB
- **Python 3.6+** con pip
- Servidor web (Apache, Nginx, etc.)

### Configuración

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/albertohilal/chatBETO.git
   cd chatBETO
   ```

2. **Configura la base de datos**
   
   Edita `db_connection.php` con tus credenciales:
   ```php
   $host = "tu_host";
   $dbname = "tu_base_de_datos";
   $username = "tu_usuario";
   $password = "tu_contraseña";
   ```

3. **Instala dependencias Python**
   ```bash
   pip install pymysql
   ```

4. **Crea las tablas**
   
   Las tablas se crean automáticamente al ejecutar el script de importación, pero también puedes usar:
   ```sql
   CREATE TABLE conversations (
       conversation_id VARCHAR(255) PRIMARY KEY,
       title TEXT
   );
   
   CREATE TABLE messages (
       id VARCHAR(255) PRIMARY KEY,
       conversation_id VARCHAR(255),
       role VARCHAR(50),
       content TEXT,
       parts TEXT,
       create_time DATETIME,
       parent VARCHAR(255),
       children TEXT,
       FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
   );
   ```

## 🚀 Uso

### Importar Conversaciones

1. **Exporta tus conversaciones desde ChatGPT**
   - Ve a ChatGPT → Configuración → Exportar datos
   - Descarga el archivo `conversations.json`

2. **Coloca el archivo en la carpeta extracted/**
   ```bash
   mkdir extracted
   mv conversations.json extracted/
   ```

3. **Ejecuta el script de importación**
   ```bash
   python ImportChatgptMysql.py
   ```

### Usar la Interfaz Web

1. **Abre `index.html`** en tu navegador
2. **Escribe tu término de búsqueda** en el campo de texto
3. **Haz clic en "Buscar"** o presiona Enter
4. **Revisa los resultados** organizados por conversación
5. **Haz clic en las imágenes** para verlas ampliadas

## 🔍 Funcionalidades de Búsqueda

- **Búsqueda de texto completo** en el contenido de los mensajes
- **Filtrado automático** por rol (user/assistant)
- **Resultados contextuales** mostrando la conversación completa
- **Ordenamiento cronológico** de mensajes
- **Resaltado de contenido** Markdown y código

## 🗄️ Esquema de Base de Datos

### Tabla `conversations`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| conversation_id | VARCHAR(255) | ID único de la conversación |
| title | TEXT | Título de la conversación |

### Tabla `messages`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | VARCHAR(255) | ID único del mensaje |
| conversation_id | VARCHAR(255) | Referencia a la conversación |
| role | VARCHAR(50) | 'user' o 'assistant' |
| content | TEXT | Contenido procesado |
| parts | TEXT | JSON con partes del mensaje |
| create_time | DATETIME | Timestamp de creación |
| parent | VARCHAR(255) | Mensaje padre (threading) |
| children | TEXT | Mensajes hijos (JSON array) |

## 🔧 API Endpoints

### `buscar_chat.php`
- **Método:** GET
- **Parámetro:** `query` - Término de búsqueda
- **Respuesta:** JSON con mensajes coincidentes

**Ejemplo:**
```bash
curl "http://localhost/chatBETO/buscar_chat.php?query=python"
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 TODO

- [ ] Implementar paginación para grandes resultados
- [ ] Añadir filtros por fecha y rol
- [ ] Mejorar el manejo de imágenes y attachments
- [ ] Implementar exportación de resultados
- [ ] Añadir autenticación y usuarios múltiples
- [ ] Crear API REST más completa

## 🐛 Problemas Conocidos

- Los archivos muy grandes pueden causar timeout en la importación
- Algunas imágenes pueden no cargar correctamente
- La búsqueda es sensible a mayúsculas/minúsculas

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Alberto Hilal** - [@albertohilal](https://github.com/albertohilal)

## 🙏 Agradecimientos

- ChatGPT por proporcionar la inspiración y los datos de prueba
- La comunidad de desarrolladores por las librerías utilizadas
- Marked.js por el excelente renderizado de Markdown

---

⭐ **¡Si este proyecto te resulta útil, no olvides darle una estrella!** ⭐