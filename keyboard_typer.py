"""Simulated keyboard output using pynput."""

import time
from pynput.keyboard import Controller, Key


class KeyboardTyper:
    """Types text at the current cursor position."""

    CHAR_DELAY = 0.01  # 10ms delay between characters

    def __init__(self):
        self.keyboard = Controller()

    def type_text(self, text: str):
        """Type the given text character by character."""
        if not text:
            return

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
