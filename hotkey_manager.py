"""Global hotkey handling using pynput."""

from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyManager(QObject):
    """Manages global hotkeys for the application."""

    toggle_recording = pyqtSignal()
    undo_last = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.listener = None
        self.hotkey_listener = None
        self.release_listener = None
        self._hotkey_pressed = False

    def _on_activate(self):
        """Called when hotkey is pressed."""
        # Prevent multiple triggers
        if not self._hotkey_pressed:
            self._hotkey_pressed = True
            self.toggle_recording.emit()

    def _on_release_any(self, key):
        """Reset hotkey state when any key is released."""
        # Reset the flag when Ctrl or Shift is released
        try:
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                      keyboard.Key.shift_l, keyboard.Key.shift_r):
                self._hotkey_pressed = False
        except:
            pass

    def _on_undo(self):
        self.undo_last.emit()

    def start(self):
        """Start listening for hotkeys."""
        # Use GlobalHotKeys for reliable hotkey detection
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+r': self._on_activate,
            '<ctrl>+<shift>+R': self._on_activate,
            '<ctrl>+<shift>+z': self._on_undo,
            '<ctrl>+<shift>+Z': self._on_undo,
        })
        self.hotkey_listener.start()

        # Also listen for key releases to reset state
        self.release_listener = keyboard.Listener(on_release=self._on_release_any)
        self.release_listener.start()

    def stop(self):
        """Stop listening for hotkeys."""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        if self.release_listener:
            self.release_listener.stop()
            self.release_listener = None
