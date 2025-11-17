<?php
header('Content-Type: application/json; charset=UTF-8');
require_once 'db_connection.php';

try {
    // Test simple: obtener solo 10 mensajes recientes
    $sql = "SELECT 
                c.id as conversation_id,
                c.title,
                m.id,
                m.author_role,
                LEFT(m.content_text, 100) as message_content
            FROM messages m
            INNER JOIN conversations c ON m.conversation_id = c.id
            WHERE m.content_text IS NOT NULL
              AND m.content_text <> ''
              AND m.author_role IN ('user', 'assistant')
            ORDER BY m.created_at DESC
            LIMIT 10";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode([
        'success' => true,
        'count' => count($result),
        'messages' => $result
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>