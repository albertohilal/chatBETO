"""
Cargador de variables de entorno para Python
Equivalente al env_loader.php
"""
import os
from typing import Any, Optional, Dict

class EnvLoader:
    _loaded = False
    _env = {}
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> None:
        if cls._loaded:
            return
        
        if path is None:
            path = os.path.join(os.path.dirname(__file__), '.env')
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Archivo .env no encontrado en: {path}")
        
        with open(path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                
                # Ignorar líneas vacías y comentarios
                if not line or line.startswith('#'):
                    continue
                
                # Buscar líneas con formato KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remover comillas si existen
                    if ((value.startswith('"') and value.endswith('"')) or
                        (value.startswith("'") and value.endswith("'"))):
                        value = value[1:-1]
                    
                    # Guardar en diccionario interno y en variables de entorno
                    cls._env[key] = value
                    os.environ[key] = value
        
        cls._loaded = True
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        cls.load()
        return cls._env.get(key, default)
    
    @classmethod
    def get_all(cls) -> Dict[str, str]:
        cls.load()
        return cls._env.copy()

def env(key: str, default: Any = None) -> Any:
    """Función helper para obtener variables de entorno"""
    return EnvLoader.get(key, default)

def get_db_config():
    """Obtener configuración de base de datos desde .env"""
    return {
        'host': env('DB_HOST', 'localhost'),
        'database': env('DB_NAME', 'chatBeto'),
        'user': env('DB_USERNAME', 'root'),
        'password': env('DB_PASSWORD', ''),
        'charset': 'utf8mb4'
    }

def get_app_config():
    """Obtener configuración de aplicación desde .env"""
    return {
        'name': env('APP_NAME', 'ChatBETO'),
        'environment': env('APP_ENV', 'production'),
        'debug': env('APP_DEBUG', 'false').lower() in ('true', '1', 'yes')
    }