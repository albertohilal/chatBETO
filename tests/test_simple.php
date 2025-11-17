<?php
// Test simple de la API de búsqueda
require_once 'db_connection.php';

try {
    $conn = connect_to_db();
    
    if (!$conn) {
        echo "Error de conexión\n";
        exit(1);
    }
    
    // Hacer una consulta simple
    $stmt = $conn->prepare("SELECT parts FROM messages WHERE parts LIKE ? LIMIT 1");
    $stmt->bindValue(1, "%help%", PDO::PARAM_STR);
    $stmt->execute();
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($result) {
        echo "✅ Búsqueda funciona: " . substr($result['parts'], 0, 50) . "...\n";
    } else {
        echo "⚠️ No se encontraron resultados para 'help'\n";
        
        // Probar con cualquier contenido
        $stmt = $conn->prepare("SELECT parts FROM messages WHERE parts IS NOT NULL AND parts != '' LIMIT 3");
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo "📊 Ejemplos de contenido en la DB:\n";
        foreach ($results as $i => $row) {
            echo ($i+1) . ". " . substr($row['parts'], 0, 100) . "...\n";
        }
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>