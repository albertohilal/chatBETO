<?php
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
require_once 'db_connection.php';

try {
    // Consulta super simple para debugging
    $sql = "SELECT 
                c.id as conversation_id,
                c.title,
                'Sin proyecto' as project_name,
                NULL as project_id,
                c.id as id,
                c.create_time,
                'conversation' as message_role,
                'Conversación simple' as message_content
            FROM conversations c
            ORDER BY c.create_time DESC 
            LIMIT 10";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Respuesta simple
    echo json_encode([
        'success' => true,
        'total_results' => count($result),
        'query' => '',
        'search_type' => 'test',
        'results' => $result
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
        'results' => []
    ], JSON_UNESCAPED_UNICODE);
}
?>