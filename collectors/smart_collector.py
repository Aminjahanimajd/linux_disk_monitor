from __future__ import annotations

import shutil
import subprocess

from .base import CollectorResult, HardwareCollector


class SmartCollector(HardwareCollector):
    name = "smartctl"

    def collect(self) -> CollectorResult:
        if shutil.which("smartctl") is None:
            return CollectorResult(self.name, False, {}, "smartctl not installed")

        try:
            proc = subprocess.run(
                ["smartctl", "--scan-open"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            metrics = {
                "disks_detected": str(len(lines)),
            }
            if lines:
                metrics["first_device"] = lines[0].split(" ")[0]
            status = "ok"
            return CollectorResult(self.name, True, metrics, status)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CollectorResult(self.name, False, {}, f"error: {exc}")
