import mysql from 'mysql2/promise';
import fs from 'fs/promises';
import path from 'path';

async function investigarProblema() {
    try {
        // Cargar configuración
        const configPath = path.join(process.cwd(), 'db_config.json');
        const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
        
        // Conectar a MySQL
        const connection = await mysql.createConnection(config);
        console.log('🔗 Conectado a MySQL');
        
        // Contar mensajes con [object Object]
        const [objectMessages] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE content_text LIKE '%[object Object]%'
        `);
        
        console.log(`📊 Mensajes con [object Object]: ${objectMessages[0].count}`);
        
        // Obtener algunos ejemplos
        const [ejemplos] = await connection.execute(`
            SELECT id, conversation_id, author_role, 
                   LEFT(content_text, 200) as sample_content
            FROM messages 
            WHERE content_text LIKE '%[object Object]%'
            LIMIT 5
        `);
        
        console.log('\n🔍 Ejemplos de contenido problemático:');
        ejemplos.forEach(msg => {
            console.log(`ID: ${msg.id}`);
            console.log(`Rol: ${msg.author_role}`);
            console.log(`Contenido: ${msg.sample_content}`);
            console.log('---');
        });
        
        // Contar mensajes totales
        const [totalMessages] = await connection.execute(`
            SELECT COUNT(*) as count FROM messages
        `);
        
        console.log(`\n📈 Total mensajes: ${totalMessages[0].count}`);
        
        await connection.end();
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

investigarProblema();