<?php
header('Content-Type: application/json; charset=utf-8');
require_once 'db_connection.php';

try {
    echo "Probando conexión...\n";
    
    // Test básico de conexión
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM projects");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "✅ Proyectos: " . $result['count'] . "\n";
    
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM conversations");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "✅ Conversaciones: " . $result['count'] . "\n";
    
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM messages");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "✅ Mensajes: " . $result['count'] . "\n";
    
    // Test de estructura
    echo "\n📋 Columnas de projects:\n";
    $stmt = $pdo->query("DESCRIBE projects");
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "- " . $row['Field'] . " (" . $row['Type'] . ")\n";
    }
    
    echo "\n📋 Columnas de messages:\n";
    $stmt = $pdo->query("DESCRIBE messages");
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "- " . $row['Field'] . " (" . $row['Type'] . ")\n";
    }
    
    echo "\n✅ Conexión y estructura OK!";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage();
}
?>