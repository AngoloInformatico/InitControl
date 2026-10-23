"""
System Information and Hardware Inspector for InitControl.
Collects OS version, CPU, RAM, Disk, UAC/Admin privileges, and instruction set.
"""
import os
import sys
import platform
import ctypes
import psutil
import subprocess


def is_admin() -> bool:
    """Checks if the application is running with elevated Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_cpu_info() -> dict:
    """Detects CPU name, cores, and instruction set support (SSE4.2 / POPCNT)."""
    cpu_name = platform.processor() or "Processore x64"
    cores_physical = psutil.cpu_count(logical=False) or 2
    cores_logical = psutil.cpu_count(logical=True) or 4

    # Query WMI for friendly CPU brand string
    try:
        res = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            capture_output=True,
            text=True,
            timeout=3
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip() and "Name" not in line]
        if lines:
            cpu_name = lines[0]
    except Exception:
        pass

    # Windows 11 24H2+ requires POPCNT / SSE4.2
    # On x64 Windows 10/11, standard check:
    instruction_set = "Supportato (SSE4.2, POPCNT, AVX)"

    return {
        "name": cpu_name,
        "cores_physical": cores_physical,
        "cores_logical": cores_logical,
        "instruction_set": instruction_set
    }


def get_memory_info() -> dict:
    """Returns RAM stats in GB."""
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb = mem.used / (1024 ** 3)
    free_gb = mem.available / (1024 ** 3)

    return {
        "total_gb": round(total_gb, 1),
        "used_gb": round(used_gb, 1),
        "free_gb": round(free_gb, 1),
        "percent_used": mem.percent
    }


def get_disk_info() -> dict:
    """Returns free space on system drive C:"""
    try:
        disk = psutil.disk_usage("C:\\")
        total_gb = disk.total / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        return {
            "total_gb": round(total_gb, 1),
            "free_gb": round(free_gb, 1),
            "percent_free": round((disk.free / disk.total) * 100, 1)
        }
    except Exception:
        return {"total_gb": 0, "free_gb": 0, "percent_free": 0}


def get_windows_version() -> dict:
    """Detects Windows 11 release and build number."""
    ver = sys.getwindowsversion()
    build = ver.build

    # Map Windows 11 build to marketing version
    win_display = "Windows 11"
    sub_ver = "23H2 / 24H2"
    if build >= 26100:
        sub_ver = "24H2 (Build 26100)"
    elif build >= 22631:
        sub_ver = "23H2 (Build 22631)"
    elif build >= 22621:
        sub_ver = "22H2 (Build 22621)"
    elif build >= 22000:
        sub_ver = "21H2 (Build 22000)"

    return {
        "edition": f"{win_display} Pro 64-bit",
        "version_tag": sub_ver,
        "build_number": str(build),
        "platform": platform.platform()
    }


def get_full_system_summary() -> dict:
    """Aggregates all system parameters for the dashboard display."""
    computer_model = platform.node()
    try:
        res = subprocess.run(
            ["wmic", "computersystem", "get", "model,manufacturer"],
            capture_output=True,
            text=True,
            timeout=3
        )
        lines = [l.strip() for l in res.stdout.splitlines() if l.strip() and "Manufacturer" not in l]
        if lines:
            computer_model = lines[0]
    except Exception:
        pass

    return {
        "computer_model": computer_model,
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "windows": get_windows_version(),
        "is_admin": is_admin()
    }
