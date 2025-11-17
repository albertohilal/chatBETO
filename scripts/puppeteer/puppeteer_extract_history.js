import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class ChatGPTHistoryExtractor {
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

    async navigateToMainChatPage() {
        try {
            console.log('🏠 Navegando a página principal de ChatGPT...');
            await this.page.goto('https://chatgpt.com/', { 
                waitUntil: 'networkidle2',
                timeout: 15000 
            });
            
            await this.page.waitForTimeout(3000);
            console.log('✅ En página principal');
            
        } catch (error) {
            console.error('❌ Error navegando a página principal:', error.message);
            throw error;
        }
    }

    async scrollAndLoadAllHistory() {
        console.log('📜 Cargando todo el historial de conversaciones...');
        
        let previousCount = 0;
        let stableAttempts = 0;
        let maxAttempts = 30;
        let attempt = 0;
        
        while (attempt < maxAttempts && stableAttempts < 5) {
            try {
                // Scroll en el sidebar de historial
                await this.page.evaluate(() => {
                    const sidebar = document.querySelector('nav[aria-label="Chat history"]');
                    if (sidebar) {
                        sidebar.scrollTop = sidebar.scrollHeight;
                    }
                    
                    // También scroll en toda la página
                    window.scrollTo(0, document.body.scrollHeight);
                });
                
                await this.page.waitForTimeout(2000);
                
                // Contar conversaciones actuales
                const currentCount = await this.page.evaluate(() => {
                    const conversationLinks = document.querySelectorAll('a[href*="/c/"]');
                    return conversationLinks.length;
                });
                
                console.log(`⏳ Intento ${attempt + 1}: ${currentCount} conversaciones cargadas`);
                
                if (currentCount === previousCount) {
                    stableAttempts++;
                } else {
                    stableAttempts = 0;
                    previousCount = currentCount;
                }
                
                attempt++;
                
            } catch (error) {
                console.log(`⚠️ Error en intento ${attempt}: ${error.message}`);
                attempt++;
            }
        }
        
        console.log(`✅ Carga completa: ${previousCount} conversaciones encontradas`);
        return previousCount;
    }

    async extractAllConversations() {
        try {
            console.log('🔍 Extrayendo TODAS las conversaciones...');
            
            const conversations = await this.page.evaluate(() => {
                const results = [];
                
                // Buscar todos los enlaces de conversaciones
                const conversationLinks = document.querySelectorAll('a[href*="/c/"]');
                
                conversationLinks.forEach((link, index) => {
                    try {
                        const href = link.href;
                        const conversationId = href.match(/\/c\/([^?\/]+)/)?.[1];
                        const title = link.textContent?.trim() || 'Sin título';
                        
                        // Buscar información adicional en el elemento padre
                        let parentInfo = '';
                        let projectInfo = '';
                        
                        // Buscar en elementos hermanos o padres para info de proyecto
                        let current = link.parentElement;
                        for (let i = 0; i < 5 && current; i++) {
                            const text = current.textContent;
                            if (text && text.includes('Beto') || text.includes('Personal')) {
                                projectInfo = text.substring(0, 100);
                                break;
                            }
                            current = current.parentElement;
                        }
                        
                        if (conversationId && title.length > 0) {
                            results.push({
                                id: conversationId,
                                title: title,
                                href: href,
                                projectInfo: projectInfo,
                                index: index
                            });
                        }
                    } catch (e) {
                        console.log(`Error procesando conversación ${index}:`, e.message);
                    }
                });
                
                return results;
            });
            
            console.log(`📋 Total conversaciones extraídas: ${conversations.length}`);
            
            // Filtrar las que contienen "Beto" o "Personal"
            const betoConversations = conversations.filter(conv => 
                conv.title.toLowerCase().includes('beto') || 
                conv.title.toLowerCase().includes('personal') ||
                conv.projectInfo.toLowerCase().includes('beto') ||
                conv.projectInfo.toLowerCase().includes('personal')
            );
            
            console.log(`🎯 Conversaciones relacionadas con "Beto/Personal": ${betoConversations.length}`);
            betoConversations.forEach((conv, index) => {
                console.log(`${index + 1}. "${conv.title}" - ID: ${conv.id}`);
                if (conv.projectInfo) {
                    console.log(`   Proyecto: ${conv.projectInfo}`);
                }
            });
            
            return { allConversations: conversations, betoConversations };
            
        } catch (error) {
            console.error('❌ Error extrayendo conversaciones:', error.message);
            return { allConversations: [], betoConversations: [] };
        }
    }

    async searchInConversationContent(conversationId, title) {
        try {
            console.log(`🔍 Analizando conversación: "${title}" (${conversationId})`);
            
            // Navegar a la conversación
            await this.page.goto(`https://chatgpt.com/c/${conversationId}`, {
                waitUntil: 'networkidle2',
                timeout: 10000
            });
            
            await this.page.waitForTimeout(2000);
            
            // Extraer contenido
            const content = await this.page.evaluate(() => {
                const messages = [];
                
                // Buscar diferentes selectores para mensajes
                const messageSelectors = [
                    '[data-message-author-role]',
                    '.message',
                    '[role="presentation"]',
                    '.conversation-turn'
                ];
                
                messageSelectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach((msg, index) => {
                            const text = msg.textContent?.trim();
                            if (text && text.length > 10) {
                                messages.push({
                                    index: index,
                                    text: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
                                    selector: selector
                                });
                            }
                        });
                    } catch (e) {}
                });
                
                return {
                    messageCount: messages.length,
                    messages: messages.slice(0, 5), // Primeros 5 mensajes
                    hasBetoContent: document.body.textContent?.toLowerCase().includes('beto') || false,
                    hasPersonalContent: document.body.textContent?.toLowerCase().includes('personal') || false
                };
            });
            
            console.log(`   📊 ${content.messageCount} mensajes, Beto: ${content.hasBetoContent}, Personal: ${content.hasPersonalContent}`);
            
            if (content.hasBetoContent || content.hasPersonalContent) {
                console.log(`   ⭐ CONTENIDO RELEVANTE ENCONTRADO`);
                content.messages.forEach((msg, index) => {
                    console.log(`      ${index + 1}. ${msg.text}`);
                });
            }
            
            return content;
            
        } catch (error) {
            console.log(`   ❌ Error analizando conversación: ${error.message}`);
            return null;
        }
    }

    async findBetoPersonalConversations() {
        console.log('\n🎯 BÚSQUEDA COMPLETA DE CONVERSACIONES "BETO PERSONAL":');
        console.log('=====================================================');
        
        // 1. Navegar a página principal
        await this.navigateToMainChatPage();
        await this.takeScreenshot('main_page_loaded');
        
        // 2. Cargar todo el historial
        const totalConversations = await this.scrollAndLoadAllHistory();
        await this.takeScreenshot('full_history_loaded');
        
        // 3. Extraer todas las conversaciones
        const { allConversations, betoConversations } = await this.extractAllConversations();
        
        // 4. Analizar las conversaciones candidatas
        const detailedResults = [];
        
        if (betoConversations.length > 0) {
            console.log('\n🔬 ANÁLISIS DETALLADO DE CONVERSACIONES CANDIDATAS:');
            
            for (const conv of betoConversations.slice(0, 5)) { // Analizar máximo 5
                const detail = await this.searchInConversationContent(conv.id, conv.title);
                if (detail) {
                    detailedResults.push({
                        conversation: conv,
                        detail: detail
                    });
                }
            }
        }
        
        console.log('\n📊 RESUMEN FINAL:');
        console.log(`- Total conversaciones en historial: ${totalConversations}`);
        console.log(`- Conversaciones extraídas: ${allConversations.length}`);
        console.log(`- Candidatas "Beto/Personal": ${betoConversations.length}`);
        console.log(`- Analizadas en detalle: ${detailedResults.length}`);
        
        return { allConversations, betoConversations, detailedResults };
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
    const extractor = new ChatGPTHistoryExtractor();
    
    try {
        await extractor.init();
        await extractor.connectDB();
        
        const results = await extractor.findBetoPersonalConversations();
        
        console.log('\n✅ INVESTIGACIÓN COMPLETA TERMINADA');
        
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await extractor.cleanup();
    }
}

main();