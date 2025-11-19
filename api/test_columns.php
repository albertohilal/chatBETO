<?php
require_once '../database/db_connection.php';
header('Content-Type: text/plain');

try {
    echo "=== PRUEBA DIRECTA DE COLUMNAS ===\n\n";
    
    // Probar diferentes nombres de columnas
    $tests = [
        ['role', 'content'],
        ['author_role', 'content_text'],
        ['role', 'content_text'],
        ['author_role', 'content']
    ];
    
    foreach ($tests as $i => $test) {
        echo "Prueba " . ($i+1) . ": role=" . $test[0] . ", content=" . $test[1] . "\n";
        
        try {
            $sql = "SELECT c.title, m.{$test[0]} as role_col, m.{$test[1]} as content_col 
                    FROM conversations c 
                    INNER JOIN messages m ON m.conversation_id = c.id 
                    LIMIT 1";
            
            $stmt = $pdo->query($sql);
            $result = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($result) {
                echo "✅ FUNCIONA - " . $test[0] . ", " . $test[1] . "\n";
                echo "Título: " . $result['title'] . "\n";
                echo "Rol: " . $result['role_col'] . "\n";
                echo "Contenido: " . substr($result['content_col'], 0, 50) . "...\n";
                break;
            }
            
        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
        }
        echo "\n";
    }
    
} catch (Exception $e) {
    echo "ERROR GENERAL: " . $e->getMessage() . "\n";
}
?>