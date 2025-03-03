<?php
header("Content-Type: application/json; charset=UTF-8");

// Incluir el archivo de conexión
require_once "db_connection.php";

// Consulta SQL
$sql = "
    WITH FirstUserMessage AS (
        SELECT 
            conversation_id, 
            content AS titulo_conversacion
        FROM messages 
        WHERE author_role = 'user' 
        AND create_time = (SELECT MIN(create_time) 
                           FROM messages m2 
                           WHERE m2.conversation_id = messages.conversation_id 
                           AND m2.author_role = 'user')
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
    LEFT JOIN FirstUserMessage fum 
        ON c.conversation_id = fum.conversation_id
    JOIN messages m 
        ON c.conversation_id = m.conversation_id
    WHERE m.author_role IN ('user', 'assistant') -- Excluimos 'system'
    ORDER BY c.conversation_id, m.create_time;
";

// Ejecutar la consulta
$result = $conn->query($sql);

// Verificar si hay resultados
if ($result->num_rows > 0) {
    $data = [];
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} else {
    echo json_encode(["message" => "No se encontraron resultados"], JSON_PRETTY_PRINT);
}

// Cerrar conexión
$conn->close();
?>
