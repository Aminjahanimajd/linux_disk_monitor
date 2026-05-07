from __future__ import annotations

import shutil
import subprocess

from .base import CollectorResult, HardwareCollector


class NvidiaSmiCollector(HardwareCollector):
    name = "nvidia-smi"

    def collect(self) -> CollectorResult:
        if shutil.which("nvidia-smi") is None:
            return CollectorResult(self.name, False, {}, "nvidia-smi not installed")

        try:
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            if not rows:
                return CollectorResult(self.name, True, {"gpus": "0"}, "ok")

            first = [item.strip() for item in rows[0].split(",")]
            metrics = {
                "gpus": str(len(rows)),
                "gpu0_name": first[0],
                "gpu0_temp_c": first[1],
                "gpu0_util_percent": first[2],
                "gpu0_mem_used_mb": first[3],
                "gpu0_mem_total_mb": first[4],
            }
            return CollectorResult(self.name, True, metrics, "ok")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CollectorResult(self.name, False, {}, f"error: {exc}")


class AmdRocmCollector(HardwareCollector):
    name = "rocm-smi"

    def collect(self) -> CollectorResult:
        if shutil.which("rocm-smi") is None:
            return CollectorResult(self.name, False, {}, "rocm-smi not installed")

        try:
            proc = subprocess.run(
                ["rocm-smi", "--showtemp", "--showuse"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            gpu_lines = [line for line in lines if "GPU" in line]
            metrics = {
                "gpu_lines": str(len(gpu_lines)),
            }
            return CollectorResult(self.name, True, metrics, "ok")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CollectorResult(self.name, False, {}, f"error: {exc}")
