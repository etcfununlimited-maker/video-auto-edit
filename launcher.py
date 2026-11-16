"""
ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR
Desktop Studio Launcher (v2.6.1)

Handles instant one-click launch:
- Automatically detects if the server is already running on port 8000.
- If already running, immediately opens the browser dashboard.
- If not running, launches the Uvicorn backend and opens the browser.
- Displays live logs and rendering progress.
"""

import sys
import os
import time
import socket
import subprocess
import threading
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)

PORT = 8000
DASHBOARD_URL = f"http://localhost:{PORT}"

def is_server_running(port: int = PORT) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def open_browser_when_ready():
    for _ in range(40):
        time.sleep(0.4)
        if is_server_running(PORT):
            print(f"[+] Server ready! Opening dashboard: {DASHBOARD_URL}")
            webbrowser.open(DASHBOARD_URL)
            return
    print("[!] Warning: Server did not respond within 16s. Please check logs.")

def main():
    print("=" * 75)
    print("            ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR")
    print("                 Professional Desktop Video Suite v2.6.1")
    print("=" * 75)
    print()

    if is_server_running(PORT):
        print(f"[+] Studio Server is already active and running on {DASHBOARD_URL}!")
        print("[+] Opening dashboard in your default browser...")
        webbrowser.open(DASHBOARD_URL)
        print()
        print("Done! You may keep or close this launcher window.")
        time.sleep(3)
        return

    print(f"[1/2] Starting Studio Server on 127.0.0.1:{PORT}...")
    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", str(PORT)
    ]

    print("[2/2] Backend initializing... Press Ctrl+C to stop.")
    print()
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[+] Studio Server stopped.")

if __name__ == "__main__":
    main()
