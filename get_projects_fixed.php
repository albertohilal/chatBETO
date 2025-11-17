<?php
header('Content-Type: application/json; charset=utf-8');
require_once 'db_connection.php';

try {
    // Obtener todos los proyectos con conteo real de conversaciones
    $stmt = $pdo->query("
        SELECT 
            p.id,
            p.name,
            p.description,
            p.is_starred,
            p.chatgpt_project_id,
            COUNT(c.id) as actual_conversations
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        GROUP BY p.id, p.name, p.description, p.is_starred, p.chatgpt_project_id
        ORDER BY p.is_starred DESC, actual_conversations DESC, p.name ASC
    ");
    
    $projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear datos
    foreach ($projects as &$project) {
        $project['id'] = (int)$project['id'];
        $project['actual_conversations'] = (int)$project['actual_conversations'];
        $project['is_starred'] = (bool)$project['is_starred'];
    }
    
    // Respuesta compatible con la interfaz
    echo json_encode([
        'total_projects' => count($projects),
        'projects' => $projects
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Error: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>