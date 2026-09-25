# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Specification File for WinBatch Video Downloader
Được cấu hình tối ưu để gom CustomTkinter theme assets, font, và các thư viện phụ thuộc.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 1. Thu thập dữ liệu tài nguyên (themes, fonts, icons) của CustomTkinter
customtkinter_datas = collect_data_files('customtkinter')

# Thu thập certificates của certifi/requests nếu cần
requests_datas = collect_data_files('requests')

datas = []
datas += customtkinter_datas
datas += requests_datas

# 2. Thu thập hiddenimports cần thiết để tránh lỗi ModuleNotFoundError khi chạy EXE
hiddenimports = [
    'customtkinter',
    'playwright',
    'playwright.sync_api',
    'yt_dlp',
    'PIL',
    'PIL._tkinter_finder',
    'requests',
    'urllib.parse',
    'concurrent.futures',
    'queue',
]
hiddenimports += collect_submodules('yt_dlp')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Chế độ Thư mục (--onedir - Khuyên dùng cho Playwright & yt-dlp để tối ưu tốc độ khởi động)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WinBatchDownloader',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WinBatchDownloader',
)

