"""Model selection dialog — curated list, HuggingFace ID, or local file."""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QFileDialog, QFrame, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor


# ---------------------------------------------------------------------------
# Curated model catalogue
# ---------------------------------------------------------------------------
RECOMMENDED_MODELS = [
    {
        "id": "nvidia/parakeet-tdt-1.1b",
        "name": "Parakeet TDT 1.1B",
        "size": "~4 GB",
        "description": "Best accuracy. Recommended for most users.",
        "badge": "★ Default",
    },
    {
        "id": "nvidia/parakeet-tdt-0.6b",
        "name": "Parakeet TDT 0.6B",
        "size": "~2.3 GB",
        "description": "Faster, lower memory. Good for older GPUs or CPU.",
        "badge": "⚡ Fast",
    },
    {
        "id": "nvidia/parakeet-rnnt-1.1b",
        "name": "Parakeet RNNT 1.1B",
        "size": "~4 GB",
        "description": "Alternative architecture, similar accuracy.",
        "badge": "",
    },
    {
        "id": "nvidia/parakeet-ctc-1.1b",
        "name": "Parakeet CTC 1.1B",
        "size": "~4 GB",
        "description": "CTC decoder, fastest inference of the 1.1B family.",
        "badge": "",
    },
    {
        "id": "nvidia/parakeet-ctc-0.6b",
        "name": "Parakeet CTC 0.6B",
        "size": "~2.3 GB",
        "description": "Smallest and fastest option. Lower accuracy.",
        "badge": "⚡ Fastest",
    },
]


# ---------------------------------------------------------------------------
# HuggingFace validation thread
# ---------------------------------------------------------------------------
class _ValidateThread(QThread):
    result = pyqtSignal(bool, str)   # (valid, message)

    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id.strip()

    def run(self):
        if not self.model_id or "/" not in self.model_id:
            self.result.emit(False, "Enter a valid HuggingFace model ID (e.g. org/model-name)")
            return
        try:
            from huggingface_hub import model_info
            info = model_info(self.model_id)

            tags = [t.lower() for t in (info.tags or [])]
            pipeline = (info.pipeline_tag or "").lower()

            is_asr = (
                pipeline == "automatic-speech-recognition"
                or "asr" in tags
                or "nemo" in tags
                or "speech-recognition" in tags
            )
            has_nemo = any(
                f.rfilename.endswith(".nemo")
                for f in (info.siblings or [])
            )

            if not is_asr:
                self.result.emit(
                    False,
                    "This model doesn't appear to be a speech recognition model.\n"
                    "Check that it has the 'automatic-speech-recognition' tag on HuggingFace."
                )
                return
            if not has_nemo:
                self.result.emit(
                    False,
                    "No .nemo file found in this repository.\n"
                    "DevVoice requires NeMo-format models (.nemo)."
                )
                return

            likes = getattr(info, "likes", None)
            likes_str = f"  ·  {likes} ❤" if likes else ""
            self.result.emit(True, f"✓ Valid NeMo ASR model{likes_str}")

        except Exception as e:
            msg = str(e)
            if "404" in msg or "not found" in msg.lower():
                self.result.emit(False, "Model not found on HuggingFace. Check the ID.")
            else:
                self.result.emit(False, f"Could not validate: {msg}")


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------
class ModelSelectorDialog(QDialog):
    """
    Modal dialog for choosing a speech recognition model.
    Call exec() — if accepted, read .selected_model for the chosen value
    (HF model ID string or absolute local file path).
    """

    def __init__(self, current_model: str, parent=None):
        super().__init__(parent)
        self.current_model = current_model
        self.selected_model = current_model
        self._validate_thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Choose Speech Recognition Model")
        self.setMinimumWidth(520)
        self.setMinimumHeight(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title = QLabel("Speech Recognition Model")
        title.setFont(QFont(title.font().family(), 13, QFont.Weight.Bold))
        layout.addWidget(title)

        current_label = QLabel(f"Active: <b>{self.current_model}</b>")
        current_label.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(current_label)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_recommended_tab(), "Recommended")
        tabs.addTab(self._build_hf_tab(), "HuggingFace")
        tabs.addTab(self._build_local_tab(), "Local File")
        layout.addWidget(tabs)

        # Status / preview
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("color: #555; font-size: 11px; padding: 4px 0;")
        layout.addWidget(self._status_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._apply_btn = QPushButton("Apply && Reload Model")
        self._apply_btn.setDefault(True)
        self._apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #aaa; }
        """)
        self._apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(self._apply_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Tab: Recommended
    # ------------------------------------------------------------------
    def _build_recommended_tab(self):
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 8, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        self._rec_group = QButtonGroup(inner)
        vbox = QVBoxLayout(inner)
        vbox.setSpacing(6)

        for m in RECOMMENDED_MODELS:
            card = self._make_model_card(m, self._rec_group, vbox)
            if m["id"] == self.current_model:
                card.setChecked(True)

        vbox.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._rec_group.buttonClicked.connect(
            lambda btn: self._set_preview(btn.property("model_id"))
        )
        return widget

    def _make_model_card(self, m: dict, group: QButtonGroup, layout) -> QRadioButton:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 8, 10, 8)

        radio = QRadioButton()
        radio.setProperty("model_id", m["id"])
        group.addButton(radio)
        row.addWidget(radio)

        text_col = QVBoxLayout()
        name_row = QHBoxLayout()

        name_lbl = QLabel(f"<b>{m['name']}</b>  <span style='color:#888;font-size:11px'>{m['size']}</span>")
        name_row.addWidget(name_lbl)
        if m.get("badge"):
            badge = QLabel(m["badge"])
            badge.setStyleSheet(
                "background:#E3F2FD; color:#1565C0; border-radius:3px; "
                "padding:1px 6px; font-size:10px;"
            )
            name_row.addWidget(badge)
        name_row.addStretch()
        text_col.addLayout(name_row)

        desc = QLabel(m["description"])
        desc.setStyleSheet("color:#666; font-size:11px;")
        text_col.addWidget(desc)

        id_lbl = QLabel(m["id"])
        id_lbl.setStyleSheet("color:#999; font-size:10px;")
        text_col.addWidget(id_lbl)

        row.addLayout(text_col)

        # Clicking anywhere on the card selects the radio
        frame.mousePressEvent = lambda _e, r=radio: r.setChecked(True) or \
            self._set_preview(r.property("model_id"))

        layout.addWidget(frame)
        return radio

    # ------------------------------------------------------------------
    # Tab: HuggingFace custom ID
    # ------------------------------------------------------------------
    def _build_hf_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(10)

        layout.addWidget(QLabel(
            "Enter any HuggingFace model ID.\n"
            "The model must be in NeMo format (.nemo) and support speech recognition."
        ))

        input_row = QHBoxLayout()
        self._hf_input = QLineEdit()
        self._hf_input.setPlaceholderText("e.g.  nvidia/parakeet-tdt-0.6b")
        input_row.addWidget(self._hf_input)

        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self._validate_hf)
        input_row.addWidget(validate_btn)
        layout.addLayout(input_row)

        self._hf_status = QLabel("")
        self._hf_status.setWordWrap(True)
        self._hf_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._hf_status)

        use_btn = QPushButton("Use this model")
        use_btn.setEnabled(False)
        use_btn.clicked.connect(self._use_hf_model)
        self._hf_use_btn = use_btn
        layout.addWidget(use_btn)

        layout.addStretch()
        return widget

    def _validate_hf(self):
        model_id = self._hf_input.text().strip()
        if not model_id:
            return
        self._hf_status.setText("Checking HuggingFace...")
        self._hf_status.setStyleSheet("color: #888; font-size: 11px;")
        self._hf_use_btn.setEnabled(False)

        self._validate_thread = _ValidateThread(model_id)
        self._validate_thread.result.connect(self._on_hf_validated)
        self._validate_thread.start()

    def _on_hf_validated(self, valid: bool, message: str):
        if valid:
            self._hf_status.setStyleSheet("color: #2e7d32; font-size: 11px;")
            self._hf_use_btn.setEnabled(True)
        else:
            self._hf_status.setStyleSheet("color: #c62828; font-size: 11px;")
            self._hf_use_btn.setEnabled(False)
        self._hf_status.setText(message)

    def _use_hf_model(self):
        model_id = self._hf_input.text().strip()
        self._set_preview(model_id)

    # ------------------------------------------------------------------
    # Tab: Local file
    # ------------------------------------------------------------------
    def _build_local_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(10)

        layout.addWidget(QLabel(
            "Point to a locally downloaded NeMo model file (.nemo).\n"
            "Useful if you've already downloaded a model or have a custom one."
        ))

        file_row = QHBoxLayout()
        self._local_path = QLineEdit()
        self._local_path.setPlaceholderText("Path to .nemo file...")
        self._local_path.setReadOnly(True)
        file_row.addWidget(self._local_path)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_local)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        self._local_status = QLabel("")
        self._local_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._local_status)

        use_btn = QPushButton("Use this file")
        use_btn.setEnabled(False)
        use_btn.clicked.connect(self._use_local_model)
        self._local_use_btn = use_btn
        layout.addWidget(use_btn)

        layout.addStretch()
        return widget

    def _browse_local(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select NeMo model file", "", "NeMo models (*.nemo)"
        )
        if not path:
            return
        self._local_path.setText(path)

        if not path.endswith(".nemo"):
            self._local_status.setText("File must have a .nemo extension.")
            self._local_status.setStyleSheet("color: #c62828; font-size: 11px;")
            self._local_use_btn.setEnabled(False)
            return
        if not os.path.isfile(path):
            self._local_status.setText("File not found.")
            self._local_status.setStyleSheet("color: #c62828; font-size: 11px;")
            self._local_use_btn.setEnabled(False)
            return

        size_mb = os.path.getsize(path) / (1024 * 1024)
        self._local_status.setText(f"✓ Valid file  ·  {size_mb:.0f} MB")
        self._local_status.setStyleSheet("color: #2e7d32; font-size: 11px;")
        self._local_use_btn.setEnabled(True)

    def _use_local_model(self):
        self._set_preview(self._local_path.text())

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _set_preview(self, model: str):
        self.selected_model = model
        self._status_label.setText(f"Selected: <b>{model}</b>")
        self._apply_btn.setEnabled(model != self.current_model)

    def _on_apply(self):
        if self.selected_model:
            self.accept()
