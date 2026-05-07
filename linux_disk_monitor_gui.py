#!/usr/bin/env python3

import platform
import sys
import time
from collections import deque
from datetime import datetime

import psutil
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def format_bytes(value: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(value)
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class StatCard(QFrame):
    def __init__(self, title: str, accent: str):
        super().__init__()
        self.setObjectName("statCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.value = QLabel("--")
        self.value.setObjectName("cardValue")
        self.meta = QLabel("waiting for data")
        self.meta.setObjectName("cardMeta")

        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"background-color: {accent}; border-radius: 2px;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.meta)
        layout.addWidget(accent_bar)


class MonitorWindow(QMainWindow):
    HISTORY_SIZE = 120

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux Hardware Monitor Pro")
        self.resize(1280, 820)

        pg.setConfigOptions(antialias=True)

        self.cpu_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self.ram_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self.net_in_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self.net_out_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)

        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

        self._build_ui()
        self._apply_style()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.refresh()

    def _build_ui(self):
        container = QWidget()
        self.setCentralWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_block = QVBoxLayout()
        heading = QLabel("Linux Hardware Monitor")
        heading.setObjectName("heading")
        subheading = QLabel("Realtime telemetry for CPU, memory, disks, network, and processes")
        subheading.setObjectName("subheading")
        title_block.addWidget(heading)
        title_block.addWidget(subheading)

        self.last_update = QLabel("Last update: --")
        self.last_update.setObjectName("lastUpdate")
        self.last_update.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addLayout(title_block)
        header_layout.addStretch(1)
        header_layout.addWidget(self.last_update)

        root.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        root.addWidget(self.tabs)

        self.dashboard_tab = QWidget()
        self.storage_tab = QWidget()
        self.process_tab = QWidget()
        self.system_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.storage_tab, "Storage")
        self.tabs.addTab(self.process_tab, "Processes")
        self.tabs.addTab(self.system_tab, "System")

        self._build_dashboard_tab()
        self._build_storage_tab()
        self._build_process_tab()
        self._build_system_tab()

    def _build_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        cards = QGridLayout()
        cards.setSpacing(12)

        self.cpu_card = StatCard("CPU Load", "#2dd4bf")
        self.mem_card = StatCard("Memory", "#38bdf8")
        self.disk_card = StatCard("Root Disk", "#f59e0b")
        self.net_card = StatCard("Network", "#a78bfa")

        cards.addWidget(self.cpu_card, 0, 0)
        cards.addWidget(self.mem_card, 0, 1)
        cards.addWidget(self.disk_card, 1, 0)
        cards.addWidget(self.net_card, 1, 1)
        layout.addLayout(cards)

        chart_grid = QGridLayout()
        chart_grid.setSpacing(12)

        self.cpu_plot = self._make_plot("CPU %")
        self.ram_plot = self._make_plot("Memory %")
        self.net_plot = self._make_plot("Network MB/s")

        self.cpu_line = self.cpu_plot.plot(pen=pg.mkPen("#2dd4bf", width=2))
        self.ram_line = self.ram_plot.plot(pen=pg.mkPen("#38bdf8", width=2))
        self.net_in_line = self.net_plot.plot(pen=pg.mkPen("#22c55e", width=2), name="In")
        self.net_out_line = self.net_plot.plot(pen=pg.mkPen("#f97316", width=2), name="Out")

        chart_grid.addWidget(self.cpu_plot, 0, 0)
        chart_grid.addWidget(self.ram_plot, 0, 1)
        chart_grid.addWidget(self.net_plot, 1, 0, 1, 2)

        layout.addLayout(chart_grid)

    def _build_storage_tab(self):
        layout = QVBoxLayout(self.storage_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Mounted Filesystems")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.storage_table = QTableWidget(0, 7)
        self.storage_table.setHorizontalHeaderLabels(
            ["Device", "Mount", "Fstype", "Total", "Used", "Free", "Usage %"]
        )
        self.storage_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.storage_table.verticalHeader().setVisible(False)
        self.storage_table.setAlternatingRowColors(True)
        self.storage_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.storage_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.storage_table)

    def _build_process_tab(self):
        layout = QVBoxLayout(self.process_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Top Processes by CPU")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.proc_table = QTableWidget(0, 6)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "User", "CPU %", "Memory %", "Status"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setAlternatingRowColors(True)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.proc_table)

    def _build_system_tab(self):
        layout = QVBoxLayout(self.system_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.system_title = QLabel("System Overview")
        self.system_title.setObjectName("sectionTitle")
        layout.addWidget(self.system_title)

        self.system_info = QLabel("")
        self.system_info.setObjectName("systemInfo")
        self.system_info.setWordWrap(True)
        self.system_info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.system_info)

    def _make_plot(self, title: str):
        plot = pg.PlotWidget(title=title)
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setYRange(0, 100)
        plot.getPlotItem().hideButtons()
        plot.getPlotItem().setMenuEnabled(False)
        plot.setMouseEnabled(x=False, y=False)
        return plot

    def _apply_style(self):
        font = QFont("Segoe UI", 10)
        QApplication.instance().setFont(font)

        self.setStyleSheet(
            """
            QWidget {
                background: #0f172a;
                color: #e2e8f0;
            }
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111827, stop:1 #1f2937);
                border: 1px solid #334155;
                border-radius: 14px;
            }
            QLabel#heading {
                font-size: 24px;
                font-weight: 700;
                color: #f8fafc;
            }
            QLabel#subheading {
                color: #94a3b8;
                font-size: 12px;
            }
            QLabel#lastUpdate {
                color: #cbd5e1;
                font-size: 12px;
            }
            QTabWidget#mainTabs::pane {
                border: 1px solid #334155;
                border-radius: 12px;
                top: -1px;
                background: #111827;
            }
            QTabBar::tab {
                background: #1f2937;
                color: #cbd5e1;
                border: 1px solid #334155;
                padding: 9px 16px;
                margin-right: 6px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #334155;
                color: #f8fafc;
            }
            QFrame#statCard {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel#cardTitle {
                color: #94a3b8;
                font-size: 12px;
            }
            QLabel#cardValue {
                color: #f8fafc;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#cardMeta {
                color: #cbd5e1;
                font-size: 11px;
            }
            QLabel#sectionTitle {
                font-size: 17px;
                font-weight: 700;
                color: #f8fafc;
            }
            QTableWidget {
                background: #0b1220;
                border: 1px solid #334155;
                border-radius: 10px;
                gridline-color: #1e293b;
                alternate-background-color: #111827;
            }
            QHeaderView::section {
                background: #1e293b;
                color: #f1f5f9;
                padding: 8px;
                border: none;
                border-right: 1px solid #334155;
                font-weight: 600;
            }
            QLabel#systemInfo {
                background: #0b1220;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 14px;
                color: #cbd5e1;
                line-height: 1.5;
            }
            """
        )

    def refresh(self):
        now = time.time()
        elapsed = max(now - self.prev_time, 0.001)
        self.prev_time = now

        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        root_disk = None
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint == "/":
                try:
                    root_disk = psutil.disk_usage(part.mountpoint)
                except PermissionError:
                    root_disk = None
                break

        net = psutil.net_io_counters()
        in_rate = max((net.bytes_recv - self.prev_net.bytes_recv) / elapsed, 0.0)
        out_rate = max((net.bytes_sent - self.prev_net.bytes_sent) / elapsed, 0.0)
        self.prev_net = net

        self.cpu_history.append(cpu_percent)
        self.ram_history.append(mem.percent)
        self.net_in_history.append(in_rate / 1024.0 / 1024.0)
        self.net_out_history.append(out_rate / 1024.0 / 1024.0)

        self.cpu_card.value.setText(f"{cpu_percent:.1f}%")
        self.cpu_card.meta.setText(f"{psutil.cpu_count(logical=True)} logical cores")

        self.mem_card.value.setText(f"{mem.percent:.1f}%")
        self.mem_card.meta.setText(f"{format_bytes(mem.used)} used / {format_bytes(mem.total)} total")

        if root_disk:
            self.disk_card.value.setText(f"{root_disk.percent:.1f}%")
            self.disk_card.meta.setText(
                f"{format_bytes(root_disk.used)} used / {format_bytes(root_disk.total)} total"
            )
        else:
            self.disk_card.value.setText("N/A")
            self.disk_card.meta.setText("Could not read root filesystem")

        self.net_card.value.setText(f"{self.net_in_history[-1]:.2f}/{self.net_out_history[-1]:.2f} MB/s")
        self.net_card.meta.setText(
            f"in: {format_bytes(net.bytes_recv)} total, out: {format_bytes(net.bytes_sent)} total"
        )

        self.cpu_line.setData(list(self.cpu_history))
        self.ram_line.setData(list(self.ram_history))
        self.net_in_line.setData(list(self.net_in_history))
        self.net_out_line.setData(list(self.net_out_history))

        max_net = max(max(self.net_in_history), max(self.net_out_history), 1.0)
        self.net_plot.setYRange(0, max_net * 1.2)

        self._update_storage_table()
        self._update_process_table()
        self._update_system_info(cpu_percent, mem)

        self.last_update.setText(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _update_storage_table(self):
        rows = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue

            rows.append(
                (
                    part.device,
                    part.mountpoint,
                    part.fstype,
                    format_bytes(usage.total),
                    format_bytes(usage.used),
                    format_bytes(usage.free),
                    f"{usage.percent:.1f}%",
                )
            )

        self.storage_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(value)
                if c == 6:
                    item.setTextAlignment(Qt.AlignCenter)
                self.storage_table.setItem(r, c, item)

    def _update_process_table(self):
        processes = []
        for proc in psutil.process_iter(attrs=["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
            try:
                info = proc.info
                processes.append(
                    (
                        str(info.get("pid", "")),
                        str(info.get("name", "")),
                        str(info.get("username", "")),
                        f"{float(info.get('cpu_percent', 0.0)):.1f}",
                        f"{float(info.get('memory_percent', 0.0)):.1f}",
                        str(info.get("status", "")),
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(key=lambda x: float(x[3]), reverse=True)
        top = processes[:20]

        self.proc_table.setRowCount(len(top))
        for r, row in enumerate(top):
            for c, value in enumerate(row):
                item = QTableWidgetItem(value)
                if c in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.proc_table.setItem(r, c, item)

    def _update_system_info(self, cpu_percent: float, mem):
        uname = platform.uname()
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600.0

        load_avg = "N/A"
        if hasattr(psutil, "getloadavg"):
            la = psutil.getloadavg()
            load_avg = f"{la[0]:.2f}, {la[1]:.2f}, {la[2]:.2f}"

        temps_text = "N/A"
        temps = psutil.sensors_temperatures(fahrenheit=False)
        if temps:
            snippets = []
            for chip, entries in temps.items():
                for entry in entries[:2]:
                    label = entry.label or chip
                    if entry.current is not None:
                        snippets.append(f"{label}: {entry.current:.1f} C")
            if snippets:
                temps_text = " | ".join(snippets[:4])

        battery_text = "N/A"
        battery = psutil.sensors_battery()
        if battery is not None:
            if battery.power_plugged:
                battery_text = f"{battery.percent:.0f}% (charging)"
            else:
                battery_text = f"{battery.percent:.0f}%"

        lines = [
            f"Hostname: {uname.node}",
            f"OS: {uname.system} {uname.release} ({uname.version})",
            f"Kernel/Arch: {uname.machine}",
            f"CPU: {uname.processor or 'Unknown'}",
            f"CPU usage: {cpu_percent:.1f}%",
            f"Load average (1/5/15): {load_avg}",
            f"Memory: {format_bytes(mem.used)} / {format_bytes(mem.total)} ({mem.percent:.1f}%)",
            f"Uptime: {uptime_hours:.1f} hours",
            f"Temperature: {temps_text}",
            f"Battery: {battery_text}",
        ]

        self.system_info.setText("\n".join(lines))


def main():
    app = QApplication(sys.argv)
    window = MonitorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()