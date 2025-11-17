<?php
header('Content-Type: application/json; charset=utf-8');
require_once '../database/db_connection.php';

try {
    // Parámetros de entrada
    $query = $_GET['query'] ?? '';
    $project_id = $_GET['project_id'] ?? '';
    $search_type = $_GET['search_type'] ?? 'messages';
    $limit = 100;
    
    $results = [];
    
    if ($search_type === 'conversations') {
        // Buscar en títulos de conversaciones
        $sql = "
            SELECT 
                c.id as conversation_id,
                c.title,
                p.name as project_name,
                c.create_time,
                'conversation' as message_role,
                CONCAT('Conversación: ', c.title) as message_content
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE 1=1
        ";
        
        $params = [];
        
        if (!empty($query)) {
            $sql .= " AND c.title LIKE ?";
            $params[] = '%' . $query . '%';
        }
        
        if (!empty($project_id)) {
            $sql .= " AND c.project_id = ?";
            $params[] = $project_id;
        }
        
        $sql .= " ORDER BY c.create_time DESC LIMIT " . $limit;
        
    } else {
        // Buscar en contenido de mensajes
        $sql = "
            SELECT 
                c.id as conversation_id,
                c.title,
                p.name as project_name,
                m.create_time,
                m.author_role as message_role,
                m.content_text as message_content
            FROM messages m
            INNER JOIN conversations c ON m.conversation_id = c.id
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE m.content_text IS NOT NULL AND m.content_text != ''
        ";
        
        $params = [];
        
        if (!empty($query)) {
            $sql .= " AND m.content_text LIKE ?";
            $params[] = '%' . $query . '%';
        }
        
        if (!empty($project_id)) {
            $sql .= " AND c.project_id = ?";
            $params[] = $project_id;
        }
        
        $sql .= " ORDER BY m.create_time DESC LIMIT " . $limit;
    }
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear resultados
    foreach ($results as &$result) {
        // Convertir timestamp a fecha si es numérico
        if (is_numeric($result['create_time'])) {
            $result['create_time'] = date('Y-m-d H:i:s', $result['create_time']);
        }
        
        // Truncar contenido largo
        if (isset($result['message_content']) && strlen($result['message_content']) > 500) {
            $result['message_content'] = substr($result['message_content'], 0, 500) . '...';
        }
        
        // Asegurar project_name
        if (empty($result['project_name'])) {
            $result['project_name'] = 'Sin proyecto';
        }
    }
    
    // Respuesta
    echo json_encode([
        'success' => true,
        'results' => $results,
        'total_results' => count($results),
        'query' => $query,
        'search_type' => $search_type
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>