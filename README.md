# Linux Hardware Monitor Pro

A professional Linux monitoring project with two complementary products:

- CLI monitor for automation and alerting: disk_monitor.sh
- Premium desktop GUI monitor: linux_disk_monitor_gui.py

## Product Vision

Build a monitor that is easier to install than enterprise stacks, more visual than terminal-only tools, and safer than cloud-first products for users who want local-first telemetry.

## Research-Driven Gap Analysis

A focused review of leading monitoring tools and documentation highlights recurring user needs:

- frictionless install and launch from app menu
- local-first operation without mandatory cloud dependency
- actionable alerts with cooldown, not noisy spam
- exportable metrics for personal analysis and reporting
- clean UX with readable hierarchy and realtime visibility
- persistent configuration for non-technical users
- process-level observability plus system-level trends

Reference sources reviewed:

- btop project docs: https://github.com/aristocratos/btop
- Glances feature docs: https://nicolargo.github.io/glances/
- Netdata project docs: https://github.com/netdata/netdata

## What Is Implemented Now

### 1) Professional GUI App

File: linux_disk_monitor_gui.py

Implemented features:

- Realtime dashboard cards for CPU, memory, root disk, and network
- Smooth live charts for CPU, memory, network in/out, and temperature
- Storage explorer table for mounted filesystems
- Process monitor with filter by process name or user
- System overview with uptime, load average, battery, and thermal data
- Insight stream for trend warnings and operational signals
- Alert event stream with timestamps

### 2) Configurable Alert Engine

- CPU threshold alert
- Memory threshold alert
- Root disk threshold alert
- Temperature threshold alert
- Cooldown control to suppress repeated alert storms
- Optional desktop notifications (notify-send)

### 3) Persistent Settings

Stored in:

- ~/.config/linux-hardware-monitor/config.json

Settings include:

- refresh interval
- history length
- thresholds
- cooldown
- process filter
- notification toggle
- auto-export toggle

### 4) Export and Data Ownership

Stored in:

- ~/.local/share/linux-hardware-monitor/latest_snapshot.json
- ~/.local/share/linux-hardware-monitor/history.csv
- ~/.local/share/linux-hardware-monitor/events.log

Capabilities:

- automatic CSV timeline export
- one-click JSON snapshot export
- manual full CSV history export

### 5) Easy Installation

Added files:

- install.sh
- uninstall.sh
- pyproject.toml
- run_gui.sh

You can install in two easy ways:

1. Local desktop install with launcher and app menu entry
2. Python package style install path via pyproject and entry point

### 6) Existing Professional CLI Monitor

File: disk_monitor.sh

- one-shot or loop mode
- threshold checks
- cooldown logic
- alert command hook
- filesystem include/exclude filtering
- dry-run mode

## Quick Start

### Run GUI Fast

1. chmod +x run_gui.sh
2. ./run_gui.sh

### Install as a Local App (Recommended)

1. chmod +x install.sh
2. ./install.sh
3. Launch from app menu: Linux Hardware Monitor
4. Or run command: linux-hardware-monitor

### Uninstall

1. chmod +x uninstall.sh
2. ./uninstall.sh

## CLI Usage

1. chmod +x disk_monitor.sh
2. ./disk_monitor.sh --help

Example:

./disk_monitor.sh --threshold 90 --loop --interval 300 --log-file /var/log/disk-monitor.log

## Why This Is Better Than Typical Lightweight Monitors

- Better than script-only monitors: rich GUI, alerts, persistent settings, exports
- Better than many terminal monitors for non-terminal users: app menu launch and visual hierarchy
- Better for privacy-sensitive users: local-first data files, no required cloud account
- Better operationally: cooldown-aware alerting and trend insight feed

## HWiNFO-Style Parity Status

This project now provides professional realtime telemetry and operational UX on Linux.

Full parity with deep proprietary hardware tools still requires larger multi-phase additions such as:

- vendor-specific motherboard and VRM probing
- advanced SMART/NVMe decoder coverage
- broader hardware chipset profile database
- extended per-sensor diagnostics and historical analytics

This repository now has a strong product-grade foundation to implement that roadmap.

## Professional Next-Phase Upgrades (Planned)

- optional plugin system for collectors (GPU, SMART, motherboard)
- report builder with PDF and Markdown export
- baseline and anomaly scoring per metric family
- multi-host agent mode with encrypted remote stream
- AppImage and .deb packaging pipeline

## License

See LICENSE.
