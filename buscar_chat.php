<?php
header("Content-Type: application/json; charset=UTF-8");

// Habilitar la visualización de errores
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

require_once "db_connection.php";

$query = isset($_GET['query']) ? trim($_GET['query']) : '';

if (empty($query)) {
    echo json_encode(["error" => "Debe ingresar un término de búsqueda"]);
    exit;
}

// Nueva consulta SQL con filtro para evitar mensajes vacíos y excluir 'tool' y 'system'
$sql = "
    WITH MatchingConversations AS (
        SELECT DISTINCT conversation_id
        FROM messages
        WHERE content LIKE ?
    )
    SELECT 
        c.conversation_id, 
        COALESCE(fum.titulo_conversacion, 'Sin título') AS titulo_conversacion, 
        FROM_UNIXTIME(m.create_time) AS fecha_hora,
        CASE 
            WHEN m.author_role = 'user' THEN m.content 
            ELSE NULL 
        END AS mensaje_usuario,
        CASE 
            WHEN m.author_role = 'assistant' THEN m.content 
            ELSE NULL 
        END AS mensaje_asistente
    FROM conversations c
    LEFT JOIN (
        SELECT conversation_id, content AS titulo_conversacion 
        FROM messages 
        WHERE author_role = 'user' 
        AND create_time = (SELECT MIN(create_time) 
                           FROM messages m2 
                           WHERE m2.conversation_id = messages.conversation_id 
                           AND m2.author_role = 'user')
    ) AS fum 
    ON c.conversation_id = fum.conversation_id
    JOIN messages m 
    ON c.conversation_id = m.conversation_id
    WHERE c.conversation_id IN (SELECT conversation_id FROM MatchingConversations)
    AND m.author_role NOT IN ('tool', 'system')  -- Excluimos mensajes de 'tool' y 'system'
    AND (m.content IS NOT NULL AND LENGTH(TRIM(m.content)) > 0) -- Filtramos mensajes vacíos
    ORDER BY c.conversation_id, m.create_time;
";

// Preparar y ejecutar consulta segura
$stmt = $conn->prepare($sql);
if (!$stmt) {
    die(json_encode(["error" => "Error en la preparación de la consulta: " . $conn->error]));
}

$searchParam = "%$query%";
$stmt->bind_param("s", $searchParam);

if (!$stmt->execute()) {
    die(json_encode(["error" => "Error al ejecutar la consulta: " . $stmt->error]));
}

// Vincular resultados manualmente
$stmt->bind_result($conversation_id, $titulo_conversacion, $fecha_hora, $mensaje_usuario, $mensaje_asistente);

$data = [];
while ($stmt->fetch()) {
    $data[] = [
        "conversation_id" => $conversation_id,
        "titulo_conversacion" => $titulo_conversacion,
        "fecha_hora" => $fecha_hora,
        "mensaje_usuario" => $mensaje_usuario,
        "mensaje_asistente" => $mensaje_asistente
    ];
}

// Si no hay resultados, mostrar un mensaje específico
if (empty($data)) {
    echo json_encode(["message" => "No se encontraron resultados para la búsqueda: '$query'"]);
    exit;
}

// Devolver JSON formateado
echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

// Cerrar conexión
$stmt->close();
$conn->close();
?>
