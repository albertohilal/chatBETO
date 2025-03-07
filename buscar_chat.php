<?php
header("Content-Type: application/json"); // Se asegura que la salida sea JSON
require_once "db_connection.php"; // Conexión a la base de datos

$conn = connect_to_db(); // Conectar a la base de datos

$query = isset($_GET['query']) ? trim($_GET['query']) : '';

if (empty($query)) {
    echo json_encode(["error" => "No se proporcionó un término de búsqueda."]);
    exit;
}

try {
    // Consulta SQL para asegurar que los mensajes alternen entre 'user' y 'assistant' en orden cronológico
    $sql = "
        SELECT conv.conversation_id, conv.title, msg.create_time, msg.role AS message_role, msg.content AS message_content
        FROM iunaorg_chatBeto.conversations conv
        JOIN iunaorg_chatBeto.messages msg ON msg.conversation_id = conv.conversation_id
        WHERE conv.conversation_id IN (
            SELECT DISTINCT sub_messages.conversation_id
            FROM iunaorg_chatBeto.messages sub_messages
            WHERE sub_messages.content LIKE :search
              AND sub_messages.content IS NOT NULL
              AND sub_messages.content <> ''
        )
        AND msg.role IN ('user', 'assistant') -- Solo mensajes de usuario y asistente
        AND msg.content IS NOT NULL
        AND msg.content <> ''
        ORDER BY conv.conversation_id, msg.create_time ASC, msg.role DESC
    ";

    $stmt = $conn->prepare($sql);
    $search = "%$query%";
    $stmt->bindParam(':search', $search, PDO::PARAM_STR);
    $stmt->execute();
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Devolvemos el resultado en formato JSON
    echo json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    echo json_encode(["error" => "Error en la consulta: " . $e->getMessage()]);
}

$conn = null; // Cerrar conexión
?>
