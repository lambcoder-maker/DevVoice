"""NeMo ASR model loading and inference.

Supports:
  - HuggingFace model IDs  e.g. "nvidia/parakeet-tdt-1.1b"
  - Local .nemo file paths e.g. "C:/models/my_model.nemo"
"""

import os
import numpy as np
import torch
from typing import Optional


class Transcriber:
    """Handles speech-to-text using a NeMo ASR model."""

    DEFAULT_MODEL = "nvidia/parakeet-tdt-1.1b"
    _HF_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

    def __init__(self, model: str = None):
        """
        Args:
            model: HuggingFace model ID (e.g. "nvidia/parakeet-tdt-1.1b")
                   or absolute path to a local .nemo file.
                   Defaults to config value, then DEFAULT_MODEL.
        """
        if model is None:
            try:
                import config
                model = config.get_model()
            except Exception:
                model = self.DEFAULT_MODEL

        self.model_id = model          # HF ID or local path
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cpu":
            print("WARNING: CUDA not available. Transcription will be slow.")

    def is_local_path(self) -> bool:
        """Return True if model_id points to a local file."""
        return os.path.isfile(self.model_id)

    def is_model_cached(self) -> bool:
        """Return True if the model is available without a download."""
        if self.is_local_path():
            return True  # already on disk
        model_dir = os.path.join(
            self._HF_CACHE,
            "models--" + self.model_id.replace("/", "--")
        )
        return os.path.isdir(model_dir)

    def load_model(self):
        """Load the model — from local path or HuggingFace."""
        import nemo.collections.asr as nemo_asr

        if self.is_local_path():
            self.model = nemo_asr.models.ASRModel.restore_from(
                restore_path=self.model_id
            )
        else:
            self.model = nemo_asr.models.ASRModel.from_pretrained(
                model_name=self.model_id
            )

        self.model = self.model.to(self.device)
        self.model.eval()

        warmup_audio = np.zeros(16000, dtype=np.float32)
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
