from __future__ import annotations

from typing import List

from .base import CollectorResult, HardwareCollector
from .gpu_collector import AmdRocmCollector, NvidiaSmiCollector
from .nvme_collector import NvmeCollector
from .smart_collector import SmartCollector


class CollectorManager:
    def __init__(self) -> None:
        self.collectors: List[HardwareCollector] = [
            SmartCollector(),
            NvmeCollector(),
            NvidiaSmiCollector(),
            AmdRocmCollector(),
        ]

    def collect_all(self) -> List[CollectorResult]:
        results: List[CollectorResult] = []
        for collector in self.collectors:
            results.append(collector.collect())
        return results
