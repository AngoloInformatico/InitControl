"""
Version Manager for InitControl
Tracks source code changes, automatically increments version starting from 0.1.1,
and logs builds to build_history.log.
Follows exclusively versione.json, and supports PyInstaller frozen bundles.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(sys._MEIPASS)
    VERSION_FILE = BUNDLE_DIR / "versione.json" if (BUNDLE_DIR / "versione.json").exists() else (EXE_DIR / "versione.json")
    CODEX_DIR = EXE_DIR / "Codex_Work"
    BUILD_LOG_FILE = (CODEX_DIR / "build_history.log") if CODEX_DIR.exists() else (EXE_DIR / "build_history.log")
    BASE_DIR = EXE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent
    VERSION_FILE = BASE_DIR / "versione.json"
    CODEX_DIR = BASE_DIR / "Codex_Work"
    BUILD_LOG_FILE = (CODEX_DIR / "build_history.log") if CODEX_DIR.exists() else (BASE_DIR / "build_history.log")

SOURCE_EXTENSIONS = {".py", ".html", ".css", ".js"}
IGNORE_DIRS = {"__pycache__", ".git", "build", "dist", ".pytest_cache", ".gemini", "Icona", "backups", "Codex_Work", "ScreenShot"}
IGNORE_FILES = {"versione.json", "version.json", "build_history.log", "desktop.ini", "file_version_info.txt", "README.md", "Manifesto.md", "LICENSE", "requirements.txt", ".gitignore"}


def update_readme_badges(info: dict = None) -> bool:
    """
    Dynamically updates the software and version badges in README.md
    based on the current versione.json and installed runtime packages.
    """
    if getattr(sys, "frozen", False):
        return False

    readme_path = BASE_DIR / "README.md"
    if not readme_path.exists():
        return False

    if info is None:
        info = get_current_version_info()

    ver_str = info.get("version", "0.1.4")
    build_num = info.get("build", 5)

    py_ver = sys.version.split()[0]
    pkg_versions = {
        "flask": "3.0.2",
        "pywebview": "6.2.1",
        "psutil": "7.2.2",
        "pefile": "2024.8.26",
        "pillow": "12.3.0",
        "pyinstaller": "6.22.3",
    }
    try:
        import importlib.metadata
        for k in pkg_versions:
            try:
                pkg_versions[k] = importlib.metadata.version(k)
            except Exception:
                pass
    except Exception:
        pass

    safe_initcontrol_label = f"v{ver_str}_Build_%23{build_num}"

    badge_block = (
        "<!-- TECH_BADGES_START -->\n"
        f"[![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010%20(x64)-0078D4?logo=windows&logoColor=white)](https://github.com/AngoloInformatico)\n"
        f"[![InitControl Sources](https://img.shields.io/badge/InitControl_Sources-{safe_initcontrol_label}-D4F86A?logo=powershell&logoColor=black)](versione.json)\n"
        f"[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)\n"
        f"[![Manifesto](https://img.shields.io/badge/Manifesto-Leggi%20il%20Documento-D4F86A?logo=readme&logoColor=black)](Manifesto.md)\n"
        f"<br/>\n"
        f"[![Python](https://img.shields.io/badge/Python-{py_ver}-3776AB?logo=python&logoColor=white)](https://www.python.org/)\n"
        f"[![Flask](https://img.shields.io/badge/Flask-{pkg_versions['flask']}-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)\n"
        f"[![pywebview](https://img.shields.io/badge/pywebview-{pkg_versions['pywebview']}-1B365D?logo=googlechrome&logoColor=white)](https://pywebview.flowrl.com/)\n"
        f"[![psutil](https://img.shields.io/badge/psutil-{pkg_versions['psutil']}-4B8BBE?logo=pypi&logoColor=white)](https://github.com/giampaolo/psutil)\n"
        f"[![pefile](https://img.shields.io/badge/pefile-{pkg_versions['pefile']}-orange?logo=securityscorecard&logoColor=white)](https://github.com/erocarrera/pefile)\n"
        f"[![Pillow](https://img.shields.io/badge/Pillow-{pkg_versions['pillow']}-blue?logo=pypi&logoColor=white)](https://python-pillow.org/)\n"
        f"[![PyInstaller](https://img.shields.io/badge/PyInstaller-{pkg_versions['pyinstaller']}-yellow?logo=pypi&logoColor=black)](https://www.pyinstaller.org/)\n"
        "<!-- TECH_BADGES_END -->"
    )

    table_block = (
        "<!-- TECH_TABLE_START -->\n"
        "| Componente | Software / Libreria | Versione Attiva | Ruolo Tecnologico |\n"
        "| :--- | :--- | :---: | :--- |\n"
        f"| **Sorgenti InitControl** | InitControl Core | `v{ver_str} (Build #{build_num})` | Motore di scansione, classificazione ed euristica |\n"
        f"| **Linguaggio Base** | Python | `{py_ver}` | Runtime ed elaborazione nativa Windows 64-bit |\n"
        f"| **Web Framework & API** | Flask | `{pkg_versions['flask']}` | Server HTTP locale ad alte prestazioni e routing API |\n"
        f"| **Desktop Host GUI** | pywebview | `{pkg_versions['pywebview']}` | Finestra desktop nativa accelerata GPU Edge WebView2 |\n"
        f"| **System Diagnostics** | psutil | `{pkg_versions['psutil']}` | Monitoraggio risorse hardware, RAM, disco e CPU |\n"
        f"| **Analisi Eseguibili** | pefile | `{pkg_versions['pefile']}` | Ispezione binari PE, sezioni, metadati e firme |\n"
        f"| **Elaborazione Icone** | Pillow (PIL) | `{pkg_versions['pillow']}` | Generazione grafica e rendering icone multi-risoluzione |\n"
        f"| **Toolchain Compilazione**| PyInstaller | `{pkg_versions['pyinstaller']}` | Bundling standalone PE64 con manifest UAC Administrator |\n"
        "<!-- TECH_TABLE_END -->"
    )

    try:
        import re
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "<!-- TECH_BADGES_START -->" in content and "<!-- TECH_BADGES_END -->" in content:
            content = re.sub(
                r"<!-- TECH_BADGES_START -->.*?<!-- TECH_BADGES_END -->",
                badge_block,
                content,
                flags=re.DOTALL
            )

        if "<!-- TECH_TABLE_START -->" in content and "<!-- TECH_TABLE_END -->" in content:
            content = re.sub(
                r"<!-- TECH_TABLE_START -->.*?<!-- TECH_TABLE_END -->",
                table_block,
                content,
                flags=re.DOTALL
            )

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def get_current_version_info() -> dict:
    """
    Reads the current version data strictly from versione.json.
    """
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass

    # Default initial data
    initial_data = {
        "version": "0.1.4",
        "build": 5,
        "created_at": datetime.now().isoformat(),
        "last_build_at": None,
        "last_source_hash": None,
        "channel": "Release"
    }
    save_version_info(initial_data)
    return initial_data


def save_version_info(info: dict):
    """Saves version info strictly to versione.json and refreshes README badges."""
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
    except Exception:
        pass
    update_readme_badges(info)


def calculate_source_hash() -> str:
    """Calculates SHA256 of all relevant source files in the project."""
    if getattr(sys, "frozen", False):
        return "frozen_build"

    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in sorted(files):
            if f in IGNORE_FILES:
                continue
            ext = Path(f).suffix.lower()
            if ext in SOURCE_EXTENSIONS:
                fpath = Path(root) / f
                try:
                    with open(fpath, "rb") as fp:
                        hasher.update(fp.read())
                except Exception:
                    pass
    return hasher.hexdigest()[:16]


def bump_version(bump_type="patch", reason="Modifica sorgenti") -> dict:
    """Increments version (e.g. 0.1.1 -> 0.1.2) and build number."""
    info = get_current_version_info()
    version_str = info.get("version", "0.1.1")
    parts = [int(p) for p in version_str.split(".")]
    while len(parts) < 3:
        parts.append(0)

    if bump_type == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    elif bump_type == "minor":
        parts[1] += 1
        parts[2] = 0
    else:  # patch
        parts[2] += 1

    new_version = f"{parts[0]}.{parts[1]}.{parts[2]}"
    info["version"] = new_version
    info["build"] = info.get("build", 0) + 1
    info["last_updated"] = datetime.now().isoformat()
    info["last_source_hash"] = calculate_source_hash()

    save_version_info(info)

    log_entry = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"VERSION BUMP -> v{new_version} (Build #{info['build']}) | "
        f"Motivo: {reason} | Hash: {info['last_source_hash']}\n"
    )
    with open(BUILD_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return info


def check_and_bump_if_modified(reason="Rilevata modifica ai sorgenti") -> tuple[bool, dict]:
    """Checks if source files changed compared to last recorded hash, and bumps version if so."""
    if getattr(sys, "frozen", False):
        return False, get_current_version_info()

    info = get_current_version_info()
    current_hash = calculate_source_hash()
    last_hash = info.get("last_source_hash")

    if last_hash is None or current_hash != last_hash:
        new_info = bump_version("patch", reason=reason)
        return True, new_info

    # Keep badges aligned even if version was not incremented
    update_readme_badges(info)
    return False, info


def setup_git_hook() -> bool:
    """
    Installs a git pre-commit hook if a .git repository is found.
    This ensures that committing changes will automatically bump the version,
    refresh README.md badges and table, and stage them in the commit.
    """
    git_dir = BASE_DIR / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        return False
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = (
        "#!/bin/sh\n"
        "# Auto-update InitControl version and README.md badges before commit\n"
        "python version_manager.py\n"
        "git add versione.json README.md\n"
    )
    try:
        with open(pre_commit_hook, "w", encoding="utf-8") as f:
            f.write(hook_content)
        try:
            import stat
            pre_commit_hook.chmod(pre_commit_hook.stat().st_mode | stat.S_IEXEC)
        except Exception:
            pass
        return True
    except Exception:
        return False


def watch_sources(interval_seconds: float = 2.0):
    """
    Watches source files continuously and updates README.md badges
    immediately whenever a file change is saved.
    """
    print(f"[*] InitControl File Watcher avviato (intervallo polling: {interval_seconds}s)")
    print("[*] In ascolto su modifiche ai sorgenti (.py, .html, .css, .js)...")
    print("[*] Premi CTRL+C per arrestare il monitoraggio.\n")
    try:
        import time
        while True:
            bumped, info = check_and_bump_if_modified("Modifica rilevata in tempo reale da File Watcher")
            if bumped:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Rilevata modifica ai sorgenti!")
                print(f"       -> Nuova Versione: v{info['version']} (Build #{info['build']})")
                print(f"       -> Badge e tabella in README.md aggiornati con successo.\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[*] File Watcher interrotto.")


def record_build_exe(exe_path: str = None) -> dict:
    """Logs a successful .exe generation into build_history.log."""
    info = get_current_version_info()
    info["last_build_at"] = datetime.now().isoformat()
    info["last_source_hash"] = calculate_source_hash()

    save_version_info(info)

    exe_size_str = "N/D"
    if exe_path and os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        exe_size_str = f"{size_mb:.2f} MB"

    log_entry = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"BUILD EXE SUCCESSFUL -> v{info['version']} (Build #{info['build']}) | "
        f"Target: Standalone x64 | File: {exe_path or 'InitControl.exe'} ({exe_size_str}) | "
        f"Hash: {info.get('last_source_hash', 'N/D')}\n"
    )
    with open(BUILD_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return info


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="InitControl Version & Badge Manager")
    parser.add_argument("--watch", action="store_true", help="Monitora continuamente i sorgenti e aggiorna README.md ad ogni salvataggio")
    parser.add_argument("--force", action="store_true", help="Forza l'aggiornamento immediato dei badge e della tabella in README.md")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], default=None, help="Incrementa manualmente la versione")
    parser.add_argument("--install-git-hook", action="store_true", help="Installa l'hook git pre-commit se il repository git è presente")
    args = parser.parse_args()

    if args.install_git_hook:
        res = setup_git_hook()
        print(f"Installazione Hook Git pre-commit: {'COMPLETATA' if res else 'FALLITA (repository .git non trovato)'}")
        sys.exit(0)

    if args.watch:
        watch_sources()
        sys.exit(0)

    if args.bump:
        info = bump_version(args.bump, reason="Incremento manuale da CLI")
        update_readme_badges(info)
        print(f"Versione incrementata a: v{info['version']} (Build #{info['build']})")
        sys.exit(0)

    if args.force:
        curr_info = get_current_version_info()
        updated = update_readme_badges(curr_info)
        print(f"[InitControl Version Manager - Force Refresh]")
        print(f"Versione Sorgenti: v{curr_info['version']} (Build #{curr_info['build']})")
        print(f"Aggiornamento Badge e Tabella README.md: {'RIUSCITO' if updated else 'ERRORE'}")
        sys.exit(0)

    bumped, curr_info = check_and_bump_if_modified()
    updated = update_readme_badges(curr_info)
    setup_git_hook()
    print(f"[InitControl Version Manager]")
    print(f"Versione Sorgenti: v{curr_info['version']} (Build #{curr_info['build']})")
    print(f"Hash Sorgenti: {curr_info.get('last_source_hash', 'N/D')}")
    print(f"Modifiche Rilevate: {'SI (Versione incrementata)' if bumped else 'NO (Sorgenti invariati)'}")
    print(f"Aggiornamento Badge e Tabella README.md: {'RIUSCITO' if updated else 'NON NECESSARIO / DISATTIVATO'}")

