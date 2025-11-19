/**
 * EJEMPLO DE USO DEL MÓDULO DE OPERACIONES DE MENSAJES
 * 
 * Demuestra cómo usar las funciones corregidas para:
 * - Insertar mensajes con contenido real
 * - Obtener datos para reportes
 * - Manejar conversaciones y mensajes correctamente
 */

const mysql = require('mysql2/promise');
const MessageOperations = require('./message_operations');

async function ejemploDeUso() {
    let connection;
    
    try {
        // Configurar conexión a la base de datos
        connection = await mysql.createConnection({
            host: process.env.DB_HOST || 'localhost',
            user: process.env.DB_USER || 'root',
            password: process.env.DB_PASSWORD || '',
            database: process.env.DB_NAME || 'iunaorg_chatBeto',
            charset: 'utf8mb4'
        });

        console.log('✅ Conectado a la base de datos');

        // Crear instancia del módulo de operaciones
        const messageOps = new MessageOperations(connection);

        // EJEMPLO 1: Crear una nueva conversación
        console.log('\n--- EJEMPLO 1: Crear conversación ---');
        const nuevaConversacion = await messageOps.insertConversation(
            1, // project_id
            "Consulta sobre desarrollo web"
        );
        console.log('Resultado insertar conversación:', nuevaConversacion);

        if (nuevaConversacion.success) {
            const conversationId = nuevaConversacion.conversationId;

            // EJEMPLO 2: Insertar mensajes con contenido REAL
            console.log('\n--- EJEMPLO 2: Insertar mensajes ---');
            
            // Mensaje del usuario
            const mensajeUsuario = await messageOps.insertMessage(
                conversationId,
                'user',
                '¿Cuáles son las mejores prácticas para el desarrollo de APIs REST en Node.js?'
            );
            console.log('Mensaje usuario insertado:', mensajeUsuario);

            // Mensaje del asistente
            const mensajeAsistente = await messageOps.insertMessage(
                conversationId,
                'assistant',
                'Las mejores prácticas para APIs REST en Node.js incluyen:\n1. Usar Express.js como framework\n2. Implementar middleware de validación\n3. Usar códigos de estado HTTP apropiados\n4. Implementar autenticación JWT\n5. Documentar con Swagger/OpenAPI'
            );
            console.log('Mensaje asistente insertado:', mensajeAsistente);

            // Otro mensaje del usuario
            const segundoMensaje = await messageOps.insertMessage(
                conversationId,
                'user',
                '¿Podrías darme un ejemplo de implementación de middleware de validación?'
            );
            console.log('Segundo mensaje usuario:', segundoMensaje);
        }

        // EJEMPLO 3: Obtener mensajes para reporte
        console.log('\n--- EJEMPLO 3: Obtener mensajes para reporte ---');
        const reporteMensajes = await messageOps.getMessagesForReport(1); // project_id = 1
        console.log('Reporte de mensajes:', JSON.stringify(reporteMensajes, null, 2));

        // EJEMPLO 4: Obtener mensajes de una conversación específica
        if (nuevaConversacion.success) {
            console.log('\n--- EJEMPLO 4: Mensajes de conversación específica ---');
            const mensajesConversacion = await messageOps.getMessagesByConversation(
                nuevaConversacion.conversationId
            );
            console.log('Mensajes de la conversación:', JSON.stringify(mensajesConversacion, null, 2));
        }

        // EJEMPLO 5: Estadísticas del proyecto
        console.log('\n--- EJEMPLO 5: Estadísticas del proyecto ---');
        const estadisticas = await messageOps.getProjectMessageStats(1);
        console.log('Estadísticas del proyecto:', JSON.stringify(estadisticas, null, 2));

        console.log('\n✅ Todos los ejemplos ejecutados correctamente');

    } catch (error) {
        console.error('❌ Error en el ejemplo:', error);
    } finally {
        if (connection) {
            await connection.end();
            console.log('🔌 Conexión cerrada');
        }
    }
}

// Función para demostrar el uso en un API endpoint
async function ejemploAPIEndpoint() {
    console.log('\n--- EJEMPLO DE USO EN API ENDPOINT ---');
    
    const express = require('express');
    const app = express();
    app.use(express.json());

    // Endpoint para obtener mensajes de un proyecto (para el reporte)
    app.get('/api/projects/:projectId/messages', async (req, res) => {
        const connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });

        try {
            const messageOps = new MessageOperations(connection);
            const projectId = parseInt(req.params.projectId);
            
            const result = await messageOps.getMessagesForReport(projectId);
            
            if (result.success) {
                res.json({
                    success: true,
                    data: result.data,
                    totalMessages: result.totalMessages,
                    projectId: projectId
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: result.error
                });
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        } finally {
            await connection.end();
        }
    });

    // Endpoint para insertar un nuevo mensaje
    app.post('/api/conversations/:conversationId/messages', async (req, res) => {
        const connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });

        try {
            const messageOps = new MessageOperations(connection);
            const { conversationId } = req.params;
            const { role, content } = req.body;
            
            const result = await messageOps.insertMessage(conversationId, role, content);
            
            if (result.success) {
                res.json(result);
            } else {
                res.status(400).json(result);
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        } finally {
            await connection.end();
        }
    });

    console.log(`
    Endpoints de ejemplo creados:
    - GET /api/projects/:projectId/messages (obtener mensajes para reporte)
    - POST /api/conversations/:conversationId/messages (insertar nuevo mensaje)
    `);
}

// Ejecutar ejemplo si se ejecuta directamente
if (require.main === module) {
    ejemploDeUso()
        .then(() => {
            console.log('\n🎉 Ejemplo completado');
            process.exit(0);
        })
        .catch(error => {
            console.error('💥 Error fatal:', error);
            process.exit(1);
        });
}

module.exports = {
    ejemploDeUso,
    ejemploAPIEndpoint
};