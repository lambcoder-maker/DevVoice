"""Floating control window for easy recording."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ControlWindow(QWidget):
    """Small floating window for recording control."""

    toggle_recording = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Speech-to-Text")
        self.setFixedWidth(400)
        self.setMinimumHeight(150)

        # Always on top, no taskbar icon, doesn't steal focus
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.status_label)

        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.text_display.setPlaceholderText("Transcribed text will appear here...")
        self.text_display.setMaximumHeight(80)
        self.text_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.text_display)

        # Button row
        btn_layout = QHBoxLayout()

        # Main record button
        self.record_btn = QPushButton("🎤 Start Recording")
        self.record_btn.setMinimumHeight(40)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.record_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.record_btn.clicked.connect(self._on_record_click)
        btn_layout.addWidget(self.record_btn)

        # Copy button
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.setMaximumWidth(80)
        self.copy_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copy_btn.clicked.connect(self._copy_text)
        self.copy_btn.setEnabled(False)
        btn_layout.addWidget(self.copy_btn)

        layout.addLayout(btn_layout)

        # Position at top-right of screen
        self._position_window()

    def _position_window(self):
        """Position window at top-right of screen."""
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 50)

    def _on_record_click(self):
        """Handle record button click."""
        self.toggle_recording.emit()

    def _copy_text(self):
        """Copy text to clipboard."""
        text = self.text_display.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("Copied!")

    def set_recording(self, recording: bool):
        """Update UI for recording state."""
        self.is_recording = recording
        if recording:
            self.record_btn.setText("⏹ Stop Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.status_label.setText("🔴 Recording... Click to stop")
            self.status_label.setStyleSheet("font-size: 12px; color: #F44336; font-weight: bold;")
            self.text_display.clear()
            self.copy_btn.setEnabled(False)
        else:
            self.record_btn.setText("🎤 Start Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-size: 12px; color: #666;")

    def set_processing(self):
        """Update UI for processing state."""
        self.record_btn.setEnabled(False)
        self.record_btn.setText("⏳ Processing...")
        self.status_label.setText("Transcribing audio...")
        self.status_label.setStyleSheet("font-size: 12px; color: #FF9800;")

    def set_transcription(self, text: str):
        """Show transcribed text."""
        self.record_btn.setEnabled(True)
        self.set_recording(False)
        if text:
            self.text_display.setText(text)
            self.copy_btn.setEnabled(True)
            self.status_label.setText(f"✓ Transcribed ({len(text)} chars) - Typing...")
            self.status_label.setStyleSheet("font-size: 12px; color: #4CAF50;")
        else:
            self.status_label.setText("No speech detected")
            self.status_label.setStyleSheet("font-size: 12px; color: #666;")

    def set_typing_complete(self):
        """Update status when typing is complete."""
        self.status_label.setText("✓ Done!")
        self.status_label.setStyleSheet("font-size: 12px; color: #4CAF50;")

    def set_loading(self):
        """Show loading state."""
        self.record_btn.setEnabled(False)
        self.record_btn.setText("Loading model...")
        self.status_label.setText("Loading Parakeet model, please wait...")

    def set_ready(self):
        """Show ready state after loading."""
        self.record_btn.setEnabled(True)
        self.set_recording(False)
