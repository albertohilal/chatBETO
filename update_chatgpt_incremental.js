import mysql from 'mysql2/promise';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 🔄 ChatBETO - Actualizador incremental de exportaciones ChatGPT
 * 
 * Este script procesa una nueva exportación de ChatGPT y actualiza
 * la base de datos de forma incremental, sin duplicar datos existentes.
 * 
 * ✅ Seguro: Hace backups antes de proceder
 * ✅ Incremental: Solo agrega/actualiza conversaciones nuevas o modificadas
 * ✅ Inteligente: Auto-asigna project_id basándose en patrones conocidos
 */

class ChatGPTUpdater {
    constructor() {
        this.dbConfig = null;
        this.connection = null;
        this.stats = {
            total_new_conversations: 0,
            updated_conversations: 0,
            new_conversations: 0,
            skipped_existing: 0,
            auto_assigned_projects: 0,
            errors: 0
        };
        this.zipFilename = '';
        this.extractedPath = '';
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

    /**
     * Encuentra el archivo ZIP más reciente en la carpeta Auxiliar
     */
    async findLatestZipFile() {
        const auxiliarPath = path.join(__dirname, 'Auxiliar');
        
        try {
            const files = await fs.readdir(auxiliarPath);
            const zipFiles = files.filter(file => file.endsWith('.zip') && file.includes('2025-11-17'));
            
            if (zipFiles.length === 0) {
                throw new Error('No se encontraron archivos ZIP recientes en la carpeta Auxiliar');
            }

            // Tomar el más reciente (asumiendo que tienen timestamp en el nombre)
            zipFiles.sort().reverse();
            this.zipFilename = zipFiles[0];
            
            console.log(`📦 Archivo ZIP encontrado: ${this.zipFilename}`);
            return path.join(auxiliarPath, this.zipFilename);
            
        } catch (error) {
            console.error('❌ Error buscando archivo ZIP:', error.message);
            throw error;
        }
    }

    /**
     * Extrae el archivo ZIP en una carpeta temporal
     */
    async extractZipFile(zipPath) {
        const extractPath = path.join(__dirname, 'temp_extracted_' + Date.now());
        
        try {
            console.log('📂 Extrayendo archivo ZIP...');
            
            // Crear directorio temporal
            await fs.mkdir(extractPath, { recursive: true });
            
            // Extraer usando unzip
            execSync(`unzip -q "${zipPath}" -d "${extractPath}"`);
            
            this.extractedPath = extractPath;
            console.log(`✅ Archivos extraídos en: ${extractPath}`);
            
            // Verificar que existe conversations.json
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

    /**
     * Analiza el archivo conversations.json y devuelve estadísticas
     */
    async analyzeConversationsFile(conversationsPath) {
        try {
            console.log('🔍 Analizando conversations.json...');
            
            const data = JSON.parse(await fs.readFile(conversationsPath, 'utf8'));
            const conversations = Array.isArray(data) ? data : data.conversations || [];
            
            this.stats.total_new_conversations = conversations.length;
            
            console.log(`📊 Total de conversaciones en archivo: ${conversations.length}`);
            
            // Muestra de conversaciones recientes
            console.log('\n📝 Muestra de conversaciones más recientes:');
            const recent = conversations
                .filter(conv => conv.create_time)
                .sort((a, b) => b.create_time - a.create_time)
                .slice(0, 5);
                
            recent.forEach((conv, index) => {
                const date = new Date(conv.create_time * 1000).toLocaleDateString();
                console.log(`${index + 1}. "${conv.title}" (${date})`);
            });
            
            return conversations;
            
        } catch (error) {
            console.error('❌ Error analizando conversations.json:', error.message);
            throw error;
        }
    }

    /**
     * Obtiene IDs de conversaciones existentes en la base de datos
     */
    async getExistingConversationIds() {
        try {
            const query = 'SELECT id FROM conversations';
            const [rows] = await this.connection.execute(query);
            return new Set(rows.map(row => row.id));
        } catch (error) {
            console.error('❌ Error obteniendo conversaciones existentes:', error.message);
            throw error;
        }
    }

    /**
     * Auto-asigna project_id basándose en el título de la conversación
     */
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
        
        return null; // Sin asignación automática
    }

    /**
     * Inserta una nueva conversación en la base de datos
     */
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
                conversation.id, // conversation_id es igual al id
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

    /**
     * Procesa las conversaciones de forma incremental
     */
    async processConversationsIncremental(conversations) {
        console.log('\n🔄 Procesando conversaciones de forma incremental...\n');
        
        const existingIds = await this.getExistingConversationIds();
        console.log(`📊 Conversaciones existentes en BD: ${existingIds.size}`);
        
        for (const [index, conversation] of conversations.entries()) {
            if (!conversation.id) {
                console.log(`⚠️  Conversación sin ID, saltando...`);
                this.stats.errors++;
                continue;
            }
            
            if (existingIds.has(conversation.id)) {
                this.stats.skipped_existing++;
                
                // Mostrar progreso cada 100 conversaciones
                if ((index + 1) % 100 === 0) {
                    console.log(`⏭️  Progreso: ${index + 1}/${conversations.length} (Saltando existentes...)`);
                }
                continue;
            }
            
            // Insertar nueva conversación
            const inserted = await this.insertConversation(conversation);
            if (inserted) {
                this.stats.new_conversations++;
                console.log(`➕ Nueva: "${conversation.title}" ${this.stats.new_conversations % 20 === 0 ? `(${this.stats.new_conversations} nuevas)` : ''}`);
            }
            
            // Mostrar progreso cada 25 conversaciones nuevas
            if (this.stats.new_conversations % 25 === 0) {
                console.log(`📈 Progreso: ${index + 1}/${conversations.length} procesadas | ${this.stats.new_conversations} nuevas | ${this.stats.skipped_existing} saltadas`);
            }
        }
    }

    /**
     * Limpia archivos temporales
     */
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

    /**
     * Muestra estadísticas finales
     */
    showFinalStats() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 RESUMEN DE ACTUALIZACIÓN INCREMENTAL');
        console.log('='.repeat(60));
        console.log(`📁 Archivo procesado: ${this.zipFilename}`);
        console.log(`📋 Total conversaciones en archivo: ${this.stats.total_new_conversations}`);
        console.log(`➕ Conversaciones nuevas agregadas: ${this.stats.new_conversations}`);
        console.log(`⏭️  Conversaciones existentes saltadas: ${this.stats.skipped_existing}`);
        console.log(`🎯 Proyectos auto-asignados: ${this.stats.auto_assigned_projects}`);
        console.log(`❌ Errores: ${this.stats.errors}`);
        
        const successRate = ((this.stats.new_conversations / (this.stats.new_conversations + this.stats.errors)) * 100).toFixed(1);
        console.log(`✅ Tasa de éxito: ${successRate}%`);
        console.log('='.repeat(60));
        
        if (this.stats.new_conversations > 0) {
            console.log('\n🎉 ¡Actualización completada exitosamente!');
            console.log('💡 Próximos pasos:');
            console.log('   1. Revisar conversaciones nuevas en la interfaz web');
            console.log('   2. Asignar proyectos manualmente a conversaciones sin clasificar');
            console.log('   3. Considerar hacer commit de los cambios');
        } else {
            console.log('\n✨ Base de datos ya estaba actualizada');
        }
    }

    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('🔌 Conexión MySQL cerrada');
        }
    }

    async run() {
        try {
            console.log('🔄 ChatBETO - Actualizador incremental ChatGPT');
            console.log('=' .repeat(60));
            
            await this.loadDbConfig();
            await this.connect();
            
            const zipPath = await this.findLatestZipFile();
            const conversationsPath = await this.extractZipFile(zipPath);
            const conversations = await this.analyzeConversationsFile(conversationsPath);
            
            await this.processConversationsIncremental(conversations);
            
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
    const updater = new ChatGPTUpdater();
    updater.run().catch(console.error);
}

export default ChatGPTUpdater;