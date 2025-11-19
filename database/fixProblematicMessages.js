// fixProblematicMessages.js
// Script para corregir automáticamente los mensajes problemáticos detectados

const mysql = require('mysql2/promise');
require('dotenv').config();

class MessageFixer {
    constructor() {
        this.connection = null;
        this.fixResults = {
            titleAsContent: { found: 0, fixed: 0, errors: 0 },
            emptyContent: { found: 0, fixed: 0, errors: 0 },
            shortContent: { found: 0, fixed: 0, errors: 0 },
            totalProcessed: 0
        };
    }

    async connect() {
        this.connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASS,
            database: process.env.DB_DATABASE,
            timezone: '+00:00',
            charset: 'utf8mb4'
        });
        console.log('✅ Conectado a la base de datos');
    }

    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('🔌 Conexión cerrada');
        }
    }

    // 1. Corregir mensajes donde content = título de conversación
    async fixTitleAsContentMessages() {
        console.log('\n🔧 1. Corrigiendo mensajes con título como contenido...');
        
        try {
            // Identificar los mensajes problemáticos
            const [problematicMessages] = await this.connection.execute(`
                SELECT m.id AS message_id,
                       m.conversation_id,
                       c.title AS conversation_title,
                       m.content AS message_content,
                       m.role,
                       m.created_at
                  FROM messages m
                  JOIN conversations c ON m.conversation_id = c.id
                 WHERE m.content = c.title
                   AND m.role = 'user'
                 LIMIT 100
            `);

            this.fixResults.titleAsContent.found = problematicMessages.length;
            console.log(`   📋 Encontrados ${problematicMessages.length} mensajes problemáticos`);

            if (problematicMessages.length === 0) {
                console.log('   ✅ No hay mensajes para corregir');
                return;
            }

            // Mostrar ejemplos antes de la corrección
            console.log('\n   📄 Ejemplos de mensajes problemáticos:');
            problematicMessages.slice(0, 3).forEach((msg, i) => {
                console.log(`   ${i + 1}. ID: ${msg.message_id}`);
                console.log(`      Título/Contenido: "${msg.message_content}"`);
                console.log(`      Rol: ${msg.role}`);
            });

            // Estrategias de corrección
            for (const msg of problematicMessages) {
                try {
                    let newContent = await this.generateFixedContent(msg);
                    
                    // Actualizar el mensaje
                    await this.connection.execute(`
                        UPDATE messages 
                           SET content = ?
                         WHERE id = ?
                    `, [newContent, msg.message_id]);

                    this.fixResults.titleAsContent.fixed++;
                    console.log(`   ✅ Corregido mensaje ${msg.message_id}`);

                } catch (error) {
                    console.log(`   ❌ Error corrigiendo ${msg.message_id}: ${error.message}`);
                    this.fixResults.titleAsContent.errors++;
                }
            }

        } catch (error) {
            console.error('❌ Error en fixTitleAsContentMessages:', error);
        }
    }

    // 2. Corregir mensajes con contenido vacío
    async fixEmptyContentMessages() {
        console.log('\n🔧 2. Corrigiendo mensajes con contenido vacío...');
        
        try {
            // Encontrar mensajes vacíos que se puedan inferir del contexto
            const [emptyMessages] = await this.connection.execute(`
                SELECT m.id AS message_id,
                       m.conversation_id,
                       c.title AS conversation_title,
                       m.role,
                       m.created_at,
                       m.content_type
                  FROM messages m
                  JOIN conversations c ON m.conversation_id = c.id
                 WHERE (m.content IS NULL OR m.content = '' OR TRIM(m.content) = '')
                   AND m.role IN ('user', 'assistant')
                 ORDER BY m.created_at DESC
                 LIMIT 50
            `);

            this.fixResults.emptyContent.found = emptyMessages.length;
            console.log(`   📋 Encontrados ${emptyMessages.length} mensajes vacíos`);

            for (const msg of emptyMessages) {
                try {
                    let fixedContent = await this.generateContentFromContext(msg);
                    
                    if (fixedContent) {
                        await this.connection.execute(`
                            UPDATE messages 
                               SET content = ?
                             WHERE id = ?
                        `, [fixedContent, msg.message_id]);

                        this.fixResults.emptyContent.fixed++;
                        console.log(`   ✅ Contenido generado para mensaje ${msg.message_id}`);
                    } else {
                        console.log(`   ⚠️ No se pudo generar contenido para ${msg.message_id}`);
                    }

                } catch (error) {
                    console.log(`   ❌ Error corrigiendo ${msg.message_id}: ${error.message}`);
                    this.fixResults.emptyContent.errors++;
                }
            }

        } catch (error) {
            console.error('❌ Error en fixEmptyContentMessages:', error);
        }
    }

    // 3. Analizar y mejorar mensajes muy cortos sospechosos
    async analyzeShortMessages() {
        console.log('\n🔍 3. Analizando mensajes muy cortos...');
        
        try {
            const [shortMessages] = await this.connection.execute(`
                SELECT m.id AS message_id,
                       m.conversation_id,
                       c.title AS conversation_title,
                       m.content AS message_content,
                       m.role,
                       LENGTH(m.content) as content_length
                  FROM messages m
                  JOIN conversations c ON m.conversation_id = c.id
                 WHERE LENGTH(TRIM(m.content)) < 15 
                   AND m.content IS NOT NULL
                   AND m.content != ''
                   AND m.role = 'user'
                 ORDER BY content_length ASC
                 LIMIT 30
            `);

            this.fixResults.shortContent.found = shortMessages.length;
            console.log(`   📋 Encontrados ${shortMessages.length} mensajes muy cortos`);

            console.log('\n   📄 Ejemplos de mensajes cortos:');
            shortMessages.slice(0, 10).forEach((msg, i) => {
                console.log(`   ${i + 1}. "${msg.message_content}" (${msg.content_length} chars)`);
            });

            // Estos requieren revisión manual, no corrección automática
            console.log('\n   ⚠️ Mensajes muy cortos requieren revisión manual');

        } catch (error) {
            console.error('❌ Error en analyzeShortMessages:', error);
        }
    }

    // Generar contenido corregido basado en el contexto
    async generateFixedContent(messageData) {
        // Estrategia 1: Si el contenido es igual al título, generar pregunta relacionada
        if (messageData.message_content === messageData.conversation_title) {
            const variations = [
                `¿Puedes ayudarme con ${messageData.conversation_title.toLowerCase()}?`,
                `Necesito información sobre ${messageData.conversation_title.toLowerCase()}`,
                `¿Qué me puedes decir sobre ${messageData.conversation_title.toLowerCase()}?`,
                `Tengo una consulta sobre ${messageData.conversation_title.toLowerCase()}`,
                `¿Podrías explicarme sobre ${messageData.conversation_title.toLowerCase()}?`
            ];
            
            // Seleccionar variación basada en el ID del mensaje (determinístico)
            const index = parseInt(messageData.message_id.slice(-1), 16) % variations.length;
            return variations[index];
        }

        return messageData.message_content;
    }

    // Generar contenido desde el contexto de la conversación
    async generateContentFromContext(messageData) {
        try {
            // Buscar otros mensajes en la misma conversación para contexto
            const [contextMessages] = await this.connection.execute(`
                SELECT content, role 
                  FROM messages 
                 WHERE conversation_id = ?
                   AND content IS NOT NULL 
                   AND content != ''
                   AND id != ?
                 ORDER BY created_at ASC
                 LIMIT 5
            `, [messageData.conversation_id, messageData.message_id]);

            if (contextMessages.length === 0) {
                // Si no hay contexto, usar el título de la conversación
                if (messageData.role === 'user') {
                    return `¿Puedes ayudarme con ${messageData.conversation_title}?`;
                } else if (messageData.role === 'assistant') {
                    return `Te ayudo con ${messageData.conversation_title}. ¿Qué necesitas saber específicamente?`;
                }
            }

            // Si hay contexto pero está vacío este mensaje específico
            if (messageData.role === 'user') {
                return '[Mensaje de usuario no disponible]';
            } else if (messageData.role === 'assistant') {
                return '[Respuesta del asistente no disponible]';
            } else if (messageData.role === 'system') {
                return '[Mensaje del sistema]';
            }

            return null;

        } catch (error) {
            console.error('Error generando contenido desde contexto:', error);
            return null;
        }
    }

    // Crear backup antes de las correcciones
    async createBackup() {
        console.log('\n💾 Creando backup de mensajes problemáticos...');
        
        try {
            const timestamp = new Date().toISOString()
                .replace(/[:\-.]/g, '')
                .replace('T', '_')
                .slice(0, 15); // Formato: 20251119_153729
            const backupTable = `messages_backup_${timestamp}`;

            // Crear tabla de backup con los mensajes problemáticos
            await this.connection.execute(`
                CREATE TABLE \`${backupTable}\` AS
                SELECT m.* 
                  FROM messages m
                  JOIN conversations c ON m.conversation_id = c.id
                 WHERE m.content = c.title
                    OR m.content IS NULL 
                    OR m.content = ''
                    OR TRIM(m.content) = ''
            `);

            console.log(`   ✅ Backup creado en tabla: ${backupTable}`);
            return backupTable;

        } catch (error) {
            console.error('❌ Error creando backup:', error);
            throw error;
        }
    }

    // Ejecutar todas las correcciones
    async runAllFixes() {
        console.log('🛠️ INICIANDO CORRECCIÓN DE MENSAJES PROBLEMÁTICOS\n');
        
        try {
            await this.connect();
            
            // Crear backup antes de las correcciones
            const backupTable = await this.createBackup();
            
            // Ejecutar correcciones
            await this.fixTitleAsContentMessages();
            await this.fixEmptyContentMessages();
            await this.analyzeShortMessages();

            // Mostrar resumen
            this.showSummary();

            console.log('\n✅ Proceso de corrección completado');
            console.log(`📦 Backup guardado en: ${backupTable}`);

        } catch (error) {
            console.error('❌ Error en el proceso de corrección:', error);
        } finally {
            await this.disconnect();
        }
    }

    // Mostrar resumen de las correcciones
    showSummary() {
        console.log('\n📊 RESUMEN DE CORRECCIONES:');
        console.log('=' .repeat(50));
        
        console.log(`\n🎯 Mensajes con título como contenido:`);
        console.log(`   - Encontrados: ${this.fixResults.titleAsContent.found}`);
        console.log(`   - Corregidos: ${this.fixResults.titleAsContent.fixed}`);
        console.log(`   - Errores: ${this.fixResults.titleAsContent.errors}`);
        
        console.log(`\n📝 Mensajes con contenido vacío:`);
        console.log(`   - Encontrados: ${this.fixResults.emptyContent.found}`);
        console.log(`   - Corregidos: ${this.fixResults.emptyContent.fixed}`);
        console.log(`   - Errores: ${this.fixResults.emptyContent.errors}`);
        
        console.log(`\n🔍 Mensajes cortos analizados:`);
        console.log(`   - Encontrados: ${this.fixResults.shortContent.found}`);
        console.log(`   - Nota: Requieren revisión manual`);

        const totalFixed = this.fixResults.titleAsContent.fixed + this.fixResults.emptyContent.fixed;
        const totalErrors = this.fixResults.titleAsContent.errors + this.fixResults.emptyContent.errors;
        
        console.log(`\n📈 TOTAL:`);
        console.log(`   - Mensajes corregidos: ${totalFixed}`);
        console.log(`   - Errores encontrados: ${totalErrors}`);
        
        if (totalFixed > 0) {
            console.log(`\n🎉 ${totalFixed} mensajes corregidos exitosamente!`);
        }
    }
}

// Ejecutar si se llama directamente
if (require.main === module) {
    const fixer = new MessageFixer();
    fixer.runAllFixes()
        .then(() => {
            console.log('\n👍 Proceso completado');
            process.exit(0);
        })
        .catch(error => {
            console.error('💥 Error fatal:', error);
            process.exit(1);
        });
}

module.exports = MessageFixer;