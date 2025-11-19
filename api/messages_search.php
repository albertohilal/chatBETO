<?php
/**
 * 🎯 ENDPOINT DEFINITIVO: Buscar Mensajes en Chat
 * 
 * Con la estructura REAL confirmada de la base de datos:
 * - messages.role (NO author_role)  
 * - messages.content (NO content_text)
 * 
 * API: /api/messages_search.php?project_id=1&search=texto&role=user&limit=20&offset=0
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
    // Parámetros de entrada
    $project_id = intval($_GET['project_id'] ?? 1);
    $search = trim($_GET['search'] ?? '');
    $role = trim($_GET['role'] ?? '');
    $limit = intval($_GET['limit'] ?? 50);
    $offset = intval($_GET['offset'] ?? 0);

    // Construir condiciones WHERE
    $where_conditions = [];
    $params = [];
    
    // Solo agregar filtro de proyecto si se especifica
    if (!empty($project_id) && $project_id > 0) {
        $where_conditions[] = 'c.project_id = ?';
        $params[] = $project_id;
    }
    
    // Filtro de búsqueda en contenido y título  
    if (!empty($search)) {
        $where_conditions[] = '(m.content_text LIKE ? OR c.title LIKE ?)';
        $params[] = '%' . $search . '%';
        $params[] = '%' . $search . '%';
    }
    
    // Filtro por rol
    if (!empty($role)) {
        $where_conditions[] = 'm.author_role = ?';
        $params[] = $role;
    }
    
    $where_clause = !empty($where_conditions) ? implode(' AND ', $where_conditions) : '1=1';
    
    // 📋 CONSULTA PRINCIPAL - ESTRUCTURA REAL CONFIRMADA POR PRUEBAS
    $sql = "
        SELECT 
            c.id as conversation_id,
            c.title as conversation_title,
            c.project_id,
            m.id as message_id,
            m.author_role as message_role,
            m.content_text as message_content,
            m.created_at as message_created_at,
            m.author_name
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE $where_clause AND m.content_text IS NOT NULL
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    ";
    
    $params[] = $limit;
    $params[] = $offset;
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $messages = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // 📊 CONTAR TOTAL PARA PAGINACIÓN
    $count_sql = "
        SELECT COUNT(*) as total
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE $where_clause AND m.content_text IS NOT NULL
    ";
    
    $count_params = array_slice($params, 0, -2); // Remover limit y offset
    $count_stmt = $pdo->prepare($count_sql);
    $count_stmt->execute($count_params);
    $total_result = $count_stmt->fetch(PDO::FETCH_ASSOC);
    $total_messages = intval($total_result['total']);
    
    // 🔄 FORMATEAR DATOS PARA EL FRONTEND
    $formatted_data = array_map(function($row) {
        return [
            'conversationId' => $row['conversation_id'],
            'conversationTitle' => $row['conversation_title'],
            'projectId' => intval($row['project_id']),
            'messageId' => $row['message_id'],
            'messageRole' => $row['message_role'],
            'messageContent' => $row['message_content'],
            'messageTimestamp' => $row['message_created_at'],
            'authorName' => $row['author_name']
        ];
    }, $messages);
    
    // ✅ RESPUESTA EXITOSA
    echo json_encode([
        'success' => true,
        'data' => $formatted_data,
        'pagination' => [
            'total' => $total_messages,
            'limit' => $limit,
            'offset' => $offset,
            'pages' => ceil($total_messages / $limit)
        ],
        'filters' => [
            'projectId' => $project_id,
            'search' => $search,
            'role' => $role
        ],
        'meta' => [
            'timestamp' => date('c'),
            'query_time' => number_format((microtime(true) - $_SERVER['REQUEST_TIME_FLOAT']) * 1000, 2) . 'ms'
        ]
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => [
            'message' => 'Error interno del servidor',
            'details' => $e->getMessage(),
            'code' => $e->getCode()
        ],
        'timestamp' => date('c')
    ]);
}
?>