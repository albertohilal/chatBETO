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

class ChatGPTBetoPersonalDebug {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
    }

    async init() {
        console.log('🚀 Iniciando debug para proyecto "Beto Personal"...');
        
        try {
            // Conectar a Chrome existente con debug
            this.browser = await puppeteer.connect({
                browserURL: 'http://localhost:9222',
                defaultViewport: null
            });
            
            console.log('✅ Conectado a Chrome existente');
        } catch (error) {
            console.log('❌ Error conectando a Chrome:');
            console.log('💡 Ejecuta primero:');
            console.log('   google-chrome --remote-debugging-port=9222');
            console.log('   Luego haz login en ChatGPT');
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

    async getBetoPersonalProject() {
        console.log('📊 Obteniendo info del proyecto "Beto Personal"...');
        
        const [projects] = await this.connection.execute(`
            SELECT id, name, 
                   (SELECT COUNT(*) FROM conversations WHERE project_id = projects.id) as current_conversations
            FROM projects 
            WHERE name = 'Beto Personal'
            ORDER BY id ASC
        `);
        
        if (projects.length === 0) {
            throw new Error('Proyecto "Beto Personal" no encontrado en BD');
        }
        
        const project = projects[0];
        console.log(`✅ Proyecto encontrado: ID ${project.id}, ${project.current_conversations} conversaciones`);
        
        return project;
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

    async navigateToBetoPersonal() {
        console.log('🔍 Navegando específicamente al proyecto "Beto Personal"...');
        
        try {
            // Ir al home de ChatGPT primero
            await this.page.goto('https://chatgpt.com/', {
                waitUntil: 'networkidle2',
                timeout: 15000
            });
            
            await this.page.waitForTimeout(3000);
            
            // Screenshot antes de buscar
            await this.page.screenshot({ 
                path: './debug_before_beto_personal.png', 
                fullPage: true 
            });
            console.log('📸 Screenshot guardado: debug_before_beto_personal.png');
            
            // Buscar "Beto Personal" específicamente
            const projectFound = await this.page.evaluate(() => {
                console.log('🔍 Buscando "Beto Personal" en la página...');
                
                // Registrar todos los elementos de texto para debugging
                const allTextElements = Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && 
                    el.textContent.trim().length > 0 &&
                    el.children.length === 0  // Solo elementos hoja (sin hijos)
                );
                
                console.log(`📋 Encontrados ${allTextElements.length} elementos de texto`);
                
                // Buscar específicamente "Beto Personal"
                const betoElements = allTextElements.filter(el => 
                    el.textContent.toLowerCase().includes('beto') ||
                    el.textContent.toLowerCase().includes('personal')
                );
                
                console.log(`🔎 Elementos con "beto" o "personal": ${betoElements.length}`);
                betoElements.forEach((el, idx) => {
                    console.log(`  ${idx + 1}. "${el.textContent.trim()}" (${el.tagName})`);
                });
                
                // Intentar encontrar y hacer clic en "Beto Personal"
                const betoPersonalElement = allTextElements.find(el => 
                    el.textContent.trim().toLowerCase() === 'beto personal'
                );
                
                if (betoPersonalElement) {
                    console.log('✅ Encontrado elemento "Beto Personal"');
                    const clickable = betoPersonalElement.closest('a, button') || betoPersonalElement;
                    clickable.click();
                    return { found: true, method: 'exact-match', text: betoPersonalElement.textContent };
                }
                
                // Busqueda alternativa por coincidencia parcial
                const partialMatch = allTextElements.find(el => 
                    el.textContent.toLowerCase().includes('beto personal')
                );
                
                if (partialMatch) {
                    console.log('✅ Encontrado coincidencia parcial "Beto Personal"');
                    const clickable = partialMatch.closest('a, button') || partialMatch;
                    clickable.click();
                    return { found: true, method: 'partial-match', text: partialMatch.textContent };
                }
                
                return { found: false, method: 'none' };
            });
            
            console.log('🔍 Resultado búsqueda:', projectFound);
            
            if (projectFound.found) {
                console.log(`✅ Proyecto "Beto Personal" encontrado (${projectFound.method}): "${projectFound.text}"`);
                await this.page.waitForTimeout(4000); // Esperar más tiempo para cargar
                
                // Screenshot después de seleccionar
                await this.page.screenshot({ 
                    path: './debug_after_beto_personal.png', 
                    fullPage: true 
                });
                console.log('📸 Screenshot guardado: debug_after_beto_personal.png');
                
                return true;
            } else {
                console.log('⚠️ Proyecto "Beto Personal" no encontrado en la interfaz');
                
                // Screenshot para ver qué hay disponible
                await this.page.screenshot({ 
                    path: './debug_beto_personal_not_found.png', 
                    fullPage: true 
                });
                console.log('📸 Screenshot guardado: debug_beto_personal_not_found.png');
                
                return false;
            }
            
        } catch (error) {
            console.log(`❌ Error navegando a "Beto Personal":`, error.message);
            return false;
        }
    }

    async extractBetoPersonalConversations() {
        console.log('📝 Extrayendo conversaciones de "Beto Personal"...');
        
        try {
            await this.page.waitForTimeout(3000);

            const conversations = await this.page.evaluate(() => {
                console.log('📋 Iniciando extracción de conversaciones...');
                
                const results = [];
                
                // Buscar enlaces de conversación
                const conversationLinks = document.querySelectorAll('a[href*="/c/"]');
                console.log(`🔗 Encontrados ${conversationLinks.length} enlaces de conversación`);
                
                conversationLinks.forEach((link, index) => {
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
                        
                        // Log para debugging
                        console.log(`📄 Conversación ${index + 1}: "${title}" (${conversationId})`);
                        
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
                        console.log(`❌ Error procesando conversación ${index}:`, err);
                    }
                });

                // Eliminar duplicados por conversationId
                const uniqueResults = results.filter((conv, index, self) =>
                    index === self.findIndex(c => c.conversationId === conv.conversationId)
                );

                console.log(`✅ Extraídas ${uniqueResults.length} conversaciones únicas`);
                return uniqueResults;
            });

            console.log(`✅ ${conversations.length} conversaciones extraídas de "Beto Personal"`);
            
            // Mostrar conversaciones encontradas
            if (conversations.length > 0) {
                console.log('\n📋 Conversaciones encontradas en ChatGPT:');
                conversations.forEach((conv, idx) => {
                    console.log(`  ${idx + 1}. "${conv.title}" (${conv.conversationId})`);
                });
            } else {
                console.log('⚠️ No se encontraron conversaciones');
            }
            
            return conversations;

        } catch (error) {
            console.error('❌ Error extrayendo conversaciones:', error);
            return [];
        }
    }

    async compareWithDatabase(conversations, projectId) {
        console.log('\n🔍 Comparando con base de datos...');
        
        // Obtener conversaciones de "Beto Personal" en BD
        const [bdConversations] = await this.connection.execute(`
            SELECT id, title, conversation_id, project_id,
                   (SELECT name FROM projects WHERE id = conversations.project_id) as project_name
            FROM conversations 
            WHERE project_id = ?
        `, [projectId]);
        
        console.log(`📊 BD tiene ${bdConversations.length} conversaciones para "Beto Personal"`);
        
        if (bdConversations.length > 0) {
            console.log('\n📋 Conversaciones en BD:');
            bdConversations.forEach((conv, idx) => {
                console.log(`  ${idx + 1}. "${conv.title}" (${conv.conversation_id})`);
            });
        }
        
        // Buscar las 3 conversaciones esperadas en proyecto 67
        const expectedTitles = [
            'Renault Clio Manual Resumen',
            'Asesoría plomería experto',
            'Expertos en tecnologías nuevas'
        ];
        
        console.log('\n🔍 Buscando conversaciones esperadas en proyecto 67...');
        
        for (const expectedTitle of expectedTitles) {
            const [found] = await this.connection.execute(`
                SELECT id, title, conversation_id, project_id,
                       (SELECT name FROM projects WHERE id = conversations.project_id) as project_name
                FROM conversations 
                WHERE title LIKE ?
                LIMIT 1
            `, [`%${expectedTitle}%`]);
            
            if (found.length > 0) {
                const conv = found[0];
                console.log(`  ✅ "${expectedTitle}": Encontrada en proyecto "${conv.project_name}" (ID: ${conv.project_id})`);
            } else {
                console.log(`  ❌ "${expectedTitle}": NO encontrada en BD`);
            }
        }
        
        // Análisis de coincidencias
        console.log('\n📊 Análisis de coincidencias:');
        let matchedByChatGPT = 0;
        let matchedByBD = 0;
        
        conversations.forEach(chatgptConv => {
            const foundInBD = bdConversations.find(bdConv => 
                bdConv.conversation_id === chatgptConv.conversationId ||
                bdConv.title === chatgptConv.title
            );
            
            if (foundInBD) {
                matchedByChatGPT++;
                console.log(`  🔗 "${chatgptConv.title}" → Ya está en BD`);
            } else {
                console.log(`  🆕 "${chatgptConv.title}" → Nueva, no está en BD`);
            }
        });
        
        console.log(`\n📈 Resumen:`);
        console.log(`   ChatGPT: ${conversations.length} conversaciones`);
        console.log(`   BD: ${bdConversations.length} conversaciones`);
        console.log(`   Coincidencias: ${matchedByChatGPT}`);
        console.log(`   Nuevas en ChatGPT: ${conversations.length - matchedByChatGPT}`);
    }

    async debugBetoPersonal() {
        try {
            const project = await this.getBetoPersonalProject();
            await this.setupChatGPTPage();
            
            const projectFound = await this.navigateToBetoPersonal();
            
            if (!projectFound) {
                console.log('\n❌ No se pudo navegar al proyecto "Beto Personal"');
                console.log('💡 Posibles causas:');
                console.log('   - El proyecto no existe en ChatGPT web (solo móvil)');
                console.log('   - El proyecto tiene otro nombre en web');
                console.log('   - El proyecto está en una ubicación diferente');
                return;
            }
            
            const conversations = await this.extractBetoPersonalConversations();
            await this.compareWithDatabase(conversations, project.id);
            
            console.log('\n✅ Debug completo de "Beto Personal" finalizado');
            console.log('📸 Revisa los screenshots para más detalles');
            
        } catch (error) {
            console.error('\n❌ Error en debug:', error.message);
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
    const betoDebugger = new ChatGPTBetoPersonalDebug();
    
    try {
        await betoDebugger.init();
        await betoDebugger.connectDB();
        await betoDebugger.debugBetoPersonal();
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await betoDebugger.cleanup();
    }
}

main().catch(console.error);

export default ChatGPTBetoPersonalDebug;