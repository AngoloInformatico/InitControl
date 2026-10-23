"""
GeneraExe.py - Build script for InitControl.
Compiles the application into a standalone 64-bit Windows executable (.exe)
using PyInstaller with --windowed / --noconsole, embedding the icon, web assets,
and centering the window at launch.

GUARANTEES:
1. Completely wipes the 'dist' and 'build' directories before compilation.
2. The generated .exe strictly follows the version specified in version.json / versione.json.
3. Automatically embeds Windows PE file version information (Right Click -> Properties -> Details).
4. Updates build_history.log.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from version_manager import (
    get_current_version_info,
    check_and_bump_if_modified,
    record_build_exe,
    save_version_info
)

ICON_PATH = BASE_DIR / "Icona" / "icon.ico"
WEB_DIR = BASE_DIR / "web"
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
VERSION_FILE = BASE_DIR / "versione.json"
VERSION_INFO_TMP = BASE_DIR / "file_version_info.txt"


def ensure_icon():
    """Generates the icon if missing."""
    if not ICON_PATH.exists():
        print("[+] icon.ico mancante, avvio generazione automatica...")
        from make_icon import create_modern_startup_icon
        create_modern_startup_icon()


def clean_directory(dir_path: Path):
    """Completely removes a directory and all its contents, handling read-only flags."""
    if dir_path.exists():
        def on_rm_error(func, path, exc_info):
            import stat
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        try:
            shutil.rmtree(dir_path, onerror=on_rm_error)
        except Exception:
            pass


def create_windows_version_file(version_str: str, build_num: int, output_path: Path):
    """
    Generates a Windows PE Version Resource file for PyInstaller
    so that Right Click -> Properties -> Details displays the exact version.
    """
    parts = [int(p) for p in version_str.split(".")]
    while len(parts) < 3:
        parts.append(0)

    # 4-element tuple (Major, Minor, Patch, Build)
    v_tuple = (parts[0], parts[1], parts[2], int(build_num))
    v_str = f"{parts[0]}.{parts[1]}.{parts[2]}.{build_num}"

    content = f"""# UTF-8
# Windows Version Resource definition for InitControl
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v_tuple},
    prodvers={v_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '041004b0',
          [
            StringStruct('CompanyName', 'Alex Lignola'),
            StringStruct('FileDescription', 'InitControl - Gestione e Ottimizzazione Avvio Windows 11'),
            StringStruct('FileVersion', '{v_str}'),
            StringStruct('InternalName', 'InitControl'),
            StringStruct('LegalCopyright', 'Created by Alex Lignola - © 2026 InitControl - All rights reserved.'),
            StringStruct('OriginalFilename', 'InitControl.exe'),
            StringStruct('ProductName', 'InitControl'),
            StringStruct('ProductVersion', '{version_str}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1040, 1200])])
  ]
)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def build_executable():
    print("=" * 70)
    print("  INITCONTROL - BUILD STANDALONE WINDOWS x64 EXECUTABLE")
    print("=" * 70)

    # Chiudi eventuali istanze aperte dell'eseguibile per evitare blocco file su Windows
    try:
        subprocess.run(["taskkill", "/F", "/IM", "InitControl.exe"], capture_output=True)
    except Exception:
        pass

    # 1. Ensure Icon exists
    ensure_icon()

    # 2. Check and bump version if source files were modified, and update README badges
    print("[1/5] Verifica modifiche sorgenti e sincronizzazione badge README.md...")
    bumped, version_info = check_and_bump_if_modified("Build eseguibile standalone (.exe)")
    version_str = version_info.get("version", "0.1.5")
    build_num = version_info.get("build", 6)
    if bumped:
        print(f"      -> Rilevata modifica sorgenti: Incremento versione a v{version_str} (Build #{build_num})")
    else:
        print(f"      -> Sorgenti allineati: v{version_str} (Build #{build_num})")

    # 3. Clean previous build artifacts: completely wipe dist and build
    print("[2/5] Cancellazione completa della cartella 'dist' e 'build'...")
    exe_target = DIST_DIR / "InitControl.exe"
    if exe_target.exists():
        try:
            with open(exe_target, "a+b"):
                pass
        except PermissionError:
            print("[!] ERRORE: 'dist/InitControl.exe' è attualmente aperto o in esecuzione!")
            print("[!] Chiudi la finestra di InitControl aperta e rilancia 'python GeneraExe.py'.")
            return

    clean_directory(DIST_DIR)
    clean_directory(BUILD_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print("      -> Cartella 'dist' eliminata e ricreata vuota.")

    # 4. Generate Windows PE version resource file
    create_windows_version_file(version_str, build_num, VERSION_INFO_TMP)

    exe_name = "InitControl"
    generated_exe = DIST_DIR / f"{exe_name}.exe"

    # 5. Construct PyInstaller command
    add_web = f"{WEB_DIR};web"
    add_ver = f"{VERSION_FILE};."
    add_icon = f"{BASE_DIR / 'Icona'};Icona"

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",              # No console / terminal window appears!
        "--uac-admin",             # Richiede automaticamente i permessi di amministratore (UAC) all'avvio!
        "--clean",
        f"--name={exe_name}",
        f"--icon={ICON_PATH}",
        f"--version-file={VERSION_INFO_TMP}",
        f"--add-data={add_web}",
        f"--add-data={add_ver}",
        f"--add-data={add_icon}",
        "--hidden-import=webview",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=pefile",
        "--hidden-import=psutil",
        "--hidden-import=flask",
        "--hidden-import=jinja2",
        "--hidden-import=werkzeug",
        str(BASE_DIR / "app.py")
    ]

    print(f"[3/5] Compilazione in corso con PyInstaller (--windowed, x64)...")
    res = subprocess.run(pyinstaller_cmd, cwd=str(BASE_DIR))

    # Remove temporary version info file
    if VERSION_INFO_TMP.exists():
        try:
            VERSION_INFO_TMP.unlink()
        except Exception:
            pass

    if res.returncode != 0:
        print("[!] ERRORE DURANTE LA COMPILAZIONE!")
        sys.exit(res.returncode)

    # 6. Check and finalize output
    if generated_exe.exists():
        size_mb = os.path.getsize(generated_exe) / (1024 * 1024)
        print(f"[4/5] Eseguibile generato con successo: {generated_exe.name} ({size_mb:.2f} MB)")

        # 7. Log build in build_history.log
        print("[5/5] Registrazione della build nel log storico...")
        record_build_exe(str(generated_exe))

        # Pulizia post-build di InitControl.spec e cartella build
        spec_file = BASE_DIR / "InitControl.spec"
        if spec_file.exists():
            try:
                spec_file.unlink()
            except Exception:
                pass
        clean_directory(BUILD_DIR)

        print("\n" + "=" * 70)
        print(f"  BUILD COMPLETATA CON SUCCESSO!")
        print(f"  Versione Eseguibile: v{version_str} (Build #{build_num})")
        print(f"  File Generato: dist/{generated_exe.name} (File Unico)")
        print(f"  Versione PE Windows: {version_str}.{build_num} (Proprieta file)")
        print(f"  Finestra Terminale: DISATTIVATA (--windowed)")
        print(f"  Privilegi Amministratore: RICHIESTI AUTOMATICAMENTE ALL'AVVIO (--uac-admin)")
        print(f"  Posizionamento: APERTURA AUTOMATICA AL CENTRO DELLO SCHERMO")
        print("=" * 70)
    else:
        print("[!] File .exe non trovato dopo il processo di compilazione!")


if __name__ == "__main__":
    build_executable()
