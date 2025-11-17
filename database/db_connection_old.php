<?php
// Configuración de base de datos para chatBETO
try {
    // Leer configuración desde archivo JSON
    $config_file = __DIR__ . '/db_config.json';
    if (file_exists($config_file)) {
        $config_json = file_get_contents($config_file);
        $config = json_decode($config_json, true);
        
        $host = $config['host'];
        $database = $config['database'];
        $username = $config['user'];
        $password = $config['password'];
        $port = $config['port'] ?? 3306;
    } else {
        // Configuración por defecto
        $host = 'localhost';
        $database = 'test';
        $username = 'root';
        $password = '';
        $port = 3306;
    }
    
    // Crear conexión PDO
    $dsn = "mysql:host={$host};port={$port};dbname={$database};charset=utf8mb4";
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];
    
    $pdo = new PDO($dsn, $username, $password, $options);

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

function connect_to_db() {
    global $pdo;
    return $pdo;
}

/**
 * Función para obtener información de configuración (sin credenciales sensibles)
 */
function get_db_config_info() {
    return [
        'host' => env('DB_HOST'),
        'database' => env('DB_NAME'),
        'app_name' => env('APP_NAME', 'ChatBETO'),
        'environment' => env('APP_ENV', 'production')
    ];
}
?>
