// validateChats.js
// Script para validar la integridad de datos entre conversaciones y mensajes
// Identifica problemas comunes como contenido duplicado, relaciones rotas, etc.

const mysql = require('mysql2/promise');
require('dotenv').config();

async function runValidations() {
  const connection = await mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_DATABASE,
    timezone: '+00:00',
    charset: 'utf8mb4'
    // adapt a tus parámetros
  });

  const report = {};

  console.log('🔍 Iniciando validaciones de integridad de datos...\n');

  // 1) Mensajes cuyo content_text = título de conversación
  console.log('1️⃣ Buscando mensajes con contenido igual al título de conversación...');
  const [rows1] = await connection.execute(`
    SELECT m.id AS message_id,
           m.conversation_id,
           c.title AS conversation_title,
           m.content AS message_content,
           m.role AS author_role,
           m.created_at
      FROM messages m
      JOIN conversations c ON m.conversation_id = c.id
     WHERE m.content = c.title
     LIMIT 100
  `);
  report.sameAsTitle = {
    count: rows1.length,
    examples: rows1,
    description: "Mensajes donde content_text es idéntico al título de la conversación (posible error de datos)"
  };
  console.log(`   Encontrados: ${rows1.length} mensajes`);

  // 2) Mensajes huérfanos (conversación inexistente)
  console.log('2️⃣ Buscando mensajes huérfanos...');
  const [rows2] = await connection.execute(`
    SELECT m.id AS message_id,
           m.conversation_id,
           m.role AS author_role,
           m.created_at,
           SUBSTRING(m.content, 1, 100) AS content_preview
      FROM messages m
      LEFT JOIN conversations c ON m.conversation_id = c.id
     WHERE c.id IS NULL
     LIMIT 100
  `);
  report.orphanMessages = {
    count: rows2.length,
    examples: rows2,
    description: "Mensajes que referencian conversaciones que no existen"
  };
  console.log(`   Encontrados: ${rows2.length} mensajes huérfanos`);

  // 3) Conversaciones sin mensajes
  console.log('3️⃣ Buscando conversaciones vacías...');
  const [rows3] = await connection.execute(`
    SELECT c.id AS conversation_id,
           c.title,
           c.project_id,
           c.created_at,
           c.conversation_origin
      FROM conversations c
      LEFT JOIN messages m ON m.conversation_id = c.id
     GROUP BY c.id
     HAVING COUNT(m.id) = 0
     LIMIT 100
  `);
  report.emptyConversations = {
    count: rows3.length,
    examples: rows3,
    description: "Conversaciones que no tienen ningún mensaje asociado"
  };
  console.log(`   Encontradas: ${rows3.length} conversaciones vacías`);

  // 4) Verificar índice para optimización
  console.log('4️⃣ Verificando índices de optimización...');
  const [rows4] = await connection.execute(`
    SHOW INDEX FROM messages WHERE Key_name = 'idx_convo_created'
  `);
  report.indexExist = {
    exists: rows4.length > 0,
    details: rows4,
    description: "Índice de optimización para consultas por conversación y fecha"
  };
  console.log(`   Índice idx_convo_created: ${rows4.length > 0 ? 'EXISTS' : 'NOT FOUND'}`);

  // 5) Verificar columnas clave
  console.log('5️⃣ Verificando estructura de columnas...');
  const [colsConv] = await connection.execute(`
    SHOW COLUMNS FROM conversations 
      WHERE Field IN ('title','created_at','update_time','conversation_id')
  `);
  const [colsMsg] = await connection.execute(`
    SHOW COLUMNS FROM messages 
      WHERE Field IN ('content','role','created_at','conversation_id')
  `);
  report.columns = {
    conversations: colsConv,
    messages: colsMsg,
    description: "Estructura de columnas críticas para el funcionamiento"
  };
  console.log(`   Columnas conversations: ${colsConv.length}/4 encontradas`);
  console.log(`   Columnas messages: ${colsMsg.length}/4 encontradas`);

  // 6) Estadísticas generales
  console.log('6️⃣ Recopilando estadísticas generales...');
  const [statsConv] = await connection.execute(`
    SELECT COUNT(*) as total_conversations,
           COUNT(DISTINCT project_id) as unique_projects,
           MIN(created_at) as oldest_conversation,
           MAX(created_at) as newest_conversation
      FROM conversations
  `);
  
  const [statsMsg] = await connection.execute(`
    SELECT COUNT(*) as total_messages,
           COUNT(DISTINCT author_role) as unique_roles,
           COUNT(DISTINCT conversation_id) as conversations_with_messages,
           MIN(created_at) as oldest_message,
           MAX(created_at) as newest_message
      FROM messages
  `);

  report.generalStats = {
    conversations: statsConv[0],
    messages: statsMsg[0],
    description: "Estadísticas generales de la base de datos"
  };

  // 7) Verificar roles de mensajes
  console.log('7️⃣ Analizando roles de mensajes...');
  const [rolesStats] = await connection.execute(`
    SELECT author_role, 
           COUNT(*) as count,
           COUNT(DISTINCT conversation_id) as unique_conversations
      FROM messages 
     GROUP BY author_role 
     ORDER BY count DESC
  `);

  report.messageRoles = {
    distribution: rolesStats,
    description: "Distribución de roles en los mensajes"
  };

  // 8) Buscar mensajes con contenido sospechoso
  console.log('8️⃣ Buscando patrones sospechosos en contenido...');
  const [suspiciousContent] = await connection.execute(`
    SELECT COUNT(*) as count,
           'Empty content' as issue_type
      FROM messages 
     WHERE content_text IS NULL OR content_text = '' OR TRIM(content_text) = ''
    UNION ALL
    SELECT COUNT(*) as count,
           'Very short content' as issue_type  
      FROM messages
     WHERE LENGTH(TRIM(content_text)) < 3 AND content_text IS NOT NULL
    UNION ALL
    SELECT COUNT(*) as count,
           'Extremely long content' as issue_type
      FROM messages
     WHERE LENGTH(content_text) > 50000
  `);

  report.contentIssues = {
    issues: suspiciousContent,
    description: "Problemas potenciales en el contenido de mensajes"
  };

  await connection.end();
  console.log('\n✅ Validaciones completadas');
  return report;
}

(async () => {
  try {
    const result = await runValidations();
    
    console.log('\n📊 REPORTE COMPLETO:');
    console.log('='.repeat(50));
    
    // Mostrar resumen ejecutivo
    console.log('\n🎯 RESUMEN EJECUTIVO:');
    console.log(`- Mensajes con título como contenido: ${result.sameAsTitle.count}`);
    console.log(`- Mensajes huérfanos: ${result.orphanMessages.count}`);
    console.log(`- Conversaciones vacías: ${result.emptyConversations.count}`);
    console.log(`- Índice de optimización: ${result.indexExist.exists ? 'OK' : 'FALTANTE'}`);
    console.log(`- Total conversaciones: ${result.generalStats.conversations.total_conversations}`);
    console.log(`- Total mensajes: ${result.generalStats.messages.total_messages}`);

    // Mostrar alertas críticas
    const criticalIssues = [];
    if (result.sameAsTitle.count > 0) criticalIssues.push(`${result.sameAsTitle.count} mensajes con contenido=título`);
    if (result.orphanMessages.count > 0) criticalIssues.push(`${result.orphanMessages.count} mensajes huérfanos`);
    if (!result.indexExist.exists) criticalIssues.push('Falta índice de optimización');

    if (criticalIssues.length > 0) {
      console.log('\n🚨 ALERTAS CRÍTICAS:');
      criticalIssues.forEach(issue => console.log(`  ⚠️ ${issue}`));
    } else {
      console.log('\n✅ No se encontraron problemas críticos');
    }

    // Guardar reporte completo
    const fullReport = { 
      timestamp: new Date(), 
      report: result 
    };
    
    console.log('\n💾 Guardando reporte completo en validation_report.json...');
    const fs = require('fs').promises;
    await fs.writeFile(
      '/home/beto/Documentos/Github/chatBeto/chatBETO/database/validation_report.json',
      JSON.stringify(fullReport, null, 2)
    );

    console.log('\n📄 Reporte JSON completo:');
    console.log(JSON.stringify(fullReport, null, 2));
    
    process.exit(0);
  } catch (err) {
    console.error('❌ Error al ejecutar validaciones:', err);
    console.error('Stack trace:', err.stack);
    process.exit(1);
  }
})();