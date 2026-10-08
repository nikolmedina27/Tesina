#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/steelplan"
API_URL="http://127.0.0.1:8600/api/docs"
APP_URL="http://127.0.0.1:8600"
LOG_FILE="$STATE_DIR/steelplan.log"

mkdir -p "$STATE_DIR"

# --ruta=VISTA abre directamente una vista (tproduccion, programacion, mant, tv…); el resto va al navegador
RUTA=""
ARGS=()
for a in "$@"; do
    case "$a" in
        --ruta=*) RUTA="${a#--ruta=}" ;;
        *) ARGS+=("$a") ;;
    esac
done
[ -n "$RUTA" ] && APP_URL="$APP_URL/#/$RUTA"

notify_msg() {
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "$@"
    fi
}

start_server() {
    cd "$PROJECT_DIR" || exit 1
    if [ -x "$PROJECT_DIR/.venv/bin/uvicorn" ]; then
        nohup "$PROJECT_DIR/.venv/bin/uvicorn" plataforma.server:app --host 127.0.0.1 --port 8600 >>"$LOG_FILE" 2>&1 &
    else
        nohup python3 -m uvicorn plataforma.server:app --host 127.0.0.1 --port 8600 >>"$LOG_FILE" 2>&1 &
    fi
    
    server_ready=0
    # el servidor tarda ~25 s en arrancar (entrena el modelo de horas): se espera hasta 60 s
    for _ in $(seq 1 300); do
        if curl -fsS --max-time 1 "$API_URL" >/dev/null 2>&1; then
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
if ! curl -fsS --max-time 1 "$API_URL" >/dev/null 2>&1; then
    start_server
fi

# Abre la aplicación en modo ventana o navegador por defecto
if command -v chromium >/dev/null 2>&1; then
    CHROMIUM_PROFILE="$STATE_DIR/chromium"
    CHROMIUM_BIN="$(command -v chromium)"
    exec "$CHROMIUM_BIN" \
        --app="$APP_URL" \
        --class=SteelPlan \
        --name=SteelPlan \
        --user-data-dir="$CHROMIUM_PROFILE" "${ARGS[@]}"
else
    exec xdg-open "$APP_URL"
fi
