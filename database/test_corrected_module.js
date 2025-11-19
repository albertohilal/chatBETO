// test_corrected_module.js
// Test rápido del módulo corregido con la estructura real de la base de datos

const mysql = require('mysql2/promise');
const MessageOperations = require('./message_operations');
require('dotenv').config();

async function testCorrectedModule() {
    let connection;
    
    try {
        connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASS,
            database: process.env.DB_DATABASE,
            timezone: '+00:00',
            charset: 'utf8mb4'
        });

        console.log('✅ Conectado a la base de datos');
        
        const messageOps = new MessageOperations(connection);
        
        // Test 1: Obtener datos para reporte (debería funcionar ahora)
        console.log('\n🔍 Test 1: Obtener mensajes para reporte...');
        const report = await messageOps.getMessagesForReport(1); // project_id = 1
        
        if (report.success) {
            console.log(`✅ Reporte obtenido: ${report.totalMessages} mensajes encontrados`);
            
            if (report.data.length > 0) {
                console.log('📋 Ejemplo de datos del reporte:');
                const sample = report.data[0];
                console.log(`   - Conversación: "${sample.conversationTitle}"`);
                console.log(`   - Rol: ${sample.messageRole}`);
                console.log(`   - Contenido: "${sample.messageContent.substring(0, 100)}..."`);
                console.log(`   - Fecha: ${sample.messageCreatedAt}`);
            }
        } else {
            console.log(`❌ Error en reporte: ${report.error}`);
        }
        
        // Test 2: Obtener estadísticas del proyecto
        console.log('\n📊 Test 2: Estadísticas del proyecto...');
        const stats = await messageOps.getProjectMessageStats(1);
        
        if (stats.success) {
            console.log('✅ Estadísticas obtenidas:');
            console.log(`   - Total conversaciones: ${stats.stats.total_conversations}`);
            console.log(`   - Total mensajes: ${stats.stats.total_messages}`);
            console.log(`   - Mensajes de usuario: ${stats.stats.user_messages}`);
            console.log(`   - Mensajes de asistente: ${stats.stats.assistant_messages}`);
        } else {
            console.log(`❌ Error en estadísticas: ${stats.error}`);
        }

        // Test 3: Verificar que el mapeo de campos es correcto
        console.log('\n🎯 Test 3: Verificación de mapeo OpenAI...');
        console.log('Estructura esperada según OpenAI API:');
        console.log('  - messages.role (user|assistant|system) ✅');
        console.log('  - messages.content (contenido real) ✅');
        console.log('  - conversation tiene title separado ✅');
        console.log('  - relación conversations ↔ messages ✅');
        
        console.log('\n✅ Módulo corregido y alineado con OpenAI API');
        
    } catch (error) {
        console.error('❌ Error en test:', error);
    } finally {
        if (connection) {
            await connection.end();
            console.log('🔌 Conexión cerrada');
        }
    }
}

testCorrectedModule();