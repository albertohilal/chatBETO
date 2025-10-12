<?php
header('Content-Type: application/json; charset=UTF-8');
require_once 'db_connection.php';

try {
    $conn = connect_to_db();
    
    // Parámetros de búsqueda
    $query = isset($_GET['query']) ? trim($_GET['query']) : '';
    $project_id = isset($_GET['project_id']) ? intval($_GET['project_id']) : null;
    
    // Construir la consulta SQL con filtros opcionales
    $sql = "SELECT 
                conv.conversation_id, 
                conv.title,
                p.name as project_name,
                p.id as project_id,
                msg.id,
                msg.create_time, 
                msg.role AS message_role, 
                msg.parts AS message_content
            FROM iunaorg_chatBeto.conversations conv
            LEFT JOIN iunaorg_chatBeto.projects p ON conv.project_id = p.id
            JOIN iunaorg_chatBeto.messages msg ON msg.conversation_id = conv.conversation_id
            WHERE 1=1";
    
    $params = [];
    $param_types = [];
    
    // Filtro por texto (si se proporciona)
    if (!empty($query)) {
        $sql .= " AND conv.conversation_id IN (
                    SELECT DISTINCT sub_messages.conversation_id
                    FROM iunaorg_chatBeto.messages sub_messages
                    WHERE sub_messages.parts LIKE ?
                      AND sub_messages.parts IS NOT NULL
                      AND sub_messages.parts <> ''
                  )";
        $params[] = "%$query%";
        $param_types[] = PDO::PARAM_STR;
    }
    
    // Filtro por proyecto (si se proporciona)
    if ($project_id !== null && $project_id > 0) {
        $sql .= " AND conv.project_id = ?";
        $params[] = $project_id;
        $param_types[] = PDO::PARAM_INT;
    }
    
    // Condiciones adicionales
    $sql .= " AND msg.role IN ('user', 'assistant')
              AND msg.parts IS NOT NULL
              AND msg.parts <> ''
              ORDER BY msg.create_time DESC, conv.conversation_id
              LIMIT 100";
    
    $stmt = $conn->prepare($sql);
    
    if (!$stmt) {
        throw new Exception("Error en la preparación de la consulta");
    }
    
    // Vincular parámetros
    for ($i = 0; $i < count($params); $i++) {
        $stmt->bindValue($i + 1, $params[$i], $param_types[$i]);
    }
    
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Respuesta con metadatos
    $response = [
        'total_results' => count($result),
        'query' => $query,
        'project_filter' => $project_id,
        'results' => $result
    ];
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Error de base de datos: ' . $e->getMessage(),
        'query' => $query ?? '',
        'project_filter' => $project_id ?? null
    ], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Error interno: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>