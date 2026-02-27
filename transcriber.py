"""ASR model loading and inference.

Supports two backends:
  NeMo         — NVIDIA Parakeet and other NeMo-format models
                 (.nemo local files or "nvidia/parakeet-*" HuggingFace IDs)
  Transformers — any other HuggingFace ASR model
                 (Whisper, wav2vec2, etc.)
"""

import os
import numpy as np
import torch


# HuggingFace model ID prefixes that require the NeMo backend
_NEMO_PREFIXES = (
    "nvidia/parakeet",
    "nvidia/stt_",
    "nvidia/conformer",
    "nvidia/citrinet",
)


class Transcriber:
    """Handles speech-to-text using NeMo or HuggingFace Transformers."""

    DEFAULT_MODEL = "nvidia/parakeet-tdt-1.1b"
    _DEFAULT_HF_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

    @property
    def _hf_cache(self) -> str:
        """Cache directory — respects HF_HUB_CACHE env var set from user config."""
        return os.environ.get("HF_HUB_CACHE", self._DEFAULT_HF_CACHE)

    def __init__(self, model: str = None):
        """
        Args:
            model: HuggingFace model ID (e.g. "nvidia/parakeet-tdt-1.1b",
                   "openai/whisper-large-v3") or absolute path to a .nemo file.
                   Defaults to config value, then DEFAULT_MODEL.
        """
        if model is None:
            try:
                import config
                model = config.get_model()
            except Exception:
                model = self.DEFAULT_MODEL

        self.model_id = model
        self.model = None   # NeMo model (if NeMo backend)
        self._pipe = None   # transformers pipeline (if transformers backend)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cpu":
            print("WARNING: CUDA not available. Transcription will be slow.")

    # ------------------------------------------------------------------
    # Backend detection
    # ------------------------------------------------------------------

    def is_local_path(self) -> bool:
        """Return True if model_id points to a local file or directory."""
        return os.path.isfile(self.model_id) or os.path.isdir(self.model_id)

    def uses_nemo(self) -> bool:
        """Return True if this model uses the NeMo backend."""
        if os.path.isfile(self.model_id):
            return self.model_id.endswith(".nemo")
        if os.path.isdir(self.model_id):
            return False  # local model folders use the Transformers backend
        return any(self.model_id.startswith(p) for p in _NEMO_PREFIXES)

    def backend_name(self) -> str:
        """Human-readable backend label."""
        return "NeMo" if self.uses_nemo() else "Transformers"

    # ------------------------------------------------------------------
    # Cache detection
    # ------------------------------------------------------------------

    def is_model_cached(self) -> bool:
        """Return True if the model is available without a download."""
        if self.is_local_path():
            return True
        model_dir = os.path.join(
            self._hf_cache,
            "models--" + self.model_id.replace("/", "--"),
        )
        return os.path.isdir(model_dir)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_model(self):
        """Load the model using the appropriate backend."""
        if self.uses_nemo():
            self._load_nemo()
        else:
            self._load_transformers()

    def _load_nemo(self):
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

        # Warmup pass so first real transcription isn't slow
        self._transcribe_audio(np.zeros(16000, dtype=np.float32))

    def _load_transformers(self):
        from transformers import pipeline as hf_pipeline

        device_arg = 0 if self.device == "cuda" else -1
        self._pipe = hf_pipeline(
            "automatic-speech-recognition",
            model=self.model_id,
            device=device_arg,
        )

        # Warmup
        self._transcribe_audio(np.zeros(16000, dtype=np.float32))

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _transcribe_audio(self, audio: np.ndarray) -> str:
        if self._pipe is not None:
            result = self._pipe({"array": audio, "sampling_rate": 16000})
            return result.get("text", "").strip()

        # NeMo path
        with torch.no_grad():
            transcriptions = self.model.transcribe([audio])
            if transcriptions and len(transcriptions) > 0:
                result = transcriptions[0]
                if hasattr(result, "text"):
                    return result.text
                return str(result)
        return ""

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a float32 numpy audio array (16 kHz mono) to text."""
        if self.model is None and self._pipe is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if audio is None or len(audio) == 0:
            return ""

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val

        return self._transcribe_audio(audio)
