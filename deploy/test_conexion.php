<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Información de configuración para debug
$debug_info = [
    'servidor' => $_SERVER['SERVER_NAME'] ?? 'unknown',
    'directorio_actual' => __DIR__,
    'archivo_conexion' => __DIR__ . '/database/db_connection.php',
    'existe_conexion' => file_exists(__DIR__ . '/database/db_connection.php'),
    'timestamp' => date('Y-m-d H:i:s')
];

try {
    // Intentar incluir archivo de conexión
    if (file_exists(__DIR__ . '/database/db_connection.php')) {
        require_once __DIR__ . '/database/db_connection.php';
        
        // Probar conexión a BD
        if (isset($pdo)) {
            $stmt = $pdo->query("SELECT COUNT(*) as total FROM conversations LIMIT 1");
            $result = $stmt->fetch();
            
            echo json_encode([
                'success' => true,
                'message' => 'Conexión exitosa a base de datos',
                'total_conversaciones' => $result['total'],
                'debug' => $debug_info
            ], JSON_UNESCAPED_UNICODE);
        } else {
            echo json_encode([
                'success' => false,
                'error' => 'Variable $pdo no definida',
                'debug' => $debug_info
            ], JSON_UNESCAPED_UNICODE);
        }
    } else {
        echo json_encode([
            'success' => false,
            'error' => 'Archivo de conexión no encontrado',
            'debug' => $debug_info
        ], JSON_UNESCAPED_UNICODE);
    }
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => 'Error: ' . $e->getMessage(),
        'debug' => $debug_info
    ], JSON_UNESCAPED_UNICODE);
}