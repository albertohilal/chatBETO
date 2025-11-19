<?php
header('Content-Type: text/plain');
require_once '../database/db_connection.php';

try {
    // Ver cuántos mensajes tiene cada conversación
    $sql = "SELECT c.title, COUNT(m.id) as message_count
            FROM conversations c 
            LEFT JOIN messages m ON m.conversation_id = c.id 
            WHERE m.content_text IS NOT NULL 
            GROUP BY c.id, c.title 
            ORDER BY message_count DESC 
            LIMIT 10";
    
    $stmt = $pdo->query($sql);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo "=== CONVERSACIONES CON MÁS MENSAJES ===\n\n";
    
    foreach ($results as $row) {
        echo $row['title'] . ": " . $row['message_count'] . " mensajes\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage();
}
?>