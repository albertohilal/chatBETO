#!/bin/bash

# 🚀 Servidor PHP estable con auto-restart y monitoreo
# Archivo: start_stable_server.sh

# Configuración
PORT=8002
HOST="localhost"
DOCUMENT_ROOT="/home/beto/Documentos/Github/chatBeto"
LOG_DIR="$DOCUMENT_ROOT/logs"
PID_FILE="$LOG_DIR/php_server.pid"
LOG_FILE="$LOG_DIR/php_server.log"
ACCESS_LOG="$LOG_DIR/access.log"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Función para logging con timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para verificar si el servidor está corriendo
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Server is running
        else
            rm -f "$PID_FILE"
            return 1  # PID file exists but process is dead
        fi
    fi
    return 1  # No PID file
}

# Función para detener el servidor
stop_server() {
    log_message "🛑 Deteniendo servidor PHP..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid"
                log_message "⚠️  Servidor forzadamente terminado"
            else
                log_message "✅ Servidor detenido correctamente"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Limpiar cualquier proceso PHP residual
    pkill -f "php -S $HOST:$PORT" 2>/dev/null || true
}

# Función para iniciar el servidor
start_server() {
    log_message "🚀 Iniciando servidor PHP estable..."
    log_message "📂 Directorio: $DOCUMENT_ROOT"
    log_message "🌐 Puerto: $PORT"
    
    cd "$DOCUMENT_ROOT"
    
    # Verificar que los archivos principales existan
    if [ ! -f "web/buscar_mensajes.html" ]; then
        log_message "❌ ERROR: web/buscar_mensajes.html no encontrado"
        exit 1
    fi
    
    # Iniciar servidor en background
    nohup php -S "$HOST:$PORT" -t "$DOCUMENT_ROOT" > "$ACCESS_LOG" 2>&1 &
    local server_pid=$!
    
    # Guardar PID
    echo "$server_pid" > "$PID_FILE"
    
    # Esperar un momento para verificar que inició correctamente
    sleep 2
    
    if ps -p "$server_pid" > /dev/null 2>&1; then
        log_message "✅ Servidor iniciado correctamente (PID: $server_pid)"
        log_message "🌐 URLs disponibles:"
        log_message "   - http://$HOST:$PORT/web/buscar_mensajes.html"
        log_message "   - http://$HOST:$PORT/api/health_check.php"
        return 0
    else
        log_message "❌ ERROR: El servidor falló al iniciar"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Función para verificar la salud del servidor
health_check() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST:$PORT/api/health_check.php" 2>/dev/null)
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Función para mostrar el estado
show_status() {
    echo "📊 Estado del servidor PHP:"
    echo "   Puerto: $PORT"
    echo "   PID File: $PID_FILE"
    echo "   Log: $LOG_FILE"
    echo ""
    
    if is_server_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ Estado: CORRIENDO (PID: $pid)"
        
        if health_check; then
            echo "✅ Health Check: OK"
        else
            echo "⚠️  Health Check: FALLÓ"
        fi
    else
        echo "❌ Estado: DETENIDO"
    fi
    echo ""
    echo "🌐 URL: http://$HOST:$PORT/web/buscar_mensajes.html"
}

# Función principal
main() {
    case "${1:-start}" in
        "start")
            if is_server_running; then
                log_message "⚠️  El servidor ya está corriendo"
                show_status
            else
                stop_server  # Limpieza preventiva
                if start_server; then
                    show_status
                else
                    log_message "❌ Falló al iniciar el servidor"
                    exit 1
                fi
            fi
            ;;
            
        "stop")
            stop_server
            ;;
            
        "restart")
            stop_server
            sleep 1
            start_server
            show_status
            ;;
            
        "status")
            show_status
            ;;
            
        "monitor")
            log_message "🔍 Iniciando monitoreo del servidor..."
            while true; do
                if ! is_server_running || ! health_check; then
                    log_message "⚠️  Servidor no responde, reiniciando..."
                    stop_server
                    sleep 2
                    start_server
                fi
                sleep 30
            done
            ;;
            
        "logs")
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                echo "❌ No hay logs disponibles"
            fi
            ;;
            
        *)
            echo "Uso: $0 {start|stop|restart|status|monitor|logs}"
            echo ""
            echo "Comandos:"
            echo "  start   - Iniciar el servidor"
            echo "  stop    - Detener el servidor"
            echo "  restart - Reiniciar el servidor"
            echo "  status  - Mostrar estado del servidor"
            echo "  monitor - Monitorear y auto-reiniciar"
            echo "  logs    - Mostrar logs en tiempo real"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"