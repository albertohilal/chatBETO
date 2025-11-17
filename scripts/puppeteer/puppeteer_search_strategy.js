import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class ChatGPTSearchStrategy {
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

    async useSearchFunction() {
        try {
            console.log('🔍 Usando la función de búsqueda de ChatGPT...');
            
            // Buscar el botón o campo de búsqueda
            const searchSelectors = [
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                'button[aria-label*="Search"]',
                'button[aria-label*="search"]',
                '[data-testid*="search"]',
                '.search-input',
                '#search',
                'input[type="search"]'
            ];
            
            let searchElement = null;
            
            for (const selector of searchSelectors) {
                try {
                    await this.page.waitForSelector(selector, { timeout: 2000 });
                    searchElement = await this.page.$(selector);
                    if (searchElement) {
                        console.log(`✅ Campo de búsqueda encontrado: ${selector}`);
                        break;
                    }
                } catch (e) {
                    console.log(`⏭️ No encontrado: ${selector}`);
                }
            }
            
            if (searchElement) {
                console.log('🔤 Escribiendo "Beto Personal" en la búsqueda...');
                await searchElement.click();
                await searchElement.type('Beto Personal', { delay: 100 });
                await this.page.keyboard.press('Enter');
                
                await this.page.waitForTimeout(3000); // Esperar resultados
                
                const searchResults = await this.page.evaluate(() => {
                    // Buscar resultados de búsqueda
                    const results = [];
                    const resultElements = document.querySelectorAll('*');
                    
                    resultElements.forEach(el => {
                        const text = el.textContent?.toLowerCase();
                        if (text && (text.includes('beto') || text.includes('personal'))) {
                            results.push({
                                text: el.textContent?.trim(),
                                tag: el.tagName,
                                className: el.className,
                                href: el.href || 'No link'
                            });
                        }
                    });
                    
                    return results.slice(0, 20); // Primeros 20 resultados
                });
                
                console.log(`📋 Resultados de búsqueda (${searchResults.length}):`);
                searchResults.forEach((result, index) => {
                    console.log(`${index + 1}. "${result.text}" (${result.tag})`);
                });
                
                return searchResults;
            } else {
                console.log('❌ No se encontró campo de búsqueda');
                return [];
            }
            
        } catch (error) {
            console.error('❌ Error en búsqueda:', error.message);
            return [];
        }
    }

    async exploreCurrentPage() {
        console.log('🌐 Explorando página actual...');
        
        const pageInfo = await this.page.evaluate(() => {
            return {
                url: window.location.href,
                title: document.title,
                bodyText: document.body?.textContent?.substring(0, 1000) || 'No body text'
            };
        });
        
        console.log(`📍 URL actual: ${pageInfo.url}`);
        console.log(`📄 Título: ${pageInfo.title}`);
        
        // Buscar todos los elementos clickeables
        const clickableElements = await this.page.evaluate(() => {
            const elements = [];
            const selectors = ['a', 'button', '[role="button"]', '[onclick]'];
            
            selectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.textContent?.trim();
                        if (text && text.length > 2 && text.length < 100) {
                            elements.push({
                                text: text,
                                tag: el.tagName,
                                href: el.href || 'No link',
                                className: el.className || 'No class'
                            });
                        }
                    });
                } catch (e) {}
            });
            
            return elements.slice(0, 50); // Primeros 50
        });
        
        console.log(`🔗 Elementos clickeables encontrados (${clickableElements.length}):`);
        clickableElements.forEach((element, index) => {
            if (element.text.toLowerCase().includes('beto') || 
                element.text.toLowerCase().includes('personal') ||
                element.text.toLowerCase().includes('history') ||
                element.text.toLowerCase().includes('chat')) {
                console.log(`⭐ ${index + 1}. "${element.text}" (${element.tag}) - ${element.href}`);
            }
        });
        
        return clickableElements;
    }

    async tryDirectNavigation() {
        console.log('🎯 Intentando navegación directa a conversaciones...');
        
        const urlsToTry = [
            'https://chatgpt.com/g/g-beto-personal',
            'https://chatgpt.com/c/',
            'https://chatgpt.com/?model=gpt-4',
            'https://chatgpt.com/chat'
        ];
        
        for (const url of urlsToTry) {
            try {
                console.log(`🔗 Probando: ${url}`);
                await this.page.goto(url, { waitUntil: 'networkidle2', timeout: 10000 });
                await this.page.waitForTimeout(2000);
                
                const hasContent = await this.page.evaluate(() => {
                    const bodyText = document.body?.textContent?.toLowerCase() || '';
                    return {
                        hasBeto: bodyText.includes('beto'),
                        hasPersonal: bodyText.includes('personal'),
                        hasError: bodyText.includes('error') || bodyText.includes('not found'),
                        contentLength: bodyText.length
                    };
                });
                
                console.log(`📊 ${url}: Beto=${hasContent.hasBeto}, Personal=${hasContent.hasPersonal}, Error=${hasContent.hasError}, Contenido=${hasContent.contentLength} chars`);
                
                if (hasContent.hasBeto || hasContent.hasPersonal) {
                    await this.takeScreenshot(`direct_nav_${url.replace(/[^a-zA-Z0-9]/g, '_')}`);
                }
                
            } catch (error) {
                console.log(`❌ Error en ${url}: ${error.message}`);
            }
        }
    }

    async takeScreenshot(name) {
        try {
            await this.page.screenshot({ 
                path: `${name}.png`, 
                fullPage: false 
            });
            console.log(`📸 Screenshot guardado: ${name}.png`);
        } catch (error) {
            console.error(`❌ Error guardando screenshot: ${error.message}`);
        }
    }

    async fullInvestigation() {
        console.log('\n🕵️ INVESTIGACIÓN COMPLETA "BETO PERSONAL":');
        console.log('=========================================');
        
        await this.takeScreenshot('investigation_start');
        
        // 1. Explorar página actual
        const currentPageElements = await this.exploreCurrentPage();
        
        // 2. Usar función de búsqueda
        const searchResults = await this.useSearchFunction();
        await this.takeScreenshot('after_search');
        
        // 3. Navegación directa
        await this.tryDirectNavigation();
        
        console.log('\n📊 RESUMEN DE INVESTIGACIÓN:');
        console.log(`- Elementos clickeables en página actual: ${currentPageElements.length}`);
        console.log(`- Resultados de búsqueda: ${searchResults.length}`);
        
        return { currentPageElements, searchResults };
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
    const searcher = new ChatGPTSearchStrategy();
    
    try {
        await searcher.init();
        await searcher.connectDB();
        
        const results = await searcher.fullInvestigation();
        
    } catch (error) {
        console.error('\n❌ Error general:', error.message);
    } finally {
        await searcher.cleanup();
    }
}

main();