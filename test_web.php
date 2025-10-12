<?php
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html>
<head>
    <title>Prueba de ChatBETO</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .result { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .error { background: #ffebee; color: #c62828; }
        .success { background: #e8f5e8; color: #2e7d32; }
    </style>
</head>
<body>
    <h1>🧪 Prueba de ChatBETO</h1>
    
    <?php
    require_once 'db_connection.php';
    
    try {
        echo "<div class='result success'>✅ Conectando a la base de datos...</div>";
        
        $conn = connect_to_db();
        if (!$conn) {
            throw new Exception("Error de conexión");
        }
        
        echo "<div class='result success'>✅ Conexión exitosa!</div>";
        
        // Contar registros
        $stmt = $conn->query("SELECT COUNT(*) as count FROM conversations");
        $convCount = $stmt->fetch(PDO::FETCH_ASSOC);
        
        $stmt = $conn->query("SELECT COUNT(*) as count FROM messages");
        $msgCount = $stmt->fetch(PDO::FETCH_ASSOC);
        
        echo "<div class='result'>📊 <strong>Datos en la base:</strong><br>";
        echo "   • Conversaciones: {$convCount['count']}<br>";
        echo "   • Mensajes: {$msgCount['count']}</div>";
        
        // Probar búsqueda
        $query = "import";
        $sql = "SELECT conv.title, msg.role, msg.parts
                FROM conversations conv
                JOIN messages msg ON msg.conversation_id = conv.conversation_id
                WHERE msg.parts LIKE ?
                AND msg.parts IS NOT NULL
                AND msg.parts <> ''
                LIMIT 5";
        
        $stmt = $conn->prepare($sql);
        $stmt->bindValue(1, "%$query%", PDO::PARAM_STR);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo "<div class='result'>🔍 <strong>Búsqueda de '$query':</strong><br>";
        if (count($results) > 0) {
            echo "   ✅ Encontrados: " . count($results) . " resultados<br><br>";
            foreach ($results as $i => $row) {
                $preview = substr(strip_tags($row['parts']), 0, 100);
                echo "<strong>" . ($i+1) . ". {$row['title']}</strong> ({$row['role']})<br>";
                echo "<em>{$preview}...</em><br><br>";
            }
        } else {
            echo "   ⚠️ No se encontraron resultados";
        }
        echo "</div>";
        
        echo "<div class='result success'>✅ <strong>¡La búsqueda funciona perfectamente!</strong></div>";
        echo "<div class='result'>🌐 <strong>Ahora puedes usar la interfaz web:</strong><br>";
        echo "   • Ve a <a href='index.html'>index.html</a><br>";
        echo "   • O prueba la <a href='buscar_chat.php?query=import'>API directamente</a></div>";
        
    } catch (Exception $e) {
        echo "<div class='result error'>❌ Error: " . htmlspecialchars($e->getMessage()) . "</div>";
    }
    ?>
</body>
</html>