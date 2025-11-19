<?php
/**
 * API ENDPOINT: Obtener lista de proyectos
 * Uso: api/get_projects.php
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once '../database/db_connection.php';

try {
    // Obtener proyectos con estadísticas
    $sql = "
        SELECT 
            p.id, 
            p.name, 
            p.description, 
            p.created_at, 
            p.is_starred,
            COUNT(DISTINCT c.id) as conversation_count,
            COUNT(m.id) as message_count,
            MAX(m.created_at) as last_activity
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY p.id, p.name, p.description, p.created_at, p.is_starred
        ORDER BY p.created_at DESC
    ";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear datos
    $formatted_projects = array_map(function($row) {
        return [
            'id' => intval($row['id']),
            'name' => $row['name'],
            'description' => $row['description'],
            'created_at' => $row['created_at'],
            'is_starred' => boolval($row['is_starred']),
            'conversation_count' => intval($row['conversation_count']),
            'message_count' => intval($row['message_count']),
            'last_activity' => $row['last_activity']
        ];
    }, $projects);
    
    echo json_encode([
        'success' => true,
        'data' => $formatted_projects,
        'totalProjects' => count($formatted_projects),
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error interno del servidor',
        'details' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
?>