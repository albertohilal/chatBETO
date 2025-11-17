<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

require_once '../database/db_connection.php';

try {
    $sql = "SELECT 
                p.id,
                p.name,
                p.description,
                p.is_starred,
                p.chatgpt_project_id,
                COUNT(c.id) as conversation_count
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id
            GROUP BY p.id, p.name, p.description, p.is_starred, p.chatgpt_project_id
            ORDER BY p.is_starred DESC, conversation_count DESC, p.name ASC";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    
    $projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear datos
    foreach ($projects as &$project) {
        $project['id'] = (int)$project['id'];
        $project['conversation_count'] = (int)$project['conversation_count'];
        $project['is_starred'] = (bool)$project['is_starred'];
        $project['has_chatgpt_id'] = !empty($project['chatgpt_project_id']);
    }
    
    echo json_encode($projects);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al cargar proyectos: ' . $e->getMessage()]);
}
?>