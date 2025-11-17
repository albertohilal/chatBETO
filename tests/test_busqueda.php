<?php
// Script de prueba para verificar la base de datos
require_once 'db_connection.php';

echo "🧪 Probando conexión y búsqueda...\n";

try {
    $conn = connect_to_db();
    
    if (!$conn) {
        echo "❌ Error de conexión\n";
        exit(1);
    }
    
    echo "✅ Conectado a la base de datos\n";
    
    // Contar registros
    $stmt = $conn->query("SELECT COUNT(*) as count FROM conversations");
    $convCount = $stmt->fetch(PDO::FETCH_ASSOC);
    
    $stmt = $conn->query("SELECT COUNT(*) as count FROM messages");
    $msgCount = $stmt->fetch(PDO::FETCH_ASSOC);
    
    echo "📊 Datos actuales:\n";
    echo "   - Conversaciones: {$convCount['count']}\n";
    echo "   - Mensajes: {$msgCount['count']}\n";
    
    // Hacer una búsqueda de prueba
    $query = "Help";
    $sql = "SELECT 
                conv.conversation_id, 
                conv.title,
                msg.id,
                msg.create_time, 
                msg.role AS message_role, 
                msg.parts AS message_content
            FROM conversations conv
            JOIN messages msg ON msg.conversation_id = conv.conversation_id
            WHERE conv.conversation_id IN (
                SELECT DISTINCT sub_messages.conversation_id
                FROM messages sub_messages
                WHERE sub_messages.parts LIKE ?
                  AND sub_messages.parts IS NOT NULL
                  AND sub_messages.parts <> ''
            )
            AND msg.role IN ('user', 'assistant')
            AND msg.parts IS NOT NULL
            AND msg.parts <> ''
            ORDER BY conv.conversation_id, msg.create_time ASC, msg.id ASC
            LIMIT 5";
    
    $stmt = $conn->prepare($sql);
    $stmt->bindValue(1, "%$query%", PDO::PARAM_STR);
    $stmt->execute();
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo "\n🔍 Búsqueda de '$query':\n";
    echo "   - Resultados encontrados: " . count($results) . "\n";
    
    if (count($results) > 0) {
        echo "✅ ¡La búsqueda funciona correctamente!\n";
        foreach ($results as $i => $row) {
            echo "   " . ($i+1) . ". {$row['title']} - {$row['message_role']}\n";
        }
    } else {
        echo "⚠️  No se encontraron resultados para '$query'\n";
        
        // Probar con otra búsqueda
        $query2 = "ChatGPT";
        $stmt->bindValue(1, "%$query2%", PDO::PARAM_STR);
        $stmt->execute();
        $results2 = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo "\n🔍 Búsqueda alternativa '$query2':\n";
        echo "   - Resultados encontrados: " . count($results2) . "\n";
        
        if (count($results2) > 0) {
            echo "✅ ¡La búsqueda funciona correctamente!\n";
        }
    }
    
    echo "\n✅ Prueba completada exitosamente!\n";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>