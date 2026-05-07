# Linux Disk Monitor

A production-oriented Linux monitoring project with two operational modes:

- a hardened Bash monitor for automation and alerting
- a desktop GUI application for realtime hardware and system telemetry

## Executive Summary

Disk-full incidents are one of the most common and costly operational failures in Linux environments. Services can stop writing logs, databases can fail transactions, and deployments can break without warning.

This project provides a practical answer: a dependency-light monitoring script for server-side reliability and a modern GUI dashboard for interactive observability.

It is designed for administrators, DevOps engineers, and small teams that need reliable disk monitoring without deploying a full monitoring stack.

## Storyline: From Reactive Fixes to Proactive Operations

### The problem

Many systems rely on manual checks (`df -h`) or ad-hoc cron jobs with no standards for:

- alert thresholds
- log consistency
- filesystem filtering
- duplicate alert suppression
- integration with external notification tools

The result is usually one of two extremes:

- no alert until outage
- too many alerts, causing teams to ignore notifications

### The goal

Build a professional Linux monitor that is:

- easy to run anywhere
- easy to integrate with existing tooling
- stable under repeated execution
- clear in logs and behavior
- visually smooth and operationally useful for desktop users

### The solution

`disk_monitor.sh` provides structured CLI monitoring with validation, logging, cooldown-aware alerts, and customizable filesystem scope.

`linux_disk_monitor_gui.py` adds a polished desktop experience with realtime cards, charts, storage visibility, process ranking, and system diagnostics.

## Key Features

- Configurable threshold-based alerts (`--threshold`)
- One-shot mode and continuous loop mode (`--loop`, `--interval`)
- Alert cooldown per mountpoint to reduce noise (`--cooldown`, `--state-file`)
- Built-in logging to stdout and optional file (`--log-file`)
- Optional alert command hook for integrations (`--alert-cmd`)
- Include/exclude filesystem type filters (`--include-types`, `--exclude-types`)
- Dry-run mode for safe validation in production (`--dry-run`)
- Strict input and dependency validation

## Desktop GUI Features

- Realtime dashboard cards for CPU, memory, root disk, and network throughput
- Smooth charting for CPU, memory, and inbound/outbound network rates
- Storage table for mounted filesystems with usage breakdown
- Process table showing top CPU consumers
- System overview panel with uptime, load average, temperatures, and battery (where available)
- Professional dark UI with modern spacing, contrast, and readable hierarchy

## HWiNFO-Style Capability Comparison

### What this project already delivers

- Realtime performance telemetry
- Process and storage visibility
- Temperature support where Linux sensors are available
- Lightweight footprint and transparent open-source behavior

### What full HWiNFO parity would additionally require

- Deep vendor-specific sensor decoding (chipset, VRM, SMART/NVMe internals)
- Motherboard and bus-level probing across many hardware vendors
- Historical logging engine with custom graphs and alerts per sensor
- Plugin ecosystem, report export pipelines, and broad proprietary hardware profiles

This project is now a professional Linux monitor with strong core capabilities. Full HWiNFO-level parity is feasible as a roadmap, but it is a larger multi-phase product effort rather than a single script iteration.

## Architecture and Behavior

1. Parse CLI arguments and validate runtime inputs.
2. Read mounted filesystems via `df -P -T`.
3. Filter filesystems by include/exclude rules.
4. Compare usage against threshold.
5. Trigger alert command only when cooldown allows it.
6. Persist latest alert timestamp per mountpoint in state file.
7. Emit scan summary logs.

## Result Comparison

### Before (basic/manual approach)

- Manual checks are inconsistent and human-dependent.
- Cron-based scripts often produce repeated alerts every run.
- Limited auditability due to weak or no logging.
- Hard to integrate with chat/email/pager workflows.

### After (this project)

- Standardized, repeatable checks with clear CLI contract.
- Controlled alert frequency with per-mount cooldown.
- Structured logs for troubleshooting and audits.
- Integration-ready via alert command environment variables.
- Safer rollout with dry-run mode.

## Requirements

- Linux host
- Bash
- Core utilities: `df`, `awk`, `date`, `mkdir`
- Python 3.10+
- Python packages in `requirements.txt`

## Quick Start

```bash
chmod +x disk_monitor.sh

# One-time scan with 85% threshold (default)
./disk_monitor.sh

# One-time scan with custom threshold
./disk_monitor.sh --threshold 90
```

### Launch GUI App

```bash
chmod +x run_gui.sh
./run_gui.sh
```

Or manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 linux_disk_monitor_gui.py
```

## Usage

```bash
./disk_monitor.sh [options]
```

### Options

- `-t, --threshold <percent>`: Alert threshold percentage (default: `85`)
- `-i, --interval <seconds>`: Check interval in loop mode (default: `300`)
- `-l, --loop`: Run continuously
- `--log-file <path>`: Append logs to a file
- `--alert-cmd <command>`: Command to run on alert
- `--state-file <path>`: Cooldown state file path (default: `/tmp/linux_disk_monitor.state`)
- `--cooldown <seconds>`: Minimum seconds between repeated alerts per mount (default: `1800`)
- `--include-types <list>`: Comma-separated filesystem types to include
- `--exclude-types <list>`: Comma-separated filesystem types to exclude (default: `tmpfs,devtmpfs,squashfs,overlay`)
- `--dry-run`: Simulate alerts without executing alert command
- `-h, --help`: Show help
- `-v, --version`: Show version

## Integration Examples

### 1) Log to file and scan every 5 minutes

```bash
./disk_monitor.sh --loop --interval 300 --log-file /var/log/disk-monitor.log
```

### 2) Send alerts to a webhook (example with curl)

```bash
./disk_monitor.sh \
	--threshold 88 \
	--alert-cmd 'curl -sS -X POST https://example.com/hook \
		-H "Content-Type: application/json" \
		-d "{\"mount\":\"$DISK_MONITOR_MOUNT\",\"usage\":$DISK_MONITOR_USAGE,\"threshold\":$DISK_MONITOR_THRESHOLD}"'
```

### 3) Dry-run validation before enabling real alerts

```bash
./disk_monitor.sh --threshold 80 --dry-run
```

### 4) Watch only selected filesystem types

```bash
./disk_monitor.sh --include-types ext4,xfs --exclude-types ''
```

## Alert Command Contract

When `--alert-cmd` is provided, these environment variables are exported:

- `DISK_MONITOR_MOUNT`
- `DISK_MONITOR_USAGE`
- `DISK_MONITOR_THRESHOLD`
- `DISK_MONITOR_FS`
- `DISK_MONITOR_AVAILABLE`
- `DISK_MONITOR_USED`
- `DISK_MONITOR_TOTAL`

This allows easy integration with email, Slack, Teams, PagerDuty, Opsgenie, and custom automation.

## Operational Deployment

### Cron (one-shot every 5 minutes)

```cron
*/5 * * * * /opt/linux_disk_monitor/disk_monitor.sh --threshold 85 --log-file /var/log/disk-monitor.log
```

### Systemd (continuous mode)

Create `/etc/systemd/system/linux-disk-monitor.service`:

```ini
[Unit]
Description=Linux Disk Monitor
After=network.target

[Service]
Type=simple
ExecStart=/opt/linux_disk_monitor/disk_monitor.sh --loop --interval 300 --threshold 85 --log-file /var/log/disk-monitor.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now linux-disk-monitor.service
```

## Reliability and Safety Notes

- Cooldown is tracked per mountpoint to avoid repeated alert bursts.
- State file is writable and can be relocated with `--state-file`.
- `--dry-run` is recommended during initial rollout.
- Excluding ephemeral filesystems by default reduces noisy alerts.

## Roadmap

- Native email notifier option
- JSON log output mode
- Unit tests for parser and filtering logic
- Optional Prometheus textfile exporter mode
- Per-sensor alert rule builder in GUI
- Historical timeline and exportable report generation
- Extended hardware probe adapters for advanced motherboard and NVMe stats

## License

This project is licensed under the terms in [LICENSE](LICENSE).
