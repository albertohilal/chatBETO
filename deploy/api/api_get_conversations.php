<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../database/db_connection.php';

try {
    $project_id = $_GET['project_id'] ?? null;
    
    $sql = "SELECT 
                c.id,
                c.title,
                c.created_at,
                c.create_time,
                c.project_id,
                c.openai_thread_id,
                p.name as project_name,
                (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id";
    
    $params = [];
    
    if ($project_id) {
        $sql .= " WHERE c.project_id = :project_id";
        $params['project_id'] = $project_id;
    }
    
    $sql .= " ORDER BY c.created_at DESC, c.create_time DESC LIMIT 50";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    
    $conversations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear datos
    foreach ($conversations as &$conversation) {
        $conversation['id'] = $conversation['id'];
        $conversation['message_count'] = (int)$conversation['message_count'];
        $conversation['has_openai_thread'] = !empty($conversation['openai_thread_id']);
        
        // Formatear fecha
        if ($conversation['created_at']) {
            $conversation['formatted_date'] = date('d/m/Y H:i', strtotime($conversation['created_at']));
        } elseif ($conversation['create_time']) {
            $conversation['formatted_date'] = date('d/m/Y H:i', $conversation['create_time']);
        } else {
            $conversation['formatted_date'] = 'Sin fecha';
        }
    }
    
    echo json_encode($conversations);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al cargar conversaciones: ' . $e->getMessage()]);
}