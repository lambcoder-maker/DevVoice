# Speech-to-Text

A desktop app for offline speech-to-text using NVIDIA Parakeet. Transcribes your voice and types it directly into any text field.

## Features

- **Offline transcription** - Uses NVIDIA Parakeet model locally, no internet required
- **Global hotkey** - Press `Ctrl+Shift+R` to start/stop recording from anywhere
- **Direct typing** - Transcribed text is typed at your cursor position
- **Floating control window** - Always-on-top window that doesn't steal focus
- **System tray** - Runs quietly in the background
- **Transcription history** - View and copy past transcriptions

## Requirements

- Python 3.10-3.12 (PyTorch doesn't support 3.13+ yet)
- NVIDIA GPU with CUDA support
- ~4GB disk space for the Parakeet model

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/anthropics/speech-to-text.git
   cd speech-to-text
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install PyTorch with CUDA:
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the app:
   ```bash
   python main.py
   ```

2. The floating control window appears. The model loads on first run (~4GB download).

3. To transcribe:
   - Click in any text field where you want text
   - Press `Ctrl+Shift+R` or click "Start Recording"
   - Speak
   - Press `Ctrl+Shift+R` or click "Stop Recording"
   - Text is typed at your cursor

## Roadmap

- [ ] Cross-platform support (macOS, Linux)
- [ ] Configurable hotkeys
- [ ] Multiple language support
- [ ] Smaller model options
- [ ] Auto-start on boot

## License

MIT
