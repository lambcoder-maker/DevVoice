"""Main window for transcription history."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt


class TranscriptionEntry(QFrame):
    """A single transcription entry with timestamp and copy button."""

    def __init__(self, text: str, timestamp: datetime):
        super().__init__()
        self.text = text

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            TranscriptionEntry {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }
        """)

        layout = QVBoxLayout(self)

        # Header with timestamp and copy button
        header = QHBoxLayout()

        time_label = QLabel(timestamp.strftime("%H:%M:%S"))
        time_label.setStyleSheet("color: #666; font-size: 11px;")
        header.addWidget(time_label)

        header.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setMaximumWidth(60)
        copy_btn.clicked.connect(self._copy_text)
        header.addWidget(copy_btn)

        layout.addLayout(header)

        # Text content
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 13px; padding: 4px 0;")
        layout.addWidget(text_label)

    def _copy_text(self):
        """Copy transcription text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)


class MainWindow(QMainWindow):
    """Main window showing transcription history."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech-to-Text History")
        self.setMinimumSize(400, 500)
        self.resize(500, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Header
        header = QHBoxLayout()

        title = QLabel("Transcription History")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Scrollable area for transcriptions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.entries_widget = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_widget)
        self.entries_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.entries_widget)
        layout.addWidget(scroll)

        # Hotkey hint
        hint = QLabel("Press Ctrl+Shift+R to start/stop recording")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def add_transcription(self, text: str):
        """Add a new transcription entry."""
        entry = TranscriptionEntry(text, datetime.now())
        self.entries_layout.insertWidget(0, entry)  # Add at top

    def _clear_history(self):
        """Clear all transcription entries."""
        while self.entries_layout.count():
            item = self.entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def closeEvent(self, event):
        """Hide window instead of closing."""
        event.ignore()
        self.hide()
