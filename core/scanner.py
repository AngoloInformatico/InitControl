"""
Windows 11 Startup Aggregator & Internals Scanner.
Ultra-fast aggregator scanning:
1. Startup Folders (User AppData & System ProgramData)
2. Registry Run & RunOnce (HKCU, HKLM, WoW6432Node)
3. StartupApproved Registry keys (Task Manager enabled/disabled tracking)
4. Third-Party Windows Services (Auto-start)
5. Scheduled Tasks (Logon / Boot triggers)
"""
import os
import sys
import json
import winreg
import hashlib
import subprocess
from pathlib import Path

from core.deobfuscator import inspect_and_deobfuscate_item, clean_command_line
from core.classifier import classify_and_rate_item

def _make_stable_id(prefix: str, key_str: str) -> str:
    h = hashlib.md5(key_str.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{prefix}_{h}"


_LAST_SCAN_CACHE = None


def get_last_scan_cache() -> dict | None:
    global _LAST_SCAN_CACHE
    return _LAST_SCAN_CACHE


def update_cached_item_state(item_id: str, new_state: bool):
    global _LAST_SCAN_CACHE
    if not _LAST_SCAN_CACHE:
        return
    for coll_name in ["all_items", "user_software", "system_processes"]:
        for item in _LAST_SCAN_CACHE.get(coll_name, []):
            if item.get("id") == item_id or item.get("name") == item_id or item.get("service_name") == item_id:
                item["enabled"] = new_state


REGISTRY_SCAN_TARGETS = [
    {
        "root": winreg.HKEY_CURRENT_USER,
        "root_name": "HKCU",
        "subpath": r"Software\Microsoft\Windows\CurrentVersion\Run",
        "approved_subpath": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
        "view": 0,
        "label": "HKCU Run (Utente Corrente)"
    },
    {
        "root": winreg.HKEY_CURRENT_USER,
        "root_name": "HKCU",
        "subpath": r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "approved_subpath": None,
        "view": 0,
        "label": "HKCU RunOnce (Avvio Singolo)"
    },
    {
        "root": winreg.HKEY_LOCAL_MACHINE,
        "root_name": "HKLM",
        "subpath": r"Software\Microsoft\Windows\CurrentVersion\Run",
        "approved_subpath": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
        "view": winreg.KEY_WOW64_64KEY,
        "label": "HKLM Run (Sistema x64)"
    },
    {
        "root": winreg.HKEY_LOCAL_MACHINE,
        "root_name": "HKLM",
        "subpath": r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "approved_subpath": None,
        "view": winreg.KEY_WOW64_64KEY,
        "label": "HKLM RunOnce (Sistema x64)"
    },
    {
        "root": winreg.HKEY_LOCAL_MACHINE,
        "root_name": "HKLM",
        "subpath": r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        "approved_subpath": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32",
        "view": winreg.KEY_WOW64_32KEY,
        "label": "HKLM WoW6432Node Run (App a 32-bit)"
    },
    {
        "root": winreg.HKEY_LOCAL_MACHINE,
        "root_name": "HKLM",
        "subpath": r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
        "approved_subpath": None,
        "view": winreg.KEY_WOW64_32KEY,
        "label": "HKLM WoW6432Node RunOnce (32-bit)"
    }
]


def _read_startup_approved_map(root, subpath, view=0) -> dict:
    approved = {}
    if not subpath:
        return approved
    # StartupApproved is always located in 64-bit registry (Explorer / TaskManager)
    # Check primary root first (using 64-bit key view to avoid WOW64 redirection)
    for try_view in [winreg.KEY_WOW64_64KEY, 0]:
        try:
            flags = winreg.KEY_READ | try_view
            with winreg.OpenKey(root, subpath, 0, flags) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    name, val, vtype = winreg.EnumValue(key, i)
                    if isinstance(val, (bytes, bytearray)) and len(val) > 0:
                        # Even first byte (0x02, 0x06) = Enabled; Odd first byte (0x01, 0x03, 0x07) = Disabled
                        approved[name.lower()] = ((val[0] & 1) == 0)
            if approved:
                break
        except Exception:
            pass

    # If root was HKLM, also check HKCU for per-user Task Manager overrides
    if root == winreg.HKEY_LOCAL_MACHINE:
        for try_view in [winreg.KEY_WOW64_64KEY, 0]:
            try:
                flags = winreg.KEY_READ | try_view
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subpath, 0, flags) as key:
                    num_values = winreg.QueryInfoKey(key)[1]
                    for i in range(num_values):
                        name, val, vtype = winreg.EnumValue(key, i)
                        if isinstance(val, (bytes, bytearray)) and len(val) > 0:
                            approved[name.lower()] = ((val[0] & 1) == 0)
                break
            except Exception:
                pass

    return approved


def scan_registry_items() -> list[dict]:
    items = []
    for target in REGISTRY_SCAN_TARGETS:
        approved_map = {}
        if target["approved_subpath"]:
            approved_map = _read_startup_approved_map(target["root"], target["approved_subpath"], target["view"])

        flags = winreg.KEY_READ | target["view"]
        try:
            with winreg.OpenKey(target["root"], target["subpath"], 0, flags) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    val_name, val_data, val_type = winreg.EnumValue(key, i)
                    if not val_data or not isinstance(val_data, str):
                        continue

                    is_enabled = approved_map.get(val_name.lower(), True)
                    inspection = inspect_and_deobfuscate_item(val_data, item_name=val_name)

                    item_record = {
                        "id": _make_stable_id("reg", f"{target['root_name']}_{target['subpath']}_{val_name}".lower()),
                        "name": val_name,
                        "display_name": inspection["display_title"],
                        "command": val_data,
                        "clean_exe_path": inspection["clean_exe_path"],
                        "arguments": inspection["arguments"],
                        "filename": inspection["filename"],
                        "source_type": "Registry",
                        "source_location": f"{target['root_name']}\\{target['subpath']}",
                        "source_label": target["label"],
                        "reg_root": target["root_name"],
                        "reg_subpath": target["subpath"],
                        "reg_value_name": val_name,
                        "enabled": is_enabled,
                        "metadata": inspection["metadata"],
                        "signature": inspection["signature"],
                        "intelligence": inspection["intelligence"],
                        "explanation": inspection["explanation"],
                        "virustotal_url": inspection["virustotal_url"],
                        "search_url": inspection["search_url"]
                    }

                    classification = classify_and_rate_item(item_record)
                    item_record.update(classification)
                    items.append(item_record)
        except Exception:
            pass
    return items


def scan_startup_folders() -> list[dict]:
    items = []
    folder_targets = [
        {
            "path": os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
            "approved_root": winreg.HKEY_CURRENT_USER,
            "approved_subpath": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder",
            "scope": "Utente",
            "label": "Cartella Startup Utente (%AppData%)"
        },
        {
            "path": os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup"),
            "approved_root": winreg.HKEY_LOCAL_MACHINE,
            "approved_subpath": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder",
            "scope": "Sistema",
            "label": "Cartella Startup Sistema (%ProgramData%)"
        }
    ]

    for target in folder_targets:
        dir_path = target["path"]
        if not os.path.exists(dir_path):
            continue

        approved_map = _read_startup_approved_map(target["approved_root"], target["approved_subpath"])

        try:
            for entry in os.scandir(dir_path):
                if entry.is_file():
                    fname = entry.name
                    if fname.lower() == "desktop.ini":
                        continue

                    full_path = entry.path
                    ext = entry.name.lower().split(".")[-1] if "." in entry.name else ""

                    if ext in ["lnk", "exe", "bat", "cmd", "vbs", "url", "disabled"]:
                        is_enabled = approved_map.get(fname.lower(), True)
                        if fname.lower().endswith(".disabled"):
                            is_enabled = False

                        inspection = inspect_and_deobfuscate_item(full_path, item_name=fname)

                        item_record = {
                            "id": _make_stable_id("folder", full_path.lower()),
                            "name": Path(fname).stem,
                            "display_name": inspection["display_title"],
                            "command": full_path,
                            "clean_exe_path": inspection["clean_exe_path"],
                            "arguments": inspection["arguments"],
                            "filename": inspection["filename"],
                            "source_type": "StartupFolder",
                            "source_location": dir_path,
                            "source_label": target["label"],
                            "file_entry_path": full_path,
                            "enabled": is_enabled,
                            "metadata": inspection["metadata"],
                            "signature": inspection["signature"],
                            "intelligence": inspection["intelligence"],
                            "explanation": inspection["explanation"],
                            "virustotal_url": inspection["virustotal_url"],
                            "search_url": inspection["search_url"]
                        }

                        classification = classify_and_rate_item(item_record)
                        item_record.update(classification)
                        items.append(item_record)
        except Exception:
            pass
    return items


def scan_services() -> list[dict]:
    items = []
    # Fast query: automatic services and non-Windows disabled services, excluding generic svchost internal worker instances
    ps_cmd = (
        "Get-CimInstance Win32_Service | "
        "Where-Object { "
        "  ($_.PathName -notlike '*svchost.exe*') -and "
        "  ( "
        "    ($_.StartMode -in 'Auto', 'Delayed-Auto') -or "
        "    ($_.StartMode -eq 'Disabled' -and $_.PathName -notlike '*\\\\Windows\\\\system32\\\\*' -and $_.PathName -notlike '*\\\\Windows\\\\SysWOW64\\\\*') "
        "  ) "
        "} | "
        "Select-Object Name, DisplayName, State, StartMode, PathName, Description | "
        "ConvertTo-Json -Compress"
    )

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=8
        )
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout)
            if isinstance(raw_data, dict):
                raw_data = [raw_data]

            for s in raw_data:
                name = s.get("Name", "")
                display_name = s.get("DisplayName", name)
                raw_path = s.get("PathName") or ""
                state = s.get("State", "")
                start_mode = s.get("StartMode", "")
                is_startup_enabled = (start_mode in ["Auto", "Delayed-Auto"])

                clean_path, args = clean_command_line(raw_path)
                lower_path = clean_path.lower()
                is_ms_dir = "\\windows\\system32" in lower_path or "\\windows\\syswow64" in lower_path

                inspection = inspect_and_deobfuscate_item(raw_path or name, item_name=name)
                is_third_party = not (is_ms_dir or "microsoft" in (inspection["metadata"].get("company_name", "")).lower())

                item_record = {
                    "id": _make_stable_id("srv", name.lower()),
                    "name": name,
                    "display_name": display_name or inspection["display_title"],
                    "command": raw_path,
                    "clean_exe_path": inspection["clean_exe_path"],
                    "arguments": args,
                    "filename": inspection["filename"],
                    "source_type": "Service",
                    "source_location": f"Servizio Windows: {name}",
                    "source_label": f"Servizio Windows ({start_mode or 'Auto'})",
                    "service_name": name,
                    "service_state": state,
                    "is_third_party": is_third_party,
                    "enabled": is_startup_enabled,
                    "metadata": inspection["metadata"],
                    "signature": inspection["signature"],
                    "intelligence": inspection["intelligence"],
                    "explanation": s.get("Description") or inspection["explanation"],
                    "virustotal_url": inspection["virustotal_url"],
                    "search_url": inspection["search_url"]
                }

                classification = classify_and_rate_item(item_record)
                item_record.update(classification)
                items.append(item_record)
    except Exception:
        pass
    return items


def scan_scheduled_tasks() -> list[dict]:
    items = []
    # Fast query: non-Microsoft tasks (both enabled and disabled)
    ps_cmd = (
        "Get-ScheduledTask | "
        "Where-Object { $_.TaskPath -notmatch '^\\\\Microsoft\\\\Windows\\\\' } | "
        "Select-Object TaskName, TaskPath, State, @{N='StateStr';E={$_.State.ToString()}}, Author, Description, "
        "@{N='Exec';E={$_.Actions.Execute}}, @{N='Args';E={$_.Actions.Arguments}} | "
        "ConvertTo-Json -Compress"
    )

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=8
        )
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout)
            if isinstance(raw_data, dict):
                raw_data = [raw_data]

            for t in raw_data:
                name = t.get("TaskName", "")
                task_path = t.get("TaskPath", "\\")
                exec_cmd = t.get("Exec") or ""
                args = t.get("Args") or ""
                state_str = str(t.get("StateStr") or t.get("State", "")).strip()
                raw_state = t.get("State")
                # TaskState: 1 = Disabled, 0 = Unknown, 3 = Ready, 4 = Running, 2 = Queued
                is_enabled = (
                    state_str.lower() not in ["disabled", "0", "1"] 
                    and raw_state not in [0, 1]
                )

                full_cmd = f"{exec_cmd} {args}".strip() if exec_cmd else name
                inspection = inspect_and_deobfuscate_item(exec_cmd or name, item_name=name)

                item_record = {
                    "id": _make_stable_id("task", f"{task_path}_{name}".lower()),
                    "name": name,
                    "display_name": inspection["display_title"] if inspection["display_title"] != name else name,
                    "command": full_cmd,
                    "clean_exe_path": inspection["clean_exe_path"],
                    "arguments": args or inspection["arguments"],
                    "filename": inspection["filename"],
                    "source_type": "Task",
                    "source_location": f"{task_path}{name}",
                    "source_label": f"Attività Pianificata ({state_str or ('Abilitata' if is_enabled else 'Disabilitata')})",
                    "task_name": name,
                    "task_path": task_path,
                    "author": t.get("Author", ""),
                    "enabled": is_enabled,
                    "metadata": inspection["metadata"],
                    "signature": inspection["signature"],
                    "intelligence": inspection["intelligence"],
                    "explanation": t.get("Description") or inspection["explanation"],
                    "virustotal_url": inspection["virustotal_url"],
                    "search_url": inspection["search_url"]
                }

                classification = classify_and_rate_item(item_record)
                item_record.update(classification)
                items.append(item_record)
    except Exception:
        pass
    return items


def scan_all_startup_sources() -> dict:
    reg_items = scan_registry_items()
    folder_items = scan_startup_folders()
    service_items = scan_services()
    task_items = scan_scheduled_tasks()

    all_items = reg_items + folder_items + service_items + task_items

    user_software = [item for item in all_items if item["category"] == "Software Utente"]
    system_processes = [item for item in all_items if item["category"] == "Processi di Sistema & Servizi"]

    safe_count = sum(1 for item in all_items if item["risk"] == "VERDE")
    caution_count = sum(1 for item in all_items if item["risk"] == "GIALLO")
    critical_count = sum(1 for item in all_items if item["risk"] == "ROSSO")
    enabled_count = sum(1 for item in all_items if item.get("enabled", True))
    disabled_count = len(all_items) - enabled_count

    penalty = (sum(1 for i in user_software if i.get("enabled") and i["risk"] == "VERDE") * 5) + \
              (sum(1 for i in user_software if i.get("enabled") and i["risk"] == "GIALLO") * 3)
    efficiency_score = max(25, min(98, 98 - penalty))
    est_boot_saved_sec = sum(1.2 for i in user_software if i.get("enabled") and i["risk"] == "VERDE")

    scan_result = {
        "summary": {
            "total_items": len(all_items),
            "user_software_count": len(user_software),
            "system_processes_count": len(system_processes),
            "registry_count": len(reg_items),
            "startup_folder_count": len(folder_items),
            "services_count": len(service_items),
            "tasks_count": len(task_items),
            "safe_count": safe_count,
            "caution_count": caution_count,
            "critical_count": critical_count,
            "enabled_count": enabled_count,
            "disabled_count": disabled_count,
            "efficiency_score": efficiency_score,
            "estimated_saved_seconds": round(est_boot_saved_sec, 1)
        },
        "all_items": all_items,
        "user_software": user_software,
        "system_processes": system_processes
    }
    global _LAST_SCAN_CACHE
    _LAST_SCAN_CACHE = scan_result
    return scan_result
