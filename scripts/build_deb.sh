#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/dist/deb"
PKG_NAME="linux-hardware-monitor"
VERSION="1.2.0"
ARCH="all"
INSTALL_ROOT="$BUILD_DIR/${PKG_NAME}_${VERSION}_${ARCH}"

rm -rf "$BUILD_DIR"
mkdir -p "$INSTALL_ROOT/DEBIAN"
mkdir -p "$INSTALL_ROOT/usr/lib/$PKG_NAME"
mkdir -p "$INSTALL_ROOT/usr/share/applications"
mkdir -p "$INSTALL_ROOT/usr/bin"

cp -a "$PROJECT_ROOT/collectors" "$INSTALL_ROOT/usr/lib/$PKG_NAME/"
cp "$PROJECT_ROOT/linux_disk_monitor_gui.py" "$INSTALL_ROOT/usr/lib/$PKG_NAME/"
cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_ROOT/usr/lib/$PKG_NAME/"
cp "$PROJECT_ROOT/packaging/linux-hardware-monitor.desktop" "$INSTALL_ROOT/usr/share/applications/"

cat > "$INSTALL_ROOT/usr/bin/linux-hardware-monitor" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_HOME="/usr/lib/linux-hardware-monitor"
exec python3 "$APP_HOME/linux_disk_monitor_gui.py" "$@"
EOF
chmod +x "$INSTALL_ROOT/usr/bin/linux-hardware-monitor"

cat > "$INSTALL_ROOT/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Linux Hardware Monitor Team <maintainer@example.com>
Depends: python3, python3-psutil
Description: Linux Hardware Monitor Pro GUI
 Professional Linux system and hardware monitor with alerts,
 plugin collectors, and anomaly scoring.
EOF

chmod 755 "$INSTALL_ROOT/DEBIAN"

dpkg-deb --build "$INSTALL_ROOT"

echo "Created package: ${INSTALL_ROOT}.deb"
