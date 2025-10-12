<?php
header('Content-Type: application/json; charset=utf-8');
require_once 'db_connection.php';

try {
    $pdo = connect_to_db();
    
    // Obtener todos los proyectos con su conteo de conversaciones
    $stmt = $pdo->query("
        SELECT 
            p.id,
            p.name,
            p.description,
            p.conversation_count,
            COUNT(c.conversation_id) as actual_conversations
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        GROUP BY p.id, p.name, p.description, p.conversation_count
        ORDER BY actual_conversations DESC
    ");
    
    $projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $response = [
        'total_projects' => count($projects),
        'projects' => $projects
    ];
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Error de conexión a la base de datos: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Error interno: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>