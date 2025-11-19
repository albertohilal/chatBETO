<?php
/**
 * Debug: Verificar estructura de tabla messages
 */

header('Content-Type: application/json');
require_once '../database/db_connection.php';

try {
    // Verificar estructura de la tabla
    $stmt = $pdo->query("DESCRIBE messages");
    $columns = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo "=== ESTRUCTURA DE TABLA MESSAGES ===\n";
    foreach ($columns as $col) {
        echo $col['Field'] . " - " . $col['Type'] . "\n";
    }
    
    echo "\n=== PROBANDO CONSULTA SIMPLE ===\n";
    
    // Probar consulta básica
    $sql = "SELECT c.id, c.title, m.role, m.content 
            FROM conversations c 
            INNER JOIN messages m ON c.id = m.conversation_id 
            WHERE c.project_id = 1 
            LIMIT 2";
    
    $stmt = $pdo->query($sql);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    foreach ($results as $row) {
        echo "Conversación: " . $row['title'] . "\n";
        echo "Rol: " . $row['role'] . "\n";
        echo "Contenido: " . substr($row['content'], 0, 50) . "...\n";
        echo "---\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
?>