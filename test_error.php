<?php
// Habilitar la visualización de errores
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Probar la conexión a la base de datos
require_once "db_connection.php";

if ($conn->connect_error) {
    die("Error de conexión: " . $conn->connect_error);
}

echo "Conexión exitosa a la base de datos.";

// Probar una consulta simple
$sql = "SELECT COUNT(*) AS total FROM messages";
$result = $conn->query($sql);

if ($result) {
    $row = $result->fetch_assoc();
    echo "<br>Total de mensajes en la base: " . $row["total"];
} else {
    echo "<br>Error en la consulta: " . $conn->error;
}

// Cerrar conexión
$conn->close();
?>
