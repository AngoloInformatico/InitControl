# 📜 Il Manifesto di InitControl
### *La Sovranità dell'Utente, la Trasparenza Totale e la Fine dei Punti Ciechi di Windows*

[![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010%20(x64)-0078D4?logo=windows&logoColor=white)](https://github.com/AngoloInformatico)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Alex%20Lignola%20%7C%20Angolo%20Informatico-D4F86A?logo=youtube&logoColor=black)](https://www.youtube.com/@AngoloInformatico)

---

## 🏛️ 1. La Nostra Filosofia: Il Tuo Computer Ti Appartiene

Quando accendi il tuo computer, ogni singolo ciclo di clock della CPU, ogni megabyte di memoria RAM e ogni lettura dal tuo disco SSD dovrebbero essere al servizio di **un unico padrone: TU**.

Negli ultimi anni, l'ecosistema del software moderno ha intrapreso una direzione preoccupante:
- Applicazioni di messaggistica, launcher di videogiochi, client cloud e assistenti AI si arrogano il diritto di **auto-configurarsi all'avvio del sistema**, spesso senza chiedere il consenso o nascondendosi dietro opzioni oscure.
- I sistemi operativi commerciali forniscono strumenti di gestione sempre più semplificati e opachi, che lasciano l'utente nell'illusione di avere il controllo, mentre **decine di processi in background continuano a girare indisturbati**, rubando tempo di accensione, privacy e autonomia della batteria.

> **Il principio cardine di InitControl:**  
> *"Nessun programma deve avviarsi alle tue spalle. Ciò che viene eseguito sul tuo sistema deve essere visibile, comprensibile, verificabile e disattivabile in piena sicurezza."*

---

## ⚠️ 2. L'Illusione di Gestione Attività (Task Manager)

La maggior parte degli utenti si affida alla scheda *App di avvio* di **Gestione Attività (Task Manager)** di Windows. Purtroppo, questa scheda rappresenta solo la punta dell'iceberg:

1. **Punti Ciechi Enormi**: Il Task Manager classico mostra quasi esclusivamente i file registrati nella chiave utente base (`HKCU\...\Run`). Ignora completamente il registro a 32-bit su sistemi a 64-bit (`WoW6432Node`), le chiavi `RunOnce`, le cartelle Startup globali di sistema, i **servizi di terze parti** in esecuzione automatica e le **attività pianificate (Scheduled Tasks)** che scattano all'accesso.
2. **Nomi Fuorvianti ed Editore Sconosciuto**: Quante volte hai visto voci chiamate semplicemente *"Update"*, *"Helper"*, o con un'icona generica e la dicitura *"Editore non disponibile"*? Windows non aiuta l'utente a capire cosa sia quel processo.
3. **La Paura di Disabilitare**: Poiché Gestione Attività elenca processi critici di sistema accanto a software inutili senza alcuna distinzione di colore o spiegazione, l'utente medio ha **terrore di toccare qualsiasi cosa**, temendo schermate blu (BSOD) o il blocco del PC.
4. **Il Blocco dei Pacchetti Moderni (MSIX / Store)**: Nelle app moderne del Microsoft Store (come Claude, WhatsApp e molte altre), Windows assegna permessi restrittivi (DACL) ai propri servizi di supporto, impedendo perfino agli amministratori di disattivare il servizio dalle schermate standard (*"Accesso negato"*).

**InitControl è nato per distruggere queste barriere.**

---

## 🛡️ 3. I 7 Pilastri Fondamentali di InitControl

```
+-------------------------------------------------------------------------------+
|                             INITCONTROL WORKSTATION                           |
+-------------------+-------------------+-------------------+-------------------+
| 1. Persistenza    | 2. Valutazione    | 3. Kernel Guard   | 4. Ispezione      |
|    a 360 Gradi    |    a Semaforo     |    Anti-BSOD      |    Header PE      |
+-------------------+-------------------+-------------------+-------------------+
| 5. Sblocco Servizi| 6. Ottimizzazione | 7. Metriche Reali | 8. Privacy Totale |
|    MSIX / Store   |    con Snapshot   |    Boot Impact    |    Zero Telemetria|
+-------------------+-------------------+-------------------+-------------------+
```

### 1️⃣ Copertura Totale della Persistenza
InitControl esamina in parallelo:
- Registro Utente `HKCU\...\Run` e `RunOnce`
- Registro Sistema `HKLM\...\Run` e `RunOnce` (x64)
- Registro Compatibilità `HKLM\Software\WOW6432Node\...\Run` (x86)
- Cartelle di avvio Utente (`%APPDATA%\...\Startup`) e Globale (`%PROGRAMDATA%\...\Startup`)
- Servizi Windows di terze parti (Auto, Delayed-Auto e Disabilitati riattivabili)
- Attività Pianificate (Scheduled Tasks con trigger di Logon)

### 2️⃣ Intelligenza Euristica a Semaforo (Guida Visuale)
Ogni singolo elemento rilevato viene analizzato e contrassegnato con un rating cromatico univoco:
- 🟢 **VERDE (Sicuro)**: Applicazioni utente non essenziali (Spotify, Steam, Discord, Telegram, agenti di supporto). Disattivabili subito per liberare memoria e tempo di boot senza alcun rischio.
- 🟡 **GIALLO (Attenzione)**: Driver audio, utility della scheda video, pannelli di controllo periferiche.
- 🔴 **ROSSO (Critico di Sistema)**: Moduli di sicurezza, kernel Windows, Windows Security Health, crittografia.

### 3️⃣ Kernel Guard: La Protezione Attiva contro i Crash
Su Windows Gestione Attività puoi cliccare su "Disabilita" su un file essenziale senza che nessuno ti avverta.  
In InitControl, il motore **Kernel Guard** intercetta qualsiasi tentativo di disattivare un processo classificato come **ROSSO**. L'interfaccia blocca lo switch e apre una finestra di sicurezza che spiega la funzione del processo e richiede una **doppia conferma esplicita**, azzerando il rischio di instabilità o mancato avvio.

### 4️⃣ De-Offuscamento Strutturato & Ispezione PE
InitControl non legge il nome superficiale, ma apre l'eseguibile binario ed esamina approfonditamente l'header PE (Portable Executable):
- Verifica la **Firma Digitale Authenticode** (se il file è firmato da un'azienda verificata o se è un binario anonimo).
- Estrae il vero Editore, Nome Interno, Versione del Prodotto e Descrizione del file.
- Calcola in tempo reale l'impronta crittografica **SHA-256** del file, con pulsante rapido per il confronto immediato su **VirusTotal** e ricerca Google.

### 5️⃣ Sblocco Reale dei Servizi Protetti (MSIX / Store)
Grazie a un'architettura **a 3 livelli di controllo**:
1. API standard Service Control Manager (`sc.exe config start= auto|disabled`)
2. PowerShell Cmdlet (`Set-Service`)
3. **Scrittura Diretta nel Registro HKLM** con token di amministratore per i servizi bloccati da DACL restrittive (es. pacchetti MSIX come Claude `CoworkVMService`) e arresto in tempo reale del processo in memoria.

### 6️⃣ Ottimizzazione Sicura 1-Click con Paracadute di Ripristino
Il pulsante **"Ottimizzazione Sicura 1-Click"** permette a chiunque di velocizzare il PC all'istante:
- Crea automaticamente uno **Snapshot di Backup JSON** completo dello stato attuale.
- Disattiva tutti i processi e servizi non essenziali (verdi), preservando driver e componenti di sistema.
- In qualunque momento, dalla sezione **Punti di Ripristino**, l'utente può cliccare su **Ripristina Snapshot** per riportare l'avvio del computer esattamente alle condizioni originali.

### 7️⃣ Diagnostica Quantitativa del Boot Impact
Niente più stime generiche come "Impatto di avvio: Medio".  
InitControl calcola un **Efficiency Score percentuale (0-100%)**, mostra un **Tachimetro SVG radiale**, calcola i **secondi effettivi risparmiati al boot** e visualizza i parametri hardware vitali (Cores CPU, RAM utilizzata/libera, modello disco e build specifica di Windows 11).

---

## 📊 4. Tabella Comparativa di Riepilogo

| Capacità | Gestione Attività di Windows | Monitoraggio Risorse (Resmon) | 🚀 **InitControl** |
| :--- | :---: | :---: | :---: |
| **Persistenza Nascosta (WoW64/Task)** | ❌ No | ❌ No | **✅ Sì, 100% coperta** |
| **Spiegazione Chiara del Ruolo** | ❌ No | ❌ No | **✅ Sì, con euristica estesa** |
| **Firma Digitale & Hash SHA256** | ❌ No | ❌ No | **✅ Sì, integrato con VirusTotal** |
| **Intervento su Servizi Bloccati** | ❌ Errore "Accesso negato" | ❌ Non gestibile | **✅ Sì, override amministrativo** |
| **Pulsante Ottimizza in 1 Clic** | ❌ Assente | ❌ Assente | **✅ Sì, algoritmo Safe** |
| **Rollback & Snapshot di Ripristino** | ❌ Assente | ❌ Assente | **✅ Sì, cronologia snapshot** |
| **Design Moderno & Temi Dark/Light** | ⚪ Standard grigio | ⚪ Stile Windows 7 | **✅ Dark Obsidian & Light Mica** |

---

## 🔒 5. Trasparenza e Privacy Assoluta

- **Zero Telemetria**: Nessun dato, elenco software, indirizzo IP o informazione hardware viene mai inviato a server esterni. Tutto viene elaborato localmente nella memoria del tuo computer.
- **100% Open Source**: Rilasciato sotto la licenza **GNU General Public License v3.0 (GPLv3)**. Il codice è pubblico, verificabile e modificabile da chiunque.
- **Zero Installatori Invasivi**: Compilabile in un unico file standalone `.exe` portabile da circa 18 MB, senza dipendenze e pronto all'uso.

---

## 👨‍💻 Autore e Canali Ufficiali

Creato con passione da **Alex Lignola**:
- 📺 **YouTube**: [@AngoloInformatico](https://www.youtube.com/@AngoloInformatico)
- 🐙 **GitHub**: [AngoloInformatico](https://github.com/AngoloInformatico)
- 📦 **Repository Ufficiale**: [InitControl su GitHub](https://github.com/AngoloInformatico/InitControl)

*Created by Alex Lignola - © 2026 InitControl - All rights reserved.*
