"""Model download and load dialog with visible progress."""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class _ModelLoaderThread(QThread):
    """Loads (and downloads if needed) a model off the main thread."""

    progress = pyqtSignal(str)   # status message
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, transcriber):
        super().__init__()
        self.transcriber = transcriber

    def run(self):
        try:
            # Patch NeMo's download to emit progress messages
            self.progress.emit("Connecting…")
            self._patch_nemo_progress()
            self.progress.emit("Downloading model files…")
            self.transcriber.load_model()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _patch_nemo_progress(self):
        """Best-effort: hook into huggingface_hub to forward download progress."""
        try:
            import huggingface_hub.file_download as fd
            _orig = fd.hf_hub_download

            def _patched(*args, **kwargs):
                filename = kwargs.get("filename") or (args[1] if len(args) > 1 else "model")
                self.progress.emit(f"Downloading {filename}…")
                result = _orig(*args, **kwargs)
                self.progress.emit(f"Downloaded {filename}")
                return result

            fd.hf_hub_download = _patched
        except Exception:
            pass  # Non-fatal — progress messages just won't be granular


class ModelLoadDialog(QDialog):
    """
    Shown on first run (or when model isn't cached).
    Runs model download/load in a background thread and shows progress.
    Call exec() — returns True on success, False if the user cancels or an error occurs.
    """

    def __init__(self, transcriber, parent=None):
        super().__init__(parent)
        self.transcriber = transcriber
        self._success = False
        self._setup_ui()

    def _setup_ui(self):
        model_id = getattr(self.transcriber, 'model_id', 'nvidia/parakeet-tdt-1.1b')
        model_short = model_id.split("/")[-1]

        self.setWindowTitle(f"DevVoice — Downloading {model_short}")
        self.setFixedWidth(440)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Downloading {model_short}")
        title.setFont(QFont(title.font().family(), 13, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            f"<b>{model_id}</b> will be downloaded before transcription can begin. "
            "This only happens once."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555;")
        layout.addWidget(desc)

        # Destination path
        try:
            import config as _config
            _base = _config.get_model_dir()
        except Exception:
            _base = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        cache_dir = os.path.join(_base, "models--" + model_id.replace("/", "--"))

        dest_label = QLabel("Saving to:")
        dest_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(dest_label)

        location_label = QLabel(cache_dir)
        location_label.setStyleSheet(
            "color: #666; font-size: 10px; font-family: monospace;"
        )
        location_label.setWordWrap(True)
        location_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(location_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate until done
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Starting…")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_btn)

    def start_loading(self):
        """Begin the background load and open the dialog."""
        self.thread = _ModelLoaderThread(self.transcriber)
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_finished)
        self.thread.error.connect(self._on_error)
        self.thread.start()
        self.exec()
        return self._success

    def _on_progress(self, message: str):
        self.status_label.setText(message)

    def _on_finished(self):
        self._success = True
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.status_label.setText("Model downloaded and ready.")
        self.cancel_btn.setText("Continue")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)

    def _on_error(self, message: str):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Download failed: {message}")
        self.status_label.setStyleSheet("color: #c00; font-size: 11px;")
        self.cancel_btn.setText("Close")

    def _on_cancel(self):
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
        self.reject()
