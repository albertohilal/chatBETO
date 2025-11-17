import mysql from 'mysql2/promise';
import fs from 'fs/promises';
import path from 'path';

async function limpiarMensajesSimple() {
    try {
        const configPath = path.join(process.cwd(), 'db_config.json');
        const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
        const connection = await mysql.createConnection(config);
        console.log('🔗 Conectado a MySQL');
        
        // Estrategia más simple: reemplazar directamente
        console.log('🧹 Limpiando mensajes problemáticos...');
        
        // 1. Mensajes que son solo "[object Object]" (con espacios variables)
        const [update1] = await connection.execute(`
            UPDATE messages 
            SET content_text = '[Contenido multimedia no disponible]'
            WHERE TRIM(REPLACE(content_text, '[object Object]', '')) = ''
              AND content_text LIKE '%[object Object]%'
        `);
        console.log(`✅ Mensajes solo-object limpiados: ${update1.affectedRows}`);
        
        // 2. Mensajes que empiezan con "[object Object]" pero tienen texto
        const [update2] = await connection.execute(`
            UPDATE messages 
            SET content_text = TRIM(REPLACE(content_text, '[object Object]', ''))
            WHERE content_text LIKE '%[object Object]%'
              AND TRIM(REPLACE(content_text, '[object Object]', '')) != ''
        `);
        console.log(`✅ Mensajes con texto recuperado: ${update2.affectedRows}`);
        
        // 3. Verificar resultados finales
        const [verificar] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE content_text LIKE '%[object Object]%'
        `);
        console.log(`📊 Mensajes problemáticos restantes: ${verificar[0].count}`);
        
        // 4. Contar mensajes válidos para búsqueda
        const [validos] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE content_text IS NOT NULL 
              AND content_text != '' 
              AND content_text NOT LIKE '%[object Object]%'
              AND author_role IN ('user', 'assistant')
        `);
        console.log(`✅ Mensajes válidos para búsqueda: ${validos[0].count}`);
        
        await connection.end();
        console.log('🎉 Limpieza completada');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

limpiarMensajesSimple();