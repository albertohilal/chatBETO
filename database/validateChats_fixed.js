// validateChats_fixed.js
// Script corregido para validar la integridad de datos según la estructura real de la base de datos

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
  });

  const report = {};

  console.log('🔍 Iniciando validaciones de integridad de datos...\n');

  // 1) Mensajes cuyo content = título de conversación
  console.log('1️⃣ Buscando mensajes con contenido igual al título de conversación...');
  const [rows1] = await connection.execute(`
    SELECT m.id AS message_id,
           m.conversation_id,
           c.title AS conversation_title,
           m.content AS message_content,
           m.role,
           m.created_at
      FROM messages m
      JOIN conversations c ON m.conversation_id = c.id
     WHERE m.content = c.title
     LIMIT 100
  `);
  report.sameAsTitle = {
    count: rows1.length,
    examples: rows1,
    description: "Mensajes donde content es idéntico al título de la conversación (posible error de datos)"
  };
  console.log(`   Encontrados: ${rows1.length} mensajes`);

  // 2) Mensajes huérfanos (conversación inexistente)
  console.log('2️⃣ Buscando mensajes huérfanos...');
  const [rows2] = await connection.execute(`
    SELECT m.id AS message_id,
           m.conversation_id,
           m.role,
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

  // 5) Verificar columnas clave (nombres reales)
  console.log('5️⃣ Verificando estructura de columnas...');
  const [colsConv] = await connection.execute(`
    SHOW COLUMNS FROM conversations 
      WHERE Field IN ('title','created_at','updated_at_timestamp_ms','external_conversation_id')
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
           COUNT(DISTINCT role) as unique_roles,
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
    SELECT role, 
           COUNT(*) as count,
           COUNT(DISTINCT conversation_id) as unique_conversations
      FROM messages 
     GROUP BY role 
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
     WHERE content IS NULL OR content = '' OR TRIM(content) = ''
    UNION ALL
    SELECT COUNT(*) as count,
           'Very short content' as issue_type  
      FROM messages
     WHERE LENGTH(TRIM(content)) < 3 AND content IS NOT NULL
    UNION ALL
    SELECT COUNT(*) as count,
           'Extremely long content' as issue_type
      FROM messages
     WHERE LENGTH(content) > 50000
  `);

  report.contentIssues = {
    issues: suspiciousContent,
    description: "Problemas potenciales en el contenido de mensajes"
  };

  // 9) Verificar mensajes que podrían ser títulos en lugar de contenido real
  console.log('9️⃣ Buscando mensajes que parecen títulos en lugar de contenido...');
  const [titleLikeMessages] = await connection.execute(`
    SELECT m.id AS message_id,
           m.conversation_id,
           c.title AS conversation_title,
           m.content AS message_content,
           m.role,
           LENGTH(m.content) as content_length
      FROM messages m
      JOIN conversations c ON m.conversation_id = c.id
     WHERE LENGTH(m.content) < 100 
       AND m.content NOT LIKE '%.%'
       AND m.content NOT LIKE '%?%'
       AND m.content NOT LIKE '%!%'
       AND m.role = 'user'
     LIMIT 50
  `);
  
  report.titleLikeMessages = {
    count: titleLikeMessages.length,
    examples: titleLikeMessages,
    description: "Mensajes cortos de usuario que podrían ser títulos en lugar de contenido real"
  };
  console.log(`   Encontrados: ${titleLikeMessages.length} mensajes sospechosos`);

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
    console.log(`- Mensajes sospechosos (tipo título): ${result.titleLikeMessages.count}`);
    console.log(`- Índice de optimización: ${result.indexExist.exists ? 'OK' : 'FALTANTE'}`);
    console.log(`- Total conversaciones: ${result.generalStats.conversations.total_conversations}`);
    console.log(`- Total mensajes: ${result.generalStats.messages.total_messages}`);

    // Mostrar distribución de roles
    console.log('\n👥 DISTRIBUCIÓN DE ROLES:');
    result.messageRoles.distribution.forEach(role => {
      console.log(`   ${role.role}: ${role.count} mensajes en ${role.unique_conversations} conversaciones`);
    });

    // Mostrar problemas de contenido
    console.log('\n⚠️ PROBLEMAS DE CONTENIDO:');
    result.contentIssues.issues.forEach(issue => {
      console.log(`   ${issue.issue_type}: ${issue.count} mensajes`);
    });

    // Mostrar alertas críticas
    const criticalIssues = [];
    if (result.sameAsTitle.count > 0) criticalIssues.push(`${result.sameAsTitle.count} mensajes con contenido=título`);
    if (result.orphanMessages.count > 0) criticalIssues.push(`${result.orphanMessages.count} mensajes huérfanos`);
    if (result.titleLikeMessages.count > 10) criticalIssues.push(`${result.titleLikeMessages.count} mensajes que parecen títulos`);
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

    console.log('\n📄 Reporte guardado exitosamente!');
    
    process.exit(0);
  } catch (err) {
    console.error('❌ Error al ejecutar validaciones:', err);
    console.error('Stack trace:', err.stack);
    process.exit(1);
  }
})();