<?php
/**
 * API optimizada para mostrar conversaciones con estadísticas completas
 * Basada en la estructura recomendada de ChatGPT exports
 */

header('Content-Type: application/json; charset=UTF-8');
require_once '../database/db_connection.php';

try {
    // Parámetros opcionales
    $project_id = isset($_GET['project_id']) ? intval($_GET['project_id']) : null;
    $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;
    $offset = isset($_GET['offset']) ? intval($_GET['offset']) : 0;
    $search = isset($_GET['search']) ? trim($_GET['search']) : '';
    
    // Consulta SQL optimizada con todas las estadísticas
    $sql = "SELECT 
                c.id,
                c.title,
                c.create_time,
                c.update_time,
                p.name as project_name,
                p.id as project_id,
                p.chatgpt_project_id,
                
                -- Estadísticas de mensajes
                COUNT(m.id) as total_messages,
                SUM(CASE WHEN m.author_role = 'user' THEN 1 ELSE 0 END) as user_messages,
                SUM(CASE WHEN m.author_role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
                SUM(CASE WHEN m.author_role = 'tool' THEN 1 ELSE 0 END) as tool_messages,
                
                -- Información temporal
                MIN(m.create_time) as first_message_time,
                MAX(m.create_time) as last_message_time,
                
                -- Contenido
                GROUP_CONCAT(
                    CASE WHEN m.author_role = 'user' 
                    THEN SUBSTRING(m.content_text, 1, 100) 
                    END 
                    ORDER BY m.create_time 
                    SEPARATOR ' | '
                ) as user_preview,
                
                -- Metadatos
                c.conversation_id as original_conversation_id,
                c.gizmo_id,
                c.is_starred,
                c.is_archived
                
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE 1=1";
    
    $params = [];
    $param_types = [];
    
    // Filtro por proyecto
    if ($project_id !== null && $project_id > 0) {
        $sql .= " AND c.project_id = ?";
        $params[] = $project_id;
        $param_types[] = PDO::PARAM_INT;
    }
    
    // Filtro por búsqueda
    if (!empty($search)) {
        $sql .= " AND (c.title LIKE ? OR p.name LIKE ?)";
        $search_param = '%' . $search . '%';
        $params[] = $search_param;
        $params[] = $search_param;
        $param_types[] = PDO::PARAM_STR;
        $param_types[] = PDO::PARAM_STR;
    }
    
    // Agrupar y ordenar
    $sql .= " GROUP BY c.id, c.title, c.create_time, c.update_time, p.name, p.id, p.chatgpt_project_id, 
              c.conversation_id, c.gizmo_id, c.is_starred, c.is_archived
              ORDER BY p.name ASC, c.create_time DESC
              LIMIT ? OFFSET ?";
    
    $params[] = $limit;
    $params[] = $offset;
    $param_types[] = PDO::PARAM_INT;
    $param_types[] = PDO::PARAM_INT;
    
    // Ejecutar consulta
    $stmt = $pdo->prepare($sql);
    
    for ($i = 0; $i < count($params); $i++) {
        $stmt->bindValue($i + 1, $params[$i], $param_types[$i]);
    }
    
    $stmt->execute();
    $conversations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Procesar resultados
    foreach ($conversations as &$conv) {
        // Convertir timestamps a fechas legibles
        if (is_numeric($conv['create_time'])) {
            $conv['create_time'] = date('Y-m-d H:i:s', $conv['create_time']);
        }
        if (is_numeric($conv['update_time'])) {
            $conv['update_time'] = date('Y-m-d H:i:s', $conv['update_time']);
        }
        if (is_numeric($conv['first_message_time'])) {
            $conv['first_message_time'] = date('Y-m-d H:i:s', $conv['first_message_time']);
        }
        if (is_numeric($conv['last_message_time'])) {
            $conv['last_message_time'] = date('Y-m-d H:i:s', $conv['last_message_time']);
        }
        
        // Calcular duración de conversación
        if ($conv['first_message_time'] && $conv['last_message_time']) {
            $start = strtotime($conv['first_message_time']);
            $end = strtotime($conv['last_message_time']);
            $conv['duration_minutes'] = round(($end - $start) / 60, 2);
        } else {
            $conv['duration_minutes'] = 0;
        }
        
        // Limpiar preview
        if ($conv['user_preview']) {
            $conv['user_preview'] = substr($conv['user_preview'], 0, 200) . '...';
        }
        
        // Agregar flags útiles
        $conv['has_chatgpt_id'] = !empty($conv['chatgpt_project_id']);
        $conv['is_active'] = $conv['total_messages'] > 1;
        $conv['message_ratio'] = $conv['total_messages'] > 0 ? 
            round($conv['assistant_messages'] / $conv['total_messages'], 2) : 0;
    }
    
    // Contar total para paginación
    $count_sql = "SELECT COUNT(DISTINCT c.id) as total
                  FROM conversations c
                  LEFT JOIN projects p ON c.project_id = p.id
                  WHERE 1=1";
    
    $count_params = [];
    if ($project_id !== null && $project_id > 0) {
        $count_sql .= " AND c.project_id = ?";
        $count_params[] = $project_id;
    }
    if (!empty($search)) {
        $count_sql .= " AND (c.title LIKE ? OR p.name LIKE ?)";
        $count_params[] = $search_param;
        $count_params[] = $search_param;
    }
    
    $count_stmt = $pdo->prepare($count_sql);
    $count_stmt->execute($count_params);
    $total_count = $count_stmt->fetchColumn();
    
    // Respuesta final
    $response = [
        'success' => true,
        'total_conversations' => intval($total_count),
        'returned_conversations' => count($conversations),
        'limit' => $limit,
        'offset' => $offset,
        'has_more' => ($offset + $limit) < $total_count,
        'filters' => [
            'project_id' => $project_id,
            'search' => $search
        ],
        'conversations' => $conversations
    ];
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error de base de datos: ' . $e->getMessage(),
        'conversations' => []
    ], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Error interno: ' . $e->getMessage(),
        'conversations' => []
    ], JSON_UNESCAPED_UNICODE);
}
?>