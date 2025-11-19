<?php
/**
 * API ENDPOINT: Health check para verificar conexión a la base de datos
 * Uso: api/health_check.php
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

try {
    require_once '../database/db_connection.php';
    
    // Test simple de conexión
    $stmt = $pdo->query('SELECT 1 as test');
    $result = $stmt->fetch();
    
    if ($result && $result['test'] == 1) {
        echo json_encode([
            'success' => true,
            'status' => 'healthy',
            'database' => 'connected',
            'timestamp' => date('c'),
            'version' => '1.0.0',
            'server' => $_SERVER['SERVER_NAME'] ?? 'localhost'
        ]);
    } else {
        throw new Exception('Database test failed');
    }

} catch (Exception $e) {
    http_response_code(503);
    echo json_encode([
        'success' => false,
        'status' => 'unhealthy',
        'database' => 'disconnected',
        'error' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
?>