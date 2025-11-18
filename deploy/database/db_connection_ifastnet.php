<?php
// Configuración de base de datos para iFastNet
// Actualiza estos datos con tu configuración real de iFastNet

$host = 'sql110.infinityfree.com';  // O el host que te proporcione iFastNet
$dbname = 'if0_XXXXXX_chatbeto';    // Tu base de datos en iFastNet 
$username = 'if0_XXXXXX';           // Tu usuario de BD en iFastNet
$password = 'tu_password_bd';       // Tu password de BD

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch(PDOException $e) {
    error_log("Error de conexión: " . $e->getMessage());
    die("Error de conexión a la base de datos");
}