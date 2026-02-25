"""Entry point for Speech-to-Text application."""

# Fix Windows DLL loading issues by adding torch lib to DLL search path
import os
import sys

if sys.platform == "win32":
    # Find torch installation and add its lib directory to DLL search path
    import importlib.util
    torch_spec = importlib.util.find_spec("torch")
    if torch_spec and torch_spec.origin:
        torch_lib = os.path.join(os.path.dirname(torch_spec.origin), "lib")
        if os.path.isdir(torch_lib):
            os.add_dll_directory(torch_lib)

import torch  # noqa: F401
from PyQt6.QtWidgets import QApplication
from app import SpeechToTextApp


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    speech_app = SpeechToTextApp()
    speech_app.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
