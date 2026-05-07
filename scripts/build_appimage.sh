#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPDIR="$PROJECT_ROOT/dist/appimage/AppDir"
APP_NAME="LinuxHardwareMonitor"

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool is required. Install it first."
  exit 1
fi

rm -rf "$PROJECT_ROOT/dist/appimage"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/$APP_NAME"
mkdir -p "$APPDIR/usr/share/applications"

cp -a "$PROJECT_ROOT/collectors" "$APPDIR/usr/lib/$APP_NAME/"
cp "$PROJECT_ROOT/linux_disk_monitor_gui.py" "$APPDIR/usr/lib/$APP_NAME/"
cp "$PROJECT_ROOT/requirements.txt" "$APPDIR/usr/lib/$APP_NAME/"
cp "$PROJECT_ROOT/packaging/linux-hardware-monitor.desktop" "$APPDIR/usr/share/applications/"

cat > "$APPDIR/usr/bin/linux-hardware-monitor" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APPDIR}/usr/lib/LinuxHardwareMonitor"
if [[ -z "${APPDIR:-}" ]]; then
  APP_HOME="/usr/lib/LinuxHardwareMonitor"
fi
exec python3 "$APP_HOME/linux_disk_monitor_gui.py" "$@"
EOF
chmod +x "$APPDIR/usr/bin/linux-hardware-monitor"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/linux-hardware-monitor" "$@"
EOF
chmod +x "$APPDIR/AppRun"

appimagetool "$APPDIR" "$PROJECT_ROOT/dist/${APP_NAME}.AppImage"

echo "Created AppImage: $PROJECT_ROOT/dist/${APP_NAME}.AppImage"
