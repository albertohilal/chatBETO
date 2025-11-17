import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';

// Configuración de base de datos
const dbConfig = {
    host: 'sv46.byethost46.org',
    user: 'iunaorg_b3toh',
    password: 'elgeneral2018',
    database: 'iunaorg_chatBeto',
    port: 3306
};

class ChatGPTConnectExisting {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
    }

    async init() {
        console.log('🚀 Conectando a Chrome existente...');
        
        try {
            // Conectar a una instancia de Chrome ya ejecutándose
            this.browser = await puppeteer.connect({
                browserURL: 'http://localhost:9222',
                defaultViewport: null
            });
            
            console.log('✅ Conectado a Chrome existente');
        } catch (error) {
            console.log('❌ No se pudo conectar a Chrome existente');
            console.log('💡 Instrucciones:');
            console.log('1. Abre Chrome manualmente');
            console.log('2. Haz login en ChatGPT');
            console.log('3. Ejecuta Chrome con: google-chrome --remote-debugging-port=9222');
            console.log('4. Vuelve a ejecutar este script');
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

    async useExistingTab() {
        console.log('🌐 Usando tab existente de ChatGPT...');
        
        const pages = await this.browser.pages();
        
        // Buscar una página que ya esté en ChatGPT
        let chatgptPage = pages.find(page => 
            page.url().includes('chatgpt.com') && 
            !page.url().includes('auth')
        );
        
        if (chatgptPage) {
            console.log('✅ Encontrado tab existente de ChatGPT');
            this.page = chatgptPage;
        } else {
            console.log('📄 Creando nuevo tab para ChatGPT...');
            this.page = await this.browser.newPage();
            await this.page.goto('https://chatgpt.com/', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
        }
        
        // Screenshot del estado actual
        await this.page.screenshot({ 
            path: './debug_existing_session.png', 
            fullPage: true 
        });
        
        // Verificar estado
        const isLoggedIn = await this.page.evaluate(() => {
            return !!(
                document.querySelector('a[href*="/c/"]') ||
                document.querySelector('[data-testid*="new-chat"]') ||
                (document.URL === 'https://chatgpt.com/' && 
                 !document.URL.includes('auth'))
            );
        });
        
        console.log(isLoggedIn ? '✅ Sesión activa detectada' : '❌ No hay sesión activa');
        return isLoggedIn;
    }

    async extractAllConversations() {
        console.log('📝 Extrayendo todas las conversaciones...');
        
        try {
            await this.page.waitForTimeout(3000);

            const conversations = await this.page.evaluate(() => {
                const results = [];
                
                // Buscar todos los enlaces de conversación
                const conversationLinks = document.querySelectorAll('a[href*="/c/"]');
                
                conversationLinks.forEach((link, index) => {
                    try {
                        const href = link.href;
                        const conversationId = href.match(/\/c\/([^\/\?]+)/)?.[1] || '';
                        
                        // Buscar el título en el elemento o elementos cercanos
                        let title = '';
                        
                        // Estrategia 1: texto del propio enlace
                        if (link.textContent && link.textContent.trim()) {
                            title = link.textContent.trim();
                        }
                        
                        // Estrategia 2: buscar en elementos hijos
                        if (!title) {
                            const titleElement = link.querySelector('[title], span, div');
                            if (titleElement) {
                                title = titleElement.textContent?.trim() || titleElement.getAttribute('title') || '';
                            }
                        }
                        
                        // Estrategia 3: usar el ID como título si no encontramos nada
                        if (!title) {
                            title = `Conversación ${conversationId.substring(0, 8)}`;
                        }
                        
                        if (conversationId && title && title.length > 0) {
                            results.push({
                                title: title.substring(0, 500),
                                conversationId: conversationId,
                                href: href
                            });
                        }
                    } catch (err) {
                        console.log('Error procesando conversación:', err);
                    }
                });

                return results;
            });

            console.log(`✅ Extraídas ${conversations.length} conversaciones`);
            
            if (conversations.length > 0) {
                console.log('📋 Primeras conversaciones:');
                conversations.slice(0, 10).forEach((conv, idx) => {
                    console.log(`  ${idx + 1}. "${conv.title}" (${conv.conversationId})`);
                });
            }

            return conversations;

        } catch (error) {
            console.error('❌ Error extrayendo conversaciones:', error);
            return [];
        }
    }

    async testExistingSession() {
        try {
            const sessionActive = await this.useExistingTab();
            
            if (!sessionActive) {
                console.log('❌ No hay sesión activa en ChatGPT');
                return;
            }

            // Extraer todas las conversaciones disponibles
            const conversations = await this.extractAllConversations();
            
            if (conversations.length === 0) {
                console.log('⚠️ No se encontraron conversaciones');
                return;
            }

            console.log(`\n📊 RESUMEN:`);
            console.log(`   - Conversaciones encontradas: ${conversations.length}`);
            console.log(`   - Estas se pueden mapear a proyectos en la BD`);
            console.log(`   - Para mapeo completo, se procesará proyecto por proyecto`);

        } catch (error) {
            console.error('❌ Error en testExistingSession:', error);
        }
    }

    async cleanup() {
        console.log('🧹 Limpiando recursos...');
        
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
    const tester = new ChatGPTConnectExisting();
    
    try {
        await tester.init();
        await tester.connectDB();
        await tester.testExistingSession();
    } catch (error) {
        console.error('❌ Error general:', error);
    } finally {
        await tester.cleanup();
    }
}

main().catch(console.error);

export default ChatGPTConnectExisting;