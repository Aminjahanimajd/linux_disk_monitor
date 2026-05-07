# Linux Hardware Monitor Pro

An elite-tier Linux monitoring suite with:

- a production Bash monitor for automation and alerting (`disk_monitor.sh`)
- a premium desktop GUI with collector plugins and anomaly intelligence (`linux_disk_monitor_gui.py`)

## What Was Upgraded In This Tier

This release executes the advanced roadmap in three major areas:

1. Native packaging pipeline
2. Collector plugin architecture (SMART, NVMe, GPU)
3. Baseline-drift anomaly detection and scoring

## Research-Led Needs Matrix

Based on practical gaps users report in common tools (installation friction, weak local ownership, alert noise, and missing export/insight flow), this project now targets those needs explicitly.

Needs addressed now:

- easy Linux install and uninstall
- desktop launcher integration
- local-first data ownership
- anomaly score for unusual runtime behavior
- plugin-ready hardware telemetry model
- configurable threshold and cooldown alerting
- historical exports and event logs

Reference ecosystems analyzed:

- btop: https://github.com/aristocratos/btop
- Glances: https://nicolargo.github.io/glances/
- Netdata: https://github.com/netdata/netdata

## Elite Features Implemented

### A) Native Packaging and Distribution

Added build pipeline scripts:

- `scripts/build_deb.sh`
- `scripts/build_appimage.sh`
- `packaging/linux-hardware-monitor.desktop`

Outputs:

- `.deb` package in `dist/deb/`
- `.AppImage` artifact in `dist/`

### B) Collector Plugin Architecture

Added modular collectors package:

- `collectors/base.py`
- `collectors/loader.py`
- `collectors/smart_collector.py`
- `collectors/nvme_collector.py`
- `collectors/gpu_collector.py`

Collector behavior:

- graceful capability detection if binaries are missing
- status reporting per plugin
- standardized metric payloads
- periodic polling and GUI visualization in a dedicated tab

### C) Anomaly and Baseline Drift Engine

Implemented in GUI runtime:

- per-metric rolling baseline (EWMA)
- rolling variance and sigma estimation
- anomaly score aggregation
- baseline drift indicator
- anomaly-triggered alert channel with cooldown control
- visual risk card and progress bar in GUI

### D) Premium GUI Additions

- new Hardware Plugins tab
- anomaly risk card on dashboard
- anomaly sensitivity control in settings
- richer insights stream with anomaly interpretation
- anomaly and drift fields exported to CSV and JSON snapshots

## Quick Start

### Fast Run (Dev)

```bash
chmod +x run_gui.sh
./run_gui.sh
```

### Local Desktop Install

```bash
chmod +x install.sh
./install.sh
linux-hardware-monitor
```

### Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

## Build Native Packages

### Build .deb

```bash
chmod +x scripts/build_deb.sh
./scripts/build_deb.sh
```

### Build AppImage

Requires `appimagetool`.

```bash
chmod +x scripts/build_appimage.sh
./scripts/build_appimage.sh
```

## Data Ownership

Runtime files are local by default:

- `~/.config/linux-hardware-monitor/config.json`
- `~/.local/share/linux-hardware-monitor/history.csv`
- `~/.local/share/linux-hardware-monitor/latest_snapshot.json`
- `~/.local/share/linux-hardware-monitor/events.log`

## CLI Monitor

The Bash monitor remains available for server workflows:

```bash
chmod +x disk_monitor.sh
./disk_monitor.sh --threshold 90 --loop --interval 300 --log-file /var/log/disk-monitor.log
```

## Current vs Full Deep-Hardware Parity

This release now includes a professional GUI, plugin pipeline, anomaly scoring, and packaging automation.

Remaining long-horizon parity work for proprietary deep-hardware suites may include:

- broader vendor-specific motherboard sensor decoders
- advanced SMART/NVMe health model parsing beyond CLI summaries
- deeper per-device diagnostics and fleet-grade analytics

## License

See `LICENSE`.
