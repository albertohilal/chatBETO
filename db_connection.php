<?php
// Cargar variables de entorno
require_once __DIR__ . '/env_loader.php';

function connect_to_db() {
    // Cargar configuración desde .env
    $host = env('DB_HOST', 'localhost');
    $dbname = env('DB_NAME', 'chatBeto');
    $username = env('DB_USERNAME', 'root');
    $password = env('DB_PASSWORD', '');
    
    try {
        $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $conn;
    } catch (PDOException $e) {
        $debug = env('APP_DEBUG', false);
        $error_msg = $debug ? $e->getMessage() : "Error de conexión a la base de datos";
        die("Error de conexión: " . $error_msg);
    }
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
