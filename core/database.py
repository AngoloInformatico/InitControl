"""
InitControl Knowledge Base & Process Intelligence Database
Contains definitions for known Windows startup items, publishers, risk ratings,
and heuristics for de-obfuscation and impact analysis.
"""

# Risk levels: "VERDE" (Safe to Disable), "GIALLO" (Caution), "ROSSO" (Critical)
# Categories: "Software Utente" (User Apps), "Processi di Sistema & Servizi" (System Processes/Services)

KNOWN_PROCESSES_DB = {
    # Microsoft Core System & Security (ROSSO)
    "securityhealthsystray.exe": {
        "name": "Sicurezza di Windows (Systray)",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Disabilita l'icona e le notifiche di stato di Windows Defender/Sicurezza di Windows nell'area di notifica.",
        "description": "Questo processo gestisce l'interfaccia utente dell'area di notifica di Windows Security e gli avvisi di protezione in tempo reale.",
        "safe_to_disable": False
    },
    "msmpeng.exe": {
        "name": "Antivirus Microsoft Defender",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Disabilitare espone il computer a minacce malware e viola le policy di sicurezza di Windows 11.",
        "description": "Motore principale di scansione ed esecuzione dell'antivirus nativo Microsoft Defender.",
        "safe_to_disable": False
    },
    "ctfmon.exe": {
        "name": "CTF Loader (Input e Tastiere)",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Controlla il supporto per tastiere alternative, riconoscimento vocale, scrittura a mano e input IME.",
        "description": "Componente di input di Windows per metodi di inserimento alternativi e commutazione layout tastiera.",
        "safe_to_disable": False
    },
    "explorer.exe": {
        "name": "Esplora Risorse (Windows Shell)",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Shell desktop principale, barra delle applicazioni e gestione finestre.",
        "description": "Interfaccia grafica primaria del sistema operativo Windows.",
        "safe_to_disable": False
    },
    "runtimebroker.exe": {
        "name": "Runtime Broker",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Gestisce i permessi e la sicurezza per le app UWP e dello Store.",
        "description": "Processo core di Windows che controlla l'accesso alle risorse hardware (fotocamera, microfono, posizione) da parte delle app.",
        "safe_to_disable": False
    },
    "svchost.exe": {
        "name": "Host Servizi di Windows (Generic Host)",
        "publisher": "Microsoft Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "ROSSO",
        "impact": "Critico. Ospita molteplici servizi essenziali del sistema operativo.",
        "description": "Processo di sistema condiviso utilizzato per eseguire librerie dinamiche di servizi Windows.",
        "safe_to_disable": False
    },

    # Drivers & Peripheral Helpers (GIALLO)
    "nvcontainer.exe": {
        "name": "NVIDIA Container Host",
        "publisher": "NVIDIA Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "GIALLO",
        "impact": "Attenzione. Gestisce l'overlay GeForce Experience, ShadowPlay e alcune scorciatoie grafiche.",
        "description": "Processo contenitore di NVIDIA per servizi di telemetria, GeForce Experience e funzionalità grafiche accessorie.",
        "safe_to_disable": False
    },
    "nvdisplay.container.exe": {
        "name": "NVIDIA Display Container LS",
        "publisher": "NVIDIA Corporation",
        "category": "Processi di Sistema & Servizi",
        "risk": "GIALLO",
        "impact": "Attenzione. Necessario per il pannello di controllo NVIDIA e la configurazione display avanzata.",
        "description": "Servizio di supporto per il pannello di controllo NVIDIA e la gestione dei profili schermo.",
        "safe_to_disable": False
    },
    "ravcpl64.exe": {
        "name": "Realtek HD Audio Control Panel",
        "publisher": "Realtek Semiconductor Corp.",
        "category": "Processi di Sistema & Servizi",
        "risk": "GIALLO",
        "impact": "Basso/Medio. La disattivazione impedisce l'apertura automatica del pannello Realtek al jack inserito.",
        "description": "Pannello di configurazione per codec audio Realtek ad alta definizione.",
        "safe_to_disable": True
    },
    "rtkngui64.exe": {
        "name": "Realtek Audio GUI",
        "publisher": "Realtek Semiconductor Corp.",
        "category": "Processi di Sistema & Servizi",
        "risk": "GIALLO",
        "impact": "Basso/Medio. Interfaccia grafica audio Realtek.",
        "description": "Gestione equalizzatore e rilevamento jack audio.",
        "safe_to_disable": True
    },
    "lghub.exe": {
        "name": "Logitech G HUB",
        "publisher": "Logitech Inc.",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. Disattiva il caricamento automatico dei profili DPI del mouse, illuminazione RGB e macro.",
        "description": "Software di gestione periferiche gaming Logitech. All'avvio carica profili e illuminazione.",
        "safe_to_disable": True
    },
    "razer synapse service.exe": {
        "name": "Razer Synapse Companion",
        "publisher": "Razer Inc.",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. Profili tastiera/mouse Razer non caricati finché l'app non viene avviata a mano.",
        "description": "Software cloud-based di configurazione hardware per periferiche Razer.",
        "safe_to_disable": True
    },
    "icue.exe": {
        "name": "Corsair iCUE Software",
        "publisher": "Corsair Memory, Inc.",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. Luci RGB e curve di raffreddamento ventole Corsair torneranno ai valori hardware di default.",
        "description": "Software di monitoraggio e controllo RGB per componenti e periferiche Corsair.",
        "safe_to_disable": True
    },
    "onedrive.exe": {
        "name": "Microsoft OneDrive Sync Engine",
        "publisher": "Microsoft Corporation",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. La sincronizzazione dei file sul cloud non avverrà automaticamente all'accesso.",
        "description": "Client di sincronizzazione cloud Microsoft OneDrive. Disabilitabile se non si necessita di sincronizzazione immediata.",
        "safe_to_disable": True
    },
    "googledrivesync.exe": {
        "name": "Google Drive Desktop",
        "publisher": "Google LLC",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. File e cartelle non verranno sincronizzati fino all'avvio manuale dell'app.",
        "description": "Client di sincronizzazione file Google Drive per computer.",
        "safe_to_disable": True
    },
    "dropbox.exe": {
        "name": "Dropbox Client",
        "publisher": "Dropbox, Inc.",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. File non sincronizzati in background all'avvio.",
        "description": "Client di archiviazione e condivisione file Dropbox.",
        "safe_to_disable": True
    },

    # Common User Software (VERDE - Safe to disable)
    "discord.exe": {
        "name": "Discord Voice & Chat",
        "publisher": "Discord Inc.",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. L'avvio dell'app è semplicemente rimandato a quando l'utente la apre manualmente.",
        "description": "Piattaforma di comunicazione vocale e messaggistica per community e gamer.",
        "safe_to_disable": True
    },
    "spotify.exe": {
        "name": "Spotify Music Streaming",
        "publisher": "Spotify AB",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Riduce significativamente il tempo di boot e l'uso iniziale di memoria RAM.",
        "description": "Applicazione desktop per lo streaming musicale e podcast di Spotify.",
        "safe_to_disable": True
    },
    "steam.exe": {
        "name": "Steam Gaming Client",
        "publisher": "Valve Corporation",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Risparmia fino a 350 MB di RAM all'avvio del computer.",
        "description": "Piattaforma di distribuzione digitale e community gaming di Valve.",
        "safe_to_disable": True
    },
    "epicgameslauncher.exe": {
        "name": "Epic Games Launcher",
        "publisher": "Epic Games, Inc.",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Evita l'avvio in background dell'engine Unreal e dello store.",
        "description": "Client launcher per giochi e motore grafico Unreal Engine.",
        "safe_to_disable": True
    },
    "telegram.exe": {
        "name": "Telegram Desktop",
        "publisher": "Telegram FZ-LLC",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Non riceverai notifiche finché non aprirai l'applicazione.",
        "description": "Client desktop ufficiale dell'app di messaggistica istantanea Telegram.",
        "safe_to_disable": True
    },
    "whatsapp.exe": {
        "name": "WhatsApp Desktop",
        "publisher": "Meta Platforms, Inc.",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Avvio ritardato all'apertura manuale.",
        "description": "Applicazione desktop per messaggi e chiamate WhatsApp.",
        "safe_to_disable": True
    },
    "ms-teams.exe": {
        "name": "Microsoft Teams (Work/Personal)",
        "publisher": "Microsoft Corporation",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Molto consigliato disabilitarlo per velocizzare l'avvio su Windows 11.",
        "description": "Hub di collaborazione e riunioni di Microsoft. Ha un elevato impatto sui tempi di boot.",
        "safe_to_disable": True
    },
    "teams.exe": {
        "name": "Microsoft Teams Classic",
        "publisher": "Microsoft Corporation",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Notevole risparmio di RAM e CPU durante l'accesso utente.",
        "description": "Versione classica dell'applicazione Microsoft Teams.",
        "safe_to_disable": True
    },
    "docker desktop.exe": {
        "name": "Docker Desktop",
        "publisher": "Docker Inc.",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo se non si sviluppa immediatamente all'avvio. Risparmia oltre 1.5 GB di RAM (WSL2 VM).",
        "description": "Ambiente di containerizzazione per sviluppatori con supporto WSL2 e Kubernetes locale.",
        "safe_to_disable": True
    },
    "iperius.exe": {
        "name": "Iperius Backup Suite",
        "publisher": "Enter Srl",
        "category": "Software Utente",
        "risk": "GIALLO",
        "impact": "Attenzione. Se si usano backup automatici all'accesso, l'agente deve rimanere attivo.",
        "description": "Software di backup e replica dati su cloud, NAS e disco locale.",
        "safe_to_disable": True
    },
    "robloxplayerbeta.exe": {
        "name": "Roblox Player Launcher",
        "publisher": "Roblox Corporation",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Riduce i processi inutili in background.",
        "description": "Client di gioco e launcher rapido per la piattaforma Roblox.",
        "safe_to_disable": True
    },
    "anydesk.exe": {
        "name": "AnyDesk Remote Desktop",
        "publisher": "AnyDesk Software GmbH",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Il servizio o app partirà solo quando lanciato o se configurato con accesso non presidiato.",
        "description": "Software di controllo remoto del desktop ad alte prestazioni.",
        "safe_to_disable": True
    },
    "teamviewer.exe": {
        "name": "TeamViewer Remote Access",
        "publisher": "TeamViewer Germany GmbH",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Disabilita l'icona in tray all'avvio.",
        "description": "Applicazione di assistenza e connessione remota sicura.",
        "safe_to_disable": True
    },
    "ccleaner.exe": {
        "name": "CCleaner Monitoring Tool",
        "publisher": "Piramiform Software Ltd",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Evita il monitoraggio continuo in background e notifiche promozionali.",
        "description": "Modulo di pulizia e monitoraggio dello spazio su disco.",
        "safe_to_disable": True
    },
    "bitwarden.exe": {
        "name": "Bitwarden Desktop",
        "publisher": "Bitwarden Inc.",
        "category": "Software Utente",
        "risk": "VERDE",
        "impact": "Nullo. Gestore password sicuro, apribile all'occorrenza.",
        "description": "Client desktop per la cassaforte password e credenziali Bitwarden.",
        "safe_to_disable": True
    }
}

KNOWN_PUBLISHERS = {
    "microsoft corporation": {"risk": "ROSSO_OR_CORE", "reputation": "Ufficiale Microsoft"},
    "nvidia corporation": {"risk": "GIALLO", "reputation": "Driver GPU & Hardware"},
    "advanced micro devices": {"risk": "GIALLO", "reputation": "Driver AMD & Radeon"},
    "intel corporation": {"risk": "GIALLO", "reputation": "Chipset & Driver Intel"},
    "realtek semiconductor": {"risk": "GIALLO", "reputation": "Driver Audio/Network Realtek"},
    "valve corporation": {"risk": "VERDE", "reputation": "Software Gaming Steam"},
    "discord inc.": {"risk": "VERDE", "reputation": "Chat & Voce Utente"},
    "spotify ab": {"risk": "VERDE", "reputation": "Streaming Musicale"},
    "google llc": {"risk": "VERDE", "reputation": "Applicazioni Google"},
    "docker inc.": {"risk": "VERDE", "reputation": "Strumenti Sviluppo Container"}
}


def lookup_process_intelligence(exe_name: str, file_path: str = "", publisher: str = "") -> dict:
    """
    Looks up process intelligence from database or synthesizes intelligent analysis
    for unknown binaries using internal heuristics.
    """
    clean_name = exe_name.lower().strip()
    if clean_name in KNOWN_PROCESSES_DB:
        info = dict(KNOWN_PROCESSES_DB[clean_name])
        info["known"] = True
        info["match_type"] = "Database Signature"
        return info

    # Heuristic analysis for unknown binaries
    is_system_path = False
    lower_path = file_path.lower() if file_path else ""
    if any(p in lower_path for p in ["\\windows\\system32", "\\windows\\syswow64", "\\windows\\systemapps"]):
        is_system_path = True

    is_user_appdata = "\\appdata\\" in lower_path or "\\local\\temp\\" in lower_path
    pub_lower = publisher.lower() if publisher else ""

    # Check publisher
    if "microsoft" in pub_lower:
        if is_system_path:
            return {
                "name": clean_name,
                "publisher": publisher or "Microsoft Corporation",
                "category": "Processi di Sistema & Servizi",
                "risk": "ROSSO",
                "impact": "Attenzione elevata. Processo firmato Microsoft situato nelle directory core di Windows.",
                "description": f"Questo processo appartiene al sottosistema di Windows ('{clean_name}'). Verificare attentamente prima di disabilitarlo.",
                "safe_to_disable": False,
                "known": False,
                "match_type": "Microsoft System Heuristic"
            }
        else:
            return {
                "name": clean_name,
                "publisher": publisher or "Microsoft Corporation",
                "category": "Software Utente",
                "risk": "GIALLO",
                "impact": "Impatto moderato. Componente accessorio o app Microsoft distribuita nello spazio utente.",
                "description": f"Applicazione o componente software Microsoft situato in percorso utente ('{clean_name}').",
                "safe_to_disable": True,
                "known": False,
                "match_type": "Microsoft User Heuristic"
            }

    # Unknown Third-party in AppData or Temp
    if "\\local\\temp\\" in lower_path:
        return {
            "name": clean_name,
            "publisher": publisher or "Sconosciuto (Non Firmato)",
            "category": "Software Utente",
            "risk": "GIALLO",
            "impact": "Sospetto. Eseguibile situato nella cartella temporanea Temp. Spesso associato a installer incompleti o malware.",
            "description": f"Questo file ('{clean_name}') è collocato nei file temporanei dell'utente. Si consiglia vivamente una scansione con l'antivirus.",
            "safe_to_disable": True,
            "known": False,
            "match_type": "Suspicious Temp Location Heuristic"
        }

    if is_user_appdata:
        return {
            "name": clean_name,
            "publisher": publisher or "Editore Terze Parti",
            "category": "Software Utente",
            "risk": "VERDE",
            "impact": "Nullo o trascurabile. Eseguibile installato nell'ambiente utente (AppData). Disabilitabile in piena sicurezza.",
            "description": f"Questo processo appartiene a un'applicazione installata nello spazio utente ({publisher or 'Non firmato'}). La disabilitazione non compromette l'integrità del sistema operativo.",
            "safe_to_disable": True,
            "known": False,
            "match_type": "User AppData Heuristic"
        }

    # Generic Program Files / ProgramData
    return {
        "name": clean_name,
        "publisher": publisher or "Editore Terze Parti",
        "category": "Software Utente" if not is_system_path else "Processi di Sistema & Servizi",
        "risk": "VERDE" if not is_system_path else "GIALLO",
        "impact": "Sicuro da disattivare se non strettamente necessario all'avvio." if not is_system_path else "Attenzione. Servizio/driver di sistema terze parti.",
        "description": f"Questo processo appartiene al programma installato in '{file_path}'. Scopo tipico: avvio automatico all'accesso utente per velocizzare l'apertura.",
        "safe_to_disable": not is_system_path,
        "known": False,
        "match_type": "Standard Program Heuristic"
    }
