"""System tray icon and menu."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import pyqtSignal, QObject


class SystemTray(QObject):
    """System tray icon with status indicator."""

    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()
    change_model_requested = pyqtSignal()
    help_requested = pyqtSignal()

    COLORS = {
        "idle":       "#4CAF50",
        "recording":  "#F44336",
        "processing": "#FF9800",
        "loading":    "#9E9E9E",
    }

    def __init__(self):
        super().__init__()
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("DevVoice")
        self.is_recording = False

        self.menu = QMenu()

        self.record_action = self.menu.addAction("Start Recording")
        self.record_action.triggered.connect(self._on_toggle_recording)

        self.menu.addSeparator()

        show_action = self.menu.addAction("Transcription History")
        show_action.triggered.connect(self.show_window_requested.emit)

        change_model_action = self.menu.addAction("Change Model…")
        change_model_action.triggered.connect(self.change_model_requested.emit)

        help_action = self.menu.addAction("Commands & Hotkeys…")
        help_action.triggered.connect(self.help_requested.emit)

        self.menu.addSeparator()

        quit_action = self.menu.addAction("Quit DevVoice")
        quit_action.triggered.connect(self.quit_requested.emit)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        self.set_status("idle")

    def _on_toggle_recording(self):
        self.toggle_recording_requested.emit()

    def _create_icon(self, color: str) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(QColor(color).darker(120))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()

        return QIcon(pixmap)

    def set_status(self, status: str):
        color = self.COLORS.get(status, self.COLORS["idle"])
        self.tray.setIcon(self._create_icon(color))

        tooltip_map = {
            "idle":       "DevVoice — Ready",
            "recording":  "DevVoice — Recording",
            "processing": "DevVoice — Transcribing",
            "loading":    "DevVoice — Loading model",
        }
        self.tray.setToolTip(tooltip_map.get(status, "DevVoice"))

        if status == "recording":
            self.record_action.setText("Stop Recording")
            self.record_action.setEnabled(True)
            self.is_recording = True
        elif status == "idle":
            self.record_action.setText("Start Recording")
            self.record_action.setEnabled(True)
            self.is_recording = False
        elif status == "processing":
            self.record_action.setText("Transcribing…")
            self.record_action.setEnabled(False)
        elif status == "loading":
            self.record_action.setText("Loading model…")
            self.record_action.setEnabled(False)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    def show(self):
        self.tray.show()
