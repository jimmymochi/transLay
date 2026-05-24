# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

block_cipher = None
ctk_dir = os.path.dirname(customtkinter.__file__)

# 收集 CustomTkinter 的樣式設定
datas = [
    (ctk_dir, 'customtkinter'),
]

a = Analysis(
    ['../launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'requests',
        'urllib3',
        'darkdetect',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'fitz',
        'opencc',
        'openai',
        'deepl',
        'PIL',
        'tqdm',
        'pytest',
    ], # 排除重度依賴庫，使啟動下載器體積維持在極致輕量 (3~4MB)
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
    name='TramsLay_Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='TramsLay_Launcher',
)

app = BUNDLE(
    coll,
    name='TramsLay_Launcher.app',
    icon='icon.icns',
    bundle_identifier='com.tramslay.launcher',
)
