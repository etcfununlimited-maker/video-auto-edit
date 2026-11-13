"""
AUTO VIDEO EDITOR - Studio Launcher Entrypoint
ANIRBAN AUTOMATIONS • STUDIO PRO v2.4

Handles standalone startup, runtime directory initialization,
automatic web browser launching, and graceful shutdown.
"""
import sys
import os
import time
import threading
import webbrowser
from pathlib import Path

# Support PyInstaller frozen bundle
if getattr(sys, 'frozen', False):
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    APP_ROOT = Path(__file__).resolve().parent

os.chdir(APP_ROOT)
sys.path.insert(0, str(APP_ROOT))

# Ensure required directories exist
for folder in ["raw_input", "final_export", "uploads", "exports"]:
    (APP_ROOT / folder).mkdir(parents=True, exist_ok=True)

def open_browser_delayed(url="http://127.0.0.1:8000", delay=1.5):
    """Waits for the Uvicorn server to bind to port 8000, then opens the browser."""
    time.sleep(delay)
    import urllib.request
    # Wait until server responds
    for _ in range(20):
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.3)
    webbrowser.open(url)

def print_banner():
    banner = r"""
================================================================================
          ANIRBAN AUTOMATIONS  *  AI AUTO VIDEO EDITOR STUDIO
                    STUDIO * PRO v2.4 - DESKTOP EDITION
================================================================================
  [>] AI Neural Engine: ACTIVE (Hinglish/English STT + Two-Pass Retake Arbiter)
  [>] 12-Grid Processing Pipeline: INITIALIZED & READY
  [>] Studio Dashboard: http://127.0.0.1:8000
  [>] Launching your default web browser automatically...

  [*] Quick Tips:
      - Raw clips go into:        .\raw_input\
      - Finished exports save to: .\final_export\
      - To quit, close this window or press Ctrl + C.
================================================================================
"""
    print(banner, flush=True)

def main():
    import multiprocessing
    multiprocessing.freeze_support()

    print_banner()

    # Launch browser in separate thread
    threading.Thread(target=open_browser_delayed, args=("http://127.0.0.1:8000", 1.2), daemon=True).start()

    # Import and run backend app
    import uvicorn
    from backend.main import app

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    main()
