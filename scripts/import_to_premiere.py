"""
AUTOMATED PREMIERE PRO XML & SRT IMPORTER
=========================================
Imports Final Cut Pro XML sequences and SRT subtitles directly into the running
Adobe Premiere Pro (2024 / 2025 / 2026) project using native Windows Automation.

Usage:
    python scripts/import_to_premiere.py
    python scripts/import_to_premiere.py "path/to/project.xml" "path/to/captions.srt"
"""

import sys
import os
import time
import ctypes
from ctypes import wintypes
from pathlib import Path

# Windows API constants
GENERIC_ALL = 0x10000000
SW_RESTORE = 9
SW_SHOW = 5
WM_SETTEXT = 0x000C
WM_COMMAND = 0x0111
BM_CLICK = 0x00F5
VK_CONTROL = 0x11
VK_I = 0x49
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def attach_to_desktop():
    """Attaches current thread to interactive desktop WinSta0\\Default"""
    try:
        hwinsta = user32.OpenWindowStationW("WinSta0", False, GENERIC_ALL)
        if hwinsta:
            user32.SetProcessWindowStation(hwinsta)
            hdesk = user32.OpenDesktopW("Default", 0, False, GENERIC_ALL)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
                return True
    except Exception as e:
        print(f"[!] Warning attaching to desktop: {e}")
    return False

def find_premiere_window():
    """Finds the main window handle of running Adobe Premiere Pro"""
    target_hwnd = None
    target_title = None

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def enum_cb(hwnd, lp):
        nonlocal target_hwnd, target_title
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0 and user32.IsWindowVisible(hwnd):
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            val = buff.value
            if "Adobe Premiere Pro" in val and "GDI+" not in val:
                target_hwnd = hwnd
                target_title = val
                return False  # stop
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return target_hwnd, target_title

def find_import_dialog(timeout_sec=4.0):
    """Waits for and returns the #32770 Import dialog handle"""
    dlg_hwnd = None
    start_time = time.time()
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    while time.time() - start_time < timeout_sec:
        def dlg_cb(hwnd, lp):
            nonlocal dlg_hwnd
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            if cls_buff.value == "#32770":
                t_len = user32.GetWindowTextLengthW(hwnd)
                t_buff = ctypes.create_unicode_buffer(t_len + 1)
                user32.GetWindowTextW(hwnd, t_buff, t_len + 1)
                if t_buff.value == "Import":
                    dlg_hwnd = hwnd
                    return False
            return True

        user32.EnumWindows(WNDENUMPROC(dlg_cb), 0)
        if dlg_hwnd:
            return dlg_hwnd
        time.sleep(0.1)
    return None

def dismiss_translation_reports(timeout_sec=3.0):
    """Dismisses standard Translation Report notifications from Premiere Pro"""
    start_time = time.time()
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    while time.time() - start_time < timeout_sec:
        report_hwnd = None
        def report_cb(hwnd, lp):
            nonlocal report_hwnd
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            if cls_buff.value == "#32770":
                t_len = user32.GetWindowTextLengthW(hwnd)
                t_buff = ctypes.create_unicode_buffer(t_len + 1)
                user32.GetWindowTextW(hwnd, t_buff, t_len + 1)
                if "translation report" in t_buff.value.lower():
                    report_hwnd = hwnd
                    return False
            return True

        user32.EnumWindows(WNDENUMPROC(report_cb), 0)
        if report_hwnd:
            def btn_cb(hwnd, lp):
                cls_b = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_b, 256)
                if cls_b.value == "Button":
                    cid = user32.GetDlgCtrlID(hwnd)
                    if cid in [1, 2]:  # OK or Cancel
                        user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
                return True
            user32.EnumChildWindows(report_hwnd, WNDENUMPROC(btn_cb), 0)
            user32.SendMessageW(report_hwnd, WM_COMMAND, 1, 0)
            user32.SendMessageW(report_hwnd, WM_COMMAND, 2, 0)
            time.sleep(0.5)
            break
        time.sleep(0.2)

def import_single_file(file_path: str) -> bool:
    """Imports a single media or XML/SRT file into Premiere Pro via native Ctrl+I dialog"""
    p = Path(file_path).resolve()
    if not p.exists():
        print(f"❌ File not found: {p}")
        return False

    prem_hwnd, prem_title = find_premiere_window()
    if not prem_hwnd:
        print("❌ Adobe Premiere Pro is not currently running!")
        return False

    print(f"\n🎬 Focusing Premiere Pro: '{prem_title}'")
    user32.ShowWindow(prem_hwnd, SW_RESTORE)
    user32.SetForegroundWindow(prem_hwnd)
    time.sleep(0.4)

    print(f"⌨️  Sending Ctrl+I (Import Shortcut) for {p.name}...")
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_I, 0, 0, 0)
    user32.keybd_event(VK_I, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    dlg_hwnd = find_import_dialog(timeout_sec=4.0)
    if not dlg_hwnd:
        print("⚠️  Import dialog did not respond in time.")
        return False

    print(f"📁 Import Dialog active (HWND: {dlg_hwnd})")

    # Find Edit box (ID 1148) and Open Button (ID 1)
    edit_hwnd = None
    open_btn_hwnd = None
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def find_ctrls(hwnd, lp):
        nonlocal edit_hwnd, open_btn_hwnd
        cid = user32.GetDlgCtrlID(hwnd)
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        if cid == 1148 and cls_buff.value == "Edit":
            edit_hwnd = hwnd
        elif cid == 1 and cls_buff.value == "Button":
            open_btn_hwnd = hwnd
        return True

    user32.EnumChildWindows(dlg_hwnd, WNDENUMPROC(find_ctrls), 0)
    if not edit_hwnd or not open_btn_hwnd:
        print("⚠️  Could not locate dialog input controls.")
        return False

    print(f"📝 Submitting file path: \"{str(p)}\"")
    user32.SendMessageW(edit_hwnd, WM_SETTEXT, 0, f'"{p}"')
    time.sleep(0.3)
    user32.SendMessageW(open_btn_hwnd, BM_CLICK, 0, 0)
    time.sleep(1.0)

    # Automatically dismiss any translation report dialogs
    dismiss_translation_reports(timeout_sec=2.5)
    print(f"✅ Successfully imported: {p.name}")
    return True

def main():
    print("=" * 65)
    print("🚀 AUTOMATED ADOBE PREMIERE PRO XML & SRT IMPORTER")
    print("=" * 65)

    attach_to_desktop()

    prem_hwnd, prem_title = find_premiere_window()
    if not prem_hwnd:
        print("❌ Adobe Premiere Pro is not currently running.")
        print("Please launch Premiere Pro with your active project and run this script again.")
        sys.exit(1)

    print(f"✓ Detected Active Application: {prem_title}")

    # Determine files to import
    if len(sys.argv) > 1:
        files = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent / "final_export"
        else:
            base_dir = Path(__file__).resolve().parent.parent / "final_export"
        files = [
            base_dir / "PREMIERE_PRO_PROJECT.xml",
            base_dir / "CAPTIONS.srt"
        ]

    success_count = 0
    for f in files:
        if f.exists():
            if import_single_file(str(f)):
                success_count += 1
                time.sleep(1.2)  # breathing room between imports
        else:
            print(f"⚠️  Skipping missing file: {f}")

    print("\n" + "=" * 65)
    if success_count > 0:
        print(f"🎉 IMPORT COMPLETE: {success_count} file(s) imported into Premiere Pro!")
        print("Check your Premiere Pro Project Bin for:")
        print("  1. 'Anirban_Premiere_Master_Sequence' (Multi-Track 10-Clip Edit)")
        print("  2. 'CAPTIONS.srt' (Synchronized Subtitle Track)")
    else:
        print("❌ No files were imported.")
    print("=" * 65)

if __name__ == "__main__":
    main()
