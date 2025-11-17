import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class ChatGPTPatientProjectLister {
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

    async waitForProjectsToLoad() {
        console.log('⏳ Esperando a que carguen todos los proyectos...');
        
        let attempts = 0;
        let maxAttempts = 20; // 2 minutos máximo
        let lastProjectCount = 0;
        let stableCount = 0;
        
        while (attempts < maxAttempts) {
            try {
                // Hacer scroll hacia abajo para forzar la carga
                await this.page.evaluate(() => {
                    const sidebar = document.querySelector('nav[aria-label="Chat history"]');
                    if (sidebar) {
                        sidebar.scrollTop = sidebar.scrollHeight;
                    }
                });
                
                await this.page.waitForTimeout(2000); // Esperar 2 segundos
                
                // Contar proyectos actuales
                const currentProjectCount = await this.page.evaluate(() => {
                    const selectors = [
                        'nav[aria-label="Chat history"] h3',
                        'nav[aria-label="Chat history"] [role="treeitem"]',
                        'nav[aria-label="Chat history"] a[href*="/g/"]',
                        'nav[aria-label="Chat history"] div[data-testid*="conversation"]',
                        '.group\\/sidebar-item'
                    ];
                    
                    const allElements = new Set();
                    selectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const text = el.textContent?.trim();
                                if (text && text.length > 2) {
                                    allElements.add(text);
                                }
                            });
                        } catch (e) {}
                    });
                    
                    return allElements.size;
                });
                
                console.log(`⏱️ Intento ${attempts + 1}: ${currentProjectCount} elementos encontrados`);
                
                // Si el número se mantiene estable por 3 intentos, consideramos que terminó de cargar
                if (currentProjectCount === lastProjectCount) {
                    stableCount++;
                    if (stableCount >= 3 && currentProjectCount > 10) {
                        console.log(`✅ Carga estabilizada con ${currentProjectCount} elementos`);
                        break;
                    }
                } else {
                    stableCount = 0;
                    lastProjectCount = currentProjectCount;
                }
                
                attempts++;
                
            } catch (error) {
                console.log(`⚠️ Error en intento ${attempts}: ${error.message}`);
                attempts++;
            }
        }
        
        return lastProjectCount;
    }

    async searchForBetoPersonalSpecifically() {
        console.log('🎯 Búsqueda específica de "Beto Personal"...');
        
        // Estrategia 1: Buscar directamente en el sidebar
        const found = await this.page.evaluate(() => {
            const searchTerms = ['beto personal', 'beto', 'personal'];
            const results = [];
            
            // Buscar en todos los elementos visibles
            const allElements = document.querySelectorAll('*');
            
            allElements.forEach(element => {
                const text = element.textContent?.toLowerCase() || '';
                
                searchTerms.forEach(term => {
                    if (text.includes(term) && text.length < 100) {
                        results.push({
                            text: element.textContent?.trim(),
                            tag: element.tagName,
                            className: element.className,
                            href: element.href || 'No link'
                        });
                    }
                });
            });
            
            return results;
        });
        
        console.log('🔍 Elementos que contienen "beto" o "personal":');
        found.forEach((item, index) => {
            console.log(`${index + 1}. "${item.text}" (${item.tag}.${item.className})`);
        });
        
        return found;
    }

    async getAllProjectsPatient() {
        try {
            console.log('🔍 Extrayendo TODOS los proyectos (con paciencia)...');
            
            // Primero esperar que aparezca el sidebar
            await this.page.waitForSelector('nav[aria-label="Chat history"]', { timeout: 30000 });
            console.log('✅ Sidebar de historial encontrado');
            
            // Esperar a que carguen todos los proyectos
            const totalElements = await this.waitForProjectsToLoad();
            
            // Ahora extraer todo el contenido
            const projects = await this.page.evaluate(() => {
                const projectElements = new Map();
                
                // Múltiples selectores para capturar todo
                const selectors = [
                    'nav[aria-label="Chat history"] *',
                    '[data-testid*="conversation"]',
                    '[data-testid*="project"]',
                    'a[href*="/g/"]',
                    'a[href*="/c/"]',
                    '.group\\/sidebar-item',
                    '[role="treeitem"]'
                ];
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent?.trim();
                            const href = el.href;
                            
                            if (text && text.length > 2 && text.length < 200) {
                                const key = `${text}_${href || 'nolink'}`;
                                if (!projectElements.has(key)) {
                                    projectElements.set(key, {
                                        text: text,
                                        href: href || 'No link',
                                        selector: selector,
                                        tag: el.tagName,
                                        className: el.className || 'No class'
                                    });
                                }
                            }
                        });
                    } catch (e) {
                        console.log(`Error con selector ${selector}:`, e.message);
                    }
                });
                
                return Array.from(projectElements.values());
            });
            
            console.log(`📋 TOTAL EXTRAÍDO: ${projects.length} elementos únicos:`);
            
            // Filtrar y mostrar los más relevantes
            const filtered = projects.filter(p => 
                p.text.length > 5 && 
                !p.text.includes('aria-label') && 
                !p.text.includes('button') &&
                !p.text.includes('New chat')
            );
            
            console.log(`📋 FILTRADOS: ${filtered.length} elementos relevantes:`);
            filtered.forEach((project, index) => {
                console.log(`${index + 1}. "${project.text}" (${project.tag})`);
            });
            
            return filtered;
            
        } catch (error) {
            console.error('❌ Error extrayendo proyectos:', error.message);
            return [];
        }
    }

    async findBetoPersonalProject() {
        console.log('\n🎯 BÚSQUEDA ESPECÍFICA "BETO PERSONAL":');
        console.log('======================================');
        
        const allProjects = await this.getAllProjectsPatient();
        
        // Buscar específicamente "Beto Personal"
        const betoMatches = allProjects.filter(p => {
            const text = p.text.toLowerCase();
            return text.includes('beto') || text.includes('personal');
        });
        
        console.log(`\n🔍 Elementos que contienen "beto" o "personal": ${betoMatches.length}`);
        betoMatches.forEach((match, index) => {
            console.log(`${index + 1}. "${match.text}" - ${match.href}`);
        });
        
        // Búsqueda adicional específica
        const specificSearch = await this.searchForBetoPersonalSpecifically();
        
        return { allProjects, betoMatches, specificSearch };
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
    const lister = new ChatGPTPatientProjectLister();
    
    try {
        await lister.init();
        await lister.connectDB();
        await lister.takeScreenshot('debug_patient_before_load');
        
        const results = await lister.findBetoPersonalProject();
        
        await lister.takeScreenshot('debug_patient_after_load');
        
        console.log('\n📊 RESUMEN FINAL:');
        console.log(`- Total elementos encontrados: ${results.allProjects.length}`);
        console.log(`- Coincidencias "beto/personal": ${results.betoMatches.length}`);
        console.log(`- Búsqueda específica: ${results.specificSearch.length}`);
        
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await lister.cleanup();
    }
}

main();