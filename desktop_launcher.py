"""
ANIRBAN AUTOMATIONS - Desktop Application Launcher
Starts the Uvicorn server and automatically launches the user's default browser.
"""
import os
import sys
import webbrowser
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable

def main():
    print("=" * 65)
    print("      ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR")
    print("=" * 65)
    print("\nStarting local server on http://localhost:8000 ...")

    # Start Uvicorn process
    server_process = subprocess.Popen([
        PYTHON_EXE,
        "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ], cwd=str(BASE_DIR))

    # Wait for server to bind
    time.sleep(2)
    print("Opening dashboard in browser...")
    webbrowser.open("http://localhost:8000")

    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping Auto Video Editor...")
        server_process.terminate()

if __name__ == "__main__":
    main()
