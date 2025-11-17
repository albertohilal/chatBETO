import mysql from 'mysql2/promise';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 🎯 ChatBETO - Creador automático de proyectos desde GPTs conocidos
 * 
 * Este script crea automáticamente los proyectos faltantes y después
 * permite matching manual de conversaciones por título/tema.
 */

class ProjectCreator {
    constructor() {
        this.dbConfig = null;
        this.connection = null;
        this.stats = {
            projects_created: 0,
            conversations_updated: 0,
            existing_projects: 0
        };
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

    async createGPTProjects() {
        const knownGPTs = [
            { 
                name: 'VS Code Github', 
                chatgpt_project_id: '678aca4bde1081918b303cfa0dbe0949',
                description: 'GPT especializado en integración de VS Code con GitHub, control de versiones, y desarrollo colaborativo.'
            },
            { 
                name: 'ChatBeto', 
                chatgpt_project_id: '68881bc5647c8191ba11903043f95ce9',
                description: 'Sistema de gestión de conversaciones ChatGPT con base MySQL y análisis de proyectos.'
            },
            { 
                name: 'Xubuntu', 
                chatgpt_project_id: '67bb710a9e348191bde6345e3c43f16d',
                description: 'GPT experto en distribución Xubuntu Linux, configuración del sistema y resolución de problemas.'
            },
            { 
                name: 'Fiverr-Alejandro', 
                chatgpt_project_id: '689a08ad26488191965825aff4f517fe',
                description: 'GPT para asistencia en proyectos de Fiverr, comunicación con clientes y desarrollo freelance.'
            },
            { 
                name: 'ChatGPT', 
                chatgpt_project_id: '680ce62f83148191b2dca207e85e0e99',
                description: 'GPT general para consultas variadas y asistencia técnica general.'
            },
            { 
                name: 'Galaxy S7 FE', 
                chatgpt_project_id: '6884f2e91d40819197318fa3ae3ef1f3',
                description: 'GPT especializado en Samsung Galaxy S7 FE, troubleshooting y optimización del dispositivo.'
            },
            { 
                name: 'Medios Audiovisuales', 
                chatgpt_project_id: '67eba26c610881918650a47d2f907173',
                description: 'GPT experto en producción audiovisual, edición de video, fotografía y medios digitales.'
            },
            { 
                name: 'Profesor Proyectual UNA', 
                chatgpt_project_id: '67ab14a8231c819181c69d9472e718a0',
                description: 'GPT especializado en metodología proyectual, diseño académico y pedagogía universitaria.'
            },
            { 
                name: 'Contabo', 
                chatgpt_project_id: '6853e990af508191adb81fa2be23ca08',
                description: 'GPT para administración de servidores Contabo, hosting y configuración de servicios web.'
            },
            { 
                name: 'Lenguaje Visual', 
                chatgpt_project_id: '681b4c1d7c50819193aa3bbebfac1669',
                description: 'GPT experto en teoría del diseño, lenguaje visual, composición y comunicación gráfica.'
            }
        ];

        console.log('\n🚀 Creando proyectos de GPTs personalizados...\n');

        for (const gpt of knownGPTs) {
            // Verificar si ya existe
            const checkQuery = `SELECT id, name FROM projects WHERE name = ? OR chatgpt_project_id = ?`;
            const [existing] = await this.connection.execute(checkQuery, [gpt.name, gpt.chatgpt_project_id]);

            if (existing.length === 0) {
                // Crear nuevo proyecto
                const insertQuery = `
                    INSERT INTO projects (name, description, chatgpt_project_id, is_starred) 
                    VALUES (?, ?, ?, 1)
                `;
                const [result] = await this.connection.execute(insertQuery, [
                    gpt.name,
                    gpt.description,
                    gpt.chatgpt_project_id
                ]);
                
                this.stats.projects_created++;
                console.log(`➕ Creado: ${gpt.name} (ID: ${result.insertId})`);
            } else {
                this.stats.existing_projects++;
                console.log(`✅ Existe: ${gpt.name} (ID: ${existing[0].id})`);
            }
        }
    }

    async showConversationSamples() {
        console.log('\n📋 Muestra de conversaciones para matching manual:\n');

        // Obtener algunas conversaciones representativas
        const query = `
            SELECT id, title, conversation_id, project_id 
            FROM conversations 
            WHERE project_id IS NULL
            ORDER BY RAND()
            LIMIT 20
        `;

        const [conversations] = await this.connection.execute(query);

        conversations.forEach((conv, index) => {
            console.log(`${String(index + 1).padStart(2, ' ')}. "${conv.title}" (${conv.conversation_id})`);
        });

        console.log(`\n💡 Tienes ${conversations.length > 0 ? 'muchas' : 'pocas'} conversaciones sin asignar proyecto.`);
    }

    async showProjectsCreated() {
        console.log('\n📊 Proyectos disponibles en la base:\n');

        const query = `SELECT id, name, chatgpt_project_id FROM projects ORDER BY name`;
        const [projects] = await this.connection.execute(query);

        projects.forEach((project, index) => {
            const projectId = project.chatgpt_project_id || 'Sin ID GPT';
            console.log(`${String(index + 1).padStart(2, ' ')}. ${project.name} (ID: ${project.id}) → ${projectId}`);
        });
    }

    showFinalStats() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 RESUMEN DE CREACIÓN DE PROYECTOS');
        console.log('='.repeat(60));
        console.log(`➕ Proyectos creados: ${this.stats.projects_created}`);
        console.log(`✅ Proyectos existentes: ${this.stats.existing_projects}`);
        console.log(`🔧 Total proyectos procesados: ${this.stats.projects_created + this.stats.existing_projects}`);
        console.log('='.repeat(60));

        if (this.stats.projects_created > 0) {
            console.log('\n🎯 PRÓXIMOS PASOS:');
            console.log('1. Los proyectos GPT han sido creados exitosamente');
            console.log('2. Ahora puedes usar matching manual o automático por títulos');
            console.log('3. Considera crear un script de matching por palabras clave');
        }
    }

    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('\n🔌 Conexión MySQL cerrada');
        }
    }

    async run() {
        try {
            console.log('🎯 ChatBETO - Creador automático de proyectos GPT');
            console.log('=' .repeat(60));
            
            await this.loadDbConfig();
            await this.connect();
            await this.createGPTProjects();
            await this.showProjectsCreated();
            await this.showConversationSamples();
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
    const creator = new ProjectCreator();
    creator.run().catch(console.error);
}

export default ProjectCreator;