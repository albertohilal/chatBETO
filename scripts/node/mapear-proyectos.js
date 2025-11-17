// mapear-proyectos.js - Script para mapear proyectos con gizmo_ids después del scraping
import mysql from "mysql2/promise";
import fs from "fs";

const DB_CONFIG = JSON.parse(fs.readFileSync('db_config.json', 'utf8'));

class ProjectMapper {
    constructor() {
        this.db = null;
        this.mappingResults = [];
    }

    async init() {
        console.log("🔗 Iniciando mapeador de proyectos...");
        this.db = await mysql.createConnection(DB_CONFIG);
        console.log("✅ Conectado a iunaorg_chatBeto");
    }

    async analyzeGizmoIds() {
        console.log("🔍 Analizando gizmo_ids encontrados...");
        
        // Obtener todos los gizmo_ids únicos de las conversaciones
        const [gizmoRows] = await this.db.execute(`
            SELECT gizmo_id, COUNT(*) as conversation_count,
                   GROUP_CONCAT(title SEPARATOR ' | ') as sample_titles
            FROM iunaorg_chatBeto.conversations 
            WHERE gizmo_id IS NOT NULL 
            GROUP BY gizmo_id 
            ORDER BY conversation_count DESC
        `);

        console.log(`📊 Encontrados ${gizmoRows.length} gizmo_ids únicos`);
        
        return gizmoRows;
    }

    async getProjectsWithoutGizmo() {
        console.log("📋 Obteniendo proyectos sin gizmo_id asignado...");
        
        const [projectRows] = await this.db.execute(`
            SELECT id, name, description 
            FROM iunaorg_chatBeto.projects 
            WHERE chatgpt_project_id IS NULL
            ORDER BY name
        `);

        console.log(`📂 Encontrados ${projectRows.length} proyectos sin mapear`);
        
        return projectRows;
    }

    calculateSimilarity(text1, text2) {
        // Función simple de similitud basada en palabras comunes
        const words1 = text1.toLowerCase().split(/\W+/).filter(w => w.length > 2);
        const words2 = text2.toLowerCase().split(/\W+/).filter(w => w.length > 2);
        
        const intersection = words1.filter(w => words2.includes(w));
        const union = [...new Set([...words1, ...words2])];
        
        return intersection.length / union.length;
    }

    async mapProjectsIntelligently() {
        console.log("\n🎯 Iniciando mapeo inteligente...");
        
        const gizmoData = await this.analyzeGizmoIds();
        const projects = await this.getProjectsWithoutGizmo();
        
        const mappings = [];
        
        for (const gizmo of gizmoData) {
            let bestMatch = null;
            let bestScore = 0;
            
            const gizmoTitles = gizmo.sample_titles || '';
            
            for (const project of projects) {
                // Calcular similitud entre títulos del gizmo y nombre del proyecto
                const score1 = this.calculateSimilarity(gizmoTitles, project.name);
                const score2 = this.calculateSimilarity(gizmoTitles, project.description || '');
                const finalScore = Math.max(score1, score2);
                
                if (finalScore > bestScore && finalScore > 0.3) {
                    bestScore = finalScore;
                    bestMatch = project;
                }
            }
            
            if (bestMatch) {
                mappings.push({
                    gizmo_id: gizmo.gizmo_id,
                    project_id: bestMatch.id,
                    project_name: bestMatch.name,
                    conversation_count: gizmo.conversation_count,
                    similarity_score: bestScore,
                    sample_titles: gizmo.sample_titles?.split(' | ').slice(0, 3).join(', ')
                });
                
                // Remover proyecto de la lista para evitar duplicados
                const index = projects.findIndex(p => p.id === bestMatch.id);
                if (index > -1) projects.splice(index, 1);
            } else {
                console.log(`⚠️  Sin mapeo para gizmo: ${gizmo.gizmo_id} (${gizmo.conversation_count} conv)`);
            }
        }
        
        return mappings;
    }

    async applyMappings(mappings) {
        console.log(`\n📝 Aplicando ${mappings.length} mapeos a la base de datos...`);
        
        for (const mapping of mappings) {
            try {
                // Actualizar proyecto con gizmo_id
                await this.db.execute(`
                    UPDATE iunaorg_chatBeto.projects 
                    SET chatgpt_project_id = ? 
                    WHERE id = ?
                `, [mapping.gizmo_id, mapping.project_id]);
                
                // Asignar conversaciones al proyecto
                await this.db.execute(`
                    UPDATE iunaorg_chatBeto.conversations 
                    SET project_id = ? 
                    WHERE gizmo_id = ?
                `, [mapping.project_id, mapping.gizmo_id]);
                
                console.log(`✅ ${mapping.project_name} ← ${mapping.conversation_count} conversaciones`);
                
            } catch (error) {
                console.error(`❌ Error mapeando ${mapping.project_name}: ${error.message}`);
            }
        }
    }

    async assignUnmappedConversations() {
        console.log("\n🔄 Asignando conversaciones sin gizmo_id al proyecto 'Conversaciones Generales'...");
        
        // Buscar proyecto "Conversaciones Generales"
        const [generalProject] = await this.db.execute(`
            SELECT id FROM iunaorg_chatBeto.projects 
            WHERE name = 'Conversaciones Generales' 
            LIMIT 1
        `);
        
        if (generalProject.length === 0) {
            console.log("⚠️  Proyecto 'Conversaciones Generales' no encontrado");
            return;
        }
        
        const generalProjectId = generalProject[0].id;
        
        // Asignar conversaciones sin gizmo_id
        const [result] = await this.db.execute(`
            UPDATE iunaorg_chatBeto.conversations 
            SET project_id = ? 
            WHERE gizmo_id IS NULL AND project_id IS NULL
        `, [generalProjectId]);
        
        console.log(`✅ ${result.affectedRows} conversaciones asignadas a 'Conversaciones Generales'`);
    }

    async generateSummary() {
        console.log("\n📊 Generando resumen final...");
        
        // Estadísticas finales
        const [stats] = await this.db.execute(`
            SELECT 
                COUNT(*) as total_projects,
                SUM(CASE WHEN chatgpt_project_id IS NOT NULL THEN 1 ELSE 0 END) as mapped_projects,
                SUM(CASE WHEN chatgpt_project_id IS NULL THEN 1 ELSE 0 END) as unmapped_projects
            FROM iunaorg_chatBeto.projects
        `);
        
        const [convStats] = await this.db.execute(`
            SELECT 
                COUNT(*) as total_conversations,
                SUM(CASE WHEN project_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_conversations,
                SUM(CASE WHEN project_id IS NULL THEN 1 ELSE 0 END) as unassigned_conversations
            FROM iunaorg_chatBeto.conversations
        `);
        
        const summary = {
            timestamp: new Date().toISOString(),
            projects: stats[0],
            conversations: convStats[0],
            mappings: this.mappingResults
        };
        
        fs.writeFileSync('mapping-summary.json', JSON.stringify(summary, null, 2));
        
        console.log("📊 RESUMEN FINAL:");
        console.log(`   Proyectos totales: ${stats[0].total_projects}`);
        console.log(`   Proyectos mapeados: ${stats[0].mapped_projects}`);
        console.log(`   Proyectos sin mapear: ${stats[0].unmapped_projects}`);
        console.log(`   Conversaciones totales: ${convStats[0].total_conversations}`);
        console.log(`   Conversaciones asignadas: ${convStats[0].assigned_conversations}`);
        console.log(`   Conversaciones sin asignar: ${convStats[0].unassigned_conversations}`);
        
        return summary;
    }

    async run() {
        try {
            await this.init();
            
            const mappings = await this.mapProjectsIntelligently();
            this.mappingResults = mappings;
            
            console.log(`\n🎯 MAPEOS PROPUESTOS (${mappings.length}):`);
            console.log("=".repeat(80));
            
            mappings.forEach((mapping, index) => {
                console.log(`${(index + 1).toString().padStart(2)}. ${mapping.project_name}`);
                console.log(`    Gizmo: ${mapping.gizmo_id}`);
                console.log(`    Conversaciones: ${mapping.conversation_count}`);
                console.log(`    Similitud: ${(mapping.similarity_score * 100).toFixed(1)}%`);
                console.log(`    Ejemplos: ${mapping.sample_titles}`);
                console.log(`    ${'-'.repeat(70)}`);
            });
            
            console.log("\n¿Aplicar estos mapeos? (y/n): ");
            
            // En un entorno real, podrías usar readline para input del usuario
            // Por ahora aplicamos automáticamente
            console.log("🚀 Aplicando mapeos automáticamente...");
            
            await this.applyMappings(mappings);
            await this.assignUnmappedConversations();
            await this.generateSummary();
            
            console.log("\n✅ Mapeo completado exitosamente!");
            
        } catch (error) {
            console.error("❌ Error en el mapeo:", error);
        } finally {
            if (this.db) {
                await this.db.end();
                console.log("🔌 Conexión cerrada");
            }
        }
    }
}

// Ejecutar mapeador
const mapper = new ProjectMapper();
mapper.run().catch(console.error);