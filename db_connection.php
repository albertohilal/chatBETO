<?php
function connect_to_db() {
    $host = "sv46.byethost46.org";
    $dbname = "iunaorg_chatBeto";
    $username = "iunaorg_b3toh";
    $password = "elgeneral2018";
    
    try {
        $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $conn;
    } catch (PDOException $e) {
        die("Error de conexión: " . $e->getMessage());
    }
}
?>
