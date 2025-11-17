// puppeteer-scraper.js - Script para mapear gizmo_ids reales con proyectos
// npm install puppeteer mysql2 dotenv

import puppeteer from "puppeteer";
import mysql from "mysql2/promise";
import fs from "fs";

const CHATGPT_URL = "https://chat.openai.com";
const DB_CONFIG = JSON.parse(fs.readFileSync('db_config.json', 'utf8'));

// Configuración
const CONFIG = {
    headless: false,  // Cambiar a true para ejecución sin interfaz
    delayBetweenPages: 1000,  // ms entre cada conversación
    maxConversations: 50,     // Límite para pruebas iniciales
    enableScreenshots: true   // Guardar capturas de pantalla
};

class ChatGPTScraper {
    constructor() {
        this.browser = null;
        this.page = null;
        this.db = null;
        this.results = [];
        this.errors = [];
    }

    async init() {
        console.log("🚀 Iniciando ChatGPT Scraper...");
        
        // Conectar a base de datos
        this.db = await mysql.createConnection(DB_CONFIG);
        console.log("✅ Conectado a base de datos remota");
        
        // Iniciar browser
        this.browser = await puppeteer.launch({ 
            headless: CONFIG.headless,
            defaultViewport: { width: 1280, height: 720 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        
        // Configurar user agent
        await this.page.setUserAgent('Mozilla/5.0 (Linux; Ubuntu) Chrome/120.0.0.0');
        
        console.log("✅ Browser iniciado");
    }

    async login() {
        console.log("🔑 Navegando a ChatGPT...");
        
        try {
            await this.page.goto(CHATGPT_URL, { waitUntil: 'networkidle2', timeout: 60000 });
            
            // Tomar screenshot inicial
            if (CONFIG.enableScreenshots) {
                await this.page.screenshot({ path: 'screenshots/01-login-page.png' });
            }
            
            console.log("📄 Página cargada");
            console.log("⚠️  ACCIÓN MANUAL REQUERIDA:");
            console.log("   1. Inicia sesión en ChatGPT si es necesario");
            console.log("   2. Asegúrate de estar en la página principal");
            console.log("   3. Presiona ENTER en esta consola para continuar...");
            
            // Esperar input del usuario
            await new Promise(resolve => {
                process.stdin.once('data', resolve);
            });
            
            console.log("✅ Continuando con el scraping...");
            
        } catch (error) {
            console.error("❌ Error en login:", error.message);
            throw error;
        }
    }

    async getConversationList() {
        console.log("📋 Obteniendo lista de conversaciones...");
        
        try {
            // Navegar a la lista de conversaciones si no estamos ahí
            const currentUrl = this.page.url();
            if (!currentUrl.includes('chat.openai.com')) {
                await this.page.goto(`${CHATGPT_URL}/`, { waitUntil: 'networkidle2' });
            }
            
            // Esperar a que cargue la barra lateral con conversaciones
            await this.page.waitForSelector('[data-testid="conversation-turn"]', { timeout: 30000 });
            
            // Buscar enlaces de conversaciones en la barra lateral
            const conversationLinks = await this.page.$$eval(
                'a[href*="/c/"]', 
                links => links.map(link => ({
                    href: link.href,
                    title: link.textContent?.trim() || 'Sin título',
                    conversationId: link.href.match(/\/c\/([^?]+)/)?.[1] || null
                })).filter(item => item.conversationId)
            );
            
            console.log(`📊 Encontradas ${conversationLinks.length} conversaciones`);
            
            if (CONFIG.enableScreenshots) {
                await this.page.screenshot({ path: 'screenshots/02-conversation-list.png' });
            }
            
            return conversationLinks.slice(0, CONFIG.maxConversations);
            
        } catch (error) {
            console.error("❌ Error obteniendo conversaciones:", error.message);
            return [];
        }
    }

    async scrapeConversation(conversationLink, index) {
        console.log(`🔍 ${index + 1}. Procesando: ${conversationLink.title}`);
        
        try {
            // Abrir conversación
            await this.page.goto(conversationLink.href, { 
                waitUntil: 'networkidle2', 
                timeout: 30000 
            });
            
            // Esperar a que cargue el contenido
            await this.page.waitForSelector('[data-testid="conversation-turn"]', { timeout: 10000 });
            
            // Extraer información del proyecto desde la URL o DOM
            const url = this.page.url();
            let projectId = null;
            let gizmoId = null;
            
            // Método 1: Buscar gizmo_id en la URL (/g/ pattern)
            const gizmoMatch = url.match(/\/g\/([a-zA-Z0-9\-]+)/);
            if (gizmoMatch) {
                gizmoId = gizmoMatch[1];
                console.log(`   🎯 Gizmo ID encontrado en URL: ${gizmoId}`);
            }
            
            // Método 2: Buscar project_id en la URL (/p/ pattern)
            const projectMatch = url.match(/\/p\/([a-zA-Z0-9\-]+)/);
            if (projectMatch) {
                projectId = projectMatch[1];
                console.log(`   📂 Project ID encontrado en URL: ${projectId}`);
            }
            
            // Método 3: Buscar en atributos del DOM
            if (!gizmoId && !projectId) {
                try {
                    // Buscar elementos con data-* attributes relacionados a proyectos
                    const projectInfo = await this.page.evaluate(() => {
                        const projectElements = document.querySelectorAll('[data-project-id], [data-gizmo-id]');
                        const projectLinks = document.querySelectorAll('a[href*="/g/"], a[href*="/p/"]');
                        
                        let foundGizmo = null;
                        let foundProject = null;
                        
                        // Buscar en atributos
                        projectElements.forEach(el => {
                            if (el.dataset.projectId) foundProject = el.dataset.projectId;
                            if (el.dataset.gizmoId) foundGizmo = el.dataset.gizmoId;
                        });
                        
                        // Buscar en enlaces internos
                        projectLinks.forEach(link => {
                            const gMatch = link.href.match(/\/g\/([a-zA-Z0-9\-]+)/);
                            const pMatch = link.href.match(/\/p\/([a-zA-Z0-9\-]+)/);
                            if (gMatch) foundGizmo = gMatch[1];
                            if (pMatch) foundProject = pMatch[1];
                        });
                        
                        return { gizmoId: foundGizmo, projectId: foundProject };
                    });
                    
                    if (projectInfo.gizmoId) {
                        gizmoId = projectInfo.gizmoId;
                        console.log(`   🎯 Gizmo ID encontrado en DOM: ${gizmoId}`);
                    }
                    if (projectInfo.projectId) {
                        projectId = projectInfo.projectId;
                        console.log(`   📂 Project ID encontrado en DOM: ${projectId}`);
                    }
                    
                } catch (domError) {
                    console.log(`   ⚠️  Error extrayendo del DOM: ${domError.message}`);
                }
            }
            
            // Preparar resultado
            const result = {
                conversationId: conversationLink.conversationId,
                title: conversationLink.title,
                url: url,
                gizmoId: gizmoId,
                projectId: projectId,
                timestamp: new Date().toISOString(),
                success: true
            };
            
            this.results.push(result);
            
            // Actualizar base de datos si encontramos información
            if (gizmoId || projectId) {
                await this.updateDatabase(result);
                console.log(`   ✅ Información guardada`);
            } else {
                console.log(`   ⚠️  Sin información de proyecto`);
            }
            
            // Screenshot opcional
            if (CONFIG.enableScreenshots && (index + 1) <= 5) {
                await this.page.screenshot({ 
                    path: `screenshots/conv-${(index + 1).toString().padStart(3, '0')}.png` 
                });
            }
            
            return result;
            
        } catch (error) {
            console.error(`   ❌ Error procesando conversación: ${error.message}`);
            
            const errorResult = {
                conversationId: conversationLink.conversationId,
                title: conversationLink.title,
                error: error.message,
                success: false
            };
            
            this.errors.push(errorResult);
            return errorResult;
        }
    }

    async updateDatabase(result) {
        try {
            const { conversationId, gizmoId, projectId } = result;
            
            // Actualizar conversación con gizmo_id si lo encontramos
            if (gizmoId) {
                await this.db.execute(
                    `UPDATE iunaorg_chatBeto.conversations 
                     SET gizmo_id = ? 
                     WHERE id = ? OR conversation_id = ?`,
                    [gizmoId, conversationId, conversationId]
                );
            }
            
            // Si tenemos project_id, también lo guardamos
            if (projectId) {
                await this.db.execute(
                    `UPDATE iunaorg_chatBeto.conversations 
                     SET chatgpt_project_id = ? 
                     WHERE id = ? OR conversation_id = ?`,
                    [projectId, conversationId, conversationId]
                );
            }
            
            // También actualizar la tabla de proyectos con el gizmo_id mapeado
            if (gizmoId) {
                // Buscar proyecto que coincida con el patrón del gizmo_id o título
                await this.db.execute(
                    `UPDATE iunaorg_chatBeto.projects 
                     SET chatgpt_project_id = ? 
                     WHERE chatgpt_project_id IS NULL 
                     AND (name LIKE ? OR description LIKE ?)`,
                    [gizmoId, `%${result.title}%`, `%${result.title}%`]
                );
            }
            
        } catch (dbError) {
            console.error(`   ❌ Error actualizando BD: ${dbError.message}`);
        }
    }

    async run() {
        try {
            // Crear directorio para screenshots
            if (CONFIG.enableScreenshots && !fs.existsSync('screenshots')) {
                fs.mkdirSync('screenshots');
            }
            
            await this.init();
            await this.login();
            
            const conversations = await this.getConversationList();
            
            if (conversations.length === 0) {
                console.log("❌ No se encontraron conversaciones");
                return;
            }
            
            console.log(`🔄 Procesando ${conversations.length} conversaciones...`);
            
            for (let i = 0; i < conversations.length; i++) {
                await this.scrapeConversation(conversations[i], i);
                
                // Pausa entre conversaciones
                if (i < conversations.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, CONFIG.delayBetweenPages));
                }
            }
            
            // Guardar resultados
            await this.saveResults();
            
            console.log("\n✅ Scraping completado!");
            console.log(`📊 Resultados: ${this.results.length} exitosos, ${this.errors.length} errores`);
            
        } catch (error) {
            console.error("❌ Error fatal:", error);
        } finally {
            await this.cleanup();
        }
    }

    async saveResults() {
        const summary = {
            timestamp: new Date().toISOString(),
            total_processed: this.results.length + this.errors.length,
            successful: this.results.length,
            errors: this.errors.length,
            results: this.results,
            errors_detail: this.errors,
            config: CONFIG
        };
        
        fs.writeFileSync(
            'puppeteer-results.json', 
            JSON.stringify(summary, null, 2)
        );
        
        console.log("💾 Resultados guardados en: puppeteer-results.json");
    }

    async cleanup() {
        if (this.db) {
            await this.db.end();
            console.log("🔌 Conexión BD cerrada");
        }
        
        if (this.browser) {
            await this.browser.close();
            console.log("🔌 Browser cerrado");
        }
    }
}

// Ejecutar scraper
const scraper = new ChatGPTScraper();
scraper.run().catch(console.error);