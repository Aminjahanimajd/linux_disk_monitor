#!/usr/bin/env bash

set -euo pipefail

VERSION="1.0.0"

# Defaults
THRESHOLD=85
INTERVAL=300
LOOP_MODE=0
LOG_FILE=""
ALERT_COMMAND=""
STATE_FILE="/tmp/linux_disk_monitor.state"
COOLDOWN_SECONDS=1800
INCLUDE_TYPES=""
EXCLUDE_TYPES="tmpfs,devtmpfs,squashfs,overlay"
DRY_RUN=0

usage() {
	cat <<'EOF'
Linux Disk Monitor

Usage:
	./disk_monitor.sh [options]

Options:
	-t, --threshold <percent>    Alert threshold percentage (default: 85)
	-i, --interval <seconds>     Check interval in loop mode (default: 300)
	-l, --loop                   Run continuously
	--log-file <path>            Write logs to file in addition to stdout
	--alert-cmd <command>        Command to run on alert (env vars passed)
	--state-file <path>          Path to cooldown state file (default: /tmp/linux_disk_monitor.state)
	--cooldown <seconds>         Minimum time between repeated alerts per mount (default: 1800)
	--include-types <list>       Comma-separated fs types to include (e.g. ext4,xfs)
	--exclude-types <list>       Comma-separated fs types to exclude (default: tmpfs,devtmpfs,squashfs,overlay)
	--dry-run                    Simulate alerts without running alert command
	-h, --help                   Show this help
	-v, --version                Show script version

Alert command environment variables:
	DISK_MONITOR_MOUNT
	DISK_MONITOR_USAGE
	DISK_MONITOR_THRESHOLD
	DISK_MONITOR_FS
	DISK_MONITOR_AVAILABLE
	DISK_MONITOR_USED
	DISK_MONITOR_TOTAL
EOF
}

log() {
	local level="$1"
	local message="$2"
	local ts
	ts="$(date '+%Y-%m-%d %H:%M:%S')"
	local line="${ts} [${level}] ${message}"

	echo "$line"
	if [[ -n "$LOG_FILE" ]]; then
		printf '%s\n' "$line" >>"$LOG_FILE"
	fi
}

error_exit() {
	log "ERROR" "$1"
	exit 1
}

validate_dependencies() {
	command -v df >/dev/null 2>&1 || error_exit "Missing required command: df"
	command -v awk >/dev/null 2>&1 || error_exit "Missing required command: awk"
	command -v date >/dev/null 2>&1 || error_exit "Missing required command: date"
	command -v mkdir >/dev/null 2>&1 || error_exit "Missing required command: mkdir"
}

validate_inputs() {
	[[ "$THRESHOLD" =~ ^[0-9]+$ ]] || error_exit "Threshold must be an integer."
	(( THRESHOLD >= 1 && THRESHOLD <= 100 )) || error_exit "Threshold must be between 1 and 100."

	[[ "$INTERVAL" =~ ^[0-9]+$ ]] || error_exit "Interval must be an integer."
	(( INTERVAL >= 1 )) || error_exit "Interval must be at least 1 second."

	[[ "$COOLDOWN_SECONDS" =~ ^[0-9]+$ ]] || error_exit "Cooldown must be an integer."
	(( COOLDOWN_SECONDS >= 0 )) || error_exit "Cooldown must be >= 0."

	if [[ -n "$LOG_FILE" ]]; then
		local log_dir
		log_dir="$(dirname "$LOG_FILE")"
		mkdir -p "$log_dir"
		: >>"$LOG_FILE" || error_exit "Cannot write to log file: $LOG_FILE"
	fi

	local state_dir
	state_dir="$(dirname "$STATE_FILE")"
	mkdir -p "$state_dir" || error_exit "Cannot create state directory: $state_dir"
	: >>"$STATE_FILE" || error_exit "Cannot write to state file: $STATE_FILE"
}

csv_contains() {
	local csv="$1"
	local value="$2"
	[[ ",$csv," == *",$value,"* ]]
}

should_check_fs() {
	local fs_type="$1"

	if [[ -n "$INCLUDE_TYPES" ]] && ! csv_contains "$INCLUDE_TYPES" "$fs_type"; then
		return 1
	fi

	if [[ -n "$EXCLUDE_TYPES" ]] && csv_contains "$EXCLUDE_TYPES" "$fs_type"; then
		return 1
	fi

	return 0
}

cooldown_allows_alert() {
	local mountpoint="$1"
	local now
	now="$(date +%s)"

	local last_ts=""
	if [[ -s "$STATE_FILE" ]]; then
		last_ts="$(awk -F'|' -v m="$mountpoint" '$1 == m { print $2 }' "$STATE_FILE" | tail -n 1)"
	fi

	if [[ -z "$last_ts" ]]; then
		return 0
	fi

	if (( now - last_ts >= COOLDOWN_SECONDS )); then
		return 0
	fi

	return 1
}

update_cooldown_state() {
	local mountpoint="$1"
	local now
	now="$(date +%s)"

	local tmp_file
	tmp_file="${STATE_FILE}.tmp"

	awk -F'|' -v m="$mountpoint" '$1 != m' "$STATE_FILE" >"$tmp_file" 2>/dev/null || true
	printf '%s|%s\n' "$mountpoint" "$now" >>"$tmp_file"
	mv "$tmp_file" "$STATE_FILE"
}

run_alert() {
	local fs="$1"
	local mountpoint="$2"
	local used_pct="$3"
	local used="$4"
	local avail="$5"
	local total="$6"

	local message
	message="Disk usage alert: mount=$mountpoint usage=${used_pct}%% threshold=${THRESHOLD}%% fs=$fs used=$used avail=$avail total=$total"
	log "WARN" "$message"

	if (( DRY_RUN == 1 )); then
		log "INFO" "Dry-run enabled: alert command was not executed."
		return 0
	fi

	if [[ -n "$ALERT_COMMAND" ]]; then
		DISK_MONITOR_MOUNT="$mountpoint" \
		DISK_MONITOR_USAGE="$used_pct" \
		DISK_MONITOR_THRESHOLD="$THRESHOLD" \
		DISK_MONITOR_FS="$fs" \
		DISK_MONITOR_AVAILABLE="$avail" \
		DISK_MONITOR_USED="$used" \
		DISK_MONITOR_TOTAL="$total" \
			bash -c "$ALERT_COMMAND"
		log "INFO" "Alert command executed for mount $mountpoint"
	fi
}

check_disks_once() {
	local alert_count=0
	local checked_count=0

	while IFS='|' read -r fs fstype size used avail usep mountpoint; do
		[[ -z "$mountpoint" ]] && continue

		if ! should_check_fs "$fstype"; then
			continue
		fi

		checked_count=$((checked_count + 1))
		local used_pct
		used_pct="${usep%%%}"

		if (( used_pct >= THRESHOLD )); then
			if cooldown_allows_alert "$mountpoint"; then
				run_alert "$fs" "$mountpoint" "$used_pct" "$used" "$avail" "$size"
				update_cooldown_state "$mountpoint"
				alert_count=$((alert_count + 1))
			else
				log "INFO" "Cooldown active for mount $mountpoint (usage=${used_pct}%)."
			fi
		else
			log "INFO" "OK mount=$mountpoint usage=${used_pct}% threshold=${THRESHOLD}%"
		fi
	done < <(df -P -T | awk 'NR>1 {printf "%s|%s|%s|%s|%s|%s|%s\n", $1,$2,$3,$4,$5,$6,$7}')

	log "INFO" "Scan complete. checked=$checked_count alerts=$alert_count"
}

main_loop() {
	log "INFO" "Starting linux_disk_monitor v$VERSION (threshold=${THRESHOLD}%, interval=${INTERVAL}s, cooldown=${COOLDOWN_SECONDS}s)"
	while true; do
		check_disks_once
		sleep "$INTERVAL"
	done
}

parse_args() {
	while (( "$#" > 0 )); do
		case "$1" in
			-t|--threshold)
				THRESHOLD="$2"
				shift 2
				;;
			-i|--interval)
				INTERVAL="$2"
				shift 2
				;;
			-l|--loop)
				LOOP_MODE=1
				shift
				;;
			--log-file)
				LOG_FILE="$2"
				shift 2
				;;
			--alert-cmd)
				ALERT_COMMAND="$2"
				shift 2
				;;
			--state-file)
				STATE_FILE="$2"
				shift 2
				;;
			--cooldown)
				COOLDOWN_SECONDS="$2"
				shift 2
				;;
			--include-types)
				INCLUDE_TYPES="$2"
				shift 2
				;;
			--exclude-types)
				EXCLUDE_TYPES="$2"
				shift 2
				;;
			--dry-run)
				DRY_RUN=1
				shift
				;;
			-h|--help)
				usage
				exit 0
				;;
			-v|--version)
				echo "$VERSION"
				exit 0
				;;
			*)
				error_exit "Unknown argument: $1"
				;;
		esac
	done
}

parse_args "$@"
validate_dependencies
validate_inputs

if (( LOOP_MODE == 1 )); then
	main_loop
else
	check_disks_once
fi
