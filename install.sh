#!/usr/bin/env bash
set -euo pipefail

APP_NAME="linux-hardware-monitor"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ROOT="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$TARGET_ROOT" "$BIN_DIR" "$DESKTOP_DIR"

rm -rf "$TARGET_ROOT"
mkdir -p "$TARGET_ROOT"
cp -a "$PROJECT_DIR/." "$TARGET_ROOT/"
rm -rf "$TARGET_ROOT/.git" "$TARGET_ROOT/.venv" "$TARGET_ROOT/__pycache__"

cd "$TARGET_ROOT"

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cat > "$BIN_DIR/linux-hardware-monitor" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="$HOME/.local/share/linux-hardware-monitor"
source "$APP_ROOT/.venv/bin/activate"
exec python "$APP_ROOT/linux_disk_monitor_gui.py" "$@"
EOF
chmod +x "$BIN_DIR/linux-hardware-monitor"

cat > "$DESKTOP_DIR/linux-hardware-monitor.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Linux Hardware Monitor
Comment=Realtime Linux system telemetry dashboard
Exec=$BIN_DIR/linux-hardware-monitor
Terminal=false
Categories=System;Monitor;
StartupNotify=true
EOF

if ! grep -q "$BIN_DIR" <<<":${PATH}:"; then
  echo "Add $BIN_DIR to your PATH to run: linux-hardware-monitor"
fi

echo "Installation complete."
echo "Run from terminal: linux-hardware-monitor"
echo "Or launch from app menu: Linux Hardware Monitor"
