@echo off
title ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR
color 0b

cd /d "%~dp0"

set PYTHON_EXE=C:\Users\bhupp\AppData\Local\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

"%PYTHON_EXE%" launcher.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Launcher exited with code %errorlevel%. Press any key to exit.
    pause >nul
)
