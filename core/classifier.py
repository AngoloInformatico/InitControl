"""
Classifier and Risk Assessment Engine for InitControl.
Enforces strict 2-tier categorization (Software Utente vs Processi di Sistema & Servizi)
and the 3-tier Traffic Light Rating System (VERDE, GIALLO, ROSSO).
"""

def classify_and_rate_item(item_data: dict) -> dict:
    """
    Evaluates an item (registry, startup folder, service, scheduled task)
    and assigns:
    1. Category: "Software Utente" | "Processi di Sistema & Servizi"
    2. Risk Rating: "VERDE" | "GIALLO" | "ROSSO"
    3. Impact Description & Safe to Disable flag
    """
    intel = item_data.get("intelligence", {})
    metadata = item_data.get("metadata", {})
    source_type = item_data.get("source_type", "")  # "Registry", "StartupFolder", "Service", "Task"
    clean_path = item_data.get("clean_exe_path", "").lower()
    filename = item_data.get("filename", "").lower()
    company = (metadata.get("company_name") or item_data.get("publisher") or "").lower()

    # If the intelligence DB already has a direct match, use it as baseline
    category = intel.get("category", "")
    risk = intel.get("risk", "")
    impact = intel.get("impact", "")
    safe_to_disable = intel.get("safe_to_disable", True)

    # Core System Folders
    is_windows_core_dir = any(
        dir_marker in clean_path
        for dir_marker in [
            "\\windows\\system32\\",
            "\\windows\\syswow64\\",
            "\\windows\\systemapps\\",
            "\\windows\\winsxs\\"
        ]
    )

    # Windows Defender / Antivirus / Kernel
    is_security_or_core = (
        "defender" in filename
        or "msmpeng" in filename
        or "securityhealth" in filename
        or "smartscreen" in filename
        or "csrss" in filename
        or "lsass" in filename
        or "services.exe" in filename
        or "wininit" in filename
        or "smss" in filename
    )

    # If it is a Windows Core component or critical security
    if is_security_or_core or (is_windows_core_dir and ("microsoft" in company or not company)):
        category = "Processi di Sistema & Servizi"
        risk = "ROSSO"
        safe_to_disable = False
        impact = "Critico. Componente fondamentale di Windows o sottosistema di sicurezza. Rischio instabilità o BSOD."

    # If not determined yet, evaluate category
    if not category:
        if source_type in ["StartupFolder", "Registry"]:
            if is_windows_core_dir:
                category = "Processi di Sistema & Servizi"
            else:
                category = "Software Utente"
        elif source_type == "Service":
            # Services that are third party vs Microsoft
            if "microsoft" in company or is_windows_core_dir:
                category = "Processi di Sistema & Servizi"
            else:
                category = "Software Utente"
        elif source_type == "Task":
            if "\\microsoft\\windows\\" in item_data.get("source_location", "").lower():
                category = "Processi di Sistema & Servizi"
            else:
                category = "Software Utente"
        else:
            category = "Software Utente"

    # Evaluate Risk Rating if not ROSSO
    if risk != "ROSSO":
        # Critical drivers / OEM firmware
        if any(w in filename or w in clean_path for w in ["acpi", "storport", "iaStorA", "intel_rst"]):
            risk = "ROSSO"
            safe_to_disable = False
            impact = "Critico. Driver controller di archiviazione o alimentazione essenziale."
        # Caution items (GIALLO): Mouse/Keyboard software, GPU control panels, sync engines, updater services
        elif any(w in filename for w in ["synapse", "lghub", "icue", "onedrive", "dropbox", "googledrive", "nvcontainer", "radeon", "update", "helper", "service"]):
            risk = "GIALLO"
            safe_to_disable = True
            if not impact:
                impact = "Attenzione. Servizio accessorio o software di supporto periferiche. Perdita di funzionalità accessorie."
        elif category == "Processi di Sistema & Servizi":
            risk = "GIALLO"
            safe_to_disable = False
            if not impact:
                impact = "Attenzione. Servizio di sistema secondario. Si raccomanda prudenza."
        else:
            # Safe to disable (VERDE)
            risk = "VERDE"
            safe_to_disable = True
            if not impact:
                impact = "Sicuro. Software applicativo utente. Impatto sul sistema: nullo. Risparmia RAM e riduce il boot time."

    # Strict badge colors and CSS mapping
    rating_data = {
        "VERDE": {
            "label": "Sicuro (Safe to Disable)",
            "badge_class": "badge-safe",
            "hex": "#00E676",
            "icon": "shield-check"
        },
        "GIALLO": {
            "label": "Attenzione (Caution)",
            "badge_class": "badge-caution",
            "hex": "#FFD600",
            "icon": "alert-triangle"
        },
        "ROSSO": {
            "label": "Critico (Critical / Bloccato)",
            "badge_class": "badge-critical",
            "hex": "#FF1744",
            "icon": "shield-alert"
        }
    }

    return {
        "category": category,
        "risk": risk,
        "risk_meta": rating_data.get(risk, rating_data["VERDE"]),
        "safe_to_disable": safe_to_disable,
        "impact_description": impact
    }
