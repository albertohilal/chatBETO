# 🚀 Servidor PHP Estable - chatBETO

## Instalación y Uso

### Comandos Disponibles

```bash
# Iniciar el servidor
./start_stable_server.sh start

# Verificar estado
./start_stable_server.sh status

# Reiniciar servidor
./start_stable_server.sh restart

# Detener servidor
./start_stable_server.sh stop

# Monitoreo automático (auto-restart si falla)
./start_stable_server.sh monitor

# Ver logs en tiempo real
./start_stable_server.sh logs
```

### URLs del Proyecto

- **Aplicación Principal**: http://localhost:8002/web/buscar_mensajes.html
- **API Health Check**: http://localhost:8002/api/health_check.php
- **API de Mensajes**: http://localhost:8002/api/messages_simple_working.php
- **API de Proyectos**: http://localhost:8002/api/get_projects_list.php

### Características del Servidor

✅ **Auto-restart**: Se reinicia automáticamente si falla
✅ **Logging completo**: Logs detallados en `/logs/`
✅ **Health checks**: Verificación automática de salud
✅ **Gestión de PID**: Control adecuado de procesos
✅ **Configuración centralizada**: Puerto y configuración en un lugar
✅ **Limpieza automática**: Elimina procesos residuales

### Archivos de Log

- `logs/php_server.log` - Log principal del servidor
- `logs/access.log` - Log de acceso HTTP
- `logs/php_server.pid` - PID del proceso del servidor

### Solución de Problemas

#### El servidor no inicia:
```bash
# Verificar estado
./start_stable_server.sh status

# Reiniciar completamente
./start_stable_server.sh restart

# Ver logs para diagnosticar
./start_stable_server.sh logs
```

#### Puerto ocupado:
```bash
# Detener cualquier proceso en el puerto
pkill -f "php -S"
fuser -k 8002/tcp

# Reiniciar servidor
./start_stable_server.sh restart
```

#### Monitoreo continuo:
```bash
# Ejecutar en background con monitoreo automático
nohup ./start_stable_server.sh monitor > monitor.log 2>&1 &
```

### Ventajas sobre el servidor anterior

1. **Estabilidad**: No se desconecta inesperadamente
2. **Monitoreo**: Detecta fallos y se autoreinicia
3. **Logs**: Debugging mucho más fácil
4. **Control**: Comandos claros para gestión
5. **Robustez**: Manejo adecuado de procesos y señales

### Desarrollo Recomendado

1. **Inicio de sesión**:
   ```bash
   cd /home/beto/Documentos/Github/chatBeto
   ./start_stable_server.sh start
   ```

2. **Durante desarrollo**: El servidor se mantiene estable

3. **Al finalizar**:
   ```bash
   ./start_stable_server.sh stop
   ```