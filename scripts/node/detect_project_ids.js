import mysql from 'mysql2/promise';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 🎯 ChatBETO - Detector automático de project_id
 * 
 * Este script lee las URLs de conversaciones desde la base MySQL,
 * detecta automáticamente el project_id usando patrones regex
 * y actualiza la base de datos SIN hacer scraping web.
 * 
 * ✅ 100% compatible con términos de servicio
 * ✅ Seguro y eficiente  
 * ✅ No requiere autenticación externa
 */

class ProjectIdDetector {
    constructor() {
        this.dbConfig = null;
        this.connection = null;
        this.stats = {
            processed: 0,
            updated: 0,
            errors: 0,
            projects_found: new Set()
        };
    }

    /**
     * Carga la configuración de la base de datos
     */
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

    /**
     * Establece conexión con MySQL
     */
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
     * Encuentra el project_id basándose en el conversation_id y los proyectos conocidos
     */
    findProjectForConversation(conversationId, projects) {
        // Los proyectos conocidos con sus conversation_id patterns
        const knownProjects = {
            '678aca4bde1081918b303cfa0dbe0949': { name: 'VS Code Github', id: null },
            '68881bc5647c8191ba11903043f95ce9': { name: 'ChatBeto', id: null },
            '67bb710a9e348191bde6345e3c43f16d': { name: 'Xubuntu', id: null },
            '689a08ad26488191965825aff4f517fe': { name: 'Fiverr-Alejandro', id: null },
            '680ce62f83148191b2dca207e85e0e99': { name: 'ChatGPT', id: null },
            '6884f2e91d40819197318fa3ae3ef1f3': { name: 'Galaxy S7 FE', id: null },
            '67eba26c610881918650a47d2f907173': { name: 'Medios Audiovisuales', id: null },
            '67ab14a8231c819181c69d9472e718a0': { name: 'Profesor Proyectual UNA', id: null },
            '6853e990af508191adb81fa2be23ca08': { name: 'Contabo', id: null },
            '681b4c1d7c50819193aa3bbebfac1669': { name: 'Lenguaje Visual', id: null }
        };

        // Buscar en proyectos de BD por nombre
        for (const project of projects) {
            for (const [projectId, projectInfo] of Object.entries(knownProjects)) {
                if (project.name === projectInfo.name || project.chatgpt_project_id === projectId) {
                    return project.id; // ID numérico de la tabla projects
                }
            }
        }

        return null;
    }

    /**
     * Obtiene todas las conversaciones y proyectos para matching
     */
    async getDataForMatching() {
        // Obtener conversaciones
        const convQuery = `
            SELECT id, title, conversation_id, project_id 
            FROM conversations 
            WHERE conversation_id IS NOT NULL 
            ORDER BY id
        `;
        
        // Obtener proyectos conocidos
        const projQuery = `
            SELECT id, name, chatgpt_project_id 
            FROM projects 
            WHERE chatgpt_project_id IS NOT NULL
        `;
        
        try {
            const [conversations] = await this.connection.execute(convQuery);
            const [projects] = await this.connection.execute(projQuery);
            
            console.log(`📊 Conversaciones: ${conversations.length}, Proyectos: ${projects.length}`);
            return { conversations, projects };
        } catch (error) {
            console.error('❌ Error obteniendo datos:', error.message);
            throw error;
        }
    }

    /**
     * Crea proyectos faltantes automáticamente
     */
    async createMissingProjects() {
        const knownProjects = [
            { name: 'VS Code Github', chatgpt_project_id: '678aca4bde1081918b303cfa0dbe0949' },
            { name: 'ChatBeto', chatgpt_project_id: '68881bc5647c8191ba11903043f95ce9' },
            { name: 'Xubuntu', chatgpt_project_id: '67bb710a9e348191bde6345e3c43f16d' },
            { name: 'Fiverr-Alejandro', chatgpt_project_id: '689a08ad26488191965825aff4f517fe' },
            { name: 'ChatGPT', chatgpt_project_id: '680ce62f83148191b2dca207e85e0e99' },
            { name: 'Galaxy S7 FE', chatgpt_project_id: '6884f2e91d40819197318fa3ae3ef1f3' },
            { name: 'Medios Audiovisuales', chatgpt_project_id: '67eba26c610881918650a47d2f907173' },
            { name: 'Profesor Proyectual UNA', chatgpt_project_id: '67ab14a8231c819181c69d9472e718a0' },
            { name: 'Contabo', chatgpt_project_id: '6853e990af508191adb81fa2be23ca08' },
            { name: 'Lenguaje Visual', chatgpt_project_id: '681b4c1d7c50819193aa3bbebfac1669' }
        ];

        console.log('\n🔧 Verificando proyectos faltantes...');

        for (const project of knownProjects) {
            const checkQuery = `SELECT id FROM projects WHERE name = ? OR chatgpt_project_id = ?`;
            const [existing] = await this.connection.execute(checkQuery, [project.name, project.chatgpt_project_id]);

            if (existing.length === 0) {
                const insertQuery = `
                    INSERT INTO projects (name, description, chatgpt_project_id) 
                    VALUES (?, ?, ?)
                `;
                await this.connection.execute(insertQuery, [
                    project.name,
                    `Proyecto GPT personalizado: ${project.name}`,
                    project.chatgpt_project_id
                ]);
                console.log(`➕ Creado proyecto: ${project.name}`);
            }
        }
    }

    /**
     * Actualiza el project_id de una conversación específica
     */
    async updateConversationProject(conversationId, projectId) {
        const query = `
            UPDATE conversations 
            SET project_id = ?
            WHERE id = ?
        `;
        
        try {
            const [result] = await this.connection.execute(query, [projectId, conversationId]);
            return result.affectedRows > 0;
        } catch (error) {
            console.error(`❌ Error actualizando conversación ${conversationId}:`, error.message);
            return false;
        }
    }

    /**
     * Procesa todas las conversaciones y actualiza los project_id
     */
    async processConversations() {
        console.log('\n🚀 Iniciando procesamiento de conversaciones...\n');
        
        const { conversations, projects } = await this.getDataForMatching();
        
        for (const conv of conversations) {
            this.stats.processed++;
            
            // Buscar project_id basándose en conversation_id y proyectos conocidos
            const foundProjectId = this.findProjectForConversation(conv.conversation_id, projects);
            
            if (foundProjectId) {
                // Solo actualizar si el project_id es diferente
                if (conv.project_id !== foundProjectId) {
                    const updated = await this.updateConversationProject(conv.id, foundProjectId);
                    
                    if (updated) {
                        this.stats.updated++;
                        this.stats.projects_found.add(foundProjectId);
                        
                        const projectName = projects.find(p => p.id === foundProjectId)?.name || 'Desconocido';
                        console.log(`✅ Actualizada: "${conv.title}" → Proyecto: ${projectName} (ID: ${foundProjectId})`);
                    } else {
                        this.stats.errors++;
                        console.log(`❌ Error actualizando: "${conv.title}"`);
                    }
                } else {
                    const projectName = projects.find(p => p.id === foundProjectId)?.name || 'Desconocido';
                    console.log(`⏭️  Sin cambios: "${conv.title}" → ${projectName} (ya asignado)`);
                }
            } else {
                console.log(`⚠️  Sin proyecto detectado: "${conv.title}" (${conv.conversation_id})`);
            }
            
            // Mostrar progreso cada 25 conversaciones
            if (this.stats.processed % 25 === 0) {
                console.log(`📈 Progreso: ${this.stats.processed}/${conversations.length} procesadas`);
            }
        }
    }

    /**
     * Muestra estadísticas finales
     */
    showFinalStats() {
        console.log('\n' + '='.repeat(50));
        console.log('📊 ESTADÍSTICAS FINALES');
        console.log('='.repeat(50));
        console.log(`📋 Conversaciones procesadas: ${this.stats.processed}`);
        console.log(`✅ Conversaciones actualizadas: ${this.stats.updated}`);
        console.log(`❌ Errores: ${this.stats.errors}`);
        console.log(`🎯 Proyectos únicos encontrados: ${this.stats.projects_found.size}`);
        
        if (this.stats.projects_found.size > 0) {
            console.log('\n🔗 Project IDs encontrados:');
            Array.from(this.stats.projects_found).forEach((projectId, index) => {
                console.log(`${String(index + 1).padStart(2, ' ')}. ${projectId}`);
            });
        }
        console.log('='.repeat(50));
    }

    /**
     * Cierra la conexión a la base de datos
     */
    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('🔌 Conexión MySQL cerrada');
        }
    }

    /**
     * Ejecuta todo el proceso
     */
    async run() {
        try {
            console.log('🎯 ChatBETO - Detector automático de project_id');
            console.log('=' .repeat(50));
            
            await this.loadDbConfig();
            await this.connect();
            await this.createMissingProjects();
            await this.processConversations();
            this.showFinalStats();
            
        } catch (error) {
            console.error('💥 Error crítico:', error.message);
            process.exit(1);
        } finally {
            await this.disconnect();
        }
    }
}

// Ejecutar el script
if (import.meta.url === `file://${process.argv[1]}`) {
    const detector = new ProjectIdDetector();
    detector.run().catch(console.error);
}

export default ProjectIdDetector;