import puppeteer from 'puppeteer';
import mysql from 'mysql2/promise';
import fs from 'fs';

class CompleteProjectAuditor {
    constructor() {
        this.browser = null;
        this.page = null;
        this.connection = null;
        this.auditResults = [];
        this.reassignmentPlan = [];
    }

    async init() {
        try {
            console.log('🚀 Iniciando auditoría completa de proyectos...');
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

    async getAllProjectsFromDB() {
        console.log('📊 Obteniendo todos los proyectos desde la base de datos...');
        
        const [rows] = await this.connection.execute(`
            SELECT 
                p.id,
                p.name,
                COUNT(c.id) as current_conversation_count
            FROM projects p 
            LEFT JOIN conversations c ON p.id = c.project_id 
            GROUP BY p.id, p.name
            ORDER BY p.id
        `);
        
        console.log(`📋 Total proyectos en BD: ${rows.length}`);
        
        return rows;
    }

    async findProjectUrlPattern(projectName) {
        // Buscar en la página principal si hay enlaces a proyectos
        try {
            await this.page.goto('https://chatgpt.com/', { waitUntil: 'networkidle2' });
            await this.page.waitForTimeout(2000);
            
            const projectUrl = await this.page.evaluate((name) => {
                const links = document.querySelectorAll('a[href*="/g/g-p-"]');
                
                for (const link of links) {
                    const text = link.textContent?.trim().toLowerCase();
                    const searchName = name.toLowerCase();
                    
                    // Búsqueda fuzzy
                    if (text && (text.includes(searchName) || searchName.includes(text))) {
                        return link.href;
                    }
                }
                
                return null;
            }, projectName);
            
            return projectUrl;
            
        } catch (error) {
            console.log(`⚠️ Error buscando URL para "${projectName}": ${error.message}`);
            return null;
        }
    }

    async extractConversationsFromProject(projectUrl) {
        if (!projectUrl) return [];
        
        try {
            console.log(`   🌐 Navegando a: ${projectUrl}`);
            await this.page.goto(projectUrl, { waitUntil: 'networkidle2', timeout: 15000 });
            await this.page.waitForTimeout(3000);
            
            // Scroll para cargar conversaciones
            await this.page.evaluate(() => {
                const sidebar = document.querySelector('nav[aria-label="Chat history"]');
                if (sidebar) {
                    sidebar.scrollTop = sidebar.scrollHeight;
                }
            });
            
            await this.page.waitForTimeout(2000);
            
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
                            title: title
                        });
                    }
                });
                
                return results;
            });
            
            console.log(`   📊 ${conversations.length} conversaciones encontradas`);
            return conversations;
            
        } catch (error) {
            console.log(`   ❌ Error extrayendo conversaciones: ${error.message}`);
            return [];
        }
    }

    async auditSingleProject(project) {
        console.log(`\n🔍 Auditando: "${project.name}" (ID: ${project.id})`);
        console.log(`   📊 Conversaciones actuales en BD: ${project.current_conversation_count}`);
        
        // Buscar URL del proyecto
        const projectUrl = await this.findProjectUrlPattern(project.name);
        
        if (!projectUrl) {
            console.log(`   ⚠️ No se encontró URL para "${project.name}"`);
            
            this.auditResults.push({
                projectId: project.id,
                projectName: project.name,
                status: 'no_url_found',
                currentInDB: project.current_conversation_count,
                foundInWeb: 0,
                conversationsInWeb: [],
                needsReassignment: []
            });
            
            return;
        }
        
        // Extraer conversaciones del proyecto
        const webConversations = await this.extractConversationsFromProject(projectUrl);
        
        // Verificar qué conversaciones están mal asignadas
        const needsReassignment = [];
        
        for (const webConv of webConversations) {
            // Buscar si esta conversación está asignada a otro proyecto
            const [existing] = await this.connection.execute(`
                SELECT c.id, c.project_id, p.name as current_project
                FROM conversations c
                JOIN projects p ON c.project_id = p.id
                WHERE c.conversation_id = ?
            `, [webConv.conversation_id]);
            
            if (existing.length > 0 && existing[0].project_id !== project.id) {
                needsReassignment.push({
                    conversationId: webConv.conversation_id,
                    title: webConv.title,
                    currentProjectId: existing[0].project_id,
                    currentProjectName: existing[0].current_project,
                    shouldBeProjectId: project.id,
                    shouldBeProjectName: project.name
                });
            }
        }
        
        console.log(`   🌐 Conversaciones en web: ${webConversations.length}`);
        console.log(`   🔄 Necesitan reasignación: ${needsReassignment.length}`);
        
        if (needsReassignment.length > 0) {
            console.log(`   📋 Conversaciones a reasignar:`);
            needsReassignment.forEach((conv, index) => {
                console.log(`      ${index + 1}. "${conv.title}" (desde "${conv.currentProjectName}")`);
            });
        }
        
        this.auditResults.push({
            projectId: project.id,
            projectName: project.name,
            status: 'audited',
            currentInDB: project.current_conversation_count,
            foundInWeb: webConversations.length,
            conversationsInWeb: webConversations,
            needsReassignment: needsReassignment
        });
        
        // Agregar a plan de reasignación
        this.reassignmentPlan.push(...needsReassignment);
    }

    async auditAllProjects() {
        console.log('\n🔍 INICIANDO AUDITORÍA COMPLETA DE PROYECTOS');
        console.log('============================================');
        
        const projects = await this.getAllProjectsFromDB();
        
        let processedCount = 0;
        const totalProjects = Math.min(projects.length, 10); // Procesar solo primeros 10 para prueba
        
        console.log(`📊 Auditando primeros ${totalProjects} proyectos de ${projects.length} total...`);
        
        for (const project of projects.slice(0, totalProjects)) {
            try {
                await this.auditSingleProject(project);
                processedCount++;
                
                // Pausa entre proyectos para evitar sobrecarga
                await new Promise(resolve => setTimeout(resolve, 2000));
                
            } catch (error) {
                console.log(`❌ Error auditando "${project.name}": ${error.message}`);
            }
        }
        
        console.log(`\n✅ Auditoría completada: ${processedCount}/${totalProjects} proyectos`);
    }

    async generateAuditReport() {
        console.log('\n📊 GENERANDO REPORTE DE AUDITORÍA');
        console.log('=================================');
        
        const projectsWithUrls = this.auditResults.filter(r => r.status === 'audited');
        const projectsWithoutUrls = this.auditResults.filter(r => r.status === 'no_url_found');
        const totalReassignments = this.reassignmentPlan.length;
        
        console.log(`📋 Proyectos auditados: ${this.auditResults.length}`);
        console.log(`✅ Con URLs encontradas: ${projectsWithUrls.length}`);
        console.log(`❌ Sin URLs: ${projectsWithoutUrls.length}`);
        console.log(`🔄 Total conversaciones a reasignar: ${totalReassignments}`);
        
        if (projectsWithUrls.length > 0) {
            console.log('\n📈 PROYECTOS CON CONVERSACIONES:');
            projectsWithUrls
                .filter(p => p.foundInWeb > 0)
                .sort((a, b) => b.foundInWeb - a.foundInWeb)
                .forEach((project, index) => {
                    console.log(`${index + 1}. "${project.projectName}" - ${project.foundInWeb} conversaciones (${project.needsReassignment.length} a reasignar)`);
                });
        }
        
        if (totalReassignments > 0) {
            console.log('\n🔄 PLAN DE REASIGNACIÓN:');
            const groupedBySource = {};
            
            this.reassignmentPlan.forEach(item => {
                if (!groupedBySource[item.currentProjectName]) {
                    groupedBySource[item.currentProjectName] = [];
                }
                groupedBySource[item.currentProjectName].push(item);
            });
            
            Object.keys(groupedBySource).forEach(sourceName => {
                const items = groupedBySource[sourceName];
                console.log(`\n📂 Desde "${sourceName}" (${items.length} conversaciones):`);
                items.forEach((item, index) => {
                    console.log(`   ${index + 1}. "${item.title}" → "${item.shouldBeProjectName}"`);
                });
            });
        }
        
        // Guardar reporte en archivo
        const reportData = {
            timestamp: new Date().toISOString(),
            summary: {
                totalProjects: this.auditResults.length,
                projectsWithUrls: projectsWithUrls.length,
                projectsWithoutUrls: projectsWithoutUrls.length,
                totalReassignments: totalReassignments
            },
            auditResults: this.auditResults,
            reassignmentPlan: this.reassignmentPlan
        };
        
        fs.writeFileSync('audit_report.json', JSON.stringify(reportData, null, 2));
        console.log('\n💾 Reporte guardado en: audit_report.json');
        
        return reportData;
    }

    async executeReassignments(dryRun = true) {
        if (this.reassignmentPlan.length === 0) {
            console.log('✅ No hay reasignaciones necesarias');
            return;
        }
        
        console.log(`\n🔄 ${dryRun ? 'SIMULANDO' : 'EJECUTANDO'} REASIGNACIONES`);
        console.log('=====================================');
        
        let successCount = 0;
        
        for (const item of this.reassignmentPlan) {
            try {
                if (!dryRun) {
                    await this.connection.execute(`
                        UPDATE conversations 
                        SET project_id = ? 
                        WHERE conversation_id = ?
                    `, [item.shouldBeProjectId, item.conversationId]);
                }
                
                console.log(`${dryRun ? '🔍' : '✅'} "${item.title}" → "${item.shouldBeProjectName}"`);
                successCount++;
                
            } catch (error) {
                console.log(`❌ Error reasignando "${item.title}": ${error.message}`);
            }
        }
        
        console.log(`\n📊 ${dryRun ? 'Simularían' : 'Ejecutadas'} ${successCount}/${this.reassignmentPlan.length} reasignaciones`);
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
    const auditor = new CompleteProjectAuditor();
    
    try {
        await auditor.init();
        await auditor.connectDB();
        
        // Ejecutar auditoría completa
        await auditor.auditAllProjects();
        
        // Generar reporte
        const report = await auditor.generateAuditReport();
        
        // Simular reasignaciones (cambiar a false para ejecutar realmente)
        await auditor.executeReassignments(true);
        
        console.log('\n✅ AUDITORÍA COMPLETA TERMINADA');
        console.log('Revisa el archivo audit_report.json para detalles completos');
        
    } catch (error) {
        console.error('\n❌ Error en auditoría:', error.message);
    } finally {
        await auditor.cleanup();
    }
}

main();