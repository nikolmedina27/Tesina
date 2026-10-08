#!/usr/bin/env bash
# Instala el lanzador de SteelPlan en el menú de aplicaciones de Linux (sin editar rutas a mano).
# Uso: bash lanzador/instalar_linux.sh
set -eu
PROYECTO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINO="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESTINO"
chmod +x "$PROYECTO/scripts/steelplan-launch.sh"
sed "s#RUTA_PROYECTO#$PROYECTO#g" "$PROYECTO/lanzador/SteelPlan.desktop" > "$DESTINO/SteelPlan.desktop"
chmod +x "$DESTINO/SteelPlan.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESTINO" || true
echo "SteelPlan instalado en $DESTINO/SteelPlan.desktop (proyecto: $PROYECTO)"
echo "Clic derecho en el ícono: Tablero de producción, Programación, Mantenimiento y Modo TV."
