# Módulo de Operaciones de Mensajes y Conversaciones

## 📋 Descripción

Este módulo corrige el manejo de conversaciones y mensajes en el sistema ChatBETO, asegurando que:

- ✅ Los mensajes almacenen el **contenido real** del chat (no el título de la conversación)
- ✅ Las consultas de reporte devuelvan correctamente el mapeo de campos:
  - `conversation.title` → Título de la conversación
  - `message.author_role` → Rol del emisor (user/assistant/system)
  - `message.content_text` → Contenido real del mensaje
  - `message.created_at` → Fecha/hora del mensaje
- ✅ Relación correcta `conversations ↔ messages` (uno-a-muchos)
- ✅ Uso de prepared statements para seguridad

## 🗃️ Estructura de Base de Datos

### Tabla `conversations`
```sql
- id (varchar(36), PK) 
- project_id (int, FK → projects.id)
- title (varchar(500)) -- TÍTULO de la conversación
- created_at (timestamp)
- conversation_id (varchar(100))
- create_time (decimal)
- update_time (decimal)
```

### Tabla `messages`  
```sql
- id (varchar(36), PK)
- conversation_id (varchar(36), FK → conversations.id) 
- content_text (longtext) -- CONTENIDO real del mensaje
- author_role (varchar(50)) -- ROL: user/assistant/system
- created_at (timestamp) -- FECHA/HORA del mensaje
- create_time (decimal)
- author_name (varchar(255))
- status (varchar(50))
```

### Tabla `projects`
```sql
- id (int, PK, AUTO_INCREMENT)
- name (varchar(255))
- description (text)
- created_at (timestamp)
```

## 📁 Archivos del Módulo

- **`message_operations.js`** - Módulo principal con las funciones corregidas
- **`example_usage.js`** - Ejemplos de implementación y uso
- **`test_message_operations.js`** - Tests automatizados para validar funcionamiento

## 🔧 Instalación

```bash
# Instalar dependencias
npm install mysql2

# Variables de entorno requeridas
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=tu_password
export DB_NAME=iunaorg_chatBeto
```

## 🚀 Uso Principal

### 1. Insertar Mensaje (con contenido real)

```javascript
const MessageOperations = require('./database/message_operations');
const messageOps = new MessageOperations(dbConnection);

// Insertar mensaje con CONTENIDO REAL (no título)
const resultado = await messageOps.insertMessage(
    'conversation-uuid-123',  // ID de conversación existente
    'user',                   // Rol: user/assistant/system  
    '¿Cómo implementar una API REST en Node.js?' // CONTENIDO real
);

console.log(resultado);
// {
//   success: true,
//   messageId: "msg-uuid-456",
//   conversationId: "conversation-uuid-123",
//   message: "Mensaje insertado correctamente con contenido real"
// }
```

### 2. Obtener Mensajes para Reporte

```javascript
// Obtener datos para el reporte "Buscar Mensajes en Chat"
const reporte = await messageOps.getMessagesForReport(1); // project_id

console.log(reporte.data);
// [
//   {
//     conversationTitle: "Consulta sobre APIs",     // TÍTULO conversación
//     messageRole: "user",                          // ROL emisor
//     messageContent: "¿Cómo hacer una API?",      // CONTENIDO mensaje
//     messageCreatedAt: "2025-11-19T10:30:00Z",    // FECHA/HORA mensaje
//     projectName: "Proyecto Web",
//     // ... más campos
//   }
// ]
```

## 📊 Funciones Disponibles

### Core Functions (Principales)

| Función | Descripción | Parámetros | Retorna |
|---------|-------------|------------|---------|
| `insertMessage()` | Inserta mensaje con contenido real | `conversationId`, `role`, `content` | `{success, messageId, ...}` |
| `getMessagesForReport()` | Datos para reporte con mapeo correcto | `projectId` | `{success, data[], totalMessages}` |

### Helper Functions (Auxiliares)

| Función | Descripción | Parámetros | Retorna |
|---------|-------------|------------|---------|
| `insertConversation()` | Crea nueva conversación | `projectId`, `title` | `{success, conversationId, ...}` |
| `getMessagesByConversation()` | Mensajes de una conversación | `conversationId` | `{success, data[], totalMessages}` |
| `getProjectMessageStats()` | Estadísticas del proyecto | `projectId` | `{success, stats{}}` |

## 🧪 Ejecutar Tests

```bash
# Ejecutar tests automatizados
node database/test_message_operations.js

# Ejecutar ejemplo de uso
node database/example_usage.js
```

## 🔍 Validación de Correcciones

### ❌ Problema Anterior
```javascript
// INCORRECTO: Se guardaba título como contenido
await insertMessage(convId, 'user', 'Título de conversación'); // MAL
```

### ✅ Solución Implementada  
```javascript
// CORRECTO: Se guarda contenido real
await insertMessage(convId, 'user', '¿Cuál es la mejor práctica para...?'); // BIEN
```

### ❌ Consulta Anterior
```sql
-- INCORRECTO: Confundía campos
SELECT title as message_content FROM conversations; -- MAL
```

### ✅ Consulta Corregida
```sql  
-- CORRECTO: Mapeo apropiado
SELECT 
  c.title as conversation_title,           -- TÍTULO conversación
  m.content_text as message_content,       -- CONTENIDO mensaje  
  m.author_role as message_role,           -- ROL emisor
  m.created_at as message_created_at       -- FECHA mensaje
FROM conversations c 
INNER JOIN messages m ON c.id = m.conversation_id;
```

## 🔒 Seguridad

- ✅ **Prepared Statements**: Todas las consultas usan parámetros seguros
- ✅ **Validación de Entrada**: Verificación de existencia de conversaciones
- ✅ **Manejo de Errores**: Try-catch y mensajes descriptivos
- ✅ **Escape de Datos**: Prevención de SQL injection

## 📝 Ejemplos de Implementación

### API Endpoint para Reporte
```javascript
app.get('/api/projects/:projectId/messages', async (req, res) => {
  const messageOps = new MessageOperations(dbConnection);
  const result = await messageOps.getMessagesForReport(req.params.projectId);
  
  res.json({
    success: result.success,
    messages: result.data,
    total: result.totalMessages
  });
});
```

### API Endpoint para Insertar Mensaje
```javascript
app.post('/api/conversations/:convId/messages', async (req, res) => {
  const messageOps = new MessageOperations(dbConnection);
  const result = await messageOps.insertMessage(
    req.params.convId,
    req.body.role,
    req.body.content  // CONTENIDO REAL del mensaje
  );
  
  res.json(result);
});
```

## 🎯 Casos de Uso del Reporte

El reporte "Buscar Mensajes en Chat" ahora devuelve correctamente:

```javascript
{
  "success": true,
  "data": [
    {
      "conversationTitle": "Consulta sobre desarrollo web",  // ← TÍTULO
      "messageRole": "user",                                 // ← ROL  
      "messageContent": "¿Cuáles son las mejores prácticas para APIs REST?", // ← CONTENIDO
      "messageCreatedAt": "2025-11-19T10:30:00Z",           // ← FECHA/HORA
      "projectName": "Proyecto Principal",
      "conversationId": "conv-123",
      "messageId": "msg-456"
    }
  ],
  "totalMessages": 1
}
```

## 📋 Checklist de Validación

- [x] Mensajes guardan contenido real (no título)
- [x] Consulta de reporte mapea campos correctamente  
- [x] Relación conversations ↔ messages funciona
- [x] Prepared statements implementados
- [x] No hay colisiones entre `title` y `content`
- [x] Tests automatizados incluidos
- [x] Documentación completa
- [x] Ejemplos de uso prácticos

## 🚨 Notas Importantes

1. **Tablas "_backup" y "_old"**: Son copias de seguridad de migraciones anteriores, no las uses en el código.

2. **Campo content_text**: Es el campo correcto para el contenido de mensajes (no `content`).

3. **UUIDs**: Los IDs usan formato UUID varchar(36), no integers AUTO_INCREMENT.

4. **Relaciones**: La FK `messages.conversation_id` → `conversations.id` está configurada con CASCADE DELETE.

---

**Autor**: Módulo corregido para ChatBETO  
**Fecha**: 19 de noviembre de 2025  
**Versión**: 1.0.0