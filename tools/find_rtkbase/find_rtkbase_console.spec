# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['find_rtkbase.py'],
    pathex=[],
    binaries=[],
    datas=[('rtkbase_icon.png', '.') ],
    hiddenimports=[
                    'zeroconf._utils.ipaddress',  # and potentially others in .venv\Lib\site-packages\zeroconf\_utils, but that seems to pull in every pyd file
                    'zeroconf._handlers.answers',  # and potentially others in .venv\Lib\site-packages\zeroconf\_handlers, but that seems to pull in every pyd file
                    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='find_rtkbase',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='find_rtkbase',
)
