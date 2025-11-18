<?php
// Configuración de base de datos para chatBETO
// Siempre usando la base de datos de iFastNet

$host = 'sv46.byethost46.org';
$database = 'iunaorg_chatBeto';
$username = 'iunaorg_b3toh';
$password = 'elgeneral2018';
$port = 3306;

try {
    // Crear conexión PDO directa con credenciales de iFastNet
    $dsn = "mysql:host={$host};port={$port};dbname={$database};charset=utf8mb4";
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];
    
    $pdo = new PDO($dsn, $username, $password, $options);
    
    // Verificación silenciosa de la conexión a la BD existente
    $stmt = $pdo->query("SELECT 1");

} catch (PDOException $e) {
    // Log del error para debugging
    error_log("chatBETO DB Error: " . $e->getMessage());
    
    // Respuesta JSON de error para APIs
    if (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], 'api_') !== false) {
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Error de conexión a la base de datos', 'details' => $e->getMessage()]);
        exit;
    }
    
    die("Error de conexión DB: " . $e->getMessage());
}

function connect_to_db() {
    global $pdo;
    return $pdo;
}