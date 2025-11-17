<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once 'db_connection.php';

try {
    $conversation_id = $_GET['conversation_id'] ?? null;
    
    if (!$conversation_id) {
        throw new Exception('ID de conversación requerido');
    }
    
    $sql = "SELECT 
                m.id,
                m.author_role,
                m.content_text,
                m.created_at,
                m.create_time,
                m.conversation_id
            FROM messages m
            WHERE m.conversation_id = :conversation_id
            ORDER BY 
                CASE 
                    WHEN m.create_time IS NOT NULL THEN m.create_time
                    ELSE UNIX_TIMESTAMP(m.created_at)
                END ASC,
                m.created_at ASC";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['conversation_id' => $conversation_id]);
    
    $messages = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear datos
    foreach ($messages as &$message) {
        // Limpiar y validar contenido
        if (isset($message['content_text'])) {
            $message['content_text'] = trim($message['content_text']);
            // Eliminar caracteres de control que pueden romper JSON
            $message['content_text'] = preg_replace('/[\x00-\x1F\x7F]/', '', $message['content_text']);
            // Asegurar UTF-8 válido
            $message['content_text'] = mb_convert_encoding($message['content_text'], 'UTF-8', 'UTF-8');
        } else {
            $message['content_text'] = '';
        }
        
        // Formatear fecha
        if ($message['created_at']) {
            $message['formatted_date'] = date('d/m/Y H:i:s', strtotime($message['created_at']));
        } elseif ($message['create_time']) {
            $message['formatted_date'] = date('d/m/Y H:i:s', $message['create_time']);
        } else {
            $message['formatted_date'] = 'Sin fecha';
        }
        
        // Validar rol
        if (!in_array($message['author_role'], ['user', 'assistant', 'system'])) {
            $message['author_role'] = 'system';
        }
        
        // Asegurar que todos los campos sean strings válidos
        $message['id'] = (string)($message['id'] ?? '');
        $message['author_role'] = (string)($message['author_role'] ?? 'system');
        $message['conversation_id'] = (string)($message['conversation_id'] ?? '');
    }
    
    echo json_encode($messages, JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al cargar mensajes: ' . $e->getMessage()]);
}
?>