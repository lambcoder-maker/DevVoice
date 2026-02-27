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
from ui.model_selector import ModelSelectorDialog
import config
import voice_commands


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
        self.hotkey_manager.undo_last.connect(self.on_undo_last)
        self.system_tray.show_window_requested.connect(self.main_window.show)
        self.system_tray.toggle_recording_requested.connect(self.on_toggle_recording)
        self.system_tray.quit_requested.connect(self.quit)
        self.system_tray.change_model_requested.connect(self.on_change_model)
        self.control_window.toggle_recording.connect(self.on_toggle_recording)

    def start(self):
        """Start the application."""
        self.system_tray.set_status("loading")

        if config.is_first_run() or not self.transcriber.is_model_cached():
            # First run (no settings yet) OR model missing: show setup dialog first
            self._show_setup_dialog()
        else:
            # Returning user with cached model: load in background
            self.control_window.set_loading(self.transcriber.model_id)
            self.control_window.show()
            self._load_model_async()

    def _show_setup_dialog(self):
        """Show model selector on first run or when model is not found."""
        from PyQt6.QtWidgets import QApplication
        dialog = ModelSelectorDialog(
            current_model=self.transcriber.model_id,
            is_first_run=True,
        )
        if dialog.exec() != ModelSelectorDialog.DialogCode.Accepted:
            QApplication.quit()
            return

        new_model = dialog.selected_model
        new_dir = dialog.selected_dir or config.get_model_dir()

        # Persist choices
        config.set_model(new_model)
        config.set_model_dir(new_dir)

        # Update cache dir for this session so downloads go to the right place
        import os
        os.environ["HF_HUB_CACHE"] = new_dir
        os.environ["TRANSFORMERS_CACHE"] = new_dir

        # Recreate transcriber with the chosen model
        self.transcriber = Transcriber(model=new_model)

        if not self.transcriber.is_model_cached():
            # Not downloaded yet — show download progress dialog
            dl = ModelLoadDialog(self.transcriber)
            if not dl.start_loading():
                QApplication.quit()
                return
            self._on_model_ready()
        else:
            # Already on disk — load into memory in background
            self.control_window.set_loading(new_model)
            self.control_window.show()
            self._load_model_async()

    def _load_model_async(self):
        """Load a cached model in a background thread."""
        from ui.model_download import _ModelLoaderThread
        self._loader = _ModelLoaderThread(self.transcriber)
        self._loader.progress.connect(self.control_window.set_loading_status)
        self._loader.finished.connect(self._on_model_ready)
        self._loader.error.connect(self._on_model_error)
        self._loader.start()

    def _on_model_ready(self):
        """Called when model is loaded and ready."""
        print("Model loaded. Ready for transcription.")
        self.system_tray.set_status("idle")
        self.control_window.set_model_info(
            self.transcriber.model_id,
            self.transcriber.backend_name(),
        )
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

    def on_transcription_complete(self, raw_text: str):
        """Handle completed transcription."""
        self.system_tray.set_status("idle")

        if not raw_text:
            print("No speech detected.")
            self.control_window.set_transcription("")
            self.worker = None
            return

        # Run post-processing pipeline: word map → punctuation commands → control actions
        text, action = voice_commands.process(
            raw_text,
            word_map=config.get_word_map(),
            punctuation_enabled=config.get_voice_commands_enabled(),
        )

        self.control_window.set_transcription(text or raw_text)

        if action == 'undo':
            print("Voice command: undo last")
            self.on_undo_last()
        elif action == 'select_all':
            print("Voice command: select all")
            from pynput.keyboard import Controller as KbController, Key
            kb = KbController()
            with kb.pressed(Key.ctrl):
                kb.press('a')
                kb.release('a')
        elif action == 'copy':
            print("Voice command: copy")
            from pynput.keyboard import Controller as KbController, Key
            kb = KbController()
            with kb.pressed(Key.ctrl):
                kb.press('c')
                kb.release('c')
        elif text:
            print(f"Transcribed: {text}")
            self.keyboard_typer.type_text(text)
            self.main_window.add_transcription(text)
            self.control_window.set_typing_complete()

        self.worker = None

    def on_undo_last(self):
        """Erase the last typed transcription block."""
        print("Undo last transcription")
        self.keyboard_typer.undo_last()
        self.control_window.status_label.setText("Undone")
        self.control_window.status_label.setStyleSheet("font-size: 12px; color: #888;")

    def on_change_model(self):
        """Open model selector and reload if user picks a different model."""
        dialog = ModelSelectorDialog(current_model=self.transcriber.model_id)
        if dialog.exec() != ModelSelectorDialog.DialogCode.Accepted:
            return

        new_model = dialog.selected_model
        if not new_model or new_model == self.transcriber.model_id:
            return

        # Persist choices
        config.set_model(new_model)
        new_dir = dialog.selected_dir
        if new_dir:
            config.set_model_dir(new_dir)
            import os
            os.environ["HF_HUB_CACHE"] = new_dir
            os.environ["TRANSFORMERS_CACHE"] = new_dir

        # Stop hotkey while reloading
        self.hotkey_manager.stop()
        self.is_recording = False

        # Replace transcriber with new model
        self.transcriber = Transcriber(model=new_model)

        # Show loading UI and reload
        self.system_tray.set_status("loading")
        self.control_window.set_loading(new_model)

        if not self.transcriber.is_model_cached():
            dialog = ModelLoadDialog(self.transcriber)
            if not dialog.start_loading():
                return
            self._on_model_ready()
        else:
            self._load_model_async()

    def quit(self):
        """Clean shutdown of the application."""
        self.hotkey_manager.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
