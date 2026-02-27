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


def _default_model_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")


CONFIG_PATH = os.path.join(_config_dir(), "settings.json")

DEFAULTS = {
    "model": "nvidia/parakeet-tdt-1.1b",
    "model_dir": _default_model_dir(),
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


def get_model_dir() -> str:
    return load()["model_dir"]


def set_model_dir(path: str):
    settings = load()
    settings["model_dir"] = path
    save(settings)


def is_first_run() -> bool:
    """True if the user has never completed setup (no settings file exists)."""
    return not os.path.exists(CONFIG_PATH)
