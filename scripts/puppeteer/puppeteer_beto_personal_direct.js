import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class BetoPersonalDirectNav {
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

    async findBetoPersonalProjectUrl() {
        console.log('🔍 Usando URL directa del proyecto "Beto Personal"...');
        
        // URL directa proporcionada por el usuario
        const betoPersonalUrl = 'https://chatgpt.com/g/g-p-68222650e6dc8191bd8518258c6f0f55-beto-personal/project';
        
        console.log(`🎯 URL del proyecto: ${betoPersonalUrl}`);
        
        return [{
            text: 'Beto Personal',
            href: betoPersonalUrl,
            selector: 'direct_url'
        }];
    }

    async navigateToBetoPersonalProject() {
        const projects = await this.findBetoPersonalProjectUrl();
        
        if (projects.length === 0) {
            console.log('❌ No se encontró URL directa del proyecto "Beto Personal"');
            return false;
        }
        
        const betoProject = projects[0];
        console.log(`🎯 Navegando a: ${betoProject.href}`);
        
        try {
            await this.page.goto(betoProject.href, { waitUntil: 'networkidle2', timeout: 15000 });
            await this.page.waitForTimeout(3000);
            
            console.log('✅ Navegación exitosa al proyecto');
            return true;
            
        } catch (error) {
            console.error('❌ Error navegando al proyecto:', error.message);
            return false;
        }
    }

    async extractBetoPersonalConversations() {
        console.log('📋 Extrayendo conversaciones del proyecto "Beto Personal"...');
        
        // Hacer scroll para cargar todas las conversaciones
        await this.page.evaluate(() => {
            const sidebar = document.querySelector('nav[aria-label="Chat history"]');
            if (sidebar) {
                sidebar.scrollTop = sidebar.scrollHeight;
            }
        });
        
        await this.page.waitForTimeout(3000);
        
        const conversations = await this.page.evaluate(() => {
            const results = [];
            const links = document.querySelectorAll('a[href*="/c/"]');
            
            links.forEach(link => {
                const href = link.href;
                const conversationId = href.match(/\/c\/([^?\/]+)/)?.[1];
                const title = link.textContent?.trim() || 'Sin título';
                
                if (conversationId && title) {
                    results.push({
                        conversation_id: conversationId,
                        title: title,
                        href: href,
                        project_context: 'Beto Personal'
                    });
                }
            });
            
            return results;
        });
        
        console.log(`📊 Conversaciones encontradas en "Beto Personal": ${conversations.length}`);
        conversations.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" (${conv.conversation_id})`);
        });
        
        return conversations;
    }

    async saveConversationsToDB(conversations) {
        if (conversations.length === 0) {
            console.log('❌ No hay conversaciones para guardar');
            return;
        }
        
        console.log('💾 Guardando conversaciones en la base de datos...');
        
        // Obtener ID del proyecto "Beto Personal"
        const [projectRows] = await this.connection.execute(
            'SELECT id FROM projects WHERE name LIKE ?',
            ['%Beto Personal%']
        );
        
        if (projectRows.length === 0) {
            console.log('❌ Proyecto "Beto Personal" no encontrado en BD');
            return;
        }
        
        const projectId = projectRows[0].id;
        console.log(`📁 Usando proyecto ID: ${projectId}`);
        
        let savedCount = 0;
        
        for (const conv of conversations) {
            try {
                // Verificar si ya existe
                const [existing] = await this.connection.execute(
                    'SELECT id FROM conversations WHERE conversation_id = ?',
                    [conv.conversation_id]
                );
                
                if (existing.length > 0) {
                    console.log(`⏭️ Conversación ya existe: "${conv.title}"`);
                    continue;
                }
                
                // Insertar nueva conversación
                await this.connection.execute(`
                    INSERT INTO conversations (
                        conversation_id, 
                        title, 
                        project_id,
                        created_at
                    ) VALUES (?, ?, ?, NOW())
                `, [conv.conversation_id, conv.title, projectId]);
                
                savedCount++;
                console.log(`✅ Guardado: "${conv.title}"`);
                
            } catch (error) {
                console.log(`❌ Error guardando "${conv.title}": ${error.message}`);
            }
        }
        
        console.log(`💾 Total conversaciones guardadas: ${savedCount}/${conversations.length}`);
    }

    async fullBetoPersonalSync() {
        console.log('\n🎯 SINCRONIZACIÓN COMPLETA "BETO PERSONAL":');
        console.log('==========================================');
        
        await this.takeScreenshot('beto_personal_start');
        
        // 1. Buscar y navegar al proyecto
        const navigationSuccess = await this.navigateToBetoPersonalProject();
        
        if (!navigationSuccess) {
            console.log('❌ No se pudo acceder al proyecto "Beto Personal"');
            return;
        }
        
        await this.takeScreenshot('beto_personal_project_page');
        
        // 2. Extraer conversaciones
        const conversations = await this.extractBetoPersonalConversations();
        
        // 3. Guardar en BD
        await this.saveConversationsToDB(conversations);
        
        await this.takeScreenshot('beto_personal_complete');
        
        console.log('\n📊 RESUMEN FINAL:');
        console.log(`- Conversaciones encontradas: ${conversations.length}`);
        console.log(`- Proyecto: Beto Personal (ID 43)`);
        
        return conversations;
    }

    async takeScreenshot(name) {
        try {
            await this.page.screenshot({ 
                path: `${name}.png`, 
                fullPage: false 
            });
            console.log(`📸 Screenshot: ${name}.png`);
        } catch (error) {
            console.error(`❌ Error screenshot: ${error.message}`);
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
    const navigator = new BetoPersonalDirectNav();
    
    try {
        await navigator.init();
        await navigator.connectDB();
        
        const conversations = await navigator.fullBetoPersonalSync();
        
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await navigator.cleanup();
    }
}

main();