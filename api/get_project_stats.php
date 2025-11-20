<?php
/**
 * API ENDPOINT: Obtener estadísticas de un proyecto o todos los proyectos
 * Uso: api/get_project_stats.php?project_id=1 (proyecto específico)
 * Uso: api/get_project_stats.php (todos los proyectos)
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
    $project_id = isset($_GET['project_id']) ? intval($_GET['project_id']) : null;
    
    if ($project_id) {
        // Estadísticas de un proyecto específico
        $sql = "
            SELECT 
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(m.id) as total_messages,
                COUNT(CASE WHEN m.role = 'user' THEN 1 END) as user_messages,
                COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) as assistant_messages,
                COUNT(CASE WHEN m.role = 'system' THEN 1 END) as system_messages,
                COUNT(CASE WHEN m.role = 'tool' THEN 1 END) as tool_messages,
                MIN(c.created_at) as first_conversation,
                MAX(m.created_at) as last_message
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.project_id = ?
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$project_id]);
        $stats = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // Obtener información del proyecto
        $project_sql = "SELECT name, description FROM projects WHERE id = ?";
        $project_stmt = $pdo->prepare($project_sql);
        $project_stmt->execute([$project_id]);
        $project = $project_stmt->fetch(PDO::FETCH_ASSOC);
        
        $projectName = $project['name'] ?? 'Proyecto no encontrado';
        $projectDescription = $project['description'] ?? '';
        
    } else {
        // Estadísticas de todos los proyectos
        $sql = "
            SELECT 
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(m.id) as total_messages,
                COUNT(CASE WHEN m.role = 'user' THEN 1 END) as user_messages,
                COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) as assistant_messages,
                COUNT(CASE WHEN m.role = 'system' THEN 1 END) as system_messages,
                COUNT(CASE WHEN m.role = 'tool' THEN 1 END) as tool_messages,
                MIN(c.created_at) as first_conversation,
                MAX(m.created_at) as last_message
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
        ";
        
        $stmt = $pdo->query($sql);
        $stats = $stmt->fetch(PDO::FETCH_ASSOC);
        
        $projectName = 'Todos los Proyectos';
        $projectDescription = 'Estadísticas globales de todos los proyectos';
    }
    
    echo json_encode([
        'success' => true,
        'projectId' => $project_id,
        'projectName' => $projectName,
        'projectDescription' => $projectDescription,
        'stats' => [
            'total_conversations' => intval($stats['total_conversations']),
            'total_messages' => intval($stats['total_messages']),
            'user_messages' => intval($stats['user_messages']),
            'assistant_messages' => intval($stats['assistant_messages']),
            'system_messages' => intval($stats['system_messages']),
            'tool_messages' => intval($stats['tool_messages']),
            'first_conversation' => $stats['first_conversation'],
            'last_message' => $stats['last_message']
        ],
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
