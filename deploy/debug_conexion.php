<?php
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');

// Debug completo del error
$debug = [
    'timestamp' => date('Y-m-d H:i:s'),
    'server_info' => [
        'PHP_VERSION' => PHP_VERSION,
        'SERVER_NAME' => $_SERVER['SERVER_NAME'] ?? 'unknown',
        'DOCUMENT_ROOT' => $_SERVER['DOCUMENT_ROOT'] ?? 'unknown',
        'SCRIPT_FILENAME' => $_SERVER['SCRIPT_FILENAME'] ?? 'unknown'
    ],
    'paths' => [
        'current_dir' => __DIR__,
        'db_connection_path' => __DIR__ . '/../database/db_connection.php',
        'db_connection_exists' => file_exists(__DIR__ . '/../database/db_connection.php')
    ]
];

try {
    if (!file_exists(__DIR__ . '/../database/db_connection.php')) {
        throw new Exception('Archivo de conexión no encontrado en: ' . __DIR__ . '/../database/db_connection.php');
    }
    
    require_once __DIR__ . '/../database/db_connection.php';
    
    if (!isset($pdo)) {
        throw new Exception('Variable $pdo no fue definida después de incluir conexión');
    }
    
    // Test simple de conexión
    $test = $pdo->query("SELECT 1 as test");
    if (!$test) {
        throw new Exception('No se pudo ejecutar query de prueba');
    }
    
    // Test de tabla conversations
    $count = $pdo->query("SELECT COUNT(*) as total FROM conversations LIMIT 1");
    $result = $count->fetch();
    
    echo json_encode([
        'success' => true,
        'message' => 'Conexión y consultas funcionando correctamente',
        'total_conversations' => $result['total'],
        'debug' => $debug
    ], JSON_UNESCAPED_UNICODE);
    
} catch (PDOException $e) {
    echo json_encode([
        'success' => false,
        'error_type' => 'PDO Error',
        'error' => $e->getMessage(),
        'code' => $e->getCode(),
        'debug' => $debug
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error_type' => 'General Error',
        'error' => $e->getMessage(),
        'debug' => $debug
    ], JSON_UNESCAPED_UNICODE);
}