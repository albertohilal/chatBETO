<?php
/**
 * 🎯 ENDPOINT SIMPLE - Copiando exactamente la consulta que funcionó
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
    $offset = intval($_GET['offset'] ?? 0);
    $search = trim($_GET['search'] ?? '');
    
    // CONSULTA ADAPTADA con JOIN correcto
    $sql = "SELECT 
                conversations.id as conversation_id, 
                conversations.project_id, 
                messages.created_at,
                conversations.title,
                messages.author_role as role,
                messages.content_text as content
            FROM conversations
            LEFT JOIN messages ON messages.conversation_id = conversations.id
            WHERE messages.content_text IS NOT NULL ";
    
    $params = [];
    
    if (!empty($search)) {
        $sql .= " AND (messages.content_text LIKE ? OR conversations.title LIKE ?) ";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }
    
    $sql .= " ORDER BY messages.created_at DESC 
              LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $messages = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Contar total para paginación
    $count_sql = "SELECT COUNT(*) as total
                  FROM conversations
                  LEFT JOIN messages ON messages.conversation_id = conversations.id
                  WHERE messages.content_text IS NOT NULL ";
    
    $count_params = [];
    
    if (!empty($search)) {
        $count_sql .= " AND (messages.content_text LIKE ? OR conversations.title LIKE ?) ";
        $count_params[] = "%$search%";
        $count_params[] = "%$search%";
    }
    
    $count_stmt = $pdo->prepare($count_sql);
    $count_stmt->execute($count_params);
    $total_messages = intval($count_stmt->fetchColumn());
    
    // Formatear para el frontend
    $formatted_data = array_map(function($row) {
        return [
            'conversationTitle' => $row['title'],
            'messageRole' => $row['role'],
            'messageContent' => $row['content'],
            'messageCreatedAt' => $row['created_at'] ?? date('Y-m-d H:i:s'),
            'projectId' => $row['project_id'],
            'conversationId' => $row['conversation_id']
        ];
    }, $messages);
    
    echo json_encode([
        'success' => true,
        'data' => $formatted_data,
        'count' => count($formatted_data),
        'totalMessages' => $total_messages,
        'pagination' => [
            'total' => $total_messages,
            'limit' => $limit,
            'offset' => $offset,
            'hasNext' => ($offset + $limit) < $total_messages,
            'hasPrev' => $offset > 0
        ],
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>