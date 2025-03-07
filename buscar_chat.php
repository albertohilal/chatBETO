<?php
header("Content-Type: application/json"); // Asegura que la salida sea JSON
require_once "db_connection.php"; // Conexión a la base de datos

try {
    $conn = connect_to_db(); // Llama a la función de conexión

    $query = isset($_GET['query']) ? $_GET['query'] : '';

    // Prepara la consulta
    $sql = "SELECT conv.conversation_id, conv.title, msg.create_time, msg.role AS message_role, msg.content AS message_content
            FROM iunaorg_chatBeto.conversations conv
            JOIN iunaorg_chatBeto.messages msg ON msg.conversation_id = conv.conversation_id
            WHERE msg.content IS NOT NULL 
            AND msg.content <> '' 
            AND msg.role IN ('user', 'assistant')
            AND msg.content LIKE :search
            ORDER BY conv.conversation_id, msg.create_time ASC";

    $stmt = $conn->prepare($sql);
    $search = "%$query%";
    $stmt->bindParam(':search', $search, PDO::PARAM_STR);
    $stmt->execute();
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    echo json_encode(["error" => "Error en la consulta: " . $e->getMessage()]);
}
?>
