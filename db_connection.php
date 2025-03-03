<?php
// Configuración de la base de datos
$host = "sv46.byethost46.org";
$user = "iunaorg_b3toh";
$password = "elgeneral2018"; // Cambia esto por tu contraseña real
$database = "iunaorg_chatBeto";
$port = 3306;

// Conectar a MySQL
$conn = new mysqli($host, $user, $password, $database, $port);

// Verificar conexión
if ($conn->connect_error) {
    die(json_encode(["error" => "Conexión fallida: " . $conn->connect_error]));
}

// Opcional: establecer el conjunto de caracteres para evitar problemas con acentos y caracteres especiales
$conn->set_charset("utf8mb4");
?>
