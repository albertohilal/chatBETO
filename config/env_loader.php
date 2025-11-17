<?php
/**
 * Cargador de variables de entorno desde archivo .env
 * Versión simple sin dependencias externas
 */

class EnvLoader {
    private static $loaded = false;
    private static $env = [];
    
    public static function load($path = null) {
        if (self::$loaded) {
            return;
        }
        
        if ($path === null) {
            $path = __DIR__ . '/.env';
        }
        
        if (!file_exists($path)) {
            throw new Exception("Archivo .env no encontrado en: " . $path);
        }
        
        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        
        foreach ($lines as $line) {
            // Ignorar comentarios
            if (strpos($line, '#') === 0) {
                continue;
            }
            
            // Buscar líneas con formato KEY=VALUE
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                
                $key = trim($key);
                $value = trim($value);
                
                // Remover comillas si existen
                if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') ||
                    (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                    $value = substr($value, 1, -1);
                }
                
                // Guardar en array interno y en $_ENV
                self::$env[$key] = $value;
                $_ENV[$key] = $value;
                putenv("$key=$value");
            }
        }
        
        self::$loaded = true;
    }
    
    public static function get($key, $default = null) {
        self::load();
        return isset(self::$env[$key]) ? self::$env[$key] : $default;
    }
    
    public static function getAll() {
        self::load();
        return self::$env;
    }
}

/**
 * Función helper para obtener variables de entorno
 */
function env($key, $default = null) {
    return EnvLoader::get($key, $default);
}
?>