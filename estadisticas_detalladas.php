<?php
header('Content-Type: application/json; charset=utf-8');
require_once 'db_connection.php';

try {
    // Usar la función de conexión existente
    $pdo = connect_to_db();
    
    // Total de mensajes
    $stmt = $pdo->query("SELECT COUNT(*) as total_messages FROM messages");
    $totalMessages = $stmt->fetch(PDO::FETCH_ASSOC)['total_messages'];
    
    // Total de conversaciones
    $stmt = $pdo->query("SELECT COUNT(*) as total_conversations FROM conversations");
    $totalConversations = $stmt->fetch(PDO::FETCH_ASSOC)['total_conversations'];
    
        // Proyectos con conteos desde tabla normalizada
        $stmt = $pdo->query("
            SELECT p.name as project_name, COUNT(c.conversation_id) as count 
            FROM projects p
            LEFT JOIN conversations c ON p.id = c.project_id 
            GROUP BY p.id, p.name 
            ORDER BY count DESC
        ");
        $categories = $stmt->fetchAll(PDO::FETCH_ASSOC);    // Modelos más utilizados
    $stmt = $pdo->query("
        SELECT model, COUNT(*) as count 
        FROM conversations 
        WHERE model IS NOT NULL 
        GROUP BY model 
        ORDER BY count DESC
    ");
    $models = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Actividad por mes
    $stmt = $pdo->query("
        SELECT 
            YEAR(create_time) as year, 
            MONTH(create_time) as month, 
            COUNT(*) as conversations 
        FROM conversations 
        WHERE create_time IS NOT NULL 
        GROUP BY YEAR(create_time), MONTH(create_time) 
        ORDER BY year DESC, month DESC 
        LIMIT 12
    ");
    $monthlyActivity = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Promedio de mensajes por conversación
    $stmt = $pdo->query("
        SELECT AVG(message_count) as avg_messages_per_conversation
        FROM (
            SELECT conversation_id, COUNT(*) as message_count 
            FROM messages 
            GROUP BY conversation_id
        ) as conv_counts
    ");
    $avgMessages = $stmt->fetch(PDO::FETCH_ASSOC)['avg_messages_per_conversation'];
    
    $response = [
        'total_messages' => $totalMessages,
        'total_conversations' => $totalConversations,
        'categories' => $categories,
        'models' => $models,
        'monthly_activity' => $monthlyActivity,
        'avg_messages_per_conversation' => round($avgMessages, 1)
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