<?php
/**
 * 🔄 API para actualizar el proyecto de una conversación
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Método no permitido']);
    exit();
}

require_once '../database/db_connection.php';

try {
    // Leer el JSON del request
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input || !isset($input['conversation_id']) || !isset($input['project_id'])) {
        throw new Exception('conversation_id y project_id son requeridos');
    }
    
    $conversation_id = trim($input['conversation_id']);
    $project_id = intval($input['project_id']);
    
    if (empty($conversation_id) || $project_id <= 0) {
        throw new Exception('Parámetros inválidos');
    }
    
    // Verificar que la conversación existe
    $check_sql = "SELECT id, title FROM conversations WHERE id = ?";
    $check_stmt = $pdo->prepare($check_sql);
    $check_stmt->execute([$conversation_id]);
    $conversation = $check_stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$conversation) {
        throw new Exception('Conversación no encontrada');
    }
    
    // Actualizar el proyecto de la conversación
    $update_sql = "UPDATE conversations SET project_id = ? WHERE id = ?";
    $update_stmt = $pdo->prepare($update_sql);
    $result = $update_stmt->execute([$project_id, $conversation_id]);
    
    if (!$result) {
        throw new Exception('Error al actualizar la conversación');
    }
    
    // Verificar que se actualizó al menos una fila
    if ($update_stmt->rowCount() === 0) {
        throw new Exception('No se actualizó ningún registro');
    }
    
    echo json_encode([
        'success' => true,
        'message' => 'Conversación actualizada correctamente',
        'data' => [
            'conversation_id' => $conversation_id,
            'conversation_title' => $conversation['title'],
            'new_project_id' => $project_id,
            'rows_affected' => $update_stmt->rowCount()
        ],
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>