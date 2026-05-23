# -*- mode: python ; coding: utf-8 -*-
import os
import opencc
import customtkinter

block_cipher = None

# 取得 opencc 與 customtkinter 模組安裝路徑
opencc_dir = os.path.dirname(opencc.__file__)
ctk_dir = os.path.dirname(customtkinter.__file__)

# 定義要打包的靜態資料 (專案本地 fonts, opencc 內建字典, customtkinter 主題配置)
datas = [
    ('..\\fonts', 'fonts'),
    (opencc_dir, 'opencc'),
    (ctk_dir, 'customtkinter'),
]

a = Analysis(
    ['..\\main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'fitz',
        'opencc',
        'openai',
        'deepl',
        'PIL',
        'requests',
        'dotenv',
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
    name='TramsLay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # 設為 False 隱藏黑色的命令提示字元視窗
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
    name='TramsLay',
)
