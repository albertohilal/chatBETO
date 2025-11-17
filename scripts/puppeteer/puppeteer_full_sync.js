import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs/promises';

// Configuración de base de datos
const dbConfig = {
    host: 'sv46.byethost46.org',
    user: 'iunaorg_b3toh',
    password: 'elgeneral2018',
    database: 'iunaorg_chatBeto',
    port: 3306
};

class ChatGPTFullSync {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
        this.syncReport = {
            totalProjects: 0,
            processedProjects: 0,
            totalConversations: 0,
            mappedConversations: 0,
            errors: []
        };
    }

    async init() {
        console.log('🚀 Iniciando sincronización completa de ChatGPT...');
        
        try {
            // Conectar a Chrome existente con debug
            this.browser = await puppeteer.connect({
                browserURL: 'http://localhost:9222',
                defaultViewport: null
            });
            
            console.log('✅ Conectado a Chrome existente');
        } catch (error) {
            console.log('❌ Error conectando a Chrome:');
            console.log('💡 Asegúrate de que Chrome esté corriendo con:');
            console.log('   google-chrome --remote-debugging-port=9222');
            throw error;
        }
    }

    async connectDB() {
        try {
            console.log('🔗 Conectando a la base de datos...');
            this.connection = await mysql.createConnection(dbConfig);
            console.log('✅ Conexión a BD establecida');
        } catch (error) {
            console.error('❌ Error conectando a BD:', error);
            throw error;
        }
    }

    async getAllProjects() {
        console.log('📊 Obteniendo lista de proyectos...');
        
        const [projects] = await this.connection.execute(`
            SELECT id, name, 
                   (SELECT COUNT(*) FROM conversations WHERE project_id = projects.id) as current_conversations
            FROM projects 
            ORDER BY id ASC
        `);
        
        this.syncReport.totalProjects = projects.length;
        console.log(`✅ ${projects.length} proyectos encontrados en BD`);
        
        return projects;
    }

    async setupChatGPTPage() {
        console.log('🌐 Configurando página de ChatGPT...');
        
        const pages = await this.browser.pages();
        
        // Buscar página existente de ChatGPT
        let chatgptPage = pages.find(page => 
            page.url().includes('chatgpt.com') && 
            !page.url().includes('auth')
        );
        
        if (chatgptPage) {
            console.log('✅ Usando tab existente de ChatGPT');
            this.page = chatgptPage;
        } else {
            console.log('📄 Creando nuevo tab para ChatGPT...');
            this.page = await this.browser.newPage();
            await this.page.goto('https://chatgpt.com/', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
        }
        
        // Verificar que está logueado
        const isLoggedIn = await this.page.evaluate(() => {
            return !!(
                document.querySelector('a[href*="/c/"]') ||
                document.querySelector('[data-testid*="new-chat"]') ||
                (document.URL === 'https://chatgpt.com/' && 
                 !document.URL.includes('auth'))
            );
        });
        
        if (!isLoggedIn) {
            throw new Error('No hay sesión activa en ChatGPT. Haz login primero.');
        }
        
        console.log('✅ Sesión activa confirmada');
        return true;
    }

    async navigateToProject(projectName) {
        console.log(`🔍 Navegando al proyecto: "${projectName}"`);
        
        try {
            // Ir al home de ChatGPT primero
            await this.page.goto('https://chatgpt.com/', {
                waitUntil: 'networkidle2',
                timeout: 15000
            });
            
            await this.page.waitForTimeout(2000);
            
            // Buscar el proyecto en el sidebar o menú
            const projectFound = await this.page.evaluate((name) => {
                // Estrategias para encontrar el proyecto
                const strategies = [
                    // 1. Buscar por texto exacto en enlaces
                    () => {
                        const links = Array.from(document.querySelectorAll('a'));
                        return links.find(link => 
                            link.textContent && 
                            link.textContent.trim().toLowerCase() === name.toLowerCase()
                        );
                    },
                    
                    // 2. Buscar por texto contenido
                    () => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        return elements.find(el => 
                            el.textContent && 
                            el.textContent.trim().toLowerCase().includes(name.toLowerCase()) &&
                            (el.tagName === 'A' || el.tagName === 'BUTTON' || el.closest('a, button'))
                        );
                    },
                    
                    // 3. Buscar en elementos con data attributes
                    () => {
                        return document.querySelector(`[data-project-name*="${name}"]`) ||
                               document.querySelector(`[aria-label*="${name}"]`) ||
                               document.querySelector(`[title*="${name}"]`);
                    }
                ];
                
                for (let i = 0; i < strategies.length; i++) {
                    const element = strategies[i]();
                    if (element) {
                        const clickable = element.tagName === 'A' || element.tagName === 'BUTTON' 
                            ? element 
                            : element.closest('a, button');
                        
                        if (clickable) {
                            clickable.click();
                            return { found: true, strategy: i + 1 };
                        }
                    }
                }
                
                return { found: false, strategy: 0 };
            }, projectName);
            
            if (projectFound.found) {
                console.log(`✅ Proyecto encontrado (estrategia ${projectFound.strategy})`);
                await this.page.waitForTimeout(3000);
                return true;
            } else {
                console.log(`⚠️ Proyecto "${projectName}" no encontrado en ChatGPT`);
                return false;
            }
            
        } catch (error) {
            console.log(`❌ Error navegando al proyecto "${projectName}":`, error.message);
            return false;
        }
    }

    async extractProjectConversations() {
        console.log('📝 Extrayendo conversaciones del proyecto actual...');
        
        try {
            await this.page.waitForTimeout(2000);

            const conversations = await this.page.evaluate(() => {
                const results = [];
                
                // Buscar enlaces de conversación
                const conversationLinks = document.querySelectorAll('a[href*="/c/"]');
                
                conversationLinks.forEach((link) => {
                    try {
                        const href = link.href;
                        const conversationId = href.match(/\/c\/([^\/\?]+)/)?.[1] || '';
                        
                        let title = '';
                        
                        // Obtener título del enlace
                        if (link.textContent && link.textContent.trim()) {
                            title = link.textContent.trim();
                        } else {
                            const titleElement = link.querySelector('[title], span, div');
                            if (titleElement) {
                                title = titleElement.textContent?.trim() || 
                                       titleElement.getAttribute('title') || '';
                            }
                        }
                        
                        // Filtrar títulos válidos
                        if (conversationId && title && 
                            title.length > 2 && 
                            title.length < 500 &&
                            !title.toLowerCase().includes('chatgpt') &&
                            !title.toLowerCase().includes('log in') &&
                            !title.toLowerCase().includes('sign in')) {
                            
                            results.push({
                                title: title.substring(0, 500),
                                conversationId: conversationId,
                                href: href
                            });
                        }
                    } catch (err) {
                        // Continuar con la siguiente conversación
                    }
                });

                // Eliminar duplicados por conversationId
                const uniqueResults = results.filter((conv, index, self) =>
                    index === self.findIndex(c => c.conversationId === conv.conversationId)
                );

                return uniqueResults;
            });

            console.log(`✅ ${conversations.length} conversaciones extraídas`);
            this.syncReport.totalConversations += conversations.length;
            
            return conversations;

        } catch (error) {
            console.error('❌ Error extrayendo conversaciones:', error);
            return [];
        }
    }

    async mapConversationsToProject(conversations, projectId, projectName) {
        if (conversations.length === 0) {
            console.log('⚠️ No hay conversaciones para mapear');
            return { updated: 0, notFound: 0 };
        }
        
        console.log(`💾 Mapeando ${conversations.length} conversaciones al proyecto ${projectId}...`);
        
        let updated = 0;
        let notFound = 0;

        for (const conv of conversations) {
            try {
                // Buscar por conversation_id primero
                let [result] = await this.connection.execute(
                    'UPDATE conversations SET project_id = ? WHERE conversation_id = ? AND project_id = 67',
                    [projectId, conv.conversationId]
                );

                if (result.affectedRows > 0) {
                    updated++;
                    console.log(`  ✅ ID: "${conv.title.substring(0, 50)}..."`);
                } else {
                    // Buscar por título exacto
                    [result] = await this.connection.execute(
                        'UPDATE conversations SET project_id = ? WHERE title = ? AND project_id = 67',
                        [projectId, conv.title]
                    );

                    if (result.affectedRows > 0) {
                        updated++;
                        console.log(`  ✅ Título: "${conv.title.substring(0, 50)}..."`);
                    } else {
                        notFound++;
                        console.log(`  ⚠️ No encontrada: "${conv.title.substring(0, 50)}..."`);
                    }
                }
            } catch (error) {
                console.error(`  ❌ Error: "${conv.title.substring(0, 50)}...":`, error.message);
                notFound++;
            }
        }

        this.syncReport.mappedConversations += updated;
        
        console.log(`📊 Proyecto "${projectName}": ${updated} mapeadas, ${notFound} no encontradas`);
        return { updated, notFound };
    }

    async processAllProjects() {
        console.log('🔄 Iniciando procesamiento de todos los proyectos...\n');
        
        const projects = await this.getAllProjects();
        await this.setupChatGPTPage();
        
        console.log(`\n📋 Procesando ${projects.length} proyectos...\n`);
        
        for (let i = 0; i < projects.length; i++) {
            const project = projects[i];
            
            console.log(`\n🎯 [${i + 1}/${projects.length}] Procesando: "${project.name}" (ID: ${project.id})`);
            console.log(`   Conversaciones actuales: ${project.current_conversations}`);
            
            try {
                // Navegar al proyecto específico
                const projectFound = await this.navigateToProject(project.name);
                
                if (!projectFound) {
                    console.log(`⏭️ Saltando proyecto "${project.name}" - No encontrado en ChatGPT`);
                    this.syncReport.errors.push(`Proyecto "${project.name}" no encontrado`);
                    continue;
                }
                
                // Extraer conversaciones del proyecto
                const conversations = await this.extractProjectConversations();
                
                if (conversations.length === 0) {
                    console.log(`⚠️ No se encontraron conversaciones en "${project.name}"`);
                } else {
                    // Mapear conversaciones a la BD
                    await this.mapConversationsToProject(conversations, project.id, project.name);
                }
                
                this.syncReport.processedProjects++;
                
                // Delay entre proyectos para evitar rate limiting
                if (i < projects.length - 1) {
                    console.log('⏳ Esperando antes del siguiente proyecto...');
                    await this.page.waitForTimeout(2000);
                }
                
            } catch (error) {
                console.error(`❌ Error procesando proyecto "${project.name}":`, error.message);
                this.syncReport.errors.push(`Error en "${project.name}": ${error.message}`);
                
                // Continuar con el siguiente proyecto
                continue;
            }
        }
        
        await this.generateFinalReport();
    }

    async generateFinalReport() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 REPORTE FINAL DE SINCRONIZACIÓN');
        console.log('='.repeat(60));
        
        console.log(`✅ Proyectos procesados: ${this.syncReport.processedProjects}/${this.syncReport.totalProjects}`);
        console.log(`📝 Total conversaciones encontradas: ${this.syncReport.totalConversations}`);
        console.log(`🔗 Conversaciones mapeadas: ${this.syncReport.mappedConversations}`);
        console.log(`❌ Errores: ${this.syncReport.errors.length}`);
        
        if (this.syncReport.errors.length > 0) {
            console.log('\n🚨 Errores encontrados:');
            this.syncReport.errors.forEach((error, idx) => {
                console.log(`  ${idx + 1}. ${error}`);
            });
        }
        
        // Verificar estado final en BD
        const [finalStats] = await this.connection.execute(`
            SELECT 
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN project_id = 67 THEN 1 END) as still_general,
                COUNT(CASE WHEN project_id != 67 THEN 1 END) as mapped_conversations
            FROM conversations
        `);
        
        console.log('\n📊 Estado final en base de datos:');
        console.log(`   Total conversaciones: ${finalStats[0].total_conversations}`);
        console.log(`   Aún en "General" (67): ${finalStats[0].still_general}`);
        console.log(`   Mapeadas a proyectos: ${finalStats[0].mapped_conversations}`);
        
        // Guardar reporte en archivo
        const reportData = {
            timestamp: new Date().toISOString(),
            summary: this.syncReport,
            finalStats: finalStats[0]
        };
        
        await fs.writeFile('./sync_report.json', JSON.stringify(reportData, null, 2));
        console.log('\n💾 Reporte guardado en: sync_report.json');
        
        console.log('\n✅ Sincronización completa finalizada!');
    }

    async cleanup() {
        console.log('\n🧹 Limpiando recursos...');
        
        if (this.connection) {
            await this.connection.end();
            console.log('✅ Conexión BD cerrada');
        }
        
        if (this.browser) {
            await this.browser.disconnect();
            console.log('✅ Desconectado de Chrome');
        }
    }
}

// Función principal
async function main() {
    const syncer = new ChatGPTFullSync();
    
    try {
        await syncer.init();
        await syncer.connectDB();
        await syncer.processAllProjects();
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
        console.error('🔧 Verifica que Chrome esté corriendo con debug port 9222');
    } finally {
        await syncer.cleanup();
    }
}

main().catch(console.error);

export default ChatGPTFullSync;