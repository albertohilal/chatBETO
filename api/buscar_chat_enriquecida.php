<?php
function connect_to_db() {
    $host = "sv46.byethost46.org";
    $dbname = "iunaorg_chatBeto";
    $username = "iunaorg_b3toh";
    $password = "elgeneral2018";
    
    try {
        $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $conn;
    } catch (PDOException $e) {
        die("Error de conexión: " . $e->getMessage());
    }
}

function buscar_conversaciones_enriquecida($query = '') {
    $conn = connect_to_db();
    
    if (empty($query)) {
        // Mostrar estadísticas generales si no hay query
        $sql = "SELECT 
                    COUNT(*) as total_conversaciones,
                    COUNT(DISTINCT model) as modelos_diferentes,
                    MIN(create_time) as primera_conversacion,
                    MAX(create_time) as ultima_conversacion
                FROM conversations 
                WHERE create_time IS NOT NULL";
        
        $stmt = $conn->prepare($sql);
        $stmt->execute();
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
    
    // Búsqueda enriquecida con los nuevos campos
    $sql = "SELECT DISTINCT 
                c.conversation_id,
                c.project_name,
                c.title,
                c.create_time,
                c.update_time,
                c.model,
                m.id as message_id,
                m.create_time as message_time,
                m.role as message_role,
                SUBSTRING(m.content, 1, 500) as message_content
            FROM conversations c
            INNER JOIN messages m ON c.conversation_id = m.conversation_id
            WHERE (m.content LIKE :query1 
                   OR c.title LIKE :query2 
                   OR c.project_name LIKE :query3
                   OR c.model LIKE :query4)
            ORDER BY c.create_time DESC, m.create_time ASC
            LIMIT 50";
    
    $stmt = $conn->prepare($sql);
    $search_term = '%' . $query . '%';
    $stmt->bindParam(':query1', $search_term);
    $stmt->bindParam(':query2', $search_term);
    $stmt->bindParam(':query3', $search_term);
    $stmt->bindParam(':query4', $search_term);
    $stmt->execute();
    
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// Manejar la petición
header('Content-Type: application/json; charset=utf-8');

$query = isset($_GET['query']) ? trim($_GET['query']) : '';
$resultados = buscar_conversaciones_enriquecida($query);

echo json_encode($resultados, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>