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
    # ── NVIDIA Parakeet (NeMo backend) ──────────────────────────────────────
    {
        "id": "nvidia/parakeet-tdt-1.1b",
        "name": "Parakeet TDT 1.1B",
        "size": "~4 GB",
        "description": "Best accuracy. Recommended for most users.",
        "badge": "★ Default",
        "section": "NVIDIA Parakeet  ·  English only  ·  NeMo backend",
    },
    {
        "id": "nvidia/parakeet-tdt-0.6b",
        "name": "Parakeet TDT 0.6B",
        "size": "~2.3 GB",
        "description": "Faster, lower memory. Good for older GPUs or CPU.",
        "badge": "⚡ Fast",
        "section": None,
    },
    {
        "id": "nvidia/parakeet-rnnt-1.1b",
        "name": "Parakeet RNNT 1.1B",
        "size": "~4 GB",
        "description": "Alternative architecture, similar accuracy.",
        "badge": "",
        "section": None,
    },
    {
        "id": "nvidia/parakeet-ctc-1.1b",
        "name": "Parakeet CTC 1.1B",
        "size": "~4 GB",
        "description": "CTC decoder, fastest inference of the 1.1B family.",
        "badge": "",
        "section": None,
    },
    {
        "id": "nvidia/parakeet-ctc-0.6b",
        "name": "Parakeet CTC 0.6B",
        "size": "~2.3 GB",
        "description": "Smallest and fastest option. Lower accuracy.",
        "badge": "⚡ Fastest",
        "section": None,
    },
    # ── OpenAI Whisper (Transformers backend) ────────────────────────────────
    {
        "id": "openai/whisper-large-v3",
        "name": "Whisper Large v3",
        "size": "~3 GB",
        "description": "Best multilingual accuracy. Supports 99 languages.",
        "badge": "🌍 Multilingual",
        "section": "OpenAI Whisper  ·  99 languages  ·  Transformers backend",
    },
    {
        "id": "openai/whisper-medium",
        "name": "Whisper Medium",
        "size": "~1.5 GB",
        "description": "Good balance of speed and multilingual accuracy.",
        "badge": "",
        "section": None,
    },
    {
        "id": "openai/whisper-small",
        "name": "Whisper Small",
        "size": "~500 MB",
        "description": "Fast and lightweight. Decent multilingual quality.",
        "badge": "⚡ Fast",
        "section": None,
    },
    {
        "id": "openai/whisper-base",
        "name": "Whisper Base",
        "size": "~145 MB",
        "description": "Smallest Whisper model. Good for quick testing.",
        "badge": "⚡ Fastest",
        "section": None,
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

            if not is_asr:
                self.result.emit(
                    False,
                    "This model does not appear to support speech recognition.\n"
                    "Verify the model has the 'automatic-speech-recognition' tag on HuggingFace."
                )
                return

            # Detect which backend will be used
            has_nemo = any(
                f.rfilename.endswith(".nemo")
                for f in (info.siblings or [])
            )
            from transcriber import _NEMO_PREFIXES
            is_nemo_id = any(self.model_id.startswith(p) for p in _NEMO_PREFIXES)

            if has_nemo or is_nemo_id:
                backend_label = "NeMo backend"
            else:
                backend_label = "Transformers backend"

            likes = getattr(info, "likes", None)
            likes_str = f"  ·  {likes} ❤" if likes else ""
            self.result.emit(True, f"✓ Valid ASR model  ·  {backend_label}{likes_str}")

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
    Call exec() — if accepted, read .selected_model and .selected_dir.

    Args:
        current_model: currently active HF model ID or local path
        is_first_run: True on first launch — changes title and button text,
                      and requires a storage location to be confirmed before accepting
    """

    def __init__(self, current_model: str, is_first_run: bool = False, parent=None):
        super().__init__(parent)
        self.current_model = current_model
        self.selected_model = current_model
        self.selected_dir = None   # set when user confirms storage location
        self.is_first_run = is_first_run
        self._validate_thread = None
        self._setup_ui()

    def _setup_ui(self):
        import config as _config

        if self.is_first_run:
            self.setWindowTitle("DevVoice — Setup")
        else:
            self.setWindowTitle("DevVoice — Change Model")
        self.setMinimumWidth(560)
        self.setMinimumHeight(540)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        if self.is_first_run:
            title = QLabel("Welcome to DevVoice")
            subtitle = QLabel("Select a speech recognition model to get started.")
        else:
            title = QLabel("Change Model")
            subtitle = QLabel(f"Active model: <b>{self.current_model}</b>")
        title.setFont(QFont(title.font().family(), 13, QFont.Weight.Bold))
        layout.addWidget(title)
        subtitle.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_recommended_tab(), "Recommended")
        tabs.addTab(self._build_hf_tab(), "HuggingFace")
        tabs.addTab(self._build_local_tab(), "Local File")
        layout.addWidget(tabs)

        # ── Storage location ───────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #ddd;")
        layout.addWidget(sep)

        dir_label = QLabel("📁  Models storage location")
        dir_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #444;")
        layout.addWidget(dir_label)

        dir_row = QHBoxLayout()
        self._dir_input = QLineEdit()
        self._dir_input.setText(_config.get_model_dir())
        self._dir_input.setPlaceholderText("Folder where models are downloaded and cached")
        self._dir_input.setStyleSheet("font-size: 11px; font-family: monospace;")
        dir_row.addWidget(self._dir_input, stretch=1)

        browse_dir_btn = QPushButton("Browse…")
        browse_dir_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_dir_btn)
        layout.addLayout(dir_row)

        dir_hint = QLabel("Models are downloaded to this folder. Any models already present here will be detected automatically.")
        dir_hint.setStyleSheet("color: #888; font-size: 10px;")
        dir_hint.setWordWrap(True)
        layout.addWidget(dir_hint)

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

        apply_label = "Set Up DevVoice" if self.is_first_run else "Apply && Reload"
        self._apply_btn = QPushButton(apply_label)
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
            # Section header
            if m.get("section"):
                header = QLabel(m["section"])
                header.setStyleSheet(
                    "color: #1565C0; font-size: 10px; font-weight: bold; "
                    "padding: 8px 2px 2px 2px; letter-spacing: 0.5px;"
                )
                vbox.addWidget(header)

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
            "Enter a HuggingFace model ID for any speech recognition model.\n"
            "Supports NVIDIA NeMo models and standard Transformers models (Whisper, wav2vec2, etc.)"
        ))

        input_row = QHBoxLayout()
        self._hf_input = QLineEdit()
        self._hf_input.setPlaceholderText("e.g.  openai/whisper-large-v3")
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
            "Use a model already on your machine."
        ))

        # NeMo file row
        nemo_label = QLabel("NeMo model file (.nemo)  —  NeMo backend")
        nemo_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #444; margin-top: 6px;")
        layout.addWidget(nemo_label)

        nemo_row = QHBoxLayout()
        self._local_path = QLineEdit()
        self._local_path.setPlaceholderText("Path to .nemo file…")
        self._local_path.setReadOnly(True)
        nemo_row.addWidget(self._local_path, stretch=1)
        browse_file_btn = QPushButton("Browse…")
        browse_file_btn.clicked.connect(self._browse_local_file)
        nemo_row.addWidget(browse_file_btn)
        layout.addLayout(nemo_row)

        # Transformers folder row
        tf_label = QLabel("Transformers model folder  —  Transformers backend")
        tf_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #444; margin-top: 8px;")
        layout.addWidget(tf_label)

        tf_hint = QLabel("The folder must contain a config.json file (standard HuggingFace model format).")
        tf_hint.setStyleSheet("color: #888; font-size: 10px;")
        tf_hint.setWordWrap(True)
        layout.addWidget(tf_hint)

        tf_row = QHBoxLayout()
        self._local_folder_path = QLineEdit()
        self._local_folder_path.setPlaceholderText("Path to model folder…")
        self._local_folder_path.setReadOnly(True)
        tf_row.addWidget(self._local_folder_path, stretch=1)
        browse_folder_btn = QPushButton("Browse…")
        browse_folder_btn.clicked.connect(self._browse_local_folder)
        tf_row.addWidget(browse_folder_btn)
        layout.addLayout(tf_row)

        self._local_status = QLabel("")
        self._local_status.setStyleSheet("font-size: 11px;")
        self._local_status.setWordWrap(True)
        layout.addWidget(self._local_status)

        use_btn = QPushButton("Use this model")
        use_btn.setEnabled(False)
        use_btn.clicked.connect(self._use_local_model)
        self._local_use_btn = use_btn
        layout.addWidget(use_btn)

        layout.addStretch()
        return widget

    def _browse_local_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select NeMo model file",
            "",
            "NeMo models (*.nemo)"
        )
        if not path:
            return
        self._local_path.setText(path)
        if not path.endswith(".nemo"):
            self._local_status.setText("Please select a .nemo file.")
            self._local_status.setStyleSheet("color: #c62828; font-size: 11px;")
            self._local_use_btn.setEnabled(False)
            return
        size_mb = os.path.getsize(path) / (1024 * 1024)
        self._local_status.setText(f"✓ {size_mb:.0f} MB  ·  NeMo backend")
        self._local_status.setStyleSheet("color: #2e7d32; font-size: 11px;")
        self._local_use_btn.setEnabled(True)
        self._local_folder_path.clear()
        self._set_preview(path)

    def _browse_local_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Transformers model folder", ""
        )
        if not path:
            return
        self._local_folder_path.setText(path)
        config_json = os.path.join(path, "config.json")
        if not os.path.isfile(config_json):
            self._local_status.setText(
                "No config.json found in this folder. "
                "Select the folder that directly contains config.json."
            )
            self._local_status.setStyleSheet("color: #c62828; font-size: 11px;")
            self._local_use_btn.setEnabled(False)
            return
        self._local_status.setText("✓ Valid model folder  ·  Transformers backend")
        self._local_status.setStyleSheet("color: #2e7d32; font-size: 11px;")
        self._local_use_btn.setEnabled(True)
        self._local_path.clear()
        self._set_preview(path)

    def _use_local_model(self):
        path = self._local_path.text() or self._local_folder_path.text()
        if path:
            self._set_preview(path)

    # ------------------------------------------------------------------
    # Storage location
    # ------------------------------------------------------------------
    def _browse_dir(self):
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(
            self, "Choose model storage folder", self._dir_input.text()
        )
        if path:
            self._dir_input.setText(path)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _set_preview(self, model: str):
        self.selected_model = model
        self._status_label.setText(f"Selected: <b>{model}</b>")
        self._apply_btn.setEnabled(True)

    def _on_apply(self):
        if self.selected_model:
            self.selected_dir = self._dir_input.text().strip() or None
            self.accept()
