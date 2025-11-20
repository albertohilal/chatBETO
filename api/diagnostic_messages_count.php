<?php
/**
 * 🔍 Diagnóstico de conteo de mensajes - para identificar discrepancias
 */

header('Content-Type: application/json');
require_once '../database/db_connection.php';

try {
    echo "=== DIAGNÓSTICO DE CONTEO DE MENSAJES ===\n\n";
    
    // 1. Total absoluto de mensajes
    $stmt = $pdo->query("SELECT COUNT(*) as total FROM messages");
    $total_absoluto = $stmt->fetchColumn();
    echo "📊 Total absoluto en tabla messages: $total_absoluto\n";
    
    // 2. Mensajes con content NOT NULL
    $stmt = $pdo->query("SELECT COUNT(*) as total FROM messages WHERE content IS NOT NULL");
    $not_null = $stmt->fetchColumn();
    echo "📊 Mensajes con content NOT NULL: $not_null\n";
    
    // 3. Mensajes con content no vacío
    $stmt = $pdo->query("SELECT COUNT(*) as total FROM messages WHERE content IS NOT NULL AND content != ''");
    $not_empty = $stmt->fetchColumn();
    echo "📊 Mensajes con content no vacío: $not_empty\n";
    
    // 4. Sin texto de "no disponible"
    $stmt = $pdo->query("
        SELECT COUNT(*) as total 
        FROM messages 
        WHERE content IS NOT NULL 
        AND content != '' 
        AND content NOT LIKE '%[Respuesta del asistente no disponible]%'
    ");
    $sin_no_disponible = $stmt->fetchColumn();
    echo "📊 Sin '[Respuesta del asistente no disponible]': $sin_no_disponible\n";
    
    // 5. Sin contenido multimedia
    $stmt = $pdo->query("
        SELECT COUNT(*) as total 
        FROM messages 
        WHERE content IS NOT NULL 
        AND content != '' 
        AND content NOT LIKE '%[Respuesta del asistente no disponible]%'
        AND content NOT LIKE '%[Contenido multimedia no disponible]%'
    ");
    $sin_multimedia = $stmt->fetchColumn();
    echo "📊 Sin '[Contenido multimedia no disponible]': $sin_multimedia\n";
    
    // 6. Con longitud mayor a 10 (FILTRO ACTUAL)
    $stmt = $pdo->query("
        SELECT COUNT(*) as total 
        FROM messages 
        WHERE content IS NOT NULL 
        AND content != '' 
        AND content NOT LIKE '%[Respuesta del asistente no disponible]%'
        AND content NOT LIKE '%[Contenido multimedia no disponible]%'
        AND LENGTH(content) > 10
    ");
    $filtro_actual = $stmt->fetchColumn();
    echo "📊 Con filtros actuales (LENGTH > 10): $filtro_actual\n";
    
    // 7. Mensajes únicos por conversación
    $stmt = $pdo->query("
        SELECT COUNT(DISTINCT conversation_id) as total 
        FROM messages 
        WHERE content IS NOT NULL 
        AND content != '' 
        AND LENGTH(content) > 10
    ");
    $conversaciones_unicas = $stmt->fetchColumn();
    echo "📊 Conversaciones únicas con mensajes válidos: $conversaciones_unicas\n";
    
    // 8. Con JOIN a conversations (como en la consulta actual)
    $stmt = $pdo->query("
        SELECT COUNT(*) as total
        FROM conversations
        LEFT JOIN messages ON messages.conversation_id = conversations.id
        WHERE messages.content IS NOT NULL 
        AND messages.content != '' 
        AND messages.content NOT LIKE '%[Respuesta del asistente no disponible]%' 
        AND messages.content NOT LIKE '%[Contenido multimedia no disponible]%'
        AND LENGTH(messages.content) > 10
    ");
    $con_join = $stmt->fetchColumn();
    echo "📊 Con JOIN a conversations (consulta actual): $con_join\n";
    
    echo "\n=== ANÁLISIS ===\n";
    echo "🔍 Mensajes filtrados por NULL: " . ($total_absoluto - $not_null) . "\n";
    echo "🔍 Mensajes filtrados por vacíos: " . ($not_null - $not_empty) . "\n";
    echo "🔍 Mensajes filtrados por 'no disponible': " . ($not_empty - $sin_no_disponible) . "\n";
    echo "🔍 Mensajes filtrados por 'multimedia': " . ($sin_no_disponible - $sin_multimedia) . "\n";
    echo "🔍 Mensajes filtrados por longitud: " . ($sin_multimedia - $filtro_actual) . "\n";
    
    echo "\n=== SAMPLES ===\n";
    
    // Mostrar ejemplos de mensajes filtrados
    $stmt = $pdo->query("
        SELECT content, LENGTH(content) as len 
        FROM messages 
        WHERE content IS NOT NULL 
        AND content != '' 
        AND LENGTH(content) <= 10 
        LIMIT 5
    ");
    $samples = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo "🔍 Ejemplos de mensajes filtrados por longitud <= 10:\n";
    foreach ($samples as $sample) {
        echo "   - '" . substr($sample['content'], 0, 50) . "' (len: {$sample['len']})\n";
    }
    
} catch (Exception $e) {
    echo "❌ ERROR: " . $e->getMessage();
}
?>