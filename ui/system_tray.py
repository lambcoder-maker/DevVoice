"""System tray icon and menu."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import pyqtSignal, QObject


class SystemTray(QObject):
    """System tray icon with status indicator."""

    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()

    # Status colors
    COLORS = {
        "idle": "#4CAF50",      # Green
        "recording": "#F44336", # Red
        "processing": "#FF9800", # Orange
        "loading": "#9E9E9E",   # Gray
    }

    def __init__(self):
        super().__init__()
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Speech-to-Text")
        self.is_recording = False

        # Create context menu
        self.menu = QMenu()

        # Toggle recording button
        self.record_action = self.menu.addAction("Start Recording")
        self.record_action.triggered.connect(self._on_toggle_recording)

        self.menu.addSeparator()

        show_action = self.menu.addAction("Show History")
        show_action.triggered.connect(self.show_window_requested.emit)

        self.menu.addSeparator()

        quit_action = self.menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        # Set initial icon
        self.set_status("idle")

    def _on_toggle_recording(self):
        """Handle toggle recording button click."""
        self.toggle_recording_requested.emit()

    def _create_icon(self, color: str) -> QIcon:
        """Create a simple colored circle icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(QColor(color).darker(120))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()

        return QIcon(pixmap)

    def set_status(self, status: str):
        """Update tray icon based on status."""
        color = self.COLORS.get(status, self.COLORS["idle"])
        self.tray.setIcon(self._create_icon(color))

        tooltip_map = {
            "idle": "Speech-to-Text - Ready",
            "recording": "Speech-to-Text - Recording...",
            "processing": "Speech-to-Text - Processing...",
            "loading": "Speech-to-Text - Loading model...",
        }
        self.tray.setToolTip(tooltip_map.get(status, "Speech-to-Text"))

        # Update button text
        if status == "recording":
            self.record_action.setText("Stop Recording")
            self.is_recording = True
        elif status == "idle":
            self.record_action.setText("Start Recording")
            self.is_recording = False
        elif status == "processing":
            self.record_action.setText("Processing...")
            self.record_action.setEnabled(False)

        # Re-enable when idle
        if status == "idle":
            self.record_action.setEnabled(True)

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    def show(self):
        """Show the tray icon."""
        self.tray.show()
