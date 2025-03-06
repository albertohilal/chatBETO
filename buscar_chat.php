<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
require 'db_connection.php';

$query = isset($_GET['query']) ? $_GET['query'] : '';

if (empty($query)) {
    die("No se proporcionó una consulta.");
}

try {
    $conn = connect_to_db();
    $sql = file_get_contents('conversation-messages.sql');

    $stmt = $conn->prepare($sql);
    $stmt->bindValue(':query', "%$query%", PDO::PARAM_STR);
    $stmt->execute();
    
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Imprimir directamente sin formateo
    echo "<pre>";
    print_r($results);
    echo "</pre>";

} catch (PDOException $e) {
    die("Error en la consulta: " . $e->getMessage());
}
?>
