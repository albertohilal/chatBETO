import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class ChatGPTProjectLister {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
    }

    async init() {
        try {
            console.log('🚀 Conectando a Chrome existente...');
            this.browser = await puppeteer.connect({
                browserURL: 'http://localhost:9222',
                defaultViewport: null
            });
            
            const pages = await this.browser.pages();
            this.page = pages.find(p => p.url().includes('chatgpt.com')) || pages[0];
            
            if (!this.page.url().includes('chatgpt.com')) {
                await this.page.goto('https://chatgpt.com', { waitUntil: 'networkidle2' });
            }
            
            console.log('✅ Conectado a Chrome existente');
        } catch (error) {
            console.error('❌ Error conectando a Chrome:', error.message);
            throw error;
        }
    }

    async connectDB() {
        try {
            console.log('🔗 Conectando a la base de datos...');
            const dbConfig = JSON.parse(fs.readFileSync('db_config.json', 'utf8'));
            
            this.connection = await mysql.createConnection({
                host: dbConfig.host,
                user: dbConfig.user,
                password: dbConfig.password,
                database: dbConfig.database,
                port: dbConfig.port || 3306
            });
            
            console.log('✅ Conexión a BD establecida');
        } catch (error) {
            console.error('❌ Error conectando a BD:', error.message);
            throw error;
        }
    }

    async getAllProjectsFromWeb() {
        try {
            console.log('🔍 Extrayendo todos los proyectos de la interfaz web...');
            
            await this.page.waitForSelector('nav[aria-label="Chat history"]', { timeout: 10000 });
            
            // Buscar todos los elementos que contengan proyectos
            const projects = await this.page.evaluate(() => {
                const projectElements = [];
                
                // Buscar diferentes patrones de proyectos
                const selectors = [
                    'nav[aria-label="Chat history"] h3',
                    'nav[aria-label="Chat history"] [role="treeitem"]',
                    'nav[aria-label="Chat history"] a[href*="/g/"]',
                    'nav[aria-label="Chat history"] div[data-projection-item="true"]',
                    '.group\\/sidebar-item',
                    '[data-testid*="project"]',
                    '[data-testid*="conversation"]'
                ];
                
                const foundProjects = new Set();
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent?.trim();
                            const href = el.href || el.querySelector('a')?.href;
                            
                            if (text && text.length > 0) {
                                foundProjects.add({
                                    text: text,
                                    href: href || 'No link',
                                    selector: selector,
                                    innerHTML: el.innerHTML.substring(0, 100)
                                });
                            }
                        });
                    } catch (e) {
                        console.log(`Error con selector ${selector}:`, e.message);
                    }
                });
                
                return Array.from(foundProjects);
            });
            
            console.log(`📋 Encontrados ${projects.length} elementos en la interfaz web:`);
            projects.forEach((project, index) => {
                console.log(`${index + 1}. "${project.text}" (${project.selector})`);
            });
            
            return projects;
            
        } catch (error) {
            console.error('❌ Error extrayendo proyectos:', error.message);
            return [];
        }
    }

    async getAllProjectsFromDB() {
        try {
            console.log('\n📊 Obteniendo proyectos de la base de datos...');
            
            const [rows] = await this.connection.execute(`
                SELECT 
                    p.id,
                    p.name as project_name,
                    COUNT(c.id) as conversation_count
                FROM projects p 
                LEFT JOIN conversations c ON p.id = c.project_id 
                GROUP BY p.id, p.name
                ORDER BY p.id
            `);
            
            console.log(`📋 ${rows.length} proyectos en BD:`);
            rows.forEach(project => {
                console.log(`ID ${project.id}: "${project.project_name}" (${project.conversation_count} conversaciones)`);
            });
            
            return rows;
            
        } catch (error) {
            console.error('❌ Error obteniendo proyectos de BD:', error.message);
            return [];
        }
    }

    async compareProjects() {
        const webProjects = await this.getAllProjectsFromWeb();
        const dbProjects = await this.getAllProjectsFromDB();
        
        console.log('\n🔍 ANÁLISIS COMPARATIVO:');
        console.log('========================');
        
        // Buscar "Beto Personal" específicamente
        const betoPersonalInWeb = webProjects.find(p => 
            p.text.toLowerCase().includes('beto') && 
            p.text.toLowerCase().includes('personal')
        );
        
        const betoPersonalInDB = dbProjects.find(p => 
            p.project_name.toLowerCase().includes('beto') && 
            p.project_name.toLowerCase().includes('personal')
        );
        
        console.log('\n🎯 ANÁLISIS "BETO PERSONAL":');
        console.log('En web:', betoPersonalInWeb ? `✅ SÍ - "${betoPersonalInWeb.text}"` : '❌ NO');
        console.log('En BD:', betoPersonalInDB ? `✅ SÍ - ID ${betoPersonalInDB.id} "${betoPersonalInDB.project_name}" (${betoPersonalInDB.conversation_count} conversaciones)` : '❌ NO');
        
        // Proyectos en BD que no están en web
        console.log('\n📱 PROYECTOS SOLO EN BD (posiblemente solo móviles):');
        const dbProjectNames = dbProjects.map(p => p.project_name.toLowerCase());
        const webProjectNames = webProjects.map(p => p.text.toLowerCase());
        
        const onlyInDB = dbProjects.filter(dbProj => {
            const dbName = dbProj.project_name.toLowerCase();
            return !webProjectNames.some(webName => 
                webName.includes(dbName) || 
                dbName.includes(webName) ||
                this.similarity(dbName, webName) > 0.8
            );
        });
        
        onlyInDB.forEach(project => {
            console.log(`- ID ${project.id}: "${project.project_name}" (${project.conversation_count} conversaciones)`);
        });
        
        console.log(`\n📊 RESUMEN:`);
        console.log(`- Elementos en interfaz web: ${webProjects.length}`);
        console.log(`- Proyectos en BD: ${dbProjects.length}`);
        console.log(`- Proyectos solo en BD: ${onlyInDB.length}`);
        
        return { webProjects, dbProjects, onlyInDB };
    }

    similarity(s1, s2) {
        const longer = s1.length > s2.length ? s1 : s2;
        const shorter = s1.length > s2.length ? s2 : s1;
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }

    levenshteinDistance(str1, str2) {
        const matrix = [];
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        return matrix[str2.length][str1.length];
    }

    async takeScreenshot(name) {
        try {
            await this.page.screenshot({ 
                path: `${name}.png`, 
                fullPage: true 
            });
            console.log(`📸 Screenshot guardado: ${name}.png`);
        } catch (error) {
            console.error(`❌ Error guardando screenshot: ${error.message}`);
        }
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
    const lister = new ChatGPTProjectLister();
    
    try {
        await lister.init();
        await lister.connectDB();
        await lister.takeScreenshot('debug_projects_before_analysis');
        await lister.compareProjects();
        await lister.takeScreenshot('debug_projects_after_analysis');
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await lister.cleanup();
    }
}

main();