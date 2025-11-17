import mysql from 'mysql2/promise';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 🔄 ChatBETO - Importador completo de conversaciones Y mensajes
 * 
 * Este script procesa la exportación de ChatGPT e importa tanto
 * conversaciones como todos sus mensajes de forma incremental.
 */

class CompleteImporter {
    constructor() {
        this.dbConfig = null;
        this.connection = null;
        this.stats = {
            conversations_processed: 0,
            conversations_new: 0,
            conversations_existing: 0,
            messages_processed: 0,
            messages_new: 0,
            messages_existing: 0,
            auto_assigned_projects: 0,
            errors: 0
        };
        this.zipFilename = '';
        this.extractedPath = '';
        this.existingConversations = new Set();
        this.existingMessages = new Set();
    }

    async loadDbConfig() {
        try {
            const configPath = path.join(__dirname, 'db_config.json');
            const configData = await fs.readFile(configPath, 'utf8');
            this.dbConfig = JSON.parse(configData);
            console.log('✅ Configuración de BD cargada correctamente');
        } catch (error) {
            console.error('❌ Error cargando db_config.json:', error.message);
            throw error;
        }
    }

    async connect() {
        try {
            this.connection = await mysql.createConnection({
                host: this.dbConfig.host,
                user: this.dbConfig.user,
                password: this.dbConfig.password,
                database: this.dbConfig.database,
                port: this.dbConfig.port || 3306
            });
            console.log('🔗 Conectado a MySQL exitosamente');
        } catch (error) {
            console.error('❌ Error conectando a MySQL:', error.message);
            throw error;
        }
    }

    async findLatestZipFile() {
        const auxiliarPath = path.join(__dirname, 'Auxiliar');
        
        try {
            const files = await fs.readdir(auxiliarPath);
            const zipFiles = files.filter(file => file.endsWith('.zip') && file.includes('2025-11-17'));
            
            if (zipFiles.length === 0) {
                throw new Error('No se encontraron archivos ZIP recientes en la carpeta Auxiliar');
            }

            zipFiles.sort().reverse();
            this.zipFilename = zipFiles[0];
            
            console.log(`📦 Archivo ZIP encontrado: ${this.zipFilename}`);
            return path.join(auxiliarPath, this.zipFilename);
            
        } catch (error) {
            console.error('❌ Error buscando archivo ZIP:', error.message);
            throw error;
        }
    }

    async extractZipFile(zipPath) {
        const extractPath = path.join(__dirname, 'temp_complete_' + Date.now());
        
        try {
            console.log('📂 Extrayendo archivo ZIP...');
            
            await fs.mkdir(extractPath, { recursive: true });
            execSync(`unzip -q "${zipPath}" -d "${extractPath}"`);
            
            this.extractedPath = extractPath;
            console.log(`✅ Archivos extraídos en: ${extractPath}`);
            
            const conversationsPath = path.join(extractPath, 'conversations.json');
            const exists = await fs.access(conversationsPath).then(() => true).catch(() => false);
            
            if (!exists) {
                throw new Error('No se encontró conversations.json en el archivo extraído');
            }
            
            return conversationsPath;
            
        } catch (error) {
            console.error('❌ Error extrayendo ZIP:', error.message);
            throw error;
        }
    }

    async loadExistingData() {
        try {
            // Cargar conversaciones existentes
            const convQuery = 'SELECT id FROM conversations';
            const [convRows] = await this.connection.execute(convQuery);
            this.existingConversations = new Set(convRows.map(row => row.id));
            
            // Cargar mensajes existentes
            const msgQuery = 'SELECT id FROM messages';
            const [msgRows] = await this.connection.execute(msgQuery);
            this.existingMessages = new Set(msgRows.map(row => row.id));
            
            console.log(`📊 Datos existentes: ${this.existingConversations.size} conversaciones, ${this.existingMessages.size} mensajes`);
            
        } catch (error) {
            console.error('❌ Error cargando datos existentes:', error.message);
            throw error;
        }
    }

    async autoAssignProjectId(title) {
        const patterns = {
            'fiverr': 4,        // Fiverr-Alejandro
            'github': 1,        // VS Code Github  
            'xubuntu': 3,       // Xubuntu
            'wordpress': null,  // Buscar en BD
            'processing': null, // Buscar en BD
            'p5.js': null,     // Buscar en BD
            'mysql': null,     // Buscar en BD
            'contabo': 9       // Contabo
        };

        const titleLower = title.toLowerCase();
        
        for (const [keyword, projectId] of Object.entries(patterns)) {
            if (titleLower.includes(keyword)) {
                if (projectId) {
                    return projectId;
                } else {
                    // Buscar proyecto por nombre en BD
                    const query = 'SELECT id FROM projects WHERE name LIKE ? LIMIT 1';
                    const [rows] = await this.connection.execute(query, [`%${keyword}%`]);
                    return rows.length > 0 ? rows[0].id : null;
                }
            }
        }
        
        return null;
    }

    async insertConversation(conversation) {
        try {
            const projectId = await this.autoAssignProjectId(conversation.title || '');
            
            const query = `
                INSERT INTO conversations (
                    id, title, conversation_id, create_time, update_time, 
                    is_archived, is_starred, default_model_slug, project_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;
            
            const values = [
                conversation.id,
                conversation.title || 'Sin título',
                conversation.id,
                conversation.create_time || null,
                conversation.update_time || null,
                conversation.is_archived || 0,
                conversation.is_starred || 0,
                conversation.default_model_slug || null,
                projectId
            ];
            
            await this.connection.execute(query, values);
            
            if (projectId) {
                this.stats.auto_assigned_projects++;
            }
            
            return true;
            
        } catch (error) {
            console.error(`❌ Error insertando conversación ${conversation.id}:`, error.message);
            this.stats.errors++;
            return false;
        }
    }

    async insertMessage(message, conversationId) {
        try {
            // Procesar contenido
            let content = '';
            let parts = '';
            
            if (message.content && message.content.parts) {
                content = message.content.parts.join(' ');
                parts = JSON.stringify(message.content.parts);
            }
            
            const query = `
                INSERT INTO messages (
                    id, conversation_id, parent_message_id, content_type, content_text,
                    author_role, author_name, create_time, status, end_turn, weight, channel, recipient
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;
            
            const values = [
                message.id,
                conversationId,
                message.parent || null,
                message.content?.content_type || 'text',
                content,
                message.author?.role || 'unknown',
                message.author?.name || null,
                message.create_time ? new Date(message.create_time * 1000) : null,
                message.status || 'finished_successfully',
                message.end_turn ? 1 : 0,
                message.weight || 1.0,
                message.channel || null,
                message.recipient || 'all'
            ];
            
            await this.connection.execute(query, values);
            return true;
            
        } catch (error) {
            console.error(`❌ Error insertando mensaje ${message.id}:`, error.message);
            this.stats.errors++;
            return false;
        }
    }

    async processConversationsAndMessages(conversations) {
        console.log('\n🔄 Procesando conversaciones y mensajes...\n');
        
        for (const [index, conversation] of conversations.entries()) {
            this.stats.conversations_processed++;
            
            if (!conversation.id) {
                console.log(`⚠️  Conversación sin ID, saltando...`);
                this.stats.errors++;
                continue;
            }
            
            // Procesar conversación
            let conversationIsNew = false;
            if (!this.existingConversations.has(conversation.id)) {
                const inserted = await this.insertConversation(conversation);
                if (inserted) {
                    this.stats.conversations_new++;
                    conversationIsNew = true;
                    console.log(`➕ Conv: "${conversation.title}"`);
                }
            } else {
                this.stats.conversations_existing++;
            }
            
            // Procesar mensajes de esta conversación
            if (conversation.mapping) {
                for (const [messageId, messageData] of Object.entries(conversation.mapping)) {
                    if (messageData.message && messageData.message.id) {
                        this.stats.messages_processed++;
                        
                        if (!this.existingMessages.has(messageData.message.id)) {
                            const inserted = await this.insertMessage(messageData.message, conversation.id);
                            if (inserted) {
                                this.stats.messages_new++;
                                this.existingMessages.add(messageData.message.id); // Evitar duplicados en el mismo proceso
                            }
                        } else {
                            this.stats.messages_existing++;
                        }
                    }
                }
            }
            
            // Mostrar progreso
            if ((index + 1) % 50 === 0) {
                console.log(`📈 Progreso: ${index + 1}/${conversations.length} | Conv nuevas: ${this.stats.conversations_new} | Msgs nuevos: ${this.stats.messages_new}`);
            }
        }
    }

    async cleanup() {
        if (this.extractedPath) {
            try {
                execSync(`rm -rf "${this.extractedPath}"`);
                console.log('🧹 Archivos temporales eliminados');
            } catch (error) {
                console.warn('⚠️  No se pudieron eliminar archivos temporales:', error.message);
            }
        }
    }

    showFinalStats() {
        console.log('\n' + '='.repeat(70));
        console.log('📊 RESUMEN DE IMPORTACIÓN COMPLETA');
        console.log('='.repeat(70));
        console.log(`📁 Archivo procesado: ${this.zipFilename}`);
        console.log('');
        console.log('CONVERSACIONES:');
        console.log(`📋 Total procesadas: ${this.stats.conversations_processed}`);
        console.log(`➕ Nuevas agregadas: ${this.stats.conversations_new}`);
        console.log(`⏭️  Existentes saltadas: ${this.stats.conversations_existing}`);
        console.log('');
        console.log('MENSAJES:');
        console.log(`📨 Total procesados: ${this.stats.messages_processed}`);
        console.log(`➕ Nuevos agregados: ${this.stats.messages_new}`);
        console.log(`⏭️  Existentes saltados: ${this.stats.messages_existing}`);
        console.log('');
        console.log(`🎯 Proyectos auto-asignados: ${this.stats.auto_assigned_projects}`);
        console.log(`❌ Errores: ${this.stats.errors}`);
        
        const totalNew = this.stats.conversations_new + this.stats.messages_new;
        console.log(`🎉 Total elementos nuevos: ${totalNew}`);
        console.log('='.repeat(70));
    }

    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('🔌 Conexión MySQL cerrada');
        }
    }

    async run() {
        try {
            console.log('🔄 ChatBETO - Importador completo (Conversaciones + Mensajes)');
            console.log('=' .repeat(70));
            
            await this.loadDbConfig();
            await this.connect();
            await this.loadExistingData();
            
            const zipPath = await this.findLatestZipFile();
            const conversationsPath = await this.extractZipFile(zipPath);
            
            const data = JSON.parse(await fs.readFile(conversationsPath, 'utf8'));
            const conversations = Array.isArray(data) ? data : data.conversations || [];
            
            console.log(`📊 Total de conversaciones en archivo: ${conversations.length}`);
            
            await this.processConversationsAndMessages(conversations);
            
            this.showFinalStats();
            
        } catch (error) {
            console.error('💥 Error crítico:', error.message);
            process.exit(1);
        } finally {
            await this.cleanup();
            await this.disconnect();
        }
    }
}

// Ejecutar el script
if (import.meta.url === `file://${process.argv[1]}`) {
    const importer = new CompleteImporter();
    importer.run().catch(console.error);
}

export default CompleteImporter;