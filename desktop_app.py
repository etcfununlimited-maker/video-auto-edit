"""
ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR
Windows Native Desktop Application Suite (v3.1.0)

Features:
- Native Windows Desktop Window (Powered by Edge Chromium WebView2 / pywebview)
- Automatic background Uvicorn server management
- Zero terminal clutter - standalone native window
- Embedded high-res app icon & window controls
- Fallback to default browser if native windowing cannot initialize
"""

import sys
import os
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

PORT = 8000
URL = f"http://127.0.0.1:{PORT}"
ICON_PATH = str(BASE_DIR / "app_icon.ico")

def is_server_ready(port: int = PORT) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def start_server_thread():
    """Runs Uvicorn in a dedicated thread."""
    try:
        import uvicorn
        from backend.main import app
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
    except Exception as e:
        print(f"[!] Server thread error: {e}")

def ensure_server_running():
    if not is_server_ready(PORT):
        print(f"[+] Starting backend server on {URL}...")
        t = threading.Thread(target=start_server_thread, daemon=True)
        t.start()
        for _ in range(50):
            if is_server_ready(PORT):
                print("[+] Backend server online and ready!")
                return True
            time.sleep(0.2)
        print("[!] Backend server timed out.")
        return False
    return True

def launch_native_window():
    """Launches the native Windows Desktop Window using pywebview."""
    try:
        import webview
        ensure_server_running()

        window = webview.create_window(
            title="ANIRBAN AUTOMATIONS | AI AUTO VIDEO EDITOR STUDIO",
            url=URL,
            width=1440,
            height=900,
            min_size=(1024, 700),
            background_color="#0b1120",
            text_select=True,
            zoomable=True
        )

        icon_file = ICON_PATH if os.path.exists(ICON_PATH) else None
        webview.start(icon=icon_file)
        return True
    except Exception as e:
        print(f"[!] Native window launch notice: {e}")
        return False

def main():
    print("=" * 65)
    print("      ANIRBAN AUTOMATIONS - AI AUTO VIDEO EDITOR (PRO v3.1.0)")
    print("=" * 65)

    success = launch_native_window()
    if not success:
        print("[+] Falling back to default browser...")
        ensure_server_running()
        webbrowser.open(URL)

if __name__ == "__main__":
    main()
