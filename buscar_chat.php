<?php
header('Content-Type: application/json; charset=UTF-8'); // Asegurar codificación UTF-8
require_once 'db_connection.php';
$conn = connect_to_db(); // Conectar a la base de datos

if (!$conn) {
    echo json_encode(["error" => "Error en la conexión a la base de datos"]);
    exit;
}

error_reporting(E_ALL);
ini_set('display_errors', 1);

$query = isset($_GET['query']) ? trim($_GET['query']) : '';

$sql = "SELECT 
            conv.conversation_id, 
            conv.title,
            msg.id,
            msg.create_time, 
            msg.role AS message_role, 
            msg.parts AS message_content
        FROM iunaorg_chatBeto.conversations conv
        JOIN iunaorg_chatBeto.messages msg ON msg.conversation_id = conv.conversation_id
        WHERE conv.conversation_id IN (
            SELECT DISTINCT sub_messages.conversation_id
            FROM iunaorg_chatBeto.messages sub_messages
            WHERE sub_messages.parts LIKE ?
              AND sub_messages.parts IS NOT NULL
              AND sub_messages.parts <> ''
        )
        AND msg.role IN ('user', 'assistant')
        AND msg.parts IS NOT NULL
        AND msg.parts <> ''
        ORDER BY conv.conversation_id, msg.create_time ASC, msg.id ASC";

$stmt = $conn->prepare($sql);

if (!$stmt) {
    echo json_encode(["error" => "Error en la preparación de la consulta: " . $conn->errorInfo()[2]]);
    exit;
}

$stmt->bindValue(1, "%$query%", PDO::PARAM_STR);
$stmt->execute();
$result = $stmt->fetchAll(PDO::FETCH_ASSOC);

//echo json_encode($result, JSON_PRETTY_PRINT);
echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT); // Evitar caracteres Unicode escapados y mejorar legibilidad
?>