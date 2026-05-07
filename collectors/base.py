from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class CollectorResult:
    name: str
    available: bool
    metrics: Dict[str, str]
    status: str


class HardwareCollector:
    name = "base"

    def collect(self) -> CollectorResult:
        raise NotImplementedError
