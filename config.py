"""Persistent user settings stored in %APPDATA%/DevVoice/settings.json."""

import json
import os
import sys


def _config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "DevVoice")


CONFIG_PATH = os.path.join(_config_dir(), "settings.json")

DEFAULTS = {
    "model": "nvidia/parakeet-tdt-1.1b",  # HuggingFace model ID or local path
}


def load() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return {**DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(settings: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def get_model() -> str:
    return load()["model"]


def set_model(model: str):
    settings = load()
    settings["model"] = model
    save(settings)
