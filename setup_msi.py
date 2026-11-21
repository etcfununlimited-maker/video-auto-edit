import sys
from pathlib import Path
from cx_Freeze import setup, Executable

BASE_DIR = Path(__file__).resolve().parent

# Executable configuration
executables = [
    Executable(
        script="desktop_app.py",
        base="gui",
        icon="app_icon.ico",
        target_name="AnirbanAutoVideoEditor.exe",
        shortcut_name="Anirban Auto Video Editor Studio",
        shortcut_dir="DesktopFolder"
    )
]

# Files and folders to include
include_files = [
    ("backend", "backend"),
    ("frontend", "frontend"),
    ("app_icon.ico", "app_icon.ico")
]

build_exe_options = {
    "packages": [
        "fastapi",
        "uvicorn",
        "starlette",
        "pydantic",
        "cv2",
        "numpy",
        "webview",
        "imageio_ffmpeg"
    ],
    "include_files": include_files,
    "excludes": ["tkinter", "unittest", "test", "pydoc"]
}

# MSI Configuration
bdist_msi_options = {
    "add_to_path": True,
    "initial_target_dir": r"[LocalAppDataFolder]\Anirban Automations\Auto Video Editor",
    "install_icon": "app_icon.ico",
    "all_users": False,
    "product_name": "Anirban Auto Video Editor Studio",
    "upgrade_code": "{A7D5E8B1-3E2A-4C5D-8F9E-1A2B3C4D5E6F}",
    "summary_data": {
        "author": "Anirban Automations",
        "comments": "AI Auto Video Editor Studio PRO v3.0.0",
        "keywords": "video, editor, ai, studio, hsrp, blur"
    }
}

setup(
    name="AnirbanAutoVideoEditor",
    version="3.0.0",
    author="Anirban Automations",
    description="Anirban Automations AI Auto Video Editor Studio PRO v3.0.0",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=executables
)
