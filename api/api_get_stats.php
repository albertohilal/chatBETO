<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once '../database/db_connection.php';

try {
    // Obtener estadísticas generales
    
    // Total de proyectos
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM projects");
    $projects_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    // Total de conversaciones
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM conversations");
    $conversations_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    // Total de mensajes
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM messages");
    $messages_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    // Conversaciones sincronizadas con OpenAI
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM conversations WHERE openai_thread_id IS NOT NULL");
    $synced_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    // Proyectos con ChatGPT ID
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM projects WHERE chatgpt_project_id IS NOT NULL");
    $projects_with_gpt_id = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    // Top 5 proyectos con más conversaciones
    $stmt = $pdo->prepare("
        SELECT 
            p.name,
            COUNT(c.id) as conversation_count
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        GROUP BY p.id, p.name
        ORDER BY conversation_count DESC
        LIMIT 5
    ");
    $stmt->execute();
    $top_projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Conversaciones recientes (últimos 7 días)
    $stmt = $pdo->query("
        SELECT COUNT(*) as count 
        FROM conversations 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
           OR create_time >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
    ");
    $recent_conversations = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
    
    $stats = [
        'projects' => (int)$projects_count,
        'conversations' => (int)$conversations_count,
        'messages' => (int)$messages_count,
        'synced' => (int)$synced_count,
        'projects_with_gpt_id' => (int)$projects_with_gpt_id,
        'recent_conversations' => (int)$recent_conversations,
        'sync_percentage' => $conversations_count > 0 ? round(($synced_count / $conversations_count) * 100, 1) : 0,
        'gpt_id_percentage' => $projects_count > 0 ? round(($projects_with_gpt_id / $projects_count) * 100, 1) : 0,
        'top_projects' => $top_projects
    ];
    
    echo json_encode($stats);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al cargar estadísticas: ' . $e->getMessage()]);
}
?>