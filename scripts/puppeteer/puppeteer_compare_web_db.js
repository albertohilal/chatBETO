import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class WebVsDbComparator {
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
                await this.page.goto('https://chatgpt.com/', { waitUntil: 'networkidle2' });
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

    async extractWebConversations() {
        console.log('🌐 Extrayendo conversaciones de la web...');
        
        // Scroll para cargar todo
        await this.page.evaluate(() => {
            const sidebar = document.querySelector('nav[aria-label="Chat history"]');
            if (sidebar) {
                sidebar.scrollTop = sidebar.scrollHeight;
            }
        });
        
        await this.page.waitForTimeout(3000);
        
        const webConversations = await this.page.evaluate(() => {
            const conversations = [];
            const links = document.querySelectorAll('a[href*="/c/"]');
            
            links.forEach(link => {
                const href = link.href;
                const conversationId = href.match(/\/c\/([^?\/]+)/)?.[1];
                const title = link.textContent?.trim() || 'Sin título';
                
                if (conversationId && title) {
                    conversations.push({
                        conversation_id: conversationId,
                        title: title,
                        href: href
                    });
                }
            });
            
            return conversations;
        });
        
        console.log(`📋 ${webConversations.length} conversaciones en web:`);
        webConversations.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" (${conv.conversation_id})`);
        });
        
        return webConversations;
    }

    async getDbConversations() {
        console.log('\n🗄️ Obteniendo conversaciones de la BD...');
        
        const [rows] = await this.connection.execute(`
            SELECT 
                c.id,
                c.conversation_id,
                c.title,
                p.name as project_name,
                c.created_at
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            ORDER BY c.created_at DESC
            LIMIT 50
        `);
        
        console.log(`📊 ${rows.length} conversaciones recientes en BD:`);
        rows.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" - Proyecto: "${conv.project_name}" (${conv.conversation_id})`);
        });
        
        return rows;
    }

    async compareWebVsDb() {
        const webConversations = await this.extractWebConversations();
        const dbConversations = await this.getDbConversations();
        
        console.log('\n🔍 COMPARACIÓN WEB vs BD:');
        console.log('=========================');
        
        const webIds = new Set(webConversations.map(c => c.conversation_id));
        const dbIds = new Set(dbConversations.map(c => c.conversation_id));
        
        // Conversaciones en web que NO están en BD
        const webOnly = webConversations.filter(c => !dbIds.has(c.conversation_id));
        console.log(`\n📱 CONVERSACIONES SOLO EN WEB (${webOnly.length}):`);
        webOnly.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" (${conv.conversation_id})`);
        });
        
        // Conversaciones en BD que NO están en web
        const dbOnly = dbConversations.filter(c => !webIds.has(c.conversation_id));
        console.log(`\n🗄️ CONVERSACIONES SOLO EN BD (${dbOnly.length}):`);
        dbOnly.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" - Proyecto: "${conv.project_name}" (${conv.conversation_id})`);
        });
        
        // Conversaciones en ambos
        const inBoth = dbConversations.filter(c => webIds.has(c.conversation_id));
        console.log(`\n✅ CONVERSACIONES EN AMBOS (${inBoth.length}):`);
        inBoth.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" - Proyecto: "${conv.project_name}"`);
        });
        
        // Buscar específicamente "Beto Personal"
        const betoPersonalInDb = dbConversations.filter(c => 
            c.project_name && c.project_name.toLowerCase().includes('beto') && 
            c.project_name.toLowerCase().includes('personal')
        );
        
        console.log(`\n🎯 CONVERSACIONES "BETO PERSONAL" EN BD (${betoPersonalInDb.length}):`);
        betoPersonalInDb.forEach((conv, index) => {
            console.log(`${index + 1}. "${conv.title}" (${conv.conversation_id})`);
            console.log(`   📅 Fecha: ${conv.created_at}`);
        });
        
        console.log('\n📊 RESUMEN:');
        console.log(`- Web: ${webConversations.length} conversaciones`);
        console.log(`- BD: ${dbConversations.length} conversaciones`);
        console.log(`- Solo en web: ${webOnly.length}`);
        console.log(`- Solo en BD: ${dbOnly.length}`);
        console.log(`- En ambos: ${inBoth.length}`);
        console.log(`- "Beto Personal" en BD: ${betoPersonalInDb.length}`);
        
        return {
            webConversations,
            dbConversations,
            webOnly,
            dbOnly,
            inBoth,
            betoPersonalInDb
        };
    }

    async checkBetoPersonalProject() {
        console.log('\n🔍 VERIFICANDO PROYECTO "BETO PERSONAL":');
        console.log('=====================================');
        
        const [projectRows] = await this.connection.execute(`
            SELECT 
                p.id,
                p.name,
                COUNT(c.id) as conversation_count,
                MAX(c.created_at) as last_conversation
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id
            WHERE LOWER(p.name) LIKE '%beto%' AND LOWER(p.name) LIKE '%personal%'
            GROUP BY p.id, p.name
        `);
        
        if (projectRows.length > 0) {
            const project = projectRows[0];
            console.log(`📁 Proyecto encontrado:`);
            console.log(`   ID: ${project.id}`);
            console.log(`   Nombre: "${project.name}"`);
            console.log(`   Conversaciones: ${project.conversation_count}`);
            console.log(`   Última conversación: ${project.last_conversation || 'Ninguna'}`);
            
            if (project.conversation_count > 0) {
                console.log('\n📋 Conversaciones del proyecto:');
                const [conversations] = await this.connection.execute(`
                    SELECT conversation_id, title, created_at
                    FROM conversations 
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                `, [project.id]);
                
                conversations.forEach((conv, index) => {
                    console.log(`${index + 1}. "${conv.title}" (${conv.conversation_id}) - ${conv.created_at}`);
                });
            }
            
        } else {
            console.log('❌ No se encontró proyecto "Beto Personal" en BD');
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
    const comparator = new WebVsDbComparator();
    
    try {
        await comparator.init();
        await comparator.connectDB();
        
        const comparison = await comparator.compareWebVsDb();
        await comparator.checkBetoPersonalProject();
        
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await comparator.cleanup();
    }
}

main();