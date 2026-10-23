"""
InitControl - Main Application Entrypoint
Hosts the Flask REST API & Web GUI, embedded in a centered standalone PyWebView window.
No terminal window is displayed when compiled with PyInstaller (--noconsole / --windowed).
"""
import os
import sys
import json
import socket
import threading
import subprocess
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request, Response

# Detect execution environment (PyInstaller standalone bundle vs normal python script)
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    BASE_DIR = Path(sys.executable).resolve().parent
    WEB_DIR = BUNDLE_DIR / "web"
    ICON_PATH = BUNDLE_DIR / "Icona" / "icon.ico"
else:
    BASE_DIR = Path(__file__).resolve().parent
    WEB_DIR = BASE_DIR / "web"
    ICON_PATH = BASE_DIR / "Icona" / "icon.ico"

sys.path.insert(0, str(BASE_DIR))

from core.scanner import scan_all_startup_sources
from core.deobfuscator import inspect_and_deobfuscate_item
from core.optimizer import (
    toggle_item_state,
    perform_safe_1click_optimization,
    create_backup_snapshot,
    list_backups,
    restore_backup
)
from core.system_info import get_full_system_summary
from version_manager import get_current_version_info, check_and_bump_if_modified

# Initialize Flask
app = Flask(__name__, static_folder=str(WEB_DIR))


def find_free_port() -> int:
    """Finds an available local port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


# ========================================================
# STATIC & WEB ROUTES
# ========================================================
@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(str(WEB_DIR), path)


# ========================================================
# REST API ENDPOINTS
# ========================================================
@app.route("/api/version", methods=["GET"])
def api_version():
    if not getattr(sys, "frozen", False):
        check_and_bump_if_modified("Verifica da interfaccia utente")
    info = get_current_version_info()
    return jsonify(info)


@app.route("/api/system-info", methods=["GET"])
def api_system_info():
    data = get_full_system_summary()
    return jsonify(data)


@app.route("/api/scan", methods=["GET"])
def api_scan():
    data = scan_all_startup_sources()
    return jsonify(data)


@app.route("/api/toggle", methods=["POST"])
def api_toggle():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("id")
    enabled = payload.get("enabled", True)
    confirmed_critical = payload.get("confirmed_critical", False)

    if not item_id:
        return jsonify({"success": False, "error": "ID elemento mancante."}), 400

    result = toggle_item_state(item_id, enabled, confirmed_critical=confirmed_critical)
    return jsonify(result)


@app.route("/api/optimize-safe", methods=["POST"])
def api_optimize_safe():
    result = perform_safe_1click_optimization()
    return jsonify(result)


@app.route("/api/backups", methods=["GET"])
def api_backups():
    backups = list_backups()
    return jsonify(backups)


@app.route("/api/backup", methods=["POST"])
def api_create_backup():
    result = create_backup_snapshot(name="Snapshot Manuale")
    return jsonify(result)


@app.route("/api/restore", methods=["POST"])
def api_restore_backup():
    payload = request.get_json(silent=True) or {}
    backup_id = payload.get("backup_id")
    if not backup_id:
        return jsonify({"success": False, "error": "ID backup mancante."}), 400

    result = restore_backup(backup_id)
    return jsonify(result)


@app.route("/api/open-startup", methods=["POST"])
def api_open_startup():
    folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(folder):
        os.startfile(folder)
    return jsonify({"success": True})


@app.route("/api/open-external", methods=["POST"])
def api_open_external():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "").strip()
    if url.startswith("http://") or url.startswith("https://"):
        try:
            import webbrowser
            webbrowser.open(url)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "URL non valido"}), 400


@app.route("/api/export", methods=["GET"])
def api_export():
    fmt = request.args.get("format", "json").lower()
    scan = scan_all_startup_sources()
    ver_info = get_current_version_info()
    sys_info = get_full_system_summary()

    if fmt == "html":
        items_rows = "".join([
            f"<tr><td>{i['name']}</td><td>{i.get('metadata',{}).get('company_name','-')}</td><td>{i['risk']}</td><td>{'Abilitato' if i.get('enabled') else 'Disabilitato'}</td><td>{i.get('clean_exe_path','-')}</td></tr>"
            for i in scan["all_items"]
        ])
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>InitControl Report - {sys_info['computer_model']}</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; background: #0c1017; color: #fff; padding: 24px; }}
    h1 {{ color: #D4F86A; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #1e293b; padding: 8px 12px; font-size: 13px; text-align: left; }}
    th {{ background: #131926; color: #D4F86A; }}
    tr:nth-child(even) {{ background: rgba(255,255,255,0.02); }}
  </style>
</head>
<body>
  <h1>InitControl v{ver_info['version']} - Report Analisi Avvio</h1>
  <p><strong>Computer:</strong> {sys_info['computer_model']} | <strong>OS:</strong> {sys_info['windows']['edition']}</p>
  <p><strong>Totale Elementi:</strong> {scan['summary']['total_items']} (Sicuri: {scan['summary']['safe_count']}, Attenzione: {scan['summary']['caution_count']}, Critici: {scan['summary']['critical_count']})</p>
  <table>
    <thead><tr><th>Nome</th><th>Editore</th><th>Rischio</th><th>Stato</th><th>Percorso</th></tr></thead>
    <tbody>{items_rows}</tbody>
  </table>
</body>
</html>"""
        return Response(html, mimetype="text/html")
    else:
        export_data = {
            "version": ver_info["version"],
            "system": sys_info,
            "summary": scan["summary"],
            "items": scan["all_items"]
        }
        return Response(json.dumps(export_data, indent=2), mimetype="application/json")


@app.route("/api/quit", methods=["POST"])
def api_quit():
    def do_exit():
        import time
        time.sleep(0.2)
        import os, signal
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=do_exit, daemon=True).start()
    return jsonify({"success": True})



def is_admin() -> bool:
    """Verifica se il processo corrente possiede i privilegi di amministratore."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_admin_elevation():
    """Riavvia l'applicazione con richiesta di elevazione UAC di Windows se non gia avviata come amministratore."""
    if not is_admin():
        try:
            import ctypes
            if getattr(sys, "frozen", False):
                exe = sys.executable
                params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
            else:
                python_exe = sys.executable
                script_path = str(Path(__file__).resolve())
                params = f'"{script_path}" ' + " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", python_exe, params, None, 1)

            if ret > 32:
                sys.exit(0)
        except Exception:
            pass


# ========================================================
# SERVER & PYWEBVIEW APPLICATION RUNNER
# ========================================================
def run_app():
    # Assicura sempre l'avvio con privilegi di amministratore
    request_admin_elevation()

    # Auto-bump version on source modifications
    check_and_bump_if_modified("Aggiornamento dinamico dei sorgenti")
    ver_info = get_current_version_info()
    version_str = ver_info.get("version", "0.1.1")

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Start Flask server in background thread
    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    # Determine whether to use pywebview
    use_webview = True
    try:
        import webview
    except ImportError:
        use_webview = False

    if use_webview and "--web" not in sys.argv:
        # Calculate screen center for 1260x820 window
        win_w, win_h = 1260, 820
        pos_x, pos_y = None, None

        try:
            screens = webview.screens
            if screens:
                primary = screens[0]
                pos_x = max(0, (primary.width - win_w) // 2)
                pos_y = max(0, (primary.height - win_h) // 2)
        except Exception:
            pass

        icon_file = str(ICON_PATH) if ICON_PATH.exists() else None

        window = webview.create_window(
            title=f"InitControl v{version_str} - Gestione e Ottimizzazione Avvio Windows 11",
            url=url,
            width=win_w,
            height=win_h,
            x=pos_x,
            y=pos_y,
            min_size=(1040, 680),
            background_color="#0c1017",
            text_select=True,
            resizable=True
        )

        webview.start(icon=icon_file)
    else:
        # Fallback to default browser
        import webbrowser
        print(f"InitControl in esecuzione su: {url}")
        webbrowser.open(url)
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run_app()
