/**
 * API ENDPOINTS PARA EL MÓDULO DE MENSAJES Y CONVERSACIONES
 * 
 * Endpoints para alimentar el reporte "Buscar Mensajes en Chat" y operaciones relacionadas
 * Usa el módulo MessageOperations corregido y alineado con OpenAI API
 */

const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
const MessageOperations = require('../database/message_operations');
require('dotenv').config();

const app = express();
const PORT = process.env.API_PORT || 3001;

// Middleware
app.use(express.json());
app.use(cors());
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Pool de conexiones para mejor performance
const connectionPool = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_DATABASE,
    timezone: '+00:00',
    charset: 'utf8mb4',
    connectionLimit: 10,
    queueLimit: 0
});

/**
 * GET /api/projects/:projectId/messages
 * Endpoint principal para el reporte "Buscar Mensajes en Chat"
 */
app.get('/api/projects/:projectId/messages', async (req, res) => {
    try {
        const projectId = parseInt(req.params.projectId);
        const { 
            search = '', 
            role = '', 
            limit = 100, 
            offset = 0,
            orderBy = 'created_at',
            orderDirection = 'DESC'
        } = req.query;

        if (isNaN(projectId)) {
            return res.status(400).json({
                success: false,
                error: 'Project ID must be a valid number'
            });
        }

        const connection = await connectionPool.getConnection();
        const messageOps = new MessageOperations(connection);

        try {
            // Obtener mensajes con filtros
            let result;
            if (search || role) {
                result = await getFilteredMessages(connection, projectId, {
                    search, role, limit, offset, orderBy, orderDirection
                });
            } else {
                result = await messageOps.getMessagesForReport(projectId);
                
                // Aplicar paginación si no hay filtros complejos
                if (result.success && result.data.length > 0) {
                    const startIndex = parseInt(offset);
                    const endIndex = startIndex + parseInt(limit);
                    result.data = result.data.slice(startIndex, endIndex);
                }
            }

            if (result.success) {
                res.json({
                    success: true,
                    data: result.data,
                    totalMessages: result.totalMessages || result.data.length,
                    projectId: projectId,
                    filters: { search, role, limit, offset, orderBy, orderDirection },
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: result.error,
                    projectId: projectId
                });
            }

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en /api/projects/:projectId/messages:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * GET /api/conversations/:conversationId/messages
 * Obtener mensajes de una conversación específica
 */
app.get('/api/conversations/:conversationId/messages', async (req, res) => {
    try {
        const { conversationId } = req.params;
        const connection = await connectionPool.getConnection();
        const messageOps = new MessageOperations(connection);

        try {
            const result = await messageOps.getMessagesByConversation(conversationId);

            if (result.success) {
                res.json({
                    success: true,
                    data: result.data,
                    conversationId: conversationId,
                    totalMessages: result.totalMessages,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(404).json({
                    success: false,
                    error: result.error,
                    conversationId: conversationId
                });
            }

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en /api/conversations/:conversationId/messages:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * POST /api/conversations/:conversationId/messages
 * Insertar un nuevo mensaje en una conversación
 */
app.post('/api/conversations/:conversationId/messages', async (req, res) => {
    try {
        const { conversationId } = req.params;
        const { role, content } = req.body;

        // Validaciones
        if (!role || !content) {
            return res.status(400).json({
                success: false,
                error: 'Role and content are required',
                required: ['role', 'content']
            });
        }

        if (!['user', 'assistant', 'system', 'tool'].includes(role)) {
            return res.status(400).json({
                success: false,
                error: 'Invalid role. Must be one of: user, assistant, system, tool'
            });
        }

        const connection = await connectionPool.getConnection();
        const messageOps = new MessageOperations(connection);

        try {
            const result = await messageOps.insertMessage(conversationId, role, content);

            if (result.success) {
                res.status(201).json({
                    success: true,
                    messageId: result.messageId,
                    conversationId: conversationId,
                    role: role,
                    content: content,
                    message: 'Message inserted successfully',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({
                    success: false,
                    error: result.error,
                    conversationId: conversationId
                });
            }

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en POST /api/conversations/:conversationId/messages:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * POST /api/projects/:projectId/conversations
 * Crear una nueva conversación
 */
app.post('/api/projects/:projectId/conversations', async (req, res) => {
    try {
        const projectId = parseInt(req.params.projectId);
        const { title } = req.body;

        if (isNaN(projectId) || !title) {
            return res.status(400).json({
                success: false,
                error: 'Project ID and title are required'
            });
        }

        const connection = await connectionPool.getConnection();
        const messageOps = new MessageOperations(connection);

        try {
            const result = await messageOps.insertConversation(projectId, title);

            if (result.success) {
                res.status(201).json({
                    success: true,
                    conversationId: result.conversationId,
                    projectId: projectId,
                    title: title,
                    message: 'Conversation created successfully',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({
                    success: false,
                    error: result.error,
                    projectId: projectId
                });
            }

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en POST /api/projects/:projectId/conversations:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * GET /api/projects/:projectId/stats
 * Obtener estadísticas del proyecto
 */
app.get('/api/projects/:projectId/stats', async (req, res) => {
    try {
        const projectId = parseInt(req.params.projectId);

        if (isNaN(projectId)) {
            return res.status(400).json({
                success: false,
                error: 'Project ID must be a valid number'
            });
        }

        const connection = await connectionPool.getConnection();
        const messageOps = new MessageOperations(connection);

        try {
            const result = await messageOps.getProjectMessageStats(projectId);

            if (result.success) {
                res.json({
                    success: true,
                    projectId: projectId,
                    stats: result.stats,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: result.error,
                    projectId: projectId
                });
            }

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en /api/projects/:projectId/stats:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * GET /api/projects
 * Listar todos los proyectos
 */
app.get('/api/projects', async (req, res) => {
    try {
        const connection = await connectionPool.getConnection();

        try {
            const [projects] = await connection.execute(`
                SELECT p.id, p.name, p.description, p.created_at, p.is_starred,
                       COUNT(DISTINCT c.id) as conversation_count,
                       COUNT(m.id) as message_count,
                       MAX(m.created_at) as last_activity
                FROM projects p
                LEFT JOIN conversations c ON p.id = c.project_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY p.id
                ORDER BY p.created_at DESC
            `);

            res.json({
                success: true,
                data: projects,
                totalProjects: projects.length,
                timestamp: new Date().toISOString()
            });

        } finally {
            connection.release();
        }

    } catch (error) {
        console.error('Error en /api/projects:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            details: error.message
        });
    }
});

/**
 * GET /api/health
 * Health check endpoint
 */
app.get('/api/health', async (req, res) => {
    try {
        const connection = await connectionPool.getConnection();
        
        try {
            await connection.execute('SELECT 1');
            res.json({
                success: true,
                status: 'healthy',
                database: 'connected',
                timestamp: new Date().toISOString(),
                version: '1.0.0'
            });
        } finally {
            connection.release();
        }

    } catch (error) {
        res.status(503).json({
            success: false,
            status: 'unhealthy',
            database: 'disconnected',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// Función auxiliar para búsquedas con filtros
async function getFilteredMessages(connection, projectId, filters) {
    try {
        const { search, role, limit, offset, orderBy, orderDirection } = filters;
        
        let whereConditions = ['c.project_id = ?'];
        let queryParams = [projectId];
        
        if (search) {
            whereConditions.push('(m.content LIKE ? OR c.title LIKE ?)');
            queryParams.push(`%${search}%`, `%${search}%`);
        }
        
        if (role) {
            whereConditions.push('m.role = ?');
            queryParams.push(role);
        }
        
        const whereClause = whereConditions.join(' AND ');
        const orderClause = `ORDER BY m.${orderBy} ${orderDirection}`;
        const limitClause = `LIMIT ${parseInt(limit)} OFFSET ${parseInt(offset)}`;
        
        const [rows] = await connection.execute(`
            SELECT 
                c.id as conversation_id,
                c.title as conversation_title,
                c.project_id,
                m.id as message_id,
                m.role as message_role,
                m.content as message_content,
                m.created_at as message_created_at,
                m.created_at_timestamp_ms as message_timestamp,
                m.author_name,
                m.status as message_status
            FROM conversations c
            INNER JOIN messages m ON c.id = m.conversation_id
            WHERE ${whereClause}
            ${orderClause}
            ${limitClause}
        `, queryParams);

        // Contar total para paginación
        const [countResult] = await connection.execute(`
            SELECT COUNT(*) as total
            FROM conversations c
            INNER JOIN messages m ON c.id = m.conversation_id
            WHERE ${whereClause}
        `, queryParams);

        const formattedData = rows.map(row => ({
            conversationId: row.conversation_id,
            conversationTitle: row.conversation_title,
            projectId: row.project_id,
            messageId: row.message_id,
            messageRole: row.message_role,
            messageContent: row.message_content,
            messageCreatedAt: row.message_created_at,
            messageTimestamp: row.message_timestamp,
            authorName: row.author_name,
            messageStatus: row.message_status
        }));

        return {
            success: true,
            data: formattedData,
            totalMessages: countResult[0].total
        };

    } catch (error) {
        console.error('Error in getFilteredMessages:', error);
        return {
            success: false,
            error: error.message,
            data: []
        };
    }
}

// Error handler global
app.use((error, req, res, next) => {
    console.error('Error global:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString()
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found',
        availableEndpoints: [
            'GET /api/projects',
            'GET /api/projects/:projectId/messages',
            'GET /api/projects/:projectId/stats',
            'GET /api/conversations/:conversationId/messages',
            'POST /api/conversations/:conversationId/messages',
            'POST /api/projects/:projectId/conversations',
            'GET /api/health'
        ],
        timestamp: new Date().toISOString()
    });
});

// Iniciar servidor
const server = app.listen(PORT, () => {
    console.log(`🚀 API Server iniciado en puerto ${PORT}`);
    console.log(`📊 Endpoints disponibles:`);
    console.log(`   GET  /api/health - Health check`);
    console.log(`   GET  /api/projects - Lista de proyectos`);
    console.log(`   GET  /api/projects/:id/messages - Mensajes para reporte`);
    console.log(`   GET  /api/projects/:id/stats - Estadísticas del proyecto`);
    console.log(`   GET  /api/conversations/:id/messages - Mensajes de conversación`);
    console.log(`   POST /api/conversations/:id/messages - Insertar mensaje`);
    console.log(`   POST /api/projects/:id/conversations - Crear conversación`);
    console.log(`\n✅ Servidor listo para recibir peticiones`);
});

// Manejo de cierre graceful
process.on('SIGTERM', () => {
    console.log('🔄 Cerrando servidor gracefully...');
    server.close(() => {
        connectionPool.end();
        console.log('✅ Servidor cerrado');
        process.exit(0);
    });
});

module.exports = app;