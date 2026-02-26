"""Main application class coordinating all components."""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from hotkey_manager import HotkeyManager
from keyboard_typer import KeyboardTyper
from ui.system_tray import SystemTray
from ui.main_window import MainWindow
from ui.control_window import ControlWindow
from ui.model_download import ModelLoadDialog


class TranscriptionWorker(QThread):
    """Worker thread for transcription to avoid blocking UI."""
    finished = pyqtSignal(str)

    def __init__(self, transcriber, audio_data):
        super().__init__()
        self.transcriber = transcriber
        self.audio_data = audio_data

    def run(self):
        text = self.transcriber.transcribe(self.audio_data)
        self.finished.emit(text)


class SpeechToTextApp(QObject):
    """Main application orchestrating all components."""

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.worker = None

        # Initialize components
        self.transcriber = Transcriber()
        self.audio_recorder = AudioRecorder()
        self.hotkey_manager = HotkeyManager()
        self.keyboard_typer = KeyboardTyper()

        # Initialize UI
        self.main_window = MainWindow()
        self.system_tray = SystemTray()
        self.control_window = ControlWindow()

        # Connect signals
        self.hotkey_manager.toggle_recording.connect(self.on_toggle_recording)
        self.system_tray.show_window_requested.connect(self.main_window.show)
        self.system_tray.toggle_recording_requested.connect(self.on_toggle_recording)
        self.system_tray.quit_requested.connect(self.quit)
        self.control_window.toggle_recording.connect(self.on_toggle_recording)

    def start(self):
        """Start the application, downloading the model on first run if needed."""
        self.system_tray.set_status("loading")

        if not self.transcriber.is_model_cached():
            # First run: show download + load dialog (blocks until done or cancelled)
            dialog = ModelLoadDialog(self.transcriber)
            if not dialog.start_loading():
                from PyQt6.QtWidgets import QApplication
                QApplication.quit()
                return
        else:
            # Model is cached: load in background, show control window as "loading"
            self.control_window.set_loading()
            self.control_window.show()
            self._load_model_async()
            return

        self._on_model_ready()

    def _load_model_async(self):
        """Load a cached model in a background thread."""
        from ui.model_download import _ModelLoaderThread
        self._loader = _ModelLoaderThread(self.transcriber)
        self._loader.finished.connect(self._on_model_ready)
        self._loader.error.connect(self._on_model_error)
        self._loader.start()

    def _on_model_ready(self):
        """Called when model is loaded and ready."""
        print("Model loaded. Ready for transcription.")
        self.system_tray.set_status("idle")
        self.control_window.set_ready()
        self.control_window.show()
        self.system_tray.show()
        self.hotkey_manager.start()

    def _on_model_error(self, message: str):
        """Called if model loading fails after caching."""
        print(f"Model load error: {message}")
        self.control_window.set_loading()  # leave disabled state visible
        self.system_tray.set_status("loading")

    def on_toggle_recording(self):
        """Handle hotkey toggle for recording."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start audio recording."""
        self.is_recording = True
        self.system_tray.set_status("recording")
        self.control_window.set_recording(True)
        self.audio_recorder.start()
        print("Recording started...")

    def stop_recording(self):
        """Stop recording and start transcription."""
        self.is_recording = False
        audio_data = self.audio_recorder.stop()

        if audio_data is None or len(audio_data) == 0:
            print("No audio recorded.")
            self.system_tray.set_status("idle")
            self.control_window.set_recording(False)
            return

        print("Processing audio...")
        self.system_tray.set_status("processing")
        self.control_window.set_processing()

        # Run transcription in background thread
        self.worker = TranscriptionWorker(self.transcriber, audio_data)
        self.worker.finished.connect(self.on_transcription_complete)
        self.worker.start()

    def on_transcription_complete(self, text: str):
        """Handle completed transcription."""
        self.system_tray.set_status("idle")
        self.control_window.set_transcription(text)

        if text:
            print(f"Transcribed: {text}")
            self.keyboard_typer.type_text(text)
            self.main_window.add_transcription(text)
            self.control_window.set_typing_complete()
        else:
            print("No speech detected.")

        self.worker = None

    def quit(self):
        """Clean shutdown of the application."""
        self.hotkey_manager.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
