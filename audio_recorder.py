"""Audio capture using sounddevice."""

import numpy as np
import sounddevice as sd
from typing import Optional


class AudioRecorder:
    """Records audio from the default microphone."""

    SAMPLE_RATE = 16000  # Parakeet requires 16kHz
    CHANNELS = 1

    def __init__(self):
        self.recording = False
        self.audio_chunks: list[np.ndarray] = []
        self.stream: Optional[sd.InputStream] = None

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        if self.recording:
            self.audio_chunks.append(indata.copy())

    def start(self):
        """Start recording audio."""
        self.audio_chunks = []
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=np.float32,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self) -> Optional[np.ndarray]:
        """Stop recording and return the audio data."""
        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.audio_chunks:
            return None

        # Concatenate all chunks and flatten to 1D
        audio_data = np.concatenate(self.audio_chunks, axis=0)
        audio_data = audio_data.flatten()

        return audio_data
