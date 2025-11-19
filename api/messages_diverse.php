<?php
/**
 * 🎯 ENDPOINT DIVERSIDAD - Asegurar mensajes de diferentes conversaciones
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once '../database/db_connection.php';

try {
    $limit = intval($_GET['limit'] ?? 10);
    $search = trim($_GET['search'] ?? '');
    
    // ESTRATEGIA: Obtener conversaciones únicas y luego sus mensajes
    $conversations_sql = "SELECT DISTINCT c.id, c.title 
                         FROM conversations c 
                         INNER JOIN messages m ON m.conversation_id = c.id
                         WHERE 1=1 ";
    
    $conv_params = [];
    
    if (!empty($search)) {
        $conversations_sql .= " AND (m.content_text LIKE ? OR c.title LIKE ?) ";
        $conv_params[] = "%$search%";
        $conv_params[] = "%$search%";
    }
    
    $conversations_sql .= " ORDER BY c.created_at DESC LIMIT ?";
    $conv_params[] = $limit;
    
    // Obtener conversaciones
    $stmt = $pdo->prepare($conversations_sql);
    $stmt->execute($conv_params);
    $conversations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $formatted_data = [];
    
    // Para cada conversación, obtener su mensaje más reciente
    foreach ($conversations as $conv) {
        $msg_sql = "SELECT m.author_role as role, m.content_text as content, m.created_at
                    FROM messages m 
                    WHERE m.conversation_id = ? 
                    ORDER BY m.created_at DESC 
                    LIMIT 1";
        
        $msg_stmt = $pdo->prepare($msg_sql);
        $msg_stmt->execute([$conv['id']]);
        $message = $msg_stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($message) {
            $formatted_data[] = [
                'conversationTitle' => $conv['title'],
                'messageRole' => $message['role'],
                'messageContent' => $message['content'],
                'messageCreatedAt' => $message['created_at']
            ];
        }
    }
    
    echo json_encode([
        'success' => true,
        'data' => $formatted_data,
        'count' => count($formatted_data),
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>