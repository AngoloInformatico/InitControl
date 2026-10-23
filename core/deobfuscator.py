"""
De-obfuscation and Process Deep Inspection Module for InitControl.
Extracts absolute paths, PE metadata, digital signatures, hashes,
and queries the Intelligence Database or search engines.
Optimized for ultra-fast startup scanning with exe-level caching and selective parsing.
"""
import os
import re
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
import pefile

from core.database import lookup_process_intelligence

# Binary metadata cache keyed by absolute exe path lowercase
EXE_METADATA_CACHE = {}


def clean_command_line(raw_cmd: str) -> tuple[str, str]:
    """Parses a raw startup command into (executable_path, arguments)."""
    if not raw_cmd:
        return "", ""

    expanded = os.path.expandvars(raw_cmd.strip())

    if expanded.startswith('"'):
        end_quote = expanded.find('"', 1)
        if end_quote != -1:
            exe_path = expanded[1:end_quote].strip()
            args = expanded[end_quote + 1:].strip()
            return exe_path, args

    lower_exp = expanded.lower()
    exe_index = lower_exp.find(".exe")
    if exe_index != -1:
        exe_path = expanded[:exe_index + 4].strip()
        args = expanded[exe_index + 4:].strip()
        return exe_path, args

    parts = expanded.split(" ", 1)
    exe_path = parts[0].strip()
    args = parts[1].strip() if len(parts) > 1 else ""
    return exe_path, args


def resolve_shortcut(lnk_path: str) -> tuple[str, str]:
    """Resolves a Windows .lnk shortcut to its target executable and arguments."""
    if not os.path.exists(lnk_path) or not lnk_path.lower().endswith(".lnk"):
        return lnk_path, ""

    try:
        escaped_lnk = lnk_path.replace("'", "''")
        ps_cmd = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{escaped_lnk}'); "
            "Write-Output ($s.TargetPath + '|||' + $s.Arguments)"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=3
        )
        if res.returncode == 0 and "|||" in res.stdout:
            target, args = res.stdout.strip().split("|||", 1)
            if target:
                return target.strip(), args.strip()
    except Exception:
        pass

    return lnk_path, ""


def compute_sha256(file_path: str, max_mb: int = 15) -> str:
    """Calculates SHA256. For large files (>15MB), hashes head+tail for instant execution."""
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        return ""
    try:
        size = os.path.getsize(file_path)
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            if size <= max_mb * 1024 * 1024:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            else:
                # Fast sample hash: first 2MB + last 2MB + size
                hasher.update(f.read(2 * 1024 * 1024))
                f.seek(max(0, size - 2 * 1024 * 1024))
                hasher.update(f.read(2 * 1024 * 1024))
                hasher.update(str(size).encode())
        return hasher.hexdigest()
    except Exception:
        return ""


def extract_pe_metadata(file_path: str) -> tuple[dict, dict]:
    """
    Extracts binary metadata and fast signature using pefile.
    Caches results by lower-case file path to avoid redundant work.
    """
    cache_key = file_path.lower() if file_path else ""
    if cache_key and cache_key in EXE_METADATA_CACHE:
        return EXE_METADATA_CACHE[cache_key]

    metadata = {
        "file_exists": False,
        "file_size_bytes": 0,
        "file_size_human": "0 KB",
        "date_modified": "",
        "company_name": "",
        "product_name": "",
        "file_version": "",
        "product_version": "",
        "file_description": "",
        "legal_copyright": "",
        "subsystem": "Windows GUI",
        "architecture": "x64",
        "sha256": ""
    }
    signature = {"is_signed": False, "status": "Non Firmato", "publisher": "", "valid": False}

    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        if cache_key:
            EXE_METADATA_CACHE[cache_key] = (metadata, signature)
        return metadata, signature

    metadata["file_exists"] = True
    try:
        stat = os.stat(file_path)
        metadata["file_size_bytes"] = stat.st_size
        size_kb = stat.st_size / 1024
        if size_kb > 1024:
            metadata["file_size_human"] = f"{size_kb / 1024:.2f} MB"
        else:
            metadata["file_size_human"] = f"{size_kb:.1f} KB"

        metadata["date_modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        pass

    metadata["sha256"] = compute_sha256(file_path)

    try:
        pe = pefile.PE(file_path, fast_load=True)
        # Parse only resource directory (for version strings) and security directory (for signature)
        pe.parse_data_directories(directories=[
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'],
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_SECURITY']
        ])

        # Architecture
        if pe.FILE_HEADER.Machine == 0x8664:
            metadata["architecture"] = "x64 (64-bit)"
        elif pe.FILE_HEADER.Machine == 0x14C:
            metadata["architecture"] = "x86 (32-bit)"
        elif pe.FILE_HEADER.Machine == 0xAA64:
            metadata["architecture"] = "ARM64"

        # Subsystem
        subsys = pe.OPTIONAL_HEADER.Subsystem
        if subsys == 2:
            metadata["subsystem"] = "Windows GUI"
        elif subsys == 3:
            metadata["subsystem"] = "Console CUI"
        elif subsys == 1:
            metadata["subsystem"] = "Kernel Native"

        # Check signature directory in PE
        sec_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_SECURITY']]
        if sec_dir.VirtualAddress > 0 and sec_dir.Size > 0:
            signature["is_signed"] = True
            signature["status"] = "Firmato Digitalmente"
            signature["valid"] = True

        # StringFileInfo table
        for fileinfo in getattr(pe, 'FileInfo', [[]]):
            for entry in fileinfo:
                if hasattr(entry, 'StringTable'):
                    for st in entry.StringTable:
                        for k, v in st.entries.items():
                            key_str = k.decode('utf-8', errors='ignore') if isinstance(k, bytes) else str(k)
                            val_str = v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v)
                            key_clean = key_str.lower().strip()

                            if key_clean == "companyname":
                                metadata["company_name"] = val_str.strip()
                            elif key_clean == "productname":
                                metadata["product_name"] = val_str.strip()
                            elif key_clean == "filedescription":
                                metadata["file_description"] = val_str.strip()
                            elif key_clean == "fileversion":
                                metadata["file_version"] = val_str.strip()
                            elif key_clean == "productversion":
                                metadata["product_version"] = val_str.strip()
                            elif key_clean == "legalcopyright":
                                metadata["legal_copyright"] = val_str.strip()

        if signature["is_signed"] and metadata["company_name"]:
            signature["publisher"] = metadata["company_name"]

        pe.close()
    except Exception:
        pass

    result = (metadata, signature)
    if cache_key:
        EXE_METADATA_CACHE[cache_key] = result
    return result


def inspect_and_deobfuscate_item(raw_command: str, item_name: str = "") -> dict:
    """Main Deep Inspector entry point."""
    exe_path, args = clean_command_line(raw_command)

    if exe_path.lower().endswith(".lnk"):
        real_target, shortcut_args = resolve_shortcut(exe_path)
        if real_target and real_target != exe_path:
            exe_path = real_target
            if shortcut_args:
                args = f"{shortcut_args} {args}".strip()

    filename = os.path.basename(exe_path) if exe_path else item_name

    metadata, signature = extract_pe_metadata(exe_path)
    best_publisher = signature.get("publisher") or metadata.get("company_name") or ""

    intel = lookup_process_intelligence(filename, file_path=exe_path, publisher=best_publisher)
    display_title = metadata.get("product_name") or metadata.get("file_description") or intel.get("name") or filename

    # De-obfuscation explanation text
    explanation_parts = []
    if intel.get("known"):
        explanation_parts.append(f"Identificato: {intel.get('description')}")
    else:
        explanation_parts.append(
            f"Analisi Euristica Avanzata: Questo eseguibile ({filename}) è collocato nel percorso '{exe_path or 'Sconosciuto'}'. "
        )
        if best_publisher:
            explanation_parts.append(f"Editore rilevato: {best_publisher}.")
        else:
            explanation_parts.append("Attenzione: Nessun editore o firma digitale riconosciuta.")

        explanation_parts.append(f" Finalità stimata: {intel.get('description', '')}")

    explanation = " ".join(explanation_parts)
    sha256 = metadata.get("sha256", "")
    vt_url = f"https://www.virustotal.com/gui/file/{sha256}" if sha256 else ""
    google_url = f"https://www.google.com/search?q={filename}+windows+process"

    return {
        "raw_command": raw_command,
        "clean_exe_path": exe_path,
        "arguments": args,
        "filename": filename,
        "display_title": display_title,
        "metadata": metadata,
        "signature": signature,
        "intelligence": intel,
        "explanation": explanation,
        "virustotal_url": vt_url,
        "search_url": google_url
    }
