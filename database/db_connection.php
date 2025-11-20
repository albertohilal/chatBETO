<?php
// Configuración de base de datos para chatBETO
try {
    // Función para cargar variables del archivo .env
    function loadEnv($path) {
        if (!file_exists($path)) {
            return [];
        }
        
        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $env = [];
        
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            
            list($name, $value) = explode('=', $line, 2);
            $env[trim($name)] = trim($value);
        }
        
        return $env;
    }
    
    // Cargar configuración desde archivo .env
    $env = loadEnv(__DIR__ . '/../.env');
    
    if (!empty($env)) {
        $host = $env['DB_HOST'];
        $database = $env['DB_DATABASE'];
        $username = $env['DB_USER'];
        $password = $env['DB_PASS'];
        $port = 3306; // Puerto por defecto para MySQL
    } else {
        // Configuración por defecto si no existe .env
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
}

function connect_to_db() {
    global $pdo;
    return $pdo;
}
?>