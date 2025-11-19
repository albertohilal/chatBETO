// checkDatabaseStructure.js
// Script para verificar la estructura real de las tablas en la base de datos

const mysql = require('mysql2/promise');
require('dotenv').config();

async function checkStructure() {
  const connection = await mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_DATABASE,
    timezone: '+00:00',
    charset: 'utf8mb4'
  });

  console.log('🔍 Verificando estructura de la base de datos...\n');

  try {
    // Verificar estructura de la tabla conversations
    console.log('📋 ESTRUCTURA DE LA TABLA conversations:');
    const [conversationsColumns] = await connection.execute('DESCRIBE conversations');
    console.table(conversationsColumns);

    console.log('\n📋 ESTRUCTURA DE LA TABLA messages:');
    const [messagesColumns] = await connection.execute('DESCRIBE messages');
    console.table(messagesColumns);

    console.log('\n📋 ESTRUCTURA DE LA TABLA projects:');
    const [projectsColumns] = await connection.execute('DESCRIBE projects');
    console.table(projectsColumns);

    // Verificar una muestra de datos
    console.log('\n📊 MUESTRA DE DATOS DE MESSAGES (5 filas):');
    const [sampleMessages] = await connection.execute(`
      SELECT * FROM messages LIMIT 5
    `);
    console.table(sampleMessages);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await connection.end();
  }
}

checkStructure();