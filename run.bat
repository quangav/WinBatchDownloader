@echo off
chcp 65001 > nul
title Chạy WinBatch Video Downloader (Môi trường Dev)

echo ========================================================
echo   Khởi chạy WinBatch Video Downloader v1.0.0
echo ========================================================

REM Kiểm tra python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python 3.10 hoac 3.11.
    pause
    exit /b
)

REM Kiểm tra venv
if not exist "venv" (
    echo [INFO] Dang khoi tao virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo [INFO] Dang cai dat thu vien tu requirements.txt...
    pip install -r requirements.txt
    playwright install chromium
) else (
    call venv\Scripts\activate
)

echo [INFO] Dang chay main.py...
python main.py

pause
