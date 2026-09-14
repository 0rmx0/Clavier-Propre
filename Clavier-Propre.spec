# -*- mode: python ; coding: utf-8 -*-
"""Spécification PyInstaller pour Clavier-Propre.

Génère un exécutable Windows autonome (fenêtré, sans console) en incluant
les imports cachés nécessaires (pywin32, slint n/a ici).

Build (sur Windows, dans le venv) :
    pyinstaller --noconfirm Clavier-Propre.spec
"""

block_cipher = None

a = Analysis(
    ["clavier_propre/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # pywin32 / COM
        "win32com",
        "win32com.client",
        "pythoncom",
        "win32api",
        "pywintypes",
        # winreg est un module built-in sous Windows, pas besoin de l'ajouter.
        # Service Windows (optionnel)
        "win32serviceutil",
        "win32service",
        "servicemanager",
        "win32evtlogutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "test",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Mode fenêtré (GUI) : pas de console.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Clavier-Propre",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,  # GUI : pas de fenêtre console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # ajouter icon="clavier.ico" si disponible
)
