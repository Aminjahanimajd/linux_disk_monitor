# Linux Hardware Monitor Pro

A professional Linux monitoring platform designed to combine operations reliability, high-quality visual telemetry, and practical daily usability.

This project delivers two integrated products:

- **CLI monitor** for automation and infrastructure workflows: `disk_monitor.sh`
- **Desktop GUI monitor** for realtime observability and diagnostics: `linux_disk_monitor_gui.py`

## Executive Storyline

Most Linux teams begin monitoring with one of two extremes:

- lightweight scripts that are fast but limited in visualization and user experience
- heavy stacks that are powerful but expensive in setup, maintenance, and resources

This project was built to close that gap.

The storyline is simple: create a monitor that is **easy to install**, **professional to operate**, **clear to read under pressure**, and **extensible for deep hardware telemetry**.

## Problem Statement

Common pain points users repeatedly face in system-monitoring tools:

1. Installation friction and weak desktop integration
2. Alert noise without cooldown and prioritization
3. Limited local ownership of data and exports
4. Poor bridge between raw telemetry and actionable insights
5. No simple path to extend hardware collectors over time

## Goals

Primary goals of this platform:

1. Deliver fast local monitoring with modern GUI quality
2. Keep automation-first workflows available through CLI
3. Provide alerting that is useful, not noisy
4. Preserve local-first data ownership and easy export
5. Establish an architecture that can scale to deeper hardware support

## Solution Approach

The implementation is intentionally split into layered capabilities:

1. **Core telemetry layer**
- CPU, memory, disk, network, process, temperature, uptime, and load metrics

2. **Intelligence layer**
- baseline modeling
- variance and drift estimation
- anomaly scoring

3. **Collector extension layer**
- plugin architecture for optional hardware collectors (SMART, NVMe, GPU)

4. **Operations layer**
- alerts with cooldown
- desktop notifications
- historical CSV + JSON snapshots + event log

5. **Distribution layer**
- local installer
- uninstall path
- `.deb` and AppImage build scripts

## User Need Satisfaction Matrix

| User Need | Implementation | Status |
|---|---|---|
| Easy install on Linux | `install.sh`, desktop entry, command launcher | Implemented |
| Easy removal | `uninstall.sh` | Implemented |
| Realtime visibility | Dashboard cards + charts + process/storage/system tabs | Implemented |
| Actionable alerts | Thresholds, cooldown, desktop notifications | Implemented |
| Local data ownership | Config + CSV + JSON + logs in user home | Implemented |
| Hardware extensibility | Collector plugin framework | Implemented |
| Outlier detection | Anomaly score + baseline drift engine | Implemented |
| Package distribution | `.deb` and AppImage build scripts | Implemented |

## Feature Set (Professional Scope)

### GUI Platform

- Realtime dashboard cards for CPU, memory, root disk, network, anomaly risk
- Realtime charts for CPU, memory, network in/out, and temperature
- Process explorer with filter by name/user
- Storage table for mounted filesystems
- System details panel (uptime, load, battery, architecture, etc.)
- Hardware Plugins tab for collector status and metrics
- Settings panel for thresholds, refresh rate, history window, and sensitivity

### Intelligence and Alerts

- Per-metric baseline tracking using EWMA
- Rolling variance and sigma-based drift evaluation
- Aggregated anomaly score and risk visualization
- Anomaly-triggered alert channel with cooldown control
- CPU/memory/disk/temp thresholds with cooldown protection

### Data and Outputs

Generated artifacts:

- `~/.config/linux-hardware-monitor/config.json`
- `~/.local/share/linux-hardware-monitor/history.csv`
- `~/.local/share/linux-hardware-monitor/latest_snapshot.json`
- `~/.local/share/linux-hardware-monitor/events.log`

Export fields include:

- raw resource metrics
- anomaly score
- baseline drift

## Result and Output Quality

Expected operational outcomes after deployment:

1. Faster diagnosis of resource pressure events
2. Lower alert fatigue due to cooldown-aware notification logic
3. Better trend awareness through anomaly and drift indicators
4. Clear local audit trail via event logs and timeline exports
5. Better portability through package/build workflows

## Guide-Level Comparison and Pros

### Compared with script-only monitoring

Pros:

- richer UI and trend visibility
- anomaly and drift analytics
- plugin extension path
- native package build scripts

### Compared with terminal-only monitors

Pros:

- desktop-first accessibility for non-terminal users
- structured settings screen and export controls
- integrated alert + insight panes

### Compared with heavier cloud stacks

Pros:

- local-first by default
- lower setup overhead
- transparent file-based outputs and configuration

## Installation and Usage Guide

### Quick Development Run

```bash
chmod +x run_gui.sh
./run_gui.sh
```

### Local Desktop Installation

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

### CLI Mode (Automation)

```bash
chmod +x disk_monitor.sh
./disk_monitor.sh --threshold 90 --loop --interval 300 --log-file /var/log/disk-monitor.log
```

## Package Build Guide

### Build Debian Package

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

## Testing Guide (How To Test This App)

This section is designed for practical verification from developer laptop to production-like usage.

### 1) Static Validation

```bash
python -m py_compile linux_disk_monitor_gui.py collectors/base.py collectors/loader.py collectors/smart_collector.py collectors/nvme_collector.py collectors/gpu_collector.py
bash -n install.sh
bash -n uninstall.sh
bash -n run_gui.sh
bash -n disk_monitor.sh
bash -n scripts/build_deb.sh
bash -n scripts/build_appimage.sh
```

Success criteria:

- no syntax errors returned

### 2) Functional GUI Smoke Test

1. Launch GUI with `./run_gui.sh`
2. Confirm tabs render: Dashboard, Storage, Processes, System, Hardware Plugins, Settings
3. Confirm cards and charts update every second
4. Apply a process filter and verify table updates
5. Save settings and restart app; verify values persist

Success criteria:

- no crashes
- metrics update continuously
- settings persist correctly

### 3) Alert Behavior Test

1. Set low thresholds (for example CPU to 5)
2. Generate load (`yes > /dev/null` in another terminal)
3. Verify alert appears in Alert stream
4. Verify cooldown prevents repeated spam

Success criteria:

- first alert fires
- repeated alerts respect cooldown

### 4) Anomaly and Drift Test

1. Keep system idle for baseline warm-up
2. Trigger a sudden load burst (CPU/network/disk)
3. Observe anomaly risk card and progress bar
4. Confirm anomaly insight appears in insight feed

Success criteria:

- risk score rises under abnormal behavior
- drift value changes meaningfully

### 5) Collector Plugin Test

1. Open Hardware Plugins tab
2. Verify each collector reports availability/status
3. If tools exist (`smartctl`, `nvme`, `nvidia-smi`, or `rocm-smi`), verify metrics appear

Success criteria:

- missing binaries are reported gracefully
- installed collectors return metrics without breaking UI

### 6) Export Test

1. Click Export Snapshot
2. Click Export CSV Now
3. Open data folder from settings
4. Verify files exist and include anomaly fields

Success criteria:

- JSON snapshot created
- CSV history created with expected columns
- events log updates over runtime

### 7) Packaging Test

1. Run `./scripts/build_deb.sh`
2. Install resulting package on test VM
3. Launch from app menu and command line
4. Repeat with AppImage build script where toolchain is available

Success criteria:

- package builds successfully
- app launches from installed artifact

## Current Scope vs Deep-Proprietary Parity

The platform now delivers a professional monitoring experience with strong architecture and practical intelligence.

Future deep-hardware parity opportunities include:

- broader vendor-specific motherboard/VRM sensors
- richer SMART/NVMe health interpretation models
- larger device-profile coverage across distributions and kernels

## License

See `LICENSE`.
