import mysql from 'mysql2/promise';
import fs from 'fs/promises';
import path from 'path';

async function limpiarMensajesProblematicos() {
    try {
        // Cargar configuración
        const configPath = path.join(process.cwd(), 'db_config.json');
        const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
        
        // Conectar a MySQL
        const connection = await mysql.createConnection(config);
        console.log('🔗 Conectado a MySQL');
        
        // Contar mensajes problemáticos antes
        const [antes] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE content_text LIKE '%[object Object]%'
        `);
        
        console.log(`📊 Mensajes problemáticos encontrados: ${antes[0].count}`);
        
        // Opción 1: Limpiar mensajes que son solo [object Object]
        const [soloObjects] = await connection.execute(`
            UPDATE messages 
            SET content_text = '[Contenido multimedia no disponible]'
            WHERE content_text REGEXP '^(\\[object Object\\]\\s*)+$'
        `);
        
        console.log(`🧹 Mensajes limpiados (solo objects): ${soloObjects.affectedRows}`);
        
        // Opción 2: Limpiar mensajes que empiezan con [object Object] pero tienen texto después
        const [conTexto] = await connection.execute(`
            UPDATE messages 
            SET content_text = TRIM(REGEXP_REPLACE(content_text, '^(\\[object Object\\]\\s*)+', ''))
            WHERE content_text LIKE '%[object Object]%'
              AND content_text NOT REGEXP '^(\\[object Object\\]\\s*)+$'
              AND TRIM(REGEXP_REPLACE(content_text, '^(\\[object Object\\]\\s*)+', '')) != ''
        `);
        
        console.log(`✂️ Mensajes con texto recuperado: ${conTexto.affectedRows}`);
        
        // Verificar resultados
        const [despues] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE content_text LIKE '%[object Object]%'
        `);
        
        console.log(`📈 Mensajes problemáticos restantes: ${despues[0].count}`);
        
        // Si aún quedan mensajes problemáticos, mostrar ejemplos
        if (despues[0].count > 0) {
            const [ejemplos] = await connection.execute(`
                SELECT id, LEFT(content_text, 100) as sample 
                FROM messages 
                WHERE content_text LIKE '%[object Object]%'
                LIMIT 3
            `);
            
            console.log('\n🔍 Ejemplos restantes:');
            ejemplos.forEach(msg => {
                console.log(`- ${msg.sample}`);
            });
        }
        
        await connection.end();
        console.log('✅ Limpieza completada');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

limpiarMensajesProblematicos();