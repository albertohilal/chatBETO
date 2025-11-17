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

class ChatGPTPuppeteerTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
    }

    async init() {
        console.log('🚀 Iniciando Puppeteer con Chrome...');
        
        // Configurar Puppeteer para usar un perfil temporal pero importar cookies
        const userHomeDir = process.env.HOME;
        const tempProfileDir = '/tmp/puppeteer-chatgpt-profile';
        
        console.log('📋 Copiando sesión de Chrome...');
        
        // Crear directorio temporal si no existe
        await import('fs').then(fs => fs.promises.mkdir(tempProfileDir, { recursive: true }));
        
        this.browser = await puppeteer.launch({
            headless: false, // Cambiar a true para producción
            executablePath: '/usr/bin/google-chrome',
            userDataDir: tempProfileDir, // Usar perfil temporal
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--remote-debugging-port=9222'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Configurar viewport y user agent
        await this.page.setViewport({ width: 1366, height: 768 });
        await this.page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36');

        console.log('✅ Puppeteer iniciado');
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

    async getProjectInfo(projectId) {
        const [rows] = await this.connection.execute(
            'SELECT id, name FROM projects WHERE id = ?',
            [projectId]
        );
        return rows[0] || null;
    }

    async copyChromeSession() {
        console.log('🔗 Intentando importar sesión de Chrome...');
        
        try {
            const userHomeDir = process.env.HOME;
            const chromeCookiesPath = `${userHomeDir}/.config/google-chrome/Default/Cookies`;
            
            // Verificar si existen cookies de Chrome
            const fs = await import('fs');
            const cookiesExist = await fs.promises.access(chromeCookiesPath).then(() => true).catch(() => false);
            
            if (cookiesExist) {
                console.log('✅ Cookies de Chrome encontradas');
                // Nota: Las cookies se manejan automáticamente por el userDataDir
                return true;
            } else {
                console.log('⚠️ No se encontraron cookies de Chrome');
                return false;
            }
        } catch (error) {
            console.log('⚠️ Error accediendo cookies:', error.message);
            return false;
        }
    }

    async navigateToChatGPT() {
        console.log('🌐 Navegando a ChatGPT...');
        
        // Copiar sesión de Chrome primero
        await this.copyChromeSession();
        
        try {
            await this.page.goto('https://chatgpt.com/', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            
            console.log('✅ ChatGPT cargado');
            
            // Esperar a que aparezca la interfaz principal
            await this.page.waitForTimeout(3000);
            
            // Capturar screenshot inicial
            await this.page.screenshot({ 
                path: './debug_chatgpt_loaded.png', 
                fullPage: true 
            });

            // Verificar estado de login usando sesión guardada
            await this.page.waitForTimeout(3000); // Dar tiempo para cargar
            
            const pageState = await this.page.evaluate(() => {
                const isLoggedIn = !!(
                    document.querySelector('a[href*="/c/"]') ||  // Enlaces de conversación
                    document.querySelector('[data-testid*="new-chat"]') ||  // Botón nuevo chat
                    document.querySelector('nav[aria-label*="Chat history"]') ||  // Navegación
                    (document.URL === 'https://chatgpt.com/' && 
                     !document.URL.includes('auth') && 
                     !document.body.textContent.toLowerCase().includes('sign in'))
                );
                
                const hasError = document.URL.includes('error') || 
                               document.URL.includes('auth');
                
                return {
                    isLoggedIn: isLoggedIn && !hasError,
                    currentUrl: document.URL,
                    hasError: hasError,
                    pageTitle: document.title
                };
            });

            console.log('🔍 Estado de sesión guardada:', pageState);
            
            const needsLogin = !pageState.isLoggedIn;

            if (needsLogin) {
                console.log('❌ =============================================');
                console.log('❌ SESIÓN NO ENCONTRADA - EJECUTA PASO PREVIO');
                console.log('❌ =============================================');
                console.log('');
                console.log('� SOLUCIÓN:');
                console.log('1. Para este script (Ctrl+C)');
                console.log('2. Ejecuta: ./run_puppeteer_with_login.sh');
                console.log('3. Sigue las instrucciones para hacer login manual');
                console.log('');
                console.log('💡 O haz login manual ahora:');
                console.log('👉 Abre Chrome normal y ve a https://chatgpt.com/');
                console.log('👉 Haz login con tu cuenta de pago');
                console.log('👉 Cierra Chrome completamente');
                console.log('👉 Ejecuta de nuevo este script');
                console.log('');
                console.log('⏳ Esperando 30 segundos por si quieres hacer login ahora...');
                
                // Esperar 30 segundos más corto
                for (let i = 30; i > 0; i--) {
                    process.stdout.write(`\r⏰ ${i} segundos restantes...`);
                    await this.page.waitForTimeout(1000);
                }
                console.log('\n');
                
                // Screenshot para debug
                await this.page.screenshot({ 
                    path: './debug_no_session.png', 
                    fullPage: true 
                });
                
                console.log('📸 Screenshot guardado: debug_no_session.png');
                console.log('⚠️ Continuando sin login (probablemente fallará)...');
            } else {
                console.log('✅ Sesión activa detectada - Continuando...');
            }
            
            return true;
        } catch (error) {
            console.error('❌ Error navegando a ChatGPT:', error);
            return false;
        }
    }

    async findProject(projectName) {
        console.log(`🔍 Buscando proyecto: "${projectName}"`);
        
        try {
            // Intentar ir directamente a la página de proyectos
            console.log('📂 Intentando ir a la página de proyectos...');
            
            // Buscar el botón/enlace de proyectos o historial en el sidebar
            const sidebarSelectors = [
                'nav a[href*="project"]',
                'button[aria-label*="project"]',
                '[data-testid*="project"]',
                'a[href="/gpts"]',
                'button:contains("Projects")',
                'nav button[data-testid*="history"]',
                'nav[aria-label*="Chat history"]',
                '[data-testid="history-button"]'
            ];

            let sidebarFound = false;
            for (const selector of sidebarSelectors) {
                try {
                    const element = await this.page.$(selector);
                    if (element) {
                        console.log(`✅ Encontrado elemento sidebar: ${selector}`);
                        await element.click();
                        await this.page.waitForTimeout(2000);
                        sidebarFound = true;
                        break;
                    }
                } catch (e) {
                    // Continuar con el siguiente selector
                }
            }

            // Screenshot del estado actual
            await this.page.screenshot({ 
                path: './debug_searching_project.png', 
                fullPage: true 
            });

            // Buscar el proyecto por nombre usando múltiples estrategias
            console.log(`🎯 Buscando proyecto específico: "${projectName}"`);
            
            const projectFound = await this.page.evaluate((name) => {
                // Estrategia 1: Buscar por texto exacto
                let elements = Array.from(document.querySelectorAll('*'));
                let projectElement = elements.find(el => 
                    el.textContent && 
                    el.textContent.trim().toLowerCase() === name.toLowerCase()
                );
                
                if (projectElement && projectElement.closest('a, button')) {
                    const clickable = projectElement.closest('a, button');
                    clickable.click();
                    return { found: true, method: 'exact-text' };
                }

                // Estrategia 2: Buscar por texto contenido
                projectElement = elements.find(el => 
                    el.textContent && 
                    el.textContent.trim().toLowerCase().includes(name.toLowerCase())
                );
                
                if (projectElement && projectElement.closest('a, button')) {
                    const clickable = projectElement.closest('a, button');
                    clickable.click();
                    return { found: true, method: 'contains-text' };
                }

                // Estrategia 3: Buscar en enlaces específicamente
                const links = Array.from(document.querySelectorAll('a, button'));
                projectElement = links.find(link => 
                    link.textContent && 
                    link.textContent.trim().toLowerCase().includes(name.toLowerCase())
                );

                if (projectElement) {
                    projectElement.click();
                    return { found: true, method: 'link-search' };
                }

                return { found: false, method: 'none' };
            }, projectName);

            if (projectFound.found) {
                console.log(`✅ Proyecto "${projectName}" encontrado (método: ${projectFound.method})`);
                await this.page.waitForTimeout(3000);
                
                // Screenshot después de seleccionar proyecto
                await this.page.screenshot({ 
                    path: './debug_project_selected.png', 
                    fullPage: true 
                });
                
                return true;
            } else {
                console.log(`⚠️ Proyecto "${projectName}" no encontrado`);
                return false;
            }

        } catch (error) {
            console.error('❌ Error buscando proyecto:', error);
            return false;
        }
    }

    async extractConversations() {
        console.log('📝 Extrayendo conversaciones del proyecto...');
        
        try {
            // Esperar a que carguen las conversaciones
            await this.page.waitForTimeout(5000);

            const conversations = await this.page.evaluate(() => {
                const results = [];
                
                // Selectores actualizados para ChatGPT 2024/2025
                const conversationSelectors = [
                    'a[href*="/c/"]',              // Enlaces de conversación
                    '[data-testid*="conversation"]', // Elementos con conversation en testid
                    'nav a[href^="/c/"]',          // Enlaces en navegación
                    '.conversation-item',          // Clase conversation-item
                    '[data-conversation-id]',      // Atributo data-conversation-id
                    'li a[href*="/c/"]',          // Enlaces en listas
                    'div[role="button"] a[href*="/c/"]', // Botones con enlaces
                    'button[data-testid*="history"]',     // Botones de historial
                    '.sidebar a[href*="/c/"]'      // Enlaces en sidebar
                ];

                let foundConversations = [];

                // Buscar conversaciones con diferentes selectores
                for (const selector of conversationSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        foundConversations = Array.from(elements);
                        break;
                    }
                }

                // Si no encontramos con selectores específicos, buscar por patrones
                if (foundConversations.length === 0) {
                    const allLinks = document.querySelectorAll('a');
                    foundConversations = Array.from(allLinks).filter(link => 
                        link.href && link.href.includes('/c/')
                    );
                }

                // Estrategia adicional: buscar elementos de texto que parezcan títulos de conversación
                if (foundConversations.length === 0) {
                    const textElements = document.querySelectorAll('div, span, p, h1, h2, h3, h4, h5, h6');
                    foundConversations = Array.from(textElements).filter(el => {
                        const text = el.textContent?.trim();
                        return text && 
                               text.length > 5 && 
                               text.length < 200 && 
                               !text.includes('\n') &&
                               el.closest('a, button');
                    });
                }

                // Extraer información de cada conversación
                foundConversations.forEach((element, index) => {
                    try {
                        const title = element.textContent?.trim() || 
                                    element.querySelector('[title]')?.getAttribute('title') || 
                                    `Conversación ${index + 1}`;
                        
                        const href = element.href || element.querySelector('a')?.href || '';
                        const conversationId = href.match(/\/c\/([^\/\?]+)/)?.[1] || '';
                        
                        if (title && title.length > 0) {
                            results.push({
                                title: title.substring(0, 500), // Limitar título
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
            
            // Screenshot para debugging si no encontramos conversaciones
            if (conversations.length === 0) {
                await this.page.screenshot({ 
                    path: './debug_no_conversations.png', 
                    fullPage: true 
                });
                console.log('📸 Screenshot guardado: debug_no_conversations.png');
            }
            
            // Log de las primeras conversaciones para debugging
            if (conversations.length > 0) {
                console.log('📋 Primeras conversaciones encontradas:');
                conversations.slice(0, 5).forEach((conv, idx) => {
                    console.log(`  ${idx + 1}. "${conv.title}" (ID: ${conv.conversationId})`);
                });
            }

            return conversations;

        } catch (error) {
            console.error('❌ Error extrayendo conversaciones:', error);
            return [];
        }
    }

    async updateConversationProjects(conversations, projectId) {
        console.log(`💾 Actualizando conversaciones para proyecto ID ${projectId}...`);
        
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
                    console.log(`  ✅ Actualizada por ID: "${conv.title}"`);
                } else {
                    // Buscar por título si no se encontró por ID
                    [result] = await this.connection.execute(
                        'UPDATE conversations SET project_id = ? WHERE title = ? AND project_id = 67',
                        [projectId, conv.title]
                    );

                    if (result.affectedRows > 0) {
                        updated++;
                        console.log(`  ✅ Actualizada por título: "${conv.title}"`);
                    } else {
                        notFound++;
                        console.log(`  ⚠️ No encontrada en BD: "${conv.title}"`);
                    }
                }
            } catch (error) {
                console.error(`  ❌ Error actualizando "${conv.title}":`, error);
                notFound++;
            }
        }

        console.log(`📊 Resultado: ${updated} actualizadas, ${notFound} no encontradas`);
        return { updated, notFound };
    }

    async testFirstProject() {
        const PROJECT_ID = 1; // VS Code Github
        
        try {
            // 1. Obtener información del proyecto
            const project = await this.getProjectInfo(PROJECT_ID);
            if (!project) {
                throw new Error(`Proyecto ID ${PROJECT_ID} no encontrado`);
            }

            console.log(`\n🎯 Procesando proyecto: ${project.name} (ID: ${project.id})`);

            // 2. Navegar a ChatGPT
            const chatgptLoaded = await this.navigateToChatGPT();
            if (!chatgptLoaded) {
                throw new Error('No se pudo cargar ChatGPT');
            }

            // 3. Buscar y seleccionar el proyecto
            const projectFound = await this.findProject(project.name);
            if (!projectFound) {
                console.log(`⚠️ Proyecto "${project.name}" no encontrado en ChatGPT`);
                // Continuar para probar la extracción general
            }

            // 4. Extraer conversaciones
            const conversations = await this.extractConversations();
            
            if (conversations.length === 0) {
                console.log('⚠️ No se encontraron conversaciones');
                return;
            }

            // 5. Actualizar base de datos
            const result = await this.updateConversationProjects(conversations, PROJECT_ID);
            
            console.log(`\n✅ Proceso completado para "${project.name}"`);
            console.log(`   - Conversaciones extraídas: ${conversations.length}`);
            console.log(`   - Actualizadas en BD: ${result.updated}`);
            console.log(`   - No encontradas: ${result.notFound}`);

        } catch (error) {
            console.error('❌ Error en testFirstProject:', error);
        }
    }

    async cleanup() {
        console.log('🧹 Limpiando recursos...');
        
        if (this.connection) {
            await this.connection.end();
            console.log('✅ Conexión BD cerrada');
        }
        
        if (this.browser) {
            await this.browser.close();
            console.log('✅ Puppeteer cerrado');
        }
    }
}

// Función principal
async function main() {
    const tester = new ChatGPTPuppeteerTest();
    
    try {
        await tester.init();
        await tester.connectDB();
        await tester.testFirstProject();
    } catch (error) {
        console.error('❌ Error general:', error);
    } finally {
        await tester.cleanup();
    }
}

// Ejecutar si es llamado directamente
main().catch(console.error);

export default ChatGPTPuppeteerTest;