# Linux Disk Monitor

A lightweight, production-oriented Bash utility for proactive disk capacity monitoring on Linux hosts.

## Executive Summary

Disk-full incidents are one of the most common and costly operational failures in Linux environments. Services can stop writing logs, databases can fail transactions, and deployments can break without warning.

This project provides a practical answer: a dependency-light monitoring script that continuously checks mounted filesystems, alerts only when needed, and avoids notification storms with cooldown control.

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

Build a small but professional monitor that is:

- easy to run anywhere
- easy to integrate with existing tooling
- stable under repeated execution
- clear in logs and behavior

### The solution

`disk_monitor.sh` introduces a structured CLI with validation, logging, cooldown-aware alerts, and customizable filesystem scope.

## Key Features

- Configurable threshold-based alerts (`--threshold`)
- One-shot mode and continuous loop mode (`--loop`, `--interval`)
- Alert cooldown per mountpoint to reduce noise (`--cooldown`, `--state-file`)
- Built-in logging to stdout and optional file (`--log-file`)
- Optional alert command hook for integrations (`--alert-cmd`)
- Include/exclude filesystem type filters (`--include-types`, `--exclude-types`)
- Dry-run mode for safe validation in production (`--dry-run`)
- Strict input and dependency validation

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

## Quick Start

```bash
chmod +x disk_monitor.sh

# One-time scan with 85% threshold (default)
./disk_monitor.sh

# One-time scan with custom threshold
./disk_monitor.sh --threshold 90
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

## License

This project is licensed under the terms in [LICENSE](LICENSE).
