# PyInstaller spec for macOS (.app / notarized DMG)
# Usage: pyinstaller build/speech-to-text-mac.spec

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # repo root

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'venv/lib/python3.*/site-packages/PyQt6/Qt6/plugins/platforms'), 'PyQt6/Qt6/plugins/platforms'),
    ],
    hiddenimports=[
        'PyQt6.sip',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'nemo',
        'nemo.collections.asr',
        'nemo.collections.asr.models',
        'pytorch_lightning',
        'omegaconf',
        'hydra',
    ],
    hookspath=[str(ROOT / 'build/hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'nemo.collections.nlp',
        'nemo.collections.tts',
        'nemo.collections.vision',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SpeechToText',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # upx can break macOS code signing
    console=False,
    argv_emulation=True,  # macOS: handle Apple Events
    target_arch=None,   # Set to 'universal2' for M1+Intel fat binary
    codesign_identity=None,   # Set to your Developer ID for notarization
    entitlements_file=str(ROOT / 'build/entitlements.plist'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SpeechToText',
)

app = BUNDLE(
    coll,
    name='SpeechToText.app',
    # icon='build/assets/icon.icns',  # Uncomment when icon is added
    bundle_identifier='com.yourname.speechtotext',
    version='1.0.0',
    info_plist={
        'NSMicrophoneUsageDescription': 'Speech-to-Text needs microphone access to record audio for transcription.',
        'NSAppleEventsUsageDescription': 'Speech-to-Text uses Apple Events for keyboard simulation.',
        # The accessibility key is set at runtime; users will be prompted by macOS
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,   # Hide from Dock (menu bar / tray app)
    },
)
