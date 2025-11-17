<?php
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
require_once 'db_connection.php';

try {
    // Parámetros de búsqueda
    $query = isset($_GET['query']) ? trim($_GET['query']) : '';
    $project_id = isset($_GET['project_id']) ? intval($_GET['project_id']) : null;
    $search_type = isset($_GET['search_type']) ? $_GET['search_type'] : 'messages';
    
    // Límite más conservador para evitar timeouts
    $limit = 25;
    
    if ($search_type === 'conversations') {
        // Buscar en títulos de conversaciones
        $sql = "SELECT 
                    c.id as conversation_id,
                    COALESCE(c.title, 'Sin título') as title,
                    COALESCE(p.name, 'Sin proyecto') as project_name,
                    p.id as project_id,
                    c.id as id,
                    c.create_time,
                    'conversation' as message_role,
                    CONCAT('Conversación: ', COALESCE(c.title, 'Sin título')) as message_content
                FROM conversations c
                LEFT JOIN projects p ON c.project_id = p.id
                WHERE 1=1";
    } else {
        // Buscar en contenido de mensajes con filtros más estrictos
        $sql = "SELECT 
                    c.id as conversation_id,
                    COALESCE(c.title, 'Sin título') as title,
                    COALESCE(p.name, 'Sin proyecto') as project_name,
                    p.id as project_id,
                    m.id,
                    m.create_time,
                    m.author_role AS message_role,
                    COALESCE(m.content_text, '') AS message_content
                FROM messages m
                INNER JOIN conversations c ON m.conversation_id = c.id
                LEFT JOIN projects p ON c.project_id = p.id
                WHERE m.author_role IN ('user', 'assistant')
                  AND m.content_text IS NOT NULL
                  AND m.content_text != ''
                  AND m.content_text NOT LIKE '%[object Object]%'
                  AND LENGTH(m.content_text) > 3";
    }
    
    $params = [];
    $param_types = [];
    
    // Filtro por texto (si se proporciona)
    if (!empty($query)) {
        if ($search_type === 'conversations') {
            // Buscar en títulos de conversaciones
            $sql .= " AND c.title LIKE ?";
            $params[] = "%$query%";
            $param_types[] = PDO::PARAM_STR;
        } else {
            // Buscar en contenido de mensajes
            $sql .= " AND m.content_text LIKE ?";
            $params[] = "%$query%";
            $param_types[] = PDO::PARAM_STR;
        }
    }
    
    // Filtro por proyecto (si se proporciona)
    if ($project_id !== null && $project_id > 0) {
        if ($search_type === 'conversations') {
            $sql .= " AND c.project_id = ?";
        } else {
            $sql .= " AND c.project_id = ?";
        }
        $params[] = $project_id;
        $param_types[] = PDO::PARAM_INT;
    }
    
    // Condiciones adicionales y ordenamiento
    if ($search_type === 'conversations') {
        // Ordenar por fecha descendente
        $sql .= " ORDER BY c.create_time DESC LIMIT $limit";
    } else {
        // Ordenar por fecha descendente
        $sql .= " ORDER BY c.create_time DESC, m.create_time ASC LIMIT $limit";
    }
    
    $stmt = $pdo->prepare($sql);
    
    if (!$stmt) {
        throw new Exception("Error en la preparación de la consulta");
    }
    
    // Vincular parámetros
    for ($i = 0; $i < count($params); $i++) {
        $stmt->bindValue($i + 1, $params[$i], $param_types[$i]);
    }
    
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Formatear resultados de forma segura
    $formatted_results = [];
    foreach ($result as $row) {
        $formatted_row = [
            'id' => (string)($row['id'] ?? ''),
            'conversation_id' => (string)($row['conversation_id'] ?? ''),
            'title' => trim($row['title'] ?? 'Sin título'),
            'project_name' => trim($row['project_name'] ?? 'Sin proyecto'),
            'project_id' => $row['project_id'] ? (int)$row['project_id'] : null,
            'message_role' => trim($row['message_role'] ?? 'system'),
            'create_time' => $row['create_time'] ?? date('Y-m-d H:i:s')
        ];
        
        // Limpiar y validar contenido del mensaje
        $content = $row['message_content'] ?? '';
        $content = trim($content);
        
        // Eliminar caracteres problemáticos
        $content = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $content);
        
        // Asegurar UTF-8 válido
        $content = mb_convert_encoding($content, 'UTF-8', 'UTF-8');
        
        // Truncar si es muy largo
        if (strlen($content) > 500) {
            $content = substr($content, 0, 497) . '...';
        }
        
        $formatted_row['message_content'] = $content;
        
        // Formatear fecha para display
        if (is_numeric($row['create_time'])) {
            $formatted_row['create_time'] = date('Y-m-d H:i:s', (int)floatval($row['create_time']));
        }
        
        $formatted_results[] = $formatted_row;
    }
    
    // Respuesta estructurada
    $response = [
        'success' => true,
        'total_results' => count($formatted_results),
        'query' => $query,
        'search_type' => $search_type,
        'project_filter' => $project_id,
        'results' => $formatted_results
    ];
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error de base de datos',
        'message' => $e->getMessage(),
        'results' => []
    ], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error interno', 
        'message' => $e->getMessage(),
        'results' => []
    ], JSON_UNESCAPED_UNICODE);
}
?>