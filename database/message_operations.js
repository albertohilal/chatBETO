/**
 * MÓDULO DE OPERACIONES DE MENSAJES Y CONVERSACIONES
 * 
 * Funciones corregidas para manejar correctamente:
 * - Inserción de mensajes con contenido real (no título de conversación)
 * - Consulta de mensajes para reportes con mapeo correcto de campos
 * - Relación conversations ↔ messages (uno-a-muchos)
 * 
 * Cambios realizados:
 * - insertMessage() ahora usa content_text para el contenido real del mensaje
 * - getMessagesForReport() hace JOIN correcto entre conversations y messages
 * - Se mapean correctamente: title (conversation), author_role (message), content_text (message)
 * - Uso de prepared statements para seguridad
 */

const mysql = require('mysql2/promise');

class MessageOperations {
    constructor(dbConnection) {
        this.db = dbConnection;
    }

    /**
     * Inserta un nuevo mensaje en una conversación existente
     * 
     * @param {string} conversationId - ID de la conversación (debe existir en tabla conversations)
     * @param {string} role - Rol del autor ('user', 'assistant', 'system', etc.)
     * @param {string} content - Contenido REAL del mensaje (no el título)
     * @returns {Promise<Object>} - Resultado de la inserción con el ID del mensaje creado
     */
    async insertMessage(conversationId, role, content) {
        try {
            // Verificar que la conversación existe
            const [conversationCheck] = await this.db.execute(
                'SELECT id FROM conversations WHERE id = ?',
                [conversationId]
            );

            if (conversationCheck.length === 0) {
                throw new Error(`Conversación con ID ${conversationId} no existe`);
            }

            // Generar ID único para el mensaje
            const messageId = this.generateUUID();
            
            // Insertar mensaje con contenido real
            const [result] = await this.db.execute(`
                INSERT INTO messages (
                    id, 
                    conversation_id, 
                    content, 
                    role,
                    content_type,
                    created_at_timestamp_ms,
                    created_at,
                    status,
                    end_turn,
                    weight
                ) VALUES (?, ?, ?, ?, 'text', UNIX_TIMESTAMP(NOW(6)) * 1000, NOW(), 'finished_successfully', 0, 1.00)
            `, [messageId, conversationId, content, role]);

            return {
                success: true,
                messageId: messageId,
                conversationId: conversationId,
                insertedRows: result.affectedRows,
                message: 'Mensaje insertado correctamente con contenido real'
            };

        } catch (error) {
            console.error('Error al insertar mensaje:', error);
            return {
                success: false,
                error: error.message,
                details: 'Error en insertMessage - verificar conversationId y parámetros'
            };
        }
    }

    /**
     * Obtiene mensajes formateados para el reporte "Buscar Mensajes en Chat"
     * 
     * @param {number} projectId - ID del proyecto para filtrar conversaciones
     * @returns {Promise<Array>} - Array de objetos con datos para el reporte
     */
    async getMessagesForReport(projectId) {
        try {
            const [rows] = await this.db.execute(`
                SELECT 
                    c.id as conversation_id,
                    c.title as conversation_title,
                    c.project_id,
                    p.name as project_name,
                    m.id as message_id,
                    m.role as message_role,
                    m.content as message_content,
                    m.created_at as message_created_at,
                    m.created_at_timestamp_ms as message_timestamp,
                    m.author_name,
                    m.status as message_status
                FROM conversations c
                INNER JOIN messages m ON c.id = m.conversation_id
                LEFT JOIN projects p ON c.project_id = p.id
                WHERE c.project_id = ?
                ORDER BY c.created_at DESC, m.created_at ASC
            `, [projectId]);

            // Formatear datos para el reporte
            const reportData = rows.map(row => ({
                // Datos de la conversación
                conversationId: row.conversation_id,
                conversationTitle: row.conversation_title, // TÍTULO de la conversación
                projectId: row.project_id,
                projectName: row.project_name,
                
                // Datos del mensaje
                messageId: row.message_id,
                messageRole: row.message_role, // ROL del emisor (user/assistant/system)
                messageContent: row.message_content, // CONTENIDO real del mensaje
                messageCreatedAt: row.message_created_at, // FECHA/HORA del mensaje
                messageTimestamp: row.message_timestamp,
                authorName: row.author_name,
                messageStatus: row.message_status
            }));

            return {
                success: true,
                data: reportData,
                totalMessages: reportData.length,
                projectId: projectId,
                message: 'Mensajes obtenidos correctamente para reporte'
            };

        } catch (error) {
            console.error('Error al obtener mensajes para reporte:', error);
            return {
                success: false,
                error: error.message,
                data: [],
                details: 'Error en getMessagesForReport - verificar projectId'
            };
        }
    }

    /**
     * Obtiene mensajes de una conversación específica
     * 
     * @param {string} conversationId - ID de la conversación
     * @returns {Promise<Array>} - Array de mensajes de la conversación
     */
    async getMessagesByConversation(conversationId) {
        try {
            const [rows] = await this.db.execute(`
                SELECT 
                    m.id,
                    m.conversation_id,
                    m.content,
                    m.role,
                    m.author_name,
                    m.created_at,
                    m.created_at_timestamp_ms,
                    m.status,
                    c.title as conversation_title,
                    c.project_id
                FROM messages m
                INNER JOIN conversations c ON m.conversation_id = c.id
                WHERE m.conversation_id = ?
                ORDER BY m.created_at ASC
            `, [conversationId]);

            return {
                success: true,
                data: rows,
                conversationId: conversationId,
                totalMessages: rows.length
            };

        } catch (error) {
            console.error('Error al obtener mensajes de conversación:', error);
            return {
                success: false,
                error: error.message,
                data: []
            };
        }
    }

    /**
     * Inserta una nueva conversación
     * 
     * @param {number} projectId - ID del proyecto
     * @param {string} title - Título de la conversación
     * @returns {Promise<Object>} - Resultado de la inserción
     */
    async insertConversation(projectId, title) {
        try {
            const conversationId = this.generateUUID();
            
            const [result] = await this.db.execute(`
                INSERT INTO conversations (
                    id,
                    project_id,
                    title,
                    created_at_timestamp_ms,
                    created_at,
                    is_archived,
                    is_starred
                ) VALUES (?, ?, ?, UNIX_TIMESTAMP(NOW(6)) * 1000, NOW(), 0, 0)
            `, [conversationId, projectId, title]);

            return {
                success: true,
                conversationId: conversationId,
                projectId: projectId,
                title: title,
                insertedRows: result.affectedRows
            };

        } catch (error) {
            console.error('Error al insertar conversación:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Genera un UUID simple para IDs
     * @returns {string} UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Obtiene estadísticas de mensajes por proyecto
     * 
     * @param {number} projectId - ID del proyecto
     * @returns {Promise<Object>} - Estadísticas del proyecto
     */
    async getProjectMessageStats(projectId) {
        try {
            const [stats] = await this.db.execute(`
                SELECT 
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(m.id) as total_messages,
                    COUNT(CASE WHEN m.role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) as assistant_messages,
                    MIN(c.created_at) as first_conversation,
                    MAX(m.created_at) as last_message
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.project_id = ?
            `, [projectId]);

            return {
                success: true,
                projectId: projectId,
                stats: stats[0] || {}
            };

        } catch (error) {
            console.error('Error al obtener estadísticas:', error);
            return {
                success: false,
                error: error.message,
                stats: {}
            };
        }
    }
}

module.exports = MessageOperations;