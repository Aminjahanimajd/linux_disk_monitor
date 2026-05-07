#!/usr/bin/env python3

import csv
import json
import platform
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "linux-hardware-monitor"
APP_TITLE = "Linux Hardware Monitor Pro"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"
CSV_HISTORY_FILE = DATA_DIR / "history.csv"
JSON_SNAPSHOT_FILE = DATA_DIR / "latest_snapshot.json"
EVENT_LOG_FILE = DATA_DIR / "events.log"


DEFAULT_CONFIG: Dict[str, object] = {
    "refresh_ms": 1000,
    "history_points": 180,
    "theme": "aurora",
    "auto_export_csv": True,
    "desktop_notifications": True,
    "alert_cpu": 90,
    "alert_memory": 90,
    "alert_disk": 90,
    "alert_temp": 80,
    "alert_cooldown_sec": 120,
    "process_filter": "",
}


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, object]:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    try:
        content = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)

    merged = dict(DEFAULT_CONFIG)
    merged.update(content)
    return merged


def save_config(cfg: Dict[str, object]) -> None:
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def format_bytes(value: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(value)
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


@dataclass
class Sample:
    timestamp: str
    cpu: float
    memory: float
    disk_root: float
    net_in_mbs: float
    net_out_mbs: float
    load_1: float
    temp_c: Optional[float]


class StatCard(QFrame):
    def __init__(self, title: str, accent: str):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(4)

        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")

        self.value = QLabel("--")
        self.value.setObjectName("cardValue")

        self.meta = QLabel("-")
        self.meta.setObjectName("cardMeta")

        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"background: {accent}; border-radius: 2px;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.meta)
        layout.addWidget(accent_bar)


class MonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.theme = str(self.config["theme"])

        self.history_points = int(self.config["history_points"])
        self.cpu_history = deque([0.0] * self.history_points, maxlen=self.history_points)
        self.mem_history = deque([0.0] * self.history_points, maxlen=self.history_points)
        self.net_in_history = deque([0.0] * self.history_points, maxlen=self.history_points)
        self.net_out_history = deque([0.0] * self.history_points, maxlen=self.history_points)
        self.temp_history = deque([0.0] * self.history_points, maxlen=self.history_points)

        self.snapshots: List[Sample] = []
        self.last_alert_at: Dict[str, float] = {}

        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

        self.setWindowTitle(APP_TITLE)
        self.resize(1360, 900)

        pg.setConfigOptions(antialias=True)

        self._build_ui()
        self._apply_style()
        self._load_config_to_widgets()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(int(self.config["refresh_ms"]))

        self.refresh()

    def _build_ui(self) -> None:
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_col = QVBoxLayout()
        title = QLabel("Linux Hardware Monitor")
        title.setObjectName("heading")
        subtitle = QLabel("Realtime visibility, actionable alerts, exportable history")
        subtitle.setObjectName("subheading")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.last_update = QLabel("Last update: --")
        self.last_update.setObjectName("lastUpdate")

        self.export_btn = QPushButton("Export Snapshot")
        self.export_btn.clicked.connect(self.export_snapshot)

        header_layout.addLayout(title_col)
        header_layout.addStretch(1)
        header_layout.addWidget(self.last_update)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.export_btn)

        root_layout.addWidget(header)

        self.tabs = QTabWidget()
        self.dashboard_tab = QWidget()
        self.storage_tab = QWidget()
        self.process_tab = QWidget()
        self.system_tab = QWidget()
        self.settings_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.storage_tab, "Storage")
        self.tabs.addTab(self.process_tab, "Processes")
        self.tabs.addTab(self.system_tab, "System")
        self.tabs.addTab(self.settings_tab, "Settings & Alerts")

        root_layout.addWidget(self.tabs)

        self._build_dashboard_tab()
        self._build_storage_tab()
        self._build_process_tab()
        self._build_system_tab()
        self._build_settings_tab()

    def _build_dashboard_tab(self) -> None:
        layout = QVBoxLayout(self.dashboard_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        cards = QGridLayout()
        cards.setSpacing(10)

        self.cpu_card = StatCard("CPU", "#00d1b2")
        self.mem_card = StatCard("Memory", "#4cc9f0")
        self.disk_card = StatCard("Disk Root", "#ff9f1c")
        self.net_card = StatCard("Network", "#f15bb5")

        cards.addWidget(self.cpu_card, 0, 0)
        cards.addWidget(self.mem_card, 0, 1)
        cards.addWidget(self.disk_card, 1, 0)
        cards.addWidget(self.net_card, 1, 1)

        layout.addLayout(cards)

        charts = QGridLayout()
        charts.setSpacing(10)

        self.cpu_plot = self._plot("CPU %", y_max=100)
        self.mem_plot = self._plot("Memory %", y_max=100)
        self.net_plot = self._plot("Network MB/s", y_max=10)
        self.temp_plot = self._plot("Temperature C", y_max=100)

        self.cpu_line = self.cpu_plot.plot(pen=pg.mkPen("#00d1b2", width=2))
        self.mem_line = self.mem_plot.plot(pen=pg.mkPen("#4cc9f0", width=2))
        self.net_in_line = self.net_plot.plot(pen=pg.mkPen("#80ed99", width=2))
        self.net_out_line = self.net_plot.plot(pen=pg.mkPen("#ff6b6b", width=2))
        self.temp_line = self.temp_plot.plot(pen=pg.mkPen("#ffd166", width=2))

        charts.addWidget(self.cpu_plot, 0, 0)
        charts.addWidget(self.mem_plot, 0, 1)
        charts.addWidget(self.net_plot, 1, 0)
        charts.addWidget(self.temp_plot, 1, 1)

        layout.addLayout(charts)

        splitter = QSplitter(Qt.Horizontal)
        self.alert_log = QTextEdit()
        self.alert_log.setReadOnly(True)
        self.alert_log.setObjectName("logPane")

        self.insight_log = QTextEdit()
        self.insight_log.setReadOnly(True)
        self.insight_log.setObjectName("logPane")

        splitter.addWidget(self.alert_log)
        splitter.addWidget(self.insight_log)
        splitter.setSizes([560, 560])

        layout.addWidget(splitter)

    def _build_storage_tab(self) -> None:
        layout = QVBoxLayout(self.storage_tab)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Mounted Filesystems")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.storage_table = QTableWidget(0, 7)
        self.storage_table.setHorizontalHeaderLabels(["Device", "Mount", "Type", "Total", "Used", "Free", "Usage %"])
        self.storage_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.storage_table.verticalHeader().setVisible(False)
        self.storage_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.storage_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.storage_table.setAlternatingRowColors(True)

        layout.addWidget(self.storage_table)

    def _build_process_tab(self) -> None:
        layout = QVBoxLayout(self.process_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top_bar = QHBoxLayout()
        title = QLabel("Top Processes")
        title.setObjectName("sectionTitle")
        top_bar.addWidget(title)

        top_bar.addStretch(1)

        self.process_search = QLineEdit()
        self.process_search.setPlaceholderText("Filter by process name or user")
        self.process_search.textChanged.connect(self._on_process_filter_changed)
        self.process_search.setFixedWidth(320)
        top_bar.addWidget(self.process_search)

        layout.addLayout(top_bar)

        self.proc_table = QTableWidget(0, 7)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "User", "CPU %", "MEM %", "Threads", "Status"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.proc_table.setAlternatingRowColors(True)

        layout.addWidget(self.proc_table)

    def _build_system_tab(self) -> None:
        layout = QVBoxLayout(self.system_tab)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("System Overview")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.system_info = QLabel("")
        self.system_info.setWordWrap(True)
        self.system_info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.system_info.setObjectName("systemInfo")

        layout.addWidget(self.system_info)

    def _build_settings_tab(self) -> None:
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        title = QLabel("Configuration and Alert Rules")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(250, 10000)
        self.refresh_spin.setSingleStep(250)

        self.history_spin = QSpinBox()
        self.history_spin.setRange(60, 900)

        self.cpu_alert_spin = QSpinBox()
        self.cpu_alert_spin.setRange(1, 100)

        self.mem_alert_spin = QSpinBox()
        self.mem_alert_spin.setRange(1, 100)

        self.disk_alert_spin = QSpinBox()
        self.disk_alert_spin.setRange(1, 100)

        self.temp_alert_spin = QSpinBox()
        self.temp_alert_spin.setRange(1, 120)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(10, 3600)

        self.auto_export_check = QCheckBox("Auto-export CSV history")
        self.notify_check = QCheckBox("Desktop notifications")

        grid.addWidget(QLabel("Refresh interval (ms)"), 0, 0)
        grid.addWidget(self.refresh_spin, 0, 1)

        grid.addWidget(QLabel("History points"), 1, 0)
        grid.addWidget(self.history_spin, 1, 1)

        grid.addWidget(QLabel("CPU alert threshold (%)"), 2, 0)
        grid.addWidget(self.cpu_alert_spin, 2, 1)

        grid.addWidget(QLabel("Memory alert threshold (%)"), 3, 0)
        grid.addWidget(self.mem_alert_spin, 3, 1)

        grid.addWidget(QLabel("Disk alert threshold (%)"), 4, 0)
        grid.addWidget(self.disk_alert_spin, 4, 1)

        grid.addWidget(QLabel("Temperature alert threshold (C)"), 5, 0)
        grid.addWidget(self.temp_alert_spin, 5, 1)

        grid.addWidget(QLabel("Alert cooldown (sec)"), 6, 0)
        grid.addWidget(self.cooldown_spin, 6, 1)

        grid.addWidget(self.auto_export_check, 7, 0, 1, 2)
        grid.addWidget(self.notify_check, 8, 0, 1, 2)

        layout.addLayout(grid)

        buttons = QHBoxLayout()
        self.save_config_btn = QPushButton("Save Settings")
        self.save_config_btn.clicked.connect(self.save_settings)

        self.manual_export_btn = QPushButton("Export CSV Now")
        self.manual_export_btn.clicked.connect(self.export_csv_history)

        self.open_data_btn = QPushButton("Open Data Folder")
        self.open_data_btn.clicked.connect(self.open_data_folder)

        buttons.addWidget(self.save_config_btn)
        buttons.addWidget(self.manual_export_btn)
        buttons.addWidget(self.open_data_btn)
        buttons.addStretch(1)

        layout.addLayout(buttons)

        note = QLabel(
            "Research-driven improvements implemented: alert cooldown, persistent config, process filtering, "
            "snapshot export, and low-friction install path."
        )
        note.setWordWrap(True)
        note.setObjectName("note")
        layout.addWidget(note)

        layout.addStretch(1)

    def _plot(self, title: str, y_max: int) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setYRange(0, y_max)
        plot.getPlotItem().hideButtons()
        plot.getPlotItem().setMenuEnabled(False)
        plot.setMouseEnabled(x=False, y=False)
        return plot

    def _load_config_to_widgets(self) -> None:
        self.refresh_spin.setValue(int(self.config["refresh_ms"]))
        self.history_spin.setValue(int(self.config["history_points"]))
        self.cpu_alert_spin.setValue(int(self.config["alert_cpu"]))
        self.mem_alert_spin.setValue(int(self.config["alert_memory"]))
        self.disk_alert_spin.setValue(int(self.config["alert_disk"]))
        self.temp_alert_spin.setValue(int(self.config["alert_temp"]))
        self.cooldown_spin.setValue(int(self.config["alert_cooldown_sec"]))
        self.auto_export_check.setChecked(bool(self.config["auto_export_csv"]))
        self.notify_check.setChecked(bool(self.config["desktop_notifications"]))
        self.process_search.setText(str(self.config.get("process_filter", "")))

    def _on_process_filter_changed(self, text: str) -> None:
        self.config["process_filter"] = text.strip()

    def save_settings(self) -> None:
        self.config["refresh_ms"] = int(self.refresh_spin.value())
        self.config["history_points"] = int(self.history_spin.value())
        self.config["alert_cpu"] = int(self.cpu_alert_spin.value())
        self.config["alert_memory"] = int(self.mem_alert_spin.value())
        self.config["alert_disk"] = int(self.disk_alert_spin.value())
        self.config["alert_temp"] = int(self.temp_alert_spin.value())
        self.config["alert_cooldown_sec"] = int(self.cooldown_spin.value())
        self.config["auto_export_csv"] = bool(self.auto_export_check.isChecked())
        self.config["desktop_notifications"] = bool(self.notify_check.isChecked())

        save_config(self.config)

        self.timer.stop()
        self.timer.start(int(self.config["refresh_ms"]))

        desired_points = int(self.config["history_points"])
        if desired_points != self.history_points:
            self._resize_history_buffers(desired_points)

        self.log_event("Settings saved.")

    def _resize_history_buffers(self, points: int) -> None:
        self.history_points = points

        def resize(source: deque) -> deque:
            data = list(source)[-points:]
            if len(data) < points:
                data = [0.0] * (points - len(data)) + data
            return deque(data, maxlen=points)

        self.cpu_history = resize(self.cpu_history)
        self.mem_history = resize(self.mem_history)
        self.net_in_history = resize(self.net_in_history)
        self.net_out_history = resize(self.net_out_history)
        self.temp_history = resize(self.temp_history)

    def _apply_style(self) -> None:
        QApplication.instance().setFont(QFont("Noto Sans", 10))

        self.setStyleSheet(
            """
            QWidget {
                background: #0c111d;
                color: #e5e7eb;
            }
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #1d3557);
                border: 1px solid #2a3f5f;
                border-radius: 14px;
            }
            QLabel#heading {
                color: #f8fafc;
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#subheading {
                color: #b8c4d6;
                font-size: 12px;
            }
            QLabel#lastUpdate {
                color: #dbeafe;
                font-size: 12px;
            }
            QTabWidget::pane {
                background: #0f172a;
                border: 1px solid #23324b;
                border-radius: 10px;
                top: -1px;
            }
            QTabBar::tab {
                background: #132034;
                color: #c7d2fe;
                padding: 9px 14px;
                margin-right: 5px;
                border: 1px solid #2a3f5f;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #1f3a5f;
                color: #ffffff;
            }
            QFrame#statCard {
                background: #15243a;
                border: 1px solid #2a3f5f;
                border-radius: 12px;
            }
            QLabel#cardTitle {
                color: #c3d0e3;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#cardValue {
                color: #ffffff;
                font-size: 30px;
                font-weight: 800;
            }
            QLabel#cardMeta {
                color: #b6c5da;
                font-size: 11px;
            }
            QLabel#sectionTitle {
                font-size: 17px;
                font-weight: 700;
                color: #f8fafc;
            }
            QLabel#note {
                color: #9cc2ff;
                font-size: 12px;
                border: 1px solid #2a3f5f;
                border-radius: 8px;
                padding: 10px;
                background: #102039;
            }
            QPushButton {
                background: #2a4f7b;
                color: #f8fafc;
                border: 1px solid #3f6ca1;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #366390;
            }
            QPushButton:pressed {
                background: #1e3f66;
            }
            QLineEdit, QSpinBox {
                background: #0f1d31;
                border: 1px solid #2d4364;
                border-radius: 8px;
                padding: 7px;
                color: #f8fafc;
            }
            QCheckBox {
                color: #d7e2f0;
            }
            QTableWidget {
                background: #0b1628;
                border: 1px solid #2a3f5f;
                border-radius: 10px;
                gridline-color: #182a43;
                alternate-background-color: #0f1d31;
            }
            QHeaderView::section {
                background: #183152;
                color: #eaf2ff;
                border: none;
                border-right: 1px solid #2a3f5f;
                padding: 8px;
                font-weight: 700;
            }
            QLabel#systemInfo {
                background: #0b1628;
                border: 1px solid #2a3f5f;
                border-radius: 10px;
                padding: 12px;
                color: #d9e5f5;
            }
            QTextEdit#logPane {
                background: #081220;
                border: 1px solid #2a3f5f;
                border-radius: 8px;
                color: #d7e8ff;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 11px;
            }
            """
        )

        for plot in [self.cpu_plot, self.mem_plot, self.net_plot, self.temp_plot]:
            plot.setBackground(QColor("#0b1628"))
            axis_pen = pg.mkPen("#5f7ea8")
            text_pen = pg.mkPen("#9bb4d6")
            plot.getAxis("left").setPen(axis_pen)
            plot.getAxis("bottom").setPen(axis_pen)
            plot.getAxis("left").setTextPen(text_pen)
            plot.getAxis("bottom").setTextPen(text_pen)

    def refresh(self) -> None:
        now = time.time()
        elapsed = max(now - self.prev_time, 0.001)
        self.prev_time = now

        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        root_disk_percent = self._root_disk_percent()

        net = psutil.net_io_counters()
        in_rate = max((net.bytes_recv - self.prev_net.bytes_recv) / elapsed, 0.0)
        out_rate = max((net.bytes_sent - self.prev_net.bytes_sent) / elapsed, 0.0)
        self.prev_net = net

        load_1 = psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0.0
        max_temp = self._max_temp_c()
        temp_display = max_temp if max_temp is not None else 0.0

        self.cpu_history.append(cpu_percent)
        self.mem_history.append(memory.percent)
        self.net_in_history.append(in_rate / 1024.0 / 1024.0)
        self.net_out_history.append(out_rate / 1024.0 / 1024.0)
        self.temp_history.append(temp_display)

        sample = Sample(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            cpu=cpu_percent,
            memory=memory.percent,
            disk_root=root_disk_percent,
            net_in_mbs=self.net_in_history[-1],
            net_out_mbs=self.net_out_history[-1],
            load_1=load_1,
            temp_c=max_temp,
        )
        self.snapshots.append(sample)
        if len(self.snapshots) > 5000:
            self.snapshots = self.snapshots[-5000:]

        self._update_cards(cpu_percent, memory, root_disk_percent, net)
        self._update_plots()
        self._update_storage_table()
        self._update_process_table()
        self._update_system_info(cpu_percent, memory, max_temp)
        self._run_alerts(sample)
        self._update_insights(sample)

        if bool(self.config["auto_export_csv"]):
            self._append_csv(sample)

        self._write_json_snapshot(sample)

        self.last_update.setText(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _root_disk_percent(self) -> float:
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint == "/":
                try:
                    return float(psutil.disk_usage(part.mountpoint).percent)
                except PermissionError:
                    return 0.0
        return 0.0

    def _max_temp_c(self) -> Optional[float]:
        temps = psutil.sensors_temperatures(fahrenheit=False)
        if not temps:
            return None

        max_temp = None
        for _, entries in temps.items():
            for entry in entries:
                if entry.current is None:
                    continue
                if max_temp is None or entry.current > max_temp:
                    max_temp = float(entry.current)
        return max_temp

    def _update_cards(self, cpu_percent: float, memory, disk_root_percent: float, net) -> None:
        self.cpu_card.value.setText(f"{cpu_percent:.1f}%")
        self.cpu_card.meta.setText(f"{psutil.cpu_count(logical=True)} logical cores")

        self.mem_card.value.setText(f"{memory.percent:.1f}%")
        self.mem_card.meta.setText(f"{format_bytes(memory.used)} / {format_bytes(memory.total)}")

        self.disk_card.value.setText(f"{disk_root_percent:.1f}%")
        self.disk_card.meta.setText("root filesystem")

        self.net_card.value.setText(f"{self.net_in_history[-1]:.2f} / {self.net_out_history[-1]:.2f} MB/s")
        self.net_card.meta.setText(f"totals in {format_bytes(net.bytes_recv)} out {format_bytes(net.bytes_sent)}")

    def _update_plots(self) -> None:
        self.cpu_line.setData(list(self.cpu_history))
        self.mem_line.setData(list(self.mem_history))
        self.net_in_line.setData(list(self.net_in_history))
        self.net_out_line.setData(list(self.net_out_history))
        self.temp_line.setData(list(self.temp_history))

        net_max = max(max(self.net_in_history), max(self.net_out_history), 1.0)
        self.net_plot.setYRange(0, net_max * 1.25)

        temp_max = max(max(self.temp_history), 50.0)
        self.temp_plot.setYRange(0, max(80.0, temp_max * 1.2))

    def _update_storage_table(self) -> None:
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

    def _update_process_table(self) -> None:
        filter_text = str(self.config.get("process_filter", "")).lower()
        rows = []
        for proc in psutil.process_iter(attrs=["pid", "name", "username", "cpu_percent", "memory_percent", "num_threads", "status"]):
            try:
                info = proc.info
                name = str(info.get("name", ""))
                user = str(info.get("username", ""))

                if filter_text and filter_text not in name.lower() and filter_text not in user.lower():
                    continue

                rows.append(
                    (
                        str(info.get("pid", "")),
                        name,
                        user,
                        f"{float(info.get('cpu_percent', 0.0)):.1f}",
                        f"{float(info.get('memory_percent', 0.0)):.1f}",
                        str(info.get("num_threads", "")),
                        str(info.get("status", "")),
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        rows.sort(key=lambda x: float(x[3]), reverse=True)
        top_rows = rows[:30]

        self.proc_table.setRowCount(len(top_rows))
        for r, row in enumerate(top_rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(value)
                if c in (0, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.proc_table.setItem(r, c, item)

    def _update_system_info(self, cpu_percent: float, memory, max_temp: Optional[float]) -> None:
        uname = platform.uname()
        uptime = time.time() - psutil.boot_time()
        uptime_h = uptime / 3600.0

        load = "N/A"
        if hasattr(psutil, "getloadavg"):
            la = psutil.getloadavg()
            load = f"{la[0]:.2f}, {la[1]:.2f}, {la[2]:.2f}"

        battery_text = "N/A"
        battery = psutil.sensors_battery()
        if battery:
            battery_text = f"{battery.percent:.0f}%"
            if battery.power_plugged:
                battery_text += " charging"

        temp_text = "N/A" if max_temp is None else f"{max_temp:.1f} C"

        lines = [
            f"Hostname: {uname.node}",
            f"OS: {uname.system} {uname.release} ({uname.version})",
            f"Architecture: {uname.machine}",
            f"CPU Identifier: {uname.processor or 'Unknown'}",
            f"CPU Usage: {cpu_percent:.1f}%",
            f"Load Average 1m/5m/15m: {load}",
            f"Memory: {format_bytes(memory.used)} used of {format_bytes(memory.total)} ({memory.percent:.1f}%)",
            f"Uptime: {uptime_h:.1f} hours",
            f"Maximum Temperature: {temp_text}",
            f"Battery: {battery_text}",
            f"Data Directory: {DATA_DIR}",
        ]

        self.system_info.setText("\n".join(lines))

    def _run_alerts(self, sample: Sample) -> None:
        checks = [
            ("cpu", sample.cpu, float(self.config["alert_cpu"]), f"CPU high: {sample.cpu:.1f}%"),
            ("memory", sample.memory, float(self.config["alert_memory"]), f"Memory high: {sample.memory:.1f}%"),
            ("disk", sample.disk_root, float(self.config["alert_disk"]), f"Disk root high: {sample.disk_root:.1f}%"),
        ]

        if sample.temp_c is not None:
            checks.append(
                ("temperature", sample.temp_c, float(self.config["alert_temp"]), f"Temperature high: {sample.temp_c:.1f} C")
            )

        now = time.time()
        cooldown = int(self.config["alert_cooldown_sec"])

        for key, value, threshold, message in checks:
            if value < threshold:
                continue

            last_ts = self.last_alert_at.get(key, 0.0)
            if now - last_ts < cooldown:
                continue

            self.last_alert_at[key] = now
            self.log_alert(message)
            if bool(self.config["desktop_notifications"]):
                self.notify_desktop(message)

    def _update_insights(self, sample: Sample) -> None:
        insights = []

        if len(self.cpu_history) > 10:
            recent_cpu = sum(list(self.cpu_history)[-10:]) / 10.0
            if recent_cpu > 80:
                insights.append(f"Sustained CPU pressure (10-s avg): {recent_cpu:.1f}%")

        if len(self.mem_history) > 10:
            recent_mem = sum(list(self.mem_history)[-10:]) / 10.0
            if recent_mem > 80:
                insights.append(f"Memory pressure rising (10-s avg): {recent_mem:.1f}%")

        if sample.net_in_mbs > 10 or sample.net_out_mbs > 10:
            insights.append(
                f"Network burst detected: in {sample.net_in_mbs:.2f} MB/s out {sample.net_out_mbs:.2f} MB/s"
            )

        if sample.temp_c is not None and sample.temp_c > 75:
            insights.append(f"Thermal warning trend: {sample.temp_c:.1f} C")

        if not insights:
            insights.append("System trend is stable.")

        stamp = datetime.now().strftime("%H:%M:%S")
        for item in insights[:2]:
            self.insight_log.append(f"[{stamp}] {item}")

        if self.insight_log.document().blockCount() > 250:
            cursor = self.insight_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def log_event(self, text: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {text}"
        with EVENT_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def log_alert(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {text}"
        self.alert_log.append(line)
        self.log_event(text)

    def notify_desktop(self, text: str) -> None:
        try:
            subprocess.run(["notify-send", APP_TITLE, text], check=False)
        except FileNotFoundError:
            pass

    def _append_csv(self, sample: Sample) -> None:
        ensure_dirs()
        exists = CSV_HISTORY_FILE.exists()
        with CSV_HISTORY_FILE.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if not exists:
                writer.writerow(["timestamp", "cpu", "memory", "disk_root", "net_in_mbs", "net_out_mbs", "load_1", "temp_c"])
            writer.writerow(
                [
                    sample.timestamp,
                    f"{sample.cpu:.2f}",
                    f"{sample.memory:.2f}",
                    f"{sample.disk_root:.2f}",
                    f"{sample.net_in_mbs:.4f}",
                    f"{sample.net_out_mbs:.4f}",
                    f"{sample.load_1:.4f}",
                    "" if sample.temp_c is None else f"{sample.temp_c:.2f}",
                ]
            )

    def _write_json_snapshot(self, sample: Sample) -> None:
        ensure_dirs()
        payload = {
            "timestamp": sample.timestamp,
            "cpu_percent": sample.cpu,
            "memory_percent": sample.memory,
            "disk_root_percent": sample.disk_root,
            "net_in_mbs": sample.net_in_mbs,
            "net_out_mbs": sample.net_out_mbs,
            "load_1": sample.load_1,
            "temp_c": sample.temp_c,
        }
        JSON_SNAPSHOT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def export_snapshot(self) -> None:
        if not self.snapshots:
            self.log_event("Export requested with no snapshots available.")
            return
        sample = self.snapshots[-1]
        self._write_json_snapshot(sample)
        self.log_event(f"Snapshot exported to {JSON_SNAPSHOT_FILE}")

    def export_csv_history(self) -> None:
        if not self.snapshots:
            self.log_event("CSV export requested with no snapshots.")
            return

        ensure_dirs()
        with CSV_HISTORY_FILE.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "cpu", "memory", "disk_root", "net_in_mbs", "net_out_mbs", "load_1", "temp_c"])
            for s in self.snapshots:
                writer.writerow(
                    [
                        s.timestamp,
                        f"{s.cpu:.2f}",
                        f"{s.memory:.2f}",
                        f"{s.disk_root:.2f}",
                        f"{s.net_in_mbs:.4f}",
                        f"{s.net_out_mbs:.4f}",
                        f"{s.load_1:.4f}",
                        "" if s.temp_c is None else f"{s.temp_c:.2f}",
                    ]
                )

        self.log_event(f"CSV history exported to {CSV_HISTORY_FILE}")

    def open_data_folder(self) -> None:
        ensure_dirs()
        try:
            subprocess.run(["xdg-open", str(DATA_DIR)], check=False)
        except FileNotFoundError:
            self.log_event(f"Data folder: {DATA_DIR}")
def main() -> None:
    ensure_dirs()
    app = QApplication(sys.argv)
    window = MonitorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
