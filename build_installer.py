"""
Build Script for Auto Video Editor Windows Executables and Installer
ANIRBAN AUTOMATIONS • STUDIO PRO v2.4

Generates:
1. app_icon.ico (Multi-resolution Windows application icon)
2. app_bundle.zip (Distribution package containing backend, frontend, scripts)
3. AutoVideoEditor.exe (Fast, native Windows launcher with embedded icon & manifest)
4. AutoVideoEditor_Setup.exe (Standalone Windows GUI Setup Wizard with embedded bundle)
"""
import subprocess
import os
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
CSC_COMPILER = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

def build_icon():
    print("[1/4] Generating high-resolution app_icon.ico...")
    icon_path = BASE_DIR / "app_icon.ico"
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, 248, 248], radius=56, fill=(15, 23, 42, 255), outline=(56, 189, 248, 255), width=6)
    d.rounded_rectangle([32, 32, 224, 224], radius=44, fill=(30, 41, 59, 255))
    d.polygon([(90, 68), (196, 128), (90, 188)], fill=(14, 165, 233, 255))
    d.polygon([(98, 82), (180, 128), (98, 174)], fill=(248, 250, 252, 255))
    d.ellipse([180, 52, 204, 76], fill=(239, 68, 68, 255))
    img.save(str(icon_path), format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"      -> {icon_path.name} ({icon_path.stat().st_size} bytes)")

def build_bundle():
    print("[2/4] Packaging app_bundle.zip...")
    out_zip = BASE_DIR / "app_bundle.zip"
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root_folder in ["backend", "frontend"]:
            for folder, _, files in os.walk(BASE_DIR / root_folder):
                if "__pycache__" in folder:
                    continue
                for file in files:
                    if file.endswith(".pyc"):
                        continue
                    p = Path(folder) / file
                    rel = p.relative_to(BASE_DIR)
                    z.write(p, rel.as_posix())
        for single in ["AutoVideoEditor.exe", "launcher.py", "app_icon.ico"]:
            sp = BASE_DIR / single
            if sp.exists():
                z.write(sp, single)

    print(f"      -> {out_zip.name} ({out_zip.stat().st_size} bytes)")

def compile_launcher():
    print("[3/4] Compiling AutoVideoEditor.exe (Native Windows Application Launcher)...")
    cs_path = BASE_DIR / "AutoVideoEditor.cs"
    exe_path = BASE_DIR / "AutoVideoEditor.exe"
    icon_path = BASE_DIR / "app_icon.ico"

    cmd = [
        CSC_COMPILER,
        "/target:exe",
        f"/win32icon:{icon_path}",
        f"/out:{exe_path}",
        "/r:System.Windows.Forms.dll",
        str(cs_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"      -> {exe_path.name} ({exe_path.stat().st_size} bytes)")

def compile_installer():
    print("[4/4] Compiling AutoVideoEditor_Setup.exe (Standalone Windows Setup Wizard)...")
    wizard_cs = BASE_DIR / "SetupWizard.cs"
    installer_exe = BASE_DIR / "AutoVideoEditor_Setup.exe"
    bundle_zip = BASE_DIR / "app_bundle.zip"
    icon_path = BASE_DIR / "app_icon.ico"

    cmd = [
        CSC_COMPILER,
        "/target:winexe",
        f"/win32icon:{icon_path}",
        f"/resource:{bundle_zip}",
        f"/out:{installer_exe}",
        "/r:System.Windows.Forms.dll",
        "/r:System.Drawing.dll",
        "/r:System.IO.Compression.dll",
        "/r:System.IO.Compression.FileSystem.dll",
        "/r:Microsoft.CSharp.dll",
        str(wizard_cs)
    ]
    subprocess.run(cmd, check=True)
    print(f"      -> {installer_exe.name} ({installer_exe.stat().st_size} bytes)")

def main():
    print("================================================================")
    print("      BUILDING AUTO VIDEO EDITOR EXECUTABLES & INSTALLER        ")
    print("================================================================")
    build_icon()
    compile_launcher()
    build_bundle()
    compile_installer()
    print("================================================================")
    print("      BUILD COMPLETE! ARTIFACTS READY FOR DISTRIBUTION:         ")
    print(f"      * Launcher:  {BASE_DIR / 'AutoVideoEditor.exe'}")
    print(f"      * Installer: {BASE_DIR / 'AutoVideoEditor_Setup.exe'}")
    print("================================================================")

if __name__ == "__main__":
    main()
