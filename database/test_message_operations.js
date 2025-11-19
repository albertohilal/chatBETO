/**
 * TESTS PARA EL MÓDULO DE OPERACIONES DE MENSAJES
 * 
 * Pruebas para validar:
 * - Inserción correcta de mensajes con contenido real
 * - Consultas de reporte con mapeo correcto de campos
 * - Manejo de errores y casos edge
 */

const mysql = require('mysql2/promise');
const MessageOperations = require('./message_operations');

class MessageOperationsTest {
    constructor() {
        this.connection = null;
        this.messageOps = null;
        this.testResults = {
            passed: 0,
            failed: 0,
            total: 0
        };
    }

    async setUp() {
        try {
            this.connection = await mysql.createConnection({
                host: process.env.DB_HOST || 'localhost',
                user: process.env.DB_USER || 'root',
                password: process.env.DB_PASSWORD || '',
                database: process.env.DB_NAME || 'iunaorg_chatBeto',
                charset: 'utf8mb4'
            });

            this.messageOps = new MessageOperations(this.connection);
            console.log('✅ Configuración de pruebas completada');
            return true;
        } catch (error) {
            console.error('❌ Error en configuración:', error);
            return false;
        }
    }

    async tearDown() {
        if (this.connection) {
            await this.connection.end();
            console.log('🔌 Conexión cerrada');
        }
    }

    assert(condition, message) {
        this.testResults.total++;
        if (condition) {
            this.testResults.passed++;
            console.log(`✅ ${message}`);
        } else {
            this.testResults.failed++;
            console.log(`❌ ${message}`);
        }
    }

    async testInsertMessage() {
        console.log('\n--- TEST: Insertar Mensaje ---');
        
        try {
            // Primero crear una conversación de prueba
            const testConversation = await this.messageOps.insertConversation(
                1, 
                "Conversación de prueba para testing"
            );
            
            this.assert(testConversation.success, 'Conversación de prueba creada');
            
            if (testConversation.success) {
                const conversationId = testConversation.conversationId;
                
                // Test 1: Insertar mensaje de usuario
                const userMessage = await this.messageOps.insertMessage(
                    conversationId,
                    'user',
                    'Este es un mensaje de prueba del usuario con contenido real'
                );
                
                this.assert(userMessage.success, 'Mensaje de usuario insertado correctamente');
                this.assert(userMessage.messageId !== undefined, 'ID de mensaje generado');
                this.assert(userMessage.conversationId === conversationId, 'ConversationId correcto');
                
                // Test 2: Insertar mensaje de asistente
                const assistantMessage = await this.messageOps.insertMessage(
                    conversationId,
                    'assistant',
                    'Esta es la respuesta del asistente. Contiene información técnica:\n1. Punto uno\n2. Punto dos\n3. Conclusión'
                );
                
                this.assert(assistantMessage.success, 'Mensaje de asistente insertado correctamente');
                
                // Test 3: Verificar que el contenido se guardó correctamente
                const messages = await this.messageOps.getMessagesByConversation(conversationId);
                this.assert(messages.success, 'Mensajes obtenidos de la conversación');
                this.assert(messages.data.length === 2, 'Cantidad correcta de mensajes');
                
                // Verificar contenido específico
                const userMsg = messages.data.find(m => m.role === 'user');
                const assistantMsg = messages.data.find(m => m.role === 'assistant');
                
                this.assert(
                    userMsg && userMsg.content.includes('contenido real'), 
                    'Contenido del usuario guardado correctamente'
                );
                this.assert(
                    assistantMsg && assistantMsg.content.includes('información técnica'),
                    'Contenido del asistente guardado correctamente'
                );
            }
            
        } catch (error) {
            console.error('Error en testInsertMessage:', error);
            this.assert(false, `Error inesperado: ${error.message}`);
        }
    }

    async testGetMessagesForReport() {
        console.log('\n--- TEST: Obtener Mensajes para Reporte ---');
        
        try {
            // Obtener mensajes del proyecto 1
            const report = await this.messageOps.getMessagesForReport(1);
            
            this.assert(report.success, 'Reporte obtenido correctamente');
            this.assert(Array.isArray(report.data), 'Data es un array');
            this.assert(report.totalMessages >= 0, 'Total de mensajes es un número válido');
            
            if (report.data.length > 0) {
                const firstMessage = report.data[0];
                
                // Verificar estructura de datos del reporte
                this.assert(
                    firstMessage.hasOwnProperty('conversationTitle'),
                    'Campo conversationTitle presente'
                );
                this.assert(
                    firstMessage.hasOwnProperty('messageRole'),
                    'Campo messageRole presente'
                );
                this.assert(
                    firstMessage.hasOwnProperty('messageContent'),
                    'Campo messageContent presente'
                );
                this.assert(
                    firstMessage.hasOwnProperty('messageCreatedAt'),
                    'Campo messageCreatedAt presente'
                );
                
                // Verificar que no se confunden title y content
                this.assert(
                    typeof firstMessage.conversationTitle === 'string',
                    'Título de conversación es string'
                );
                this.assert(
                    typeof firstMessage.messageContent === 'string',
                    'Contenido de mensaje es string'
                );
                this.assert(
                    ['user', 'assistant', 'system'].includes(firstMessage.messageRole),
                    'Rol de mensaje es válido'
                );
            }
            
        } catch (error) {
            console.error('Error en testGetMessagesForReport:', error);
            this.assert(false, `Error inesperado: ${error.message}`);
        }
    }

    async testErrorHandling() {
        console.log('\n--- TEST: Manejo de Errores ---');
        
        try {
            // Test 1: Insertar mensaje en conversación inexistente
            const invalidMessage = await this.messageOps.insertMessage(
                'conversacion-inexistente-123',
                'user',
                'Este mensaje debería fallar'
            );
            
            this.assert(!invalidMessage.success, 'Error detectado para conversación inexistente');
            this.assert(
                invalidMessage.error && invalidMessage.error.includes('no existe'),
                'Mensaje de error apropiado'
            );
            
            // Test 2: Reporte para proyecto inexistente
            const invalidReport = await this.messageOps.getMessagesForReport(99999);
            this.assert(invalidReport.success, 'Reporte para proyecto inexistente no falla');
            this.assert(invalidReport.data.length === 0, 'Data vacía para proyecto inexistente');
            
        } catch (error) {
            console.error('Error en testErrorHandling:', error);
            this.assert(false, `Error inesperado: ${error.message}`);
        }
    }

    async testProjectStats() {
        console.log('\n--- TEST: Estadísticas de Proyecto ---');
        
        try {
            const stats = await this.messageOps.getProjectMessageStats(1);
            
            this.assert(stats.success, 'Estadísticas obtenidas correctamente');
            this.assert(stats.stats.hasOwnProperty('total_conversations'), 'Campo total_conversations presente');
            this.assert(stats.stats.hasOwnProperty('total_messages'), 'Campo total_messages presente');
            this.assert(stats.stats.hasOwnProperty('user_messages'), 'Campo user_messages presente');
            this.assert(stats.stats.hasOwnProperty('assistant_messages'), 'Campo assistant_messages presente');
            
            // Verificar tipos de datos
            this.assert(typeof stats.stats.total_conversations === 'string', 'total_conversations es numérico');
            this.assert(typeof stats.stats.total_messages === 'string', 'total_messages es numérico');
            
        } catch (error) {
            console.error('Error en testProjectStats:', error);
            this.assert(false, `Error inesperado: ${error.message}`);
        }
    }

    async testDataIntegrity() {
        console.log('\n--- TEST: Integridad de Datos ---');
        
        try {
            // Crear conversación y mensaje, luego verificar la relación
            const conversation = await this.messageOps.insertConversation(
                1,
                "Test de integridad de datos"
            );
            
            if (conversation.success) {
                const message = await this.messageOps.insertMessage(
                    conversation.conversationId,
                    'user',
                    'Contenido para verificar integridad de la relación conversations-messages'
                );
                
                this.assert(message.success, 'Mensaje vinculado a conversación');
                
                // Verificar que el mensaje aparece en el reporte
                const report = await this.messageOps.getMessagesForReport(1);
                const foundMessage = report.data.find(
                    m => m.conversationId === conversation.conversationId && 
                         m.messageContent.includes('integridad de la relación')
                );
                
                this.assert(foundMessage !== undefined, 'Mensaje encontrado en reporte');
                this.assert(
                    foundMessage.conversationTitle === "Test de integridad de datos",
                    'Título de conversación correcto en reporte'
                );
            }
            
        } catch (error) {
            console.error('Error en testDataIntegrity:', error);
            this.assert(false, `Error inesperado: ${error.message}`);
        }
    }

    async runAllTests() {
        console.log('🧪 INICIANDO TESTS DE MESSAGE OPERATIONS\n');
        
        const setupSuccess = await this.setUp();
        if (!setupSuccess) {
            console.log('❌ No se pudo configurar el entorno de pruebas');
            return;
        }

        try {
            await this.testInsertMessage();
            await this.testGetMessagesForReport();
            await this.testErrorHandling();
            await this.testProjectStats();
            await this.testDataIntegrity();
        } catch (error) {
            console.error('❌ Error durante las pruebas:', error);
        }

        await this.tearDown();

        console.log('\n📊 RESUMEN DE RESULTADOS:');
        console.log(`Total de pruebas: ${this.testResults.total}`);
        console.log(`Exitosas: ${this.testResults.passed}`);
        console.log(`Fallidas: ${this.testResults.failed}`);
        
        if (this.testResults.failed === 0) {
            console.log('🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE');
        } else {
            console.log(`⚠️ ${this.testResults.failed} pruebas fallaron`);
        }
        
        return this.testResults.failed === 0;
    }
}

// Ejecutar tests si se llama directamente
if (require.main === module) {
    const tester = new MessageOperationsTest();
    tester.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('💥 Error fatal en tests:', error);
            process.exit(1);
        });
}

module.exports = MessageOperationsTest;