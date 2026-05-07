#!/usr/bin/env bash
set -euo pipefail

APP_NAME="linux-hardware-monitor"
TARGET_ROOT="$HOME/.local/share/$APP_NAME"
BIN_FILE="$HOME/.local/bin/linux-hardware-monitor"
DESKTOP_FILE="$HOME/.local/share/applications/linux-hardware-monitor.desktop"

rm -rf "$TARGET_ROOT"
rm -f "$BIN_FILE"
rm -f "$DESKTOP_FILE"

echo "Uninstalled Linux Hardware Monitor launcher and app files."
