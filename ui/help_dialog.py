"""Quick-reference help dialog — all hotkeys and voice commands at a glance."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QWidget, QFrame, QPushButton, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QFont


# ---------------------------------------------------------------------------
# Command reference data
# ---------------------------------------------------------------------------

_SECTIONS = [
    {
        "title": "Keyboard Shortcuts",
        "color": "#1565C0",
        "rows": [
            ("Ctrl + Shift + R", "Start or stop recording"),
            ("Ctrl + Shift + Z", "Undo — erase the last typed transcription"),
        ],
    },
    {
        "title": "Control Commands  —  say the whole phrase to trigger",
        "color": "#6A1B9A",
        "rows": [
            ("scratch that",  "Erase the last typed transcription (same as Ctrl+Shift+Z)"),
            ("delete that",   "Erase the last typed transcription"),
            ("undo that",     "Erase the last typed transcription"),
            ("delete last",   "Erase the last typed transcription"),
            ("select all",    "Select all text in the focused window  (Ctrl+A)"),
            ("copy that",     "Copy selected text to clipboard  (Ctrl+C)"),
            ("copy all",      "Copy selected text to clipboard  (Ctrl+C)"),
        ],
    },
    {
        "title": "Punctuation Commands  —  spoken inline while dictating",
        "color": "#2E7D32",
        "rows": [
            ("comma",               ","),
            ("period  /  full stop","." ),
            ("question mark",       "?"),
            ("exclamation mark  /  exclamation point", "!"),
            ("colon",               ":"),
            ("semicolon",           ";"),
            ("new line  /  newline","↵  (line break)"),
            ("new paragraph",       "↵↵  (blank line)"),
            ("tab",                 "→  (tab character)"),
            ("open paren  /  open parenthesis",  "("),
            ("close paren  /  close parenthesis", ")"),
            ("open bracket",        "["),
            ("close bracket",       "]"),
            ("open brace",          "{"),
            ("close brace",         "}"),
            ("dash",                "-"),
            ("em dash",             "—"),
            ("ellipsis",            "…"),
            ("dot",                 "."),
            ("slash",               "/"),
            ("backslash",           "\\"),
            ("at sign",             "@"),
            ("hash",                "#"),
            ("percent  /  percent sign", "%"),
            ("ampersand",           "&"),
            ("asterisk",            "*"),
            ("plus",                "+"),
            ("equals  /  equals sign", "="),
            ("greater than",        ">"),
            ("less than",           "<"),
            ("pipe",                "|"),
            ("tilde",               "~"),
            ("backtick",            "`"),
            ("quote",               '"'),
            ("single quote",        "'"),
        ],
    },
    {
        "title": "Word Substitution  —  custom spoken→typed mappings",
        "color": "#E65100",
        "rows": [
            ("Custom", 'Set up in settings.json under "word_map".\n'
                       'Example:  "dev voice" → "DevVoice",  "open paren" → "("'),
        ],
    },
]


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class HelpDialog(QDialog):
    """Searchable quick-reference dialog for all voice commands and hotkeys."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevVoice — Commands & Hotkeys")
        self.setMinimumWidth(660)
        self.setMinimumHeight(560)
        self.resize(680, 620)
        self._all_rows: list[tuple[QFrame, str]] = []  # (widget, searchable_text)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title = QLabel("Commands & Hotkeys")
        title.setFont(QFont(title.font().family(), 14, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "All available hotkeys and voice commands. "
            "Voice commands work on any transcription — just speak naturally."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(subtitle)

        # Search bar
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search commands…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(14)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        for section in _SECTIONS:
            self._add_section(section)

        self._content_layout.addStretch()
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _add_section(self, section: dict):
        color = section["color"]

        header = QLabel(section["title"])
        header.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: bold; "
            "letter-spacing: 0.4px; padding: 4px 0 0 0;"
        )
        self._content_layout.addWidget(header)

        for phrase, description in section["rows"]:
            card = self._make_row(phrase, description, color)
            searchable = (phrase + " " + description).lower()
            self._all_rows.append((header, card, searchable))
            self._content_layout.addWidget(card)

    def _make_row(self, phrase: str, description: str, accent: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 5px;
            }
        """)
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(16)

        phrase_lbl = QLabel(phrase)
        phrase_lbl.setFont(QFont("Consolas, Courier New, monospace", 10))
        phrase_lbl.setStyleSheet(
            f"background: transparent; color: {accent}; "
            "font-weight: bold; min-width: 200px; max-width: 220px;"
        )
        phrase_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(phrase_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #ddd;")
        row.addWidget(sep)

        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("background: transparent; color: #333; font-size: 11px;")
        row.addWidget(desc_lbl, stretch=1)

        return frame

    def _filter(self, query: str):
        """Show only rows whose searchable text contains the query."""
        q = query.strip().lower()
        # Track which section headers are still visible
        visible_headers: set = set()

        for header, card, text in self._all_rows:
            match = not q or q in text
            card.setVisible(match)
            if match:
                visible_headers.add(id(header))

        # Hide section headers when all their rows are hidden
        for header, card, _ in self._all_rows:
            header.setVisible(id(header) in visible_headers)
