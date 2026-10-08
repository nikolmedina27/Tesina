#!/usr/bin/env bash
set -u

PROJECT_DIR="/home/paolo/Projects/Tesina"
STATE_DIR="/home/paolo/.local/state/steelplan"
API_URL="http://127.0.0.1:8600/api/docs"
APP_URL="http://127.0.0.1:8600"
LOG_FILE="$STATE_DIR/steelplan.log"

mkdir -p "$STATE_DIR"

notify_msg() {
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "$@"
    fi
}

start_server() {
    cd "$PROJECT_DIR" || exit 1
    nohup "$PROJECT_DIR/.venv/bin/uvicorn" plataforma.server:app --host 127.0.0.1 --port 8600 >>"$LOG_FILE" 2>&1 &
    
    server_ready=0
    for _ in $(seq 1 60); do
        if /usr/bin/curl -fsS --max-time 1 "$API_URL" >/dev/null 2>&1; then
            server_ready=1
            break
        fi
        sleep 0.2
    done
    
    if [ "$server_ready" -ne 1 ]; then
        notify_msg --urgency=critical "SteelPlan" "No se pudo iniciar el servidor. Revisa $LOG_FILE"
        exit 1
    fi
}

# Inicia el backend si no está respondiendo
if ! /usr/bin/curl -fsS --max-time 1 "$API_URL" >/dev/null 2>&1; then
    start_server
fi

# Abre la aplicación en modo ventana o navegador por defecto
if command -v chromium >/dev/null 2>&1; then
    CHROMIUM_PROFILE="$STATE_DIR/chromium"
    exec /usr/bin/chromium \
        --app="$APP_URL" \
        --class=SteelPlan \
        --name=SteelPlan \
        --ozone-platform=wayland \
        --user-data-dir="$CHROMIUM_PROFILE" "$@"
else
    exec xdg-open "$APP_URL"
fi
