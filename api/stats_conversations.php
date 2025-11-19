<?php
/**
 * Verificar cuántas conversaciones diferentes existen
 */

header('Content-Type: text/plain');
require_once '../database/db_connection.php';

try {
    // Contar total de conversaciones
    $stmt = $pdo->query("SELECT COUNT(*) as total FROM conversations");
    $total_conversations = $stmt->fetchColumn();
    
    echo "=== ESTADÍSTICAS DE CONVERSACIONES ===\n\n";
    echo "Total de conversaciones: " . $total_conversations . "\n\n";
    
    // Mostrar las primeras 10 conversaciones diferentes
    $stmt = $pdo->query("SELECT title, id FROM conversations ORDER BY created_at DESC LIMIT 10");
    $conversations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo "Últimas 10 conversaciones:\n";
    echo "-" * 50 . "\n";
    foreach ($conversations as $conv) {
        echo "- " . $conv['title'] . "\n";
    }
    
    echo "\n=== MENSAJES POR CONVERSACIÓN (Top 5) ===\n";
    
    // Contar mensajes por conversación
    $stmt = $pdo->query("
        SELECT c.title, COUNT(m.id) as message_count 
        FROM conversations c 
        LEFT JOIN messages m ON m.conversation_id = c.id 
        GROUP BY c.id, c.title 
        ORDER BY message_count DESC 
        LIMIT 5
    ");
    
    $stats = $stmt->fetchAll(PDO::FETCH_ASSOC);
    foreach ($stats as $stat) {
        echo $stat['title'] . ": " . $stat['message_count'] . " mensajes\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
?>