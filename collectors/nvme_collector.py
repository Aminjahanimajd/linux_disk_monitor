from __future__ import annotations

import shutil
import subprocess

from .base import CollectorResult, HardwareCollector


class NvmeCollector(HardwareCollector):
    name = "nvme"

    def collect(self) -> CollectorResult:
        if shutil.which("nvme") is None:
            return CollectorResult(self.name, False, {}, "nvme-cli not installed")

        try:
            proc = subprocess.run(
                ["nvme", "list"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            # Skip table header lines.
            device_lines = [line for line in proc.stdout.splitlines() if line.startswith("/dev/nvme")]
            metrics = {
                "nvme_devices": str(len(device_lines)),
            }
            if device_lines:
                metrics["first_nvme"] = device_lines[0].split()[0]
            return CollectorResult(self.name, True, metrics, "ok")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CollectorResult(self.name, False, {}, f"error: {exc}")
