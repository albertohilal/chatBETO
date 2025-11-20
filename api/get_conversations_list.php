<?php
/**
 * 📋 API para obtener lista de conversaciones disponibles
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once '../database/db_connection.php';

try {
    $project_id = intval($_GET['project_id'] ?? 1);
    
    // Obtener conversaciones con conteo de mensajes
    $sql = "SELECT 
                c.id as conversation_id,
                c.title,
                c.project_id,
                c.created_at,
                COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id 
            WHERE c.project_id = ?
            AND EXISTS (
                SELECT 1 FROM messages m2 
                WHERE m2.conversation_id = c.id 
                AND m2.content IS NOT NULL 
                AND m2.content != '' 
                AND m2.content NOT LIKE '%[Respuesta del asistente no disponible]%' 
                AND m2.content NOT LIKE '%[Contenido multimedia no disponible]%'
                AND LENGTH(m2.content) > 10
            )
            GROUP BY c.id, c.title, c.project_id, c.created_at
            ORDER BY c.created_at DESC";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$project_id]);
    $conversations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear para el frontend
    $formatted_data = array_map(function($row) {
        return [
            'id' => $row['conversation_id'],
            'title' => $row['title'],
            'message_count' => intval($row['message_count']),
            'created_at' => $row['created_at'],
            'project_id' => $row['project_id']
        ];
    }, $conversations);
    
    echo json_encode([
        'success' => true,
        'data' => $formatted_data,
        'count' => count($formatted_data),
        'project_id' => $project_id,
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>