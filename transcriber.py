"""Parakeet model loading and inference."""

import os
import numpy as np
import torch
from typing import Optional


class Transcriber:
    """Handles speech-to-text using NVIDIA Parakeet model."""

    MODEL_NAME = "nvidia/parakeet-tdt-1.1b"
    # NeMo caches downloaded models here
    _NEMO_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "torch", "NeMo")

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cpu":
            print("WARNING: CUDA not available. Transcription will be slow.")

    def is_model_cached(self) -> bool:
        """Return True if the model has already been downloaded."""
        if not os.path.isdir(self._NEMO_CACHE):
            return False
        model_slug = self.MODEL_NAME.replace("/", "--")
        for entry in os.listdir(self._NEMO_CACHE):
            if model_slug in entry and entry.endswith(".nemo"):
                return True
        return False

    def load_model(self):
        """Load the Parakeet model from NeMo."""
        import nemo.collections.asr as nemo_asr

        self.model = nemo_asr.models.ASRModel.from_pretrained(
            model_name=self.MODEL_NAME
        )
        self.model = self.model.to(self.device)
        self.model.eval()

        # Warm up the model with a short silent audio
        warmup_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        self._transcribe_audio(warmup_audio)

    def _transcribe_audio(self, audio: np.ndarray) -> str:
        """Internal transcription method."""
        with torch.no_grad():
            # NeMo expects audio as a list of numpy arrays or file paths
            transcriptions = self.model.transcribe([audio])

            if transcriptions and len(transcriptions) > 0:
                # Handle different return formats
                result = transcriptions[0]
                if hasattr(result, 'text'):
                    return result.text
                return str(result)

            return ""

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio numpy array to text."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if audio is None or len(audio) == 0:
            return ""

        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize audio if needed
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val

        return self._transcribe_audio(audio)
