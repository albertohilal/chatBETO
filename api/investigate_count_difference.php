<?php
/**
 * Investigar diferencia entre phpMyAdmin y conteo directo
 */

require_once '../database/db_connection.php';

echo "=== INVESTIGACIÓN DE DIFERENCIAS DE CONTEO ===\n\n";

try {
    // 1. Conteo directo simple
    $stmt = $pdo->query("SELECT COUNT(*) as total FROM messages");
    $total_directo = $stmt->fetchColumn();
    echo "📊 Conteo directo: $total_directo\n";
    
    // 2. Conteo con DISTINCT (por si hay duplicados)
    $stmt = $pdo->query("SELECT COUNT(DISTINCT id) as total FROM messages");
    $total_distinct = $stmt->fetchColumn();
    echo "📊 Conteo DISTINCT por ID: $total_distinct\n";
    
    // 3. Verificar si hay IDs NULL o duplicados
    $stmt = $pdo->query("SELECT COUNT(*) as nulls FROM messages WHERE id IS NULL");
    $nulls = $stmt->fetchColumn();
    echo "📊 IDs NULL: $nulls\n";
    
    $stmt = $pdo->query("SELECT COUNT(*) - COUNT(DISTINCT id) as duplicados FROM messages");
    $duplicados = $stmt->fetchColumn();
    echo "📊 IDs duplicados: $duplicados\n";
    
    // 4. Verificar tabla específica
    $stmt = $pdo->query("SHOW TABLE STATUS LIKE 'messages'");
    $table_info = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "📊 Rows según SHOW TABLE STATUS: " . ($table_info['Rows'] ?? 'No disponible') . "\n";
    
    // 5. Rango de IDs
    $stmt = $pdo->query("SELECT MIN(id) as min_id, MAX(id) as max_id FROM messages");
    $range = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "📊 Rango de IDs: {$range['min_id']} - {$range['max_id']}\n";
    
    // 6. Verificar si phpMyAdmin puede tener filtros
    echo "\n=== POSIBLES EXPLICACIONES ===\n";
    echo "• Si phpMyAdmin muestra 80,801 y aquí vemos $total_directo:\n";
    
    if ($total_directo > 80801) {
        $diferencia = $total_directo - 80801;
        echo "  - Diferencia: +$diferencia registros\n";
        echo "  - Posible causa: phpMyAdmin con paginación o filtros activos\n";
        echo "  - Posible causa: Vista vs tabla completa en phpMyAdmin\n";
    } elseif ($total_directo == 80801) {
        echo "  - ✅ Los números coinciden exactamente\n";
    } else {
        echo "  - ⚠️ phpMyAdmin muestra MÁS registros que la consulta directa\n";
    }
    
    echo "\n📝 Para verificar en phpMyAdmin:\n";
    echo "   1. Asegúrate de estar en la tabla 'messages'\n";
    echo "   2. Sin filtros activos en la barra de búsqueda\n";
    echo "   3. Ver el número total en la parte inferior\n";
    
} catch (Exception $e) {
    echo "❌ ERROR: " . $e->getMessage();
}
?>