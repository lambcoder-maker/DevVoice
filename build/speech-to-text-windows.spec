# PyInstaller spec for Windows (.exe / MSIX)
# Usage: pyinstaller build/speech-to-text-windows.spec

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # repo root

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Qt platform plugins
        (str(ROOT / 'venv/Lib/site-packages/PyQt6/Qt6/plugins/platforms'), 'PyQt6/Qt6/plugins/platforms'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.sip',
        # pynput
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        # NeMo / torch
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
        # Keep the bundle smaller by excluding unused NeMo sub-collections
        'nemo.collections.nlp',
        'nemo.collections.tts',
        'nemo.collections.vision',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    upx=True,
    console=False,       # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='build/assets/icon.ico',  # Uncomment when icon is added
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SpeechToText',
)
