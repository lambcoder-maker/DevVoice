"""Simulated keyboard output using pynput."""

import time
from pynput.keyboard import Controller, Key


class KeyboardTyper:
    """Types text at the current cursor position."""

    CHAR_DELAY = 0.01  # 10ms delay between characters
    PRE_TYPE_DELAY = 0.15  # Wait for hotkey modifiers to fully release

    def __init__(self):
        self.keyboard = Controller()

    def type_text(self, text: str):
        """Type the given text character by character."""
        if not text:
            return

        # Release any modifier keys still held from the hotkey (Ctrl, Shift, etc.)
        # before typing — otherwise apps like Paint see Ctrl+Shift+<char>
        for key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r,
                    Key.shift, Key.shift_l, Key.shift_r,
                    Key.alt, Key.alt_l, Key.alt_r):
            try:
                self.keyboard.release(key)
            except Exception:
                pass

        time.sleep(self.PRE_TYPE_DELAY)

        for char in text:
            self._type_char(char)
            time.sleep(self.CHAR_DELAY)

    def _type_char(self, char: str):
        """Type a single character, handling special cases."""
        if char == '\n':
            self.keyboard.press(Key.enter)
            self.keyboard.release(Key.enter)
        elif char == '\t':
            self.keyboard.press(Key.tab)
            self.keyboard.release(Key.tab)
        else:
            self.keyboard.type(char)
