@echo off
title ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR
color 0b

echo =========================================================================
echo             ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR
echo                  Professional Desktop Video Suite
echo =========================================================================
echo.

cd /d "%~dp0"

set PYTHON_EXE=C:\Users\bhupp\AppData\Local\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [1/3] Checking environment & dependencies...
"%PYTHON_EXE%" -c "import fastapi, uvicorn, imageio_ffmpeg, faster_whisper, cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing required Python packages...
    "%PYTHON_EXE%" -m pip install fastapi uvicorn python-multipart websockets numpy opencv-python-headless pillow imageio-ffmpeg scipy faster-whisper
)

echo [2/3] Checking Sample Media in raw_input...
"%PYTHON_EXE%" -c "from backend.create_sample_media import generate_demo_video; generate_demo_video()" >nul 2>&1

echo [3/3] Launching Studio Backend & Opening Browser Dashboard...
echo.
echo Dashboard URL: http://localhost:8000
echo.

start "" "http://localhost:8000"

"%PYTHON_EXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
