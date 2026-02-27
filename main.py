"""Entry point for Speech-to-Text application."""

# Fix Windows DLL loading issues by adding torch lib to DLL search path
import os
import sys

if sys.platform == "win32":
    import importlib.util
    torch_spec = importlib.util.find_spec("torch")
    if torch_spec and torch_spec.origin:
        torch_lib = os.path.join(os.path.dirname(torch_spec.origin), "lib")
        if os.path.isdir(torch_lib):
            os.add_dll_directory(torch_lib)

# Set HuggingFace cache directory from config BEFORE any HF imports
import config as _config
_model_dir = _config.get_model_dir()
os.environ.setdefault("HF_HUB_CACHE", _model_dir)
os.environ.setdefault("TRANSFORMERS_CACHE", _model_dir)

import torch  # noqa: F401
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from app import SpeechToTextApp

_INSTANCE_KEY = "DevVoice-SingleInstance"


def _check_single_instance() -> QLocalServer | None:
    """
    Ensure only one instance runs at a time.

    Returns a live QLocalServer (keep alive!) if this is the first instance,
    or None if another instance is already running (caller should exit).
    """
    # Try to connect to an already-running instance
    probe = QLocalSocket()
    probe.connectToServer(_INSTANCE_KEY)
    if probe.waitForConnected(300):
        probe.disconnectFromServer()
        return None  # Another instance is alive

    # No existing instance — claim the slot
    server = QLocalServer()
    QLocalServer.removeServer(_INSTANCE_KEY)  # Remove stale socket from a previous crash
    server.listen(_INSTANCE_KEY)
    return server


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    server = _check_single_instance()
    if server is None:
        msg = QMessageBox()
        msg.setWindowTitle("DevVoice already running")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("DevVoice is already running.")
        msg.setInformativeText(
            "Only one instance can run at a time.\n"
            "Look for the DevVoice icon in the system tray."
        )
        msg.exec()
        sys.exit(0)

    # Keep server alive for the lifetime of the app so the socket stays open
    app._instance_server = server

    speech_app = SpeechToTextApp()
    speech_app.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
