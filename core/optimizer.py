"""
Optimizer and State Controller for InitControl.
Handles:
1. Safe enabling/disabling of startup items (Registry, Folders, Services, Tasks)
2. Strict double-confirmation enforcement for ROSSO (Critical) items
3. 1-Click Safe Optimization (disables non-essential VERDE items)
4. Snapshot Backup & Restore System
5. HTML & JSON Report Exporter
"""
import os
import json
import winreg
import subprocess
from pathlib import Path
from datetime import datetime

from core.scanner import scan_all_startup_sources, get_last_scan_cache, update_cached_item_state

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def toggle_item_state(item_id: str, new_state: bool, confirmed_critical: bool = False, item_hint: dict = None) -> dict:
    """
    Enables or disables an item based on its source type and ID.
    If the item is rated ROSSO (Critical), requires confirmed_critical=True.
    """
    target_item = None
    cache = get_last_scan_cache()
    if cache and "all_items" in cache:
        target_item = next(
            (i for i in cache["all_items"] if i.get("id") == item_id or i.get("name") == item_id or i.get("service_name") == item_id),
            None
        )

    if not target_item:
        scan = scan_all_startup_sources()
        all_items = scan.get("all_items", [])
        target_item = next(
            (i for i in all_items if i.get("id") == item_id or i.get("name") == item_id or i.get("service_name") == item_id),
            None
        )

    if not target_item and item_hint and isinstance(item_hint, dict) and item_hint.get("id") == item_id:
        target_item = item_hint

    if not target_item:
        return {"success": False, "error": f"Elemento con ID '{item_id}' non trovato."}

    # Security check for Critical (ROSSO) items
    if target_item.get("risk") == "ROSSO" and not confirmed_critical:
        return {
            "success": False,
            "requires_confirmation": True,
            "risk": "ROSSO",
            "message": "ATTENZIONE: Questo è un processo o servizio CRITICO di sistema. La disattivazione può causare instabilità o schermata blu (BSOD). È richiesta la doppia conferma esplicita per procedere."
        }

    source_type = target_item.get("source_type")

    try:
        # 1. Registry items
        if source_type == "Registry":
            root_map = {
                "HKCU": winreg.HKEY_CURRENT_USER,
                "HKLM": winreg.HKEY_LOCAL_MACHINE
            }
            root_key = root_map.get(target_item.get("reg_root"), winreg.HKEY_CURRENT_USER)
            subpath = target_item.get("reg_subpath", "")
            val_name = target_item.get("reg_value_name", "")

            # Native Task Manager StartupApproved mechanism
            approved_subpath = (
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
                if "WOW6432Node" not in subpath
                else r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"
            )
            # 0x02 = Enabled, 0x03 = Disabled by Task Manager
            val_bytes = b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" if new_state else b"\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

            written = False
            last_err = ""
            try:
                # Write to target root using KEY_WOW64_64KEY to ensure 64-bit registry access
                with winreg.CreateKeyEx(root_key, approved_subpath, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
                    winreg.SetValueEx(key, val_name, 0, winreg.REG_BINARY, val_bytes)
                written = True
            except PermissionError:
                # Fallback to HKCU if HKLM requires elevated admin rights
                try:
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, approved_subpath, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
                        winreg.SetValueEx(key, val_name, 0, winreg.REG_BINARY, val_bytes)
                    written = True
                except Exception as e_user:
                    last_err = str(e_user)
            except Exception as e:
                last_err = str(e)

            # If writing to HKLM succeeded, also sync HKCU so no conflicting user-override remains
            if written and root_key == winreg.HKEY_LOCAL_MACHINE:
                try:
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, approved_subpath, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
                        winreg.SetValueEx(key, val_name, 0, winreg.REG_BINARY, val_bytes)
                except Exception:
                    pass

            if written:
                update_cached_item_state(item_id, new_state)
                return {
                    "success": True,
                    "id": item_id,
                    "enabled": new_state,
                    "message": f"Elemento '{target_item['name']}' {'abilitato' if new_state else 'disabilitato'} con successo nel registro."
                }
            else:
                return {"success": False, "error": f"Errore scrittura registro: {last_err}"}

        # 2. Startup Folder items
        elif source_type == "StartupFolder":
            file_path = target_item.get("file_entry_path", "")
            if os.path.exists(file_path):
                # Also set in StartupApproved\StartupFolder
                approved_subpath = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
                fname = os.path.basename(file_path)
                val_bytes = b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" if new_state else b"\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

                try:
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, approved_subpath, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, fname, 0, winreg.REG_BINARY, val_bytes)
                except Exception:
                    pass

                # If toggling to disabled and user wants file extension backup
                if not new_state and not file_path.endswith(".disabled"):
                    new_path = file_path + ".disabled"
                    try:
                        os.rename(file_path, new_path)
                    except Exception:
                        pass
                elif new_state and file_path.endswith(".disabled"):
                    new_path = file_path[:-9]
                    try:
                        os.rename(file_path, new_path)
                    except Exception:
                        pass

                update_cached_item_state(item_id, new_state)
            return {
                "success": True,
                "id": item_id,
                "enabled": new_state,
                "message": f"Elemento cartella startup '{target_item['name']}' {'abilitato' if new_state else 'disabilitato'}."
            }

        # 3. Windows Service (Standard, AppX/MSIX, and Protected Services)
        elif source_type == "Service":
            srv_name = target_item.get("service_name") or target_item.get("name")
            display_title = target_item.get("display_name") or srv_name
            target_start_mode = "auto" if new_state else "disabled"
            target_ps_type = "Automatic" if new_state else "Disabled"
            target_reg_val = 2 if new_state else 4  # 2 = Automatic, 4 = Disabled

            service_configured = False
            last_err = ""

            # Method 1: SCM via sc.exe config (with mandatory space after start=)
            try:
                cmd_sc = ["sc.exe", "config", srv_name, "start=", target_start_mode]
                res_sc = subprocess.run(cmd_sc, capture_output=True, text=True, timeout=6)
                if res_sc.returncode == 0 or "SUCCESS" in (res_sc.stdout or ""):
                    service_configured = True
                else:
                    last_err = (res_sc.stderr or res_sc.stdout).strip()
            except Exception as e_sc:
                last_err = str(e_sc)

            # Method 2: PowerShell Set-Service
            if not service_configured:
                try:
                    ps_cmd = f"Set-Service -Name '{srv_name}' -StartupType {target_ps_type}"
                    res_ps = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True,
                        text=True,
                        timeout=6
                    )
                    if res_ps.returncode == 0:
                        service_configured = True
                    else:
                        last_err = (res_ps.stderr or res_ps.stdout).strip()
                except Exception as e_ps:
                    last_err = str(e_ps)

            # Method 3: Direct Registry Configuration (Essential for MSIX/Store packages like Claude CoworkVMService
            # and services where SCM DACL lacks BA, but BUILTIN\Administrators owns the Registry key)
            if not service_configured:
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        rf"SYSTEM\CurrentControlSet\Services\{srv_name}",
                        0,
                        winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
                    ) as s_key:
                        winreg.SetValueEx(s_key, "Start", 0, winreg.REG_DWORD, target_reg_val)
                        if not new_state:
                            try:
                                winreg.SetValueEx(s_key, "DelayedAutostart", 0, winreg.REG_DWORD, 0)
                            except Exception:
                                pass
                        service_configured = True
                except Exception as e_reg:
                    # Fallback via reg.exe add (requires elevation)
                    try:
                        cmd_reg = [
                            "reg.exe", "add",
                            rf"HKLM\SYSTEM\CurrentControlSet\Services\{srv_name}",
                            "/v", "Start",
                            "/t", "REG_DWORD",
                            "/d", str(target_reg_val),
                            "/f"
                        ]
                        res_reg = subprocess.run(cmd_reg, capture_output=True, text=True, timeout=5)
                        if res_reg.returncode == 0:
                            service_configured = True
                        else:
                            last_err = (res_reg.stderr or res_reg.stdout).strip()
                    except Exception as e_reg2:
                        last_err = f"Modifica registro non riuscita: {str(e_reg2)}"

            if service_configured:
                # Live runtime synchronization: Stop or Start the service instance
                if not new_state:
                    # Stopping the service
                    try:
                        subprocess.run(["sc.exe", "stop", srv_name], capture_output=True, text=True, timeout=4)
                    except Exception:
                        pass
                    try:
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command", f"Stop-Service -Name '{srv_name}' -Force -ErrorAction SilentlyContinue"],
                            capture_output=True, text=True, timeout=4
                        )
                    except Exception:
                        pass
                    # If it's a known service executable (like cowork-svc.exe), terminate running background process
                    exe_fname = target_item.get("filename")
                    if exe_fname and exe_fname.lower() not in ["svchost.exe", "services.exe", "lsass.exe"]:
                        try:
                            subprocess.run(["taskkill.exe", "/F", "/IM", exe_fname], capture_output=True, text=True, timeout=3)
                        except Exception:
                            pass
                else:
                    # Starting the service
                    try:
                        subprocess.run(["sc.exe", "start", srv_name], capture_output=True, text=True, timeout=4)
                    except Exception:
                        pass

                state_label = "ABILITATO (Avvio Automatico)" if new_state else "DISABILITATO (Arrestato)"
                update_cached_item_state(item_id, new_state)
                return {
                    "success": True,
                    "id": item_id,
                    "enabled": new_state,
                    "message": f"Servizio '{display_title}' ({srv_name}) impostato su {state_label}."
                }
            else:
                return {
                    "success": False,
                    "error": f"Impossibile modificare il servizio '{srv_name}': {last_err}. Assicurarsi che InitControl sia avviato come Amministratore."
                }

        # 4. Scheduled Task
        elif source_type == "Task":
            task_name = target_item.get("task_name") or target_item.get("name")
            task_path = target_item.get("task_path", "\\")
            full_task_name = f"{task_path.rstrip('\\')}\\{task_name}" if task_path != "\\" else f"\\{task_name}"

            task_configured = False
            last_err = ""

            # Method 1: native schtasks.exe (ultra-fast, ~30ms, handles already disabled states smoothly)
            cmd_action_sch = "/ENABLE" if new_state else "/DISABLE"
            try:
                res_sch = subprocess.run(
                    ["schtasks.exe", "/CHANGE", "/TN", full_task_name, cmd_action_sch],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res_sch.returncode == 0:
                    task_configured = True
                else:
                    last_err = (res_sch.stderr or res_sch.stdout).strip()
            except Exception as e_sch:
                last_err = str(e_sch)

            # Method 2: PowerShell Enable-ScheduledTask / Disable-ScheduledTask fallback
            if not task_configured:
                try:
                    cmd_action_ps = "Enable-ScheduledTask" if new_state else "Disable-ScheduledTask"
                    safe_name = task_name.replace("'", "''")
                    safe_path = task_path.replace("'", "''")
                    ps_cmd = f"{cmd_action_ps} -TaskName '{safe_name}' -TaskPath '{safe_path}'"
                    res_ps = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True,
                        text=True,
                        timeout=8
                    )
                    if res_ps.returncode == 0:
                        task_configured = True
                    else:
                        last_err = (res_ps.stderr or res_ps.stdout).strip()
                except Exception as e_ps:
                    last_err = str(e_ps)

            if task_configured:
                update_cached_item_state(item_id, new_state)
                return {
                    "success": True,
                    "id": item_id,
                    "enabled": new_state,
                    "message": f"Attività pianificata '{task_name}' {'abilitata' if new_state else 'disabilitata'} con successo."
                }
            else:
                return {"success": False, "error": f"Errore modifica attività: {last_err}"}

    except Exception as e:
        return {"success": False, "error": f"Eccezione durante la modifica: {str(e)}"}

    return {"success": False, "error": "Tipo sorgente non supportato."}


def create_backup_snapshot(name: str = "Snapshot Avvio") -> dict:
    """Creates a timestamped snapshot of all startup items and their enabled state."""
    scan = scan_all_startup_sources()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"snapshot_{timestamp_str}.json"

    data = {
        "id": f"snap_{timestamp_str}",
        "name": name,
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_items": scan["summary"]["total_items"],
        "enabled_count": scan["summary"]["enabled_count"],
        "items": [
            {
                "id": i["id"],
                "name": i["name"],
                "source_type": i["source_type"],
                "enabled": i.get("enabled", True),
                "risk": i.get("risk", "VERDE"),
                "command": i.get("command", "")
            }
            for i in scan["all_items"]
        ]
    }

    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return {
        "success": True,
        "backup_id": data["id"],
        "filename": backup_file.name,
        "created_at": data["created_at"],
        "total_items": data["total_items"]
    }


def list_backups() -> list[dict]:
    """Lists all available backup snapshots."""
    backups = []
    if not BACKUP_DIR.exists():
        return backups

    for f in sorted(BACKUP_DIR.glob("snapshot_*.json"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                info = json.load(fp)
                backups.append({
                    "id": info.get("id", f.stem),
                    "name": info.get("name", f.stem),
                    "created_at": info.get("created_at", ""),
                    "total_items": info.get("total_items", 0),
                    "filename": f.name
                })
        except Exception:
            pass
    return backups


def restore_backup(backup_id: str) -> dict:
    """Restores item states from a previously saved snapshot."""
    target_file = None
    for f in BACKUP_DIR.glob("snapshot_*.json"):
        if backup_id in f.name or f.stem == backup_id:
            target_file = f
            break

    if not target_file or not target_file.exists():
        return {"success": False, "error": f"Backup snapshot '{backup_id}' non trovato."}

    with open(target_file, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    restored_count = 0
    errors = []

    for item in snapshot.get("items", []):
        res = toggle_item_state(item["id"], item.get("enabled", True), confirmed_critical=True)
        if res.get("success"):
            restored_count += 1
        else:
            errors.append(f"{item['name']}: {res.get('error', 'Errore')}")

    return {
        "success": True,
        "restored_count": restored_count,
        "total": len(snapshot.get("items", [])),
        "errors": errors
    }


def perform_safe_1click_optimization() -> dict:
    """
    1-Click Safe Optimization:
    1. Creates a safety backup snapshot automatically
    2. Disables all non-critical, safe-to-disable (VERDE) User Applications
    3. Leaves caution and critical items untouched for 100% system stability.
    """
    backup_res = create_backup_snapshot(name="Ripristino pre-Ottimizzazione 1-Click")

    scan = scan_all_startup_sources()
    user_apps = scan["user_software"]

    disabled_items = []
    already_disabled = []
    failed = []

    for app in user_apps:
        if app.get("risk") == "VERDE" and app.get("safe_to_disable"):
            if app.get("enabled", True):
                res = toggle_item_state(app["id"], False, confirmed_critical=False)
                if res.get("success"):
                    disabled_items.append(app["display_name"])
                else:
                    failed.append(app["display_name"])
            else:
                already_disabled.append(app["display_name"])

    return {
        "success": True,
        "backup_created": backup_res,
        "optimized_count": len(disabled_items),
        "disabled_items": disabled_items,
        "already_disabled_count": len(already_disabled),
        "failed_count": len(failed),
        "message": f"Ottimizzazione completata con successo! {len(disabled_items)} programmi non critici disattivati in piena sicurezza."
    }
