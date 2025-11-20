<?php
/**
 * 🏥 Simple server test endpoint
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

echo json_encode([
    'status' => 'ok',
    'message' => 'Server is running',
    'timestamp' => date('c'),
    'server' => $_SERVER['SERVER_NAME'] ?? 'localhost',
    'port' => $_SERVER['SERVER_PORT'] ?? 'unknown',
    'method' => $_SERVER['REQUEST_METHOD'] ?? 'unknown'
]);
?>