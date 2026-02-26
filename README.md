# DevVoice

Offline speech-to-text for Windows and macOS. Press a hotkey, speak, and your words are typed wherever your cursor is — no cloud, no subscription.

Powered by [NVIDIA Parakeet](https://huggingface.co/nvidia/parakeet-tdt-1.1b) via NVIDIA NeMo.

---

## Features

- **Fully offline** — transcription runs locally, nothing leaves your machine
- **Global hotkey** — `Ctrl+Shift+R` starts/stops recording from any app
- **Types at cursor** — works in any text field (Notepad, Word, browser, code editors, etc.)
- **Floating control panel** — always-on-top window that never steals focus
- **System tray** — lives quietly in the background
- **Transcription history** — scrollable log of past transcriptions with copy buttons
- **Model switcher** — choose from curated Parakeet variants, any HuggingFace NeMo model, or a local `.nemo` file

---

## Requirements

- Python 3.10–3.12
- NVIDIA GPU with CUDA (recommended) — CPU works but is slow
- ~4 GB disk space for the default model (downloaded once on first run)

---

## Installation

```bash
git clone https://github.com/lambcoder-maker/DevVoice.git
cd DevVoice
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python main.py
```

**macOS:**
```bash
source venv/bin/activate
pip install torch torchaudio
pip install -r requirements.txt
python main.py
```

> On macOS, grant **Accessibility** permission when prompted — required for the global hotkey and keyboard simulation.

---

## Usage

1. Launch the app — a small control panel appears at the top-right of your screen
2. The first launch downloads the Parakeet model (~4 GB, one-time)
3. Click in any text field, then press **Ctrl+Shift+R** to start recording
4. Speak, then press **Ctrl+Shift+R** again to stop — text is typed at your cursor

### Switching models

Right-click the system tray icon → **Change Model…**

| Tab | What it does |
|---|---|
| Recommended | 5 curated Parakeet variants (different sizes/speeds) |
| HuggingFace | Paste any HF model ID — validates it's a NeMo ASR model before allowing selection |
| Local File | Point to a `.nemo` file on your disk |

The selected model is saved to `%APPDATA%/DevVoice/settings.json` (Windows) or `~/Library/Application Support/DevVoice/settings.json` (macOS).

---

## Recommended Models

| Model | Size | Notes |
|---|---|---|
| `nvidia/parakeet-tdt-1.1b` | ~4 GB | Best accuracy — **default** |
| `nvidia/parakeet-tdt-0.6b` | ~2.3 GB | Faster, lower memory |
| `nvidia/parakeet-rnnt-1.1b` | ~4 GB | Alternative architecture |
| `nvidia/parakeet-ctc-1.1b` | ~4 GB | Fastest inference |
| `nvidia/parakeet-ctc-0.6b` | ~2.3 GB | Smallest and fastest |

---

## Roadmap

- [x] Offline transcription with Parakeet 1.1B
- [x] Global hotkey (Ctrl+Shift+R)
- [x] Floating always-on-top control panel
- [x] System tray with status indicator
- [x] Transcription history window
- [x] First-run model download dialog with progress
- [x] Model switcher (curated list, HuggingFace, local file)
- [ ] App icon
- [ ] Configurable hotkey (via settings)
- [ ] Windows `.exe` installer (PyInstaller + MSIX)
- [ ] macOS notarized `.dmg`
- [ ] Auto-start on login

---

## Distribution

This app uses global hotkeys and keyboard simulation (`pynput`), which are blocked by app store sandboxing. Distribution is via direct installer:

- **Windows** — `.exe` / `.msix` installer
- **macOS** — notarized `.dmg` (requires Apple Developer ID, $99/yr)

Build scripts are in [`build/`](build/).

---

## License

MIT
