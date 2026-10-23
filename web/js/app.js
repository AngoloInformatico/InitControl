/**
 * InitControl - Windows 11 Startup Optimizer & Internals Manager
 * Frontend Logic, State Management, Traffic Light Engine & API Controller
 */

// Application State
const state = {
  currentView: "dashboard",
  scanData: null,
  systemInfo: null,
  activeFilters: {
    userRisk: "all",
    userState: "all",
    systemRisk: "all",
    searchUser: "",
    searchSystem: "",
    searchTasks: "",
    searchDeobf: ""
  },
  pendingCriticalToggle: null
};

// ========================================================
// INITIALIZATION
// ========================================================
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupNavigation();
  setupEventListeners();
  addLog("InitControl frontend caricato con successo.", "info");
  
  // Load initial data
  loadVersion();
  loadSystemInfo();
  triggerScan();
  loadBackups();
});

// ========================================================
// LOGGING SYSTEM (Console Operazioni)
// ========================================================
function addLog(message, type = "info") {
  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0];

  const logHtml = `
    <div class="log-line">
      <span class="log-time">${timeStr}</span>
      <span class="log-msg ${type}">[${type.toUpperCase()}] ${escapeHtml(message)}</span>
    </div>
  `;

  const miniConsole = document.getElementById("terminalLogs");
  const fullConsole = document.getElementById("terminalLogsFull");

  if (miniConsole) {
    miniConsole.insertAdjacentHTML("beforeend", logHtml);
    miniConsole.scrollTop = miniConsole.scrollHeight;
  }
  if (fullConsole) {
    fullConsole.insertAdjacentHTML("beforeend", logHtml);
    fullConsole.scrollTop = fullConsole.scrollHeight;
  }
}

// ========================================================
// NAVIGATION ROUTING
// ========================================================
function setupNavigation() {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const targetView = item.getAttribute("data-view");
      switchView(targetView);
    });
  });

  // Action buttons that navigate
  document.querySelectorAll("[data-nav]").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetView = btn.getAttribute("data-nav");
      switchView(targetView);
    });
  });
}

function switchView(viewName) {
  state.currentView = viewName;

  // Update sidebar active classes
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-view") === viewName);
  });

  // Update panels
  document.querySelectorAll(".view-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === `view-${viewName}`);
  });

  // Update header title
  const titles = {
    "dashboard": ["Dashboard", "Flusso di ottimizzazione e stato dell'avvio di sistema"],
    "user-software": ["Software Utente", "Applicazioni installate e programmi ad avvio automatico"],
    "system-processes": ["Processi & Servizi", "Processi core del sistema operativo e servizi di background"],
    "scheduled-tasks": ["Attività Pianificate", "Task dello Scheduler eseguiti al logon dell'utente"],
    "risk-matrix": ["Analisi di Rischio a Semaforo", "Matrice di valutazione e protezione dell'integrità del sistema"],
    "deobfuscation": ["De-Offuscamento & Intelligence", "Ispezione approfondita di binari, firme digitali e hash SHA256"],
    "backup-tools": ["Strumenti & Punti di Ripristino", "Ottimizzazione guidata 1-clic e gestione snapshot"],
    "console-log": ["Console & Log Operazioni", "Registro completo in tempo reale dei comandi e delle azioni"],
    "about-info": ["Informazioni", "Dettagli architettura, versione e Windows Internals"]
  };

  const [t, s] = titles[viewName] || ["InitControl", ""];
  document.getElementById("topHeaderTitle").innerText = t;
  document.getElementById("topHeaderSubtitle").innerText = s;
}

// ========================================================
// DATA LOADING & API CALLS
// ========================================================
async function loadVersion() {
  try {
    const res = await fetch("/api/version");
    const data = await res.json();
    if (data.version) {
      document.getElementById("sidebarVersion").innerText = `v${data.version}`;
      const badge = document.getElementById("aboutVersionBadge");
      if (badge) {
        badge.innerText = `v${data.version} (Build #${data.build || 1})`;
      }
    }
  } catch (err) {
    console.warn("Versione locale:", err);
  }
}

async function loadSystemInfo() {
  try {
    const res = await fetch("/api/system-info");
    const data = await res.json();
    state.systemInfo = data;
    renderSystemInfo(data);
    addLog(`Parametri hardware rilevati: ${data.cpu.name} | RAM: ${data.memory.total_gb} GB`, "info");
  } catch (err) {
    addLog("Impossibile caricare parametri di sistema: " + err.message, "error");
  }
}

function renderSystemInfo(data) {
  if (!data) return;

  document.getElementById("specModel").innerText = data.computer_model || "PC Windows 11";
  document.getElementById("specCpu").innerText = `${data.cpu.name} (${data.cpu.cores_physical}C/${data.cpu.cores_logical}T)`;
  document.getElementById("specInstruction").innerText = data.cpu.instruction_set;
  document.getElementById("specRam").innerText = `${data.memory.total_gb} GB (${data.memory.used_gb} GB usati)`;
  document.getElementById("specDisk").innerText = `${data.disk.free_gb} GB liberi su ${data.disk.total_gb} GB`;
  document.getElementById("specOs").innerText = `${data.windows.edition} - ${data.windows.version_tag}`;
  document.getElementById("topWinVersion").innerText = data.windows.edition;

  const adminPill = document.getElementById("adminStatusPill");
  const adminText = document.getElementById("adminStatusText");
  const specAdmin = document.getElementById("specAdmin");

  if (data.is_admin) {
    adminPill.className = "admin-status-pill";
    adminText.innerText = "Amministratore (Attivo)";
    specAdmin.innerText = "Attivo / Privilegi Elevati";
    specAdmin.style.color = "var(--accent-green)";
  } else {
    adminPill.className = "admin-status-pill not-admin";
    adminText.innerText = "Privilegi Standard";
    specAdmin.innerText = "Standard (Non Amministratore)";
    specAdmin.style.color = "var(--accent-yellow)";
  }
}

async function triggerScan() {
  addLog("Avvio scansione approfondita di tutti gli internals di avvio...", "info");
  showToast("Scansione in corso...", "info");

  try {
    const res = await fetch("/api/scan");
    const data = await res.json();
    state.scanData = data;

    addLog(`Scansione completata: ${data.summary.total_items} elementi rilevati.`, "success");
    addLog(`Ripartizione: ${data.summary.user_software_count} Software Utente, ${data.summary.system_processes_count} Processi & Servizi.`, "info");
    addLog(`Rating: ${data.summary.safe_count} Sicuri (Verde), ${data.summary.caution_count} Attenzione (Giallo), ${data.summary.critical_count} Critici (Rosso).`, "info");

    renderDashboardSummary(data.summary);
    renderUserSoftwareList();
    renderSystemProcessesList();
    renderScheduledTasksList();
    renderDeobfuscateList();
    renderRiskMatrix();

    showToast(`Scansione completata: ${data.summary.total_items} elementi rilevati.`, "success");
  } catch (err) {
    addLog("Errore durante la scansione: " + err.message, "error");
    showToast("Errore di scansione", "error");
  }
}

// ========================================================
// DASHBOARD RENDERING & GAUGE ANIMATION
// ========================================================
function renderDashboardSummary(summary) {
  // Update sidebar counter badges
  document.getElementById("badgeUserCount").innerText = summary.user_software_count;
  document.getElementById("badgeSystemCount").innerText = summary.system_processes_count;
  document.getElementById("badgeTaskCount").innerText = summary.tasks_count;

  // System specs items ratio
  document.getElementById("specItemsRatio").innerText = `${summary.enabled_count} Abilitati / ${summary.total_items} Totali`;

  // Hero Boot Times
  const baseBoot = 5.0 + (summary.enabled_count * 0.4);
  const targetBoot = Math.max(4.5, baseBoot - summary.estimated_saved_seconds);
  const reductionPct = Math.round(((baseBoot - targetBoot) / baseBoot) * 100);

  document.getElementById("heroCurrentBoot").innerText = `${baseBoot.toFixed(1)}s`;
  document.getElementById("heroTargetBoot").innerText = `${targetBoot.toFixed(1)}s / -${reductionPct}%`;

  // Radial Gauge Animation
  const score = summary.efficiency_score;
  const pctEl = document.getElementById("gaugePct");
  const circleEl = document.getElementById("gaugeCircle");

  pctEl.innerText = `${score}%`;

  // Radius = 65 -> Circumference = 2 * PI * 65 = ~408.4
  const circumference = 408.4;
  const offset = circumference - (score / 100) * circumference;
  circleEl.style.strokeDashoffset = offset;

  // Color gradient adaptation
  if (score < 50) {
    pctEl.style.color = "var(--accent-yellow)";
  } else {
    pctEl.style.color = "var(--accent-lime)";
  }
}

// ========================================================
// LIST RENDERERS (Cards with Toggles & Inspection)
// ========================================================
function renderUserSoftwareList() {
  const container = document.getElementById("userSoftwareList");
  if (!container || !state.scanData) return;

  const items = state.scanData.user_software.filter(item => {
    // Risk filter
    if (state.activeFilters.userRisk !== "all" && item.risk !== state.activeFilters.userRisk) {
      return false;
    }
    // State filter
    if (state.activeFilters.userState === "enabled" && !item.enabled) return false;
    if (state.activeFilters.userState === "disabled" && item.enabled) return false;
    // Search query
    if (state.activeFilters.searchUser) {
      const q = state.activeFilters.searchUser.toLowerCase();
      const match = (item.name || "").toLowerCase().includes(q) ||
                    (item.display_name || "").toLowerCase().includes(q) ||
                    (item.metadata?.company_name || "").toLowerCase().includes(q) ||
                    (item.clean_exe_path || "").toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  if (items.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-dim);">Nessun software utente corrisponde ai filtri impostati.</div>`;
    return;
  }

  container.innerHTML = items.map(item => createItemCardHtml(item)).join("");
  bindCardInteractions(container);
}

function renderSystemProcessesList() {
  const container = document.getElementById("systemProcessesList");
  if (!container || !state.scanData) return;

  const items = state.scanData.system_processes.filter(item => {
    if (state.activeFilters.systemRisk !== "all" && item.risk !== state.activeFilters.systemRisk) {
      return false;
    }
    if (state.activeFilters.searchSystem) {
      const q = state.activeFilters.searchSystem.toLowerCase();
      const match = (item.name || "").toLowerCase().includes(q) ||
                    (item.display_name || "").toLowerCase().includes(q) ||
                    (item.metadata?.company_name || "").toLowerCase().includes(q) ||
                    (item.clean_exe_path || "").toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  if (items.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-dim);">Nessun processo di sistema corrisponde ai filtri.</div>`;
    return;
  }

  container.innerHTML = items.map(item => createItemCardHtml(item)).join("");
  bindCardInteractions(container);
}

function renderScheduledTasksList() {
  const container = document.getElementById("scheduledTasksList");
  if (!container || !state.scanData) return;

  const tasks = state.scanData.all_items.filter(i => i.source_type === "Task").filter(item => {
    if (state.activeFilters.searchTasks) {
      const q = state.activeFilters.searchTasks.toLowerCase();
      return (item.name || "").toLowerCase().includes(q) ||
             (item.source_location || "").toLowerCase().includes(q);
    }
    return true;
  });

  if (tasks.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-dim);">Nessuna attività pianificata trovata.</div>`;
    return;
  }

  container.innerHTML = tasks.map(item => createItemCardHtml(item)).join("");
  bindCardInteractions(container);
}

function renderDeobfuscateList() {
  const container = document.getElementById("deobfuscateList");
  if (!container || !state.scanData) return;

  const items = state.scanData.all_items.filter(item => {
    if (state.activeFilters.searchDeobf) {
      const q = state.activeFilters.searchDeobf.toLowerCase();
      return (item.name || "").toLowerCase().includes(q) ||
             (item.display_name || "").toLowerCase().includes(q) ||
             (item.filename || "").toLowerCase().includes(q);
    }
    return true;
  });

  container.innerHTML = items.map(item => createItemCardHtml(item, true)).join("");
  bindCardInteractions(container);
}

function renderRiskMatrix() {
  if (!state.scanData) return;
  const s = state.scanData.summary;
  document.getElementById("matrixSafeCount").innerText = `${s.safe_count} Elementi`;
  document.getElementById("matrixCautionCount").innerText = `${s.caution_count} Elementi`;
  document.getElementById("matrixCriticalCount").innerText = `${s.critical_count} Elementi`;
}

// Item Card Component Generator
function createItemCardHtml(item, deobfuscateMode = false) {
  const riskClass = item.risk === "VERDE" ? "badge-safe" : (item.risk === "GIALLO" ? "badge-caution" : "badge-critical");
  const riskIcon = item.risk === "VERDE" ? "🟢" : (item.risk === "GIALLO" ? "🟡" : "🔴");
  const company = item.metadata?.company_name || item.intelligence?.publisher || "Editore non specificato";
  const iconEmoji = item.source_type === "Service" ? "⚙️" : (item.source_type === "Task" ? "⏰" : (item.source_type === "StartupFolder" ? "📁" : "🚀"));

  const isChecked = item.enabled ? "checked" : "";
  const isCritical = item.risk === "ROSSO";

  return `
    <div class="item-card" data-id="${item.id}">
      <div class="item-left">
        <div class="item-icon-box">${iconEmoji}</div>
        <div class="item-details">
          <div class="item-title-row">
            <span class="item-name" title="${escapeHtml(item.display_name)}">${escapeHtml(item.display_name)}</span>
            <span class="badge ${riskClass}">${riskIcon} ${item.risk}</span>
            <span class="badge badge-source">${escapeHtml(item.source_type)}</span>
            ${isCritical ? '<span class="badge badge-critical" title="Kernel Guard Attivo">🔒 Protetto</span>' : ''}
          </div>
          <div class="item-sub-info">
            <span><strong>Editore:</strong> ${escapeHtml(company)}</span>
            <span>•</span>
            <span class="item-path-preview" title="${escapeHtml(item.clean_exe_path || item.command)}">${escapeHtml(item.clean_exe_path || item.command)}</span>
          </div>
        </div>
      </div>

      <div class="item-right">
        <button class="btn-inspect" data-action="inspect" data-id="${item.id}">
          🔍 ${deobfuscateMode ? 'Analizza SHA256 & PE' : 'Ispeziona'}
        </button>

        <label class="switch" title="${item.enabled ? 'Attivo all\'avvio - Clicca per disattivare' : 'Disattivato - Clicca per abilitare'}">
          <input type="checkbox" class="item-toggle-chk" data-id="${item.id}" ${isChecked}>
          <span class="slider"></span>
        </label>
      </div>
    </div>
  `;
}

function bindCardInteractions(container) {
  // Bind toggle checkboxes
  container.querySelectorAll(".item-toggle-chk").forEach(chk => {
    chk.addEventListener("change", (e) => {
      const itemId = chk.getAttribute("data-id");
      const newState = chk.checked;
      handleItemToggle(itemId, newState, chk);
    });
  });

  // Bind inspect buttons
  container.querySelectorAll("[data-action='inspect']").forEach(btn => {
    btn.addEventListener("click", () => {
      const itemId = btn.getAttribute("data-id");
      openDeepInspectorModal(itemId);
    });
  });
}

// ========================================================
// ITEM TOGGLE & CRITICAL MODAL HANDLER
// ========================================================
async function handleItemToggle(itemId, newState, checkboxEl) {
  const item = state.scanData?.all_items.find(i => i.id === itemId);
  if (!item) return;

  // Intercept ROSSO (Critical) items to enforce double confirmation
  if (item.risk === "ROSSO" && !newState) {
    checkboxEl.checked = true; // revert temporarily until confirmed
    openCriticalConfirmModal(item, newState, checkboxEl);
    return;
  }

  // Execute toggle
  await executeToggle(itemId, newState, checkboxEl, false);
}

async function executeToggle(itemId, newState, checkboxEl, confirmedCritical) {
  try {
    const res = await fetch("/api/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: itemId,
        enabled: newState,
        confirmed_critical: confirmedCritical
      })
    });
    const result = await res.json();

    if (result.success) {
      addLog(result.message, "success");
      showToast(result.message, "success");

      // Update state locally
      const it = state.scanData.all_items.find(i => i.id === itemId);
      if (it) it.enabled = newState;

      // Recalculate summary & gauge
      recalculateStats();
    } else if (result.requires_confirmation) {
      checkboxEl.checked = !newState;
      const it = state.scanData.all_items.find(i => i.id === itemId);
      openCriticalConfirmModal(it, newState, checkboxEl);
    } else {
      checkboxEl.checked = !newState;
      addLog("Errore: " + result.error, "error");
      showToast(result.error, "error");
    }
  } catch (err) {
    checkboxEl.checked = !newState;
    addLog("Errore di connessione: " + err.message, "error");
    showToast("Errore di connessione", "error");
  }
}

function recalculateStats() {
  const all = state.scanData.all_items;
  const user = state.scanData.user_software;

  const enabledCount = all.filter(i => i.enabled).length;
  state.scanData.summary.enabled_count = enabledCount;
  state.scanData.summary.disabled_count = all.length - enabledCount;

  const penalty = (user.filter(i => i.enabled && i.risk === "VERDE").length * 5) +
                  (user.filter(i => i.enabled && i.risk === "GIALLO").length * 3);
  const score = Math.max(25, Math.min(98, 98 - penalty));
  state.scanData.summary.efficiency_score = score;

  renderDashboardSummary(state.scanData.summary);
}

// Critical Confirmation Modal
function openCriticalConfirmModal(item, targetState, checkboxEl) {
  state.pendingCriticalToggle = { itemId: item.id, targetState, checkboxEl };

  document.getElementById("criticalItemName").innerText = item.display_name;
  document.getElementById("chkCriticalConfirm").checked = false;

  const proceedBtn = document.getElementById("btnProceedCritical");
  proceedBtn.style.opacity = "0.5";
  proceedBtn.style.pointerEvents = "none";

  document.getElementById("modalCriticalConfirm").classList.add("open");
}

function closeCriticalModal() {
  document.getElementById("modalCriticalConfirm").classList.remove("open");
  state.pendingCriticalToggle = null;
}

// ========================================================
// DEEP PROCESS INSPECTOR MODAL
// ========================================================
function openDeepInspectorModal(itemId) {
  const item = state.scanData?.all_items.find(i => i.id === itemId);
  if (!item) return;

  document.getElementById("modalInspTitle").innerText = `🔍 De-Offuscamento: ${item.display_name}`;
  document.getElementById("modalInspExplanation").innerText = item.explanation || "Nessuna spiegazione disponibile.";

  const m = item.metadata || {};
  document.getElementById("modalInspProdName").innerText = m.product_name || item.name || "-";
  document.getElementById("modalInspCompany").innerText = m.company_name || item.intelligence?.publisher || "-";
  document.getElementById("modalInspSignature").innerText = item.signature?.status || "Non Firmato";
  document.getElementById("modalInspVersion").innerText = m.file_version || "-";
  document.getElementById("modalInspArch").innerText = `${m.architecture || 'x64'} (${m.subsystem || 'Windows GUI'})`;
  document.getElementById("modalInspSize").innerText = m.file_size_human || "-";
  document.getElementById("modalInspDate").innerText = m.date_modified || "-";
  document.getElementById("modalInspPath").innerText = item.clean_exe_path || item.command || "-";
  document.getElementById("modalInspArgs").innerText = item.arguments || "Nessun parametro";
  document.getElementById("modalInspSha256").innerText = m.sha256 || "In calcolo...";

  // External URLs
  const googleBtn = document.getElementById("modalInspGoogle");
  const vtBtn = document.getElementById("modalInspVt");

  googleBtn.href = item.search_url || `https://www.google.com/search?q=${encodeURIComponent(item.filename)}+process`;
  if (m.sha256) {
    vtBtn.href = `https://www.virustotal.com/gui/file/${m.sha256}`;
    vtBtn.style.display = "inline-flex";
  } else {
    vtBtn.style.display = "none";
  }

  document.getElementById("modalInspector").classList.add("open");
}

function closeInspectorModal() {
  document.getElementById("modalInspector").classList.remove("open");
}

// ========================================================
// BACKUPS & SNAPSHOTS
// ========================================================
async function loadBackups() {
  try {
    const res = await fetch("/api/backups");
    const data = await res.json();
    renderBackupsList(data);
  } catch (err) {
    console.warn("Backups loading err:", err);
  }
}

function renderBackupsList(backups) {
  const container = document.getElementById("backupsList");
  if (!container) return;

  if (!backups || backups.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-dim);">Nessun punto di ripristino salvato.</div>`;
    return;
  }

  container.innerHTML = backups.map(b => `
    <div class="item-card">
      <div class="item-left">
        <div class="item-icon-box">💾</div>
        <div class="item-details">
          <div class="item-title-row">
            <span class="item-name">${escapeHtml(b.name)}</span>
            <span class="badge badge-source">${b.total_items} Elementi</span>
          </div>
          <div class="item-sub-info">
            <span>Data creazione: ${b.created_at}</span>
            <span>•</span>
            <span class="item-path-preview">${b.filename}</span>
          </div>
        </div>
      </div>
      <div class="item-right">
        <button class="btn-lime" data-restore="${b.id}" style="padding:6px 14px; font-size:12px;">
          Ripristina Snapshot
        </button>
      </div>
    </div>
  `).join("");

  container.querySelectorAll("[data-restore]").forEach(btn => {
    btn.addEventListener("click", () => {
      const bId = btn.getAttribute("data-restore");
      restoreSnapshot(bId);
    });
  });
}

async function restoreSnapshot(backupId) {
  if (!confirm(`Sei sicuro di voler ripristinare il punto di configurazione '${backupId}'?`)) return;

  addLog(`Ripristino snapshot ${backupId} in corso...`, "warning");
  showToast("Ripristino configurazione in corso...", "info");

  try {
    const res = await fetch("/api/restore", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backup_id: backupId })
    });
    const result = await res.json();

    if (result.success) {
      addLog(`Ripristino completato: ${result.restored_count} elementi ripristinati.`, "success");
      showToast(`Snapshot ripristinato (${result.restored_count} elementi)`, "success");
      triggerScan();
    } else {
      addLog("Errore ripristino: " + result.error, "error");
      showToast(result.error, "error");
    }
  } catch (err) {
    addLog("Errore ripristino: " + err.message, "error");
  }
}

async function createManualBackup() {
  addLog("Creazione snapshot di backup in corso...", "info");
  try {
    const res = await fetch("/api/backup", { method: "POST" });
    const result = await res.json();
    if (result.success) {
      addLog(`Snapshot '${result.filename}' salvato con successo.`, "success");
      showToast("Punto di ripristino creato!", "success");
      loadBackups();
    }
  } catch (err) {
    addLog("Errore salvataggio snapshot: " + err.message, "error");
  }
}

// ========================================================
// 1-CLICK SAFE OPTIMIZATION
// ========================================================
async function run1ClickSafeOptimization() {
  if (!confirm("Avviare l'Ottimizzazione Sicura in 1-Clic?\n\nVerrà creato automaticamente uno snapshot di ripristino e verranno disabilitati tutti i programmi utente non essenziali (VERDE).\nI processi di sistema e i driver rimarranno intatti.")) {
    return;
  }

  addLog("Avvio procedura 1-Clic: Ottimizzazione Sicura...", "info");
  showToast("Ottimizzazione in corso...", "info");

  try {
    const res = await fetch("/api/optimize-safe", { method: "POST" });
    const result = await res.json();

    if (result.success) {
      addLog(result.message, "success");
      if (result.disabled_items.length > 0) {
        addLog(`Disattivati: ${result.disabled_items.join(", ")}`, "info");
      }
      showToast(`Ottimizzazione completata! (${result.optimized_count} programmi disattivati)`, "success");
      triggerScan();
      loadBackups();
    } else {
      addLog("Errore durante l'ottimizzazione: " + result.error, "error");
      showToast("Errore ottimizzazione", "error");
    }
  } catch (err) {
    addLog("Errore ottimizzazione: " + err.message, "error");
  }
}

// ========================================================
// GLOBAL EVENT LISTENERS
// ========================================================
function setupEventListeners() {
  // Scans
  document.getElementById("btnHeaderScan")?.addEventListener("click", triggerScan);
  document.getElementById("btnHeroScan")?.addEventListener("click", triggerScan);
  document.getElementById("btnRescanQuick")?.addEventListener("click", triggerScan);
  document.getElementById("btnRefreshSys")?.addEventListener("click", loadSystemInfo);

  // 1-Click
  document.getElementById("btnHero1Click")?.addEventListener("click", run1ClickSafeOptimization);
  document.getElementById("btnTools1Click")?.addEventListener("click", run1ClickSafeOptimization);
  document.getElementById("btnDisableAllSafe")?.addEventListener("click", run1ClickSafeOptimization);

  // Backup
  document.getElementById("btnHeroBackup")?.addEventListener("click", createManualBackup);
  document.getElementById("btnToolsCreateBackup")?.addEventListener("click", createManualBackup);

  // Open Startup folder
  document.getElementById("btnOpenStartupFolder")?.addEventListener("click", () => {
    fetch("/api/open-startup", { method: "POST" });
    addLog("Apertura cartella Startup in Esplora Risorse.", "info");
  });

  // Modal Closers
  document.getElementById("btnCloseInspModal")?.addEventListener("click", closeInspectorModal);
  document.getElementById("modalInspCloseBtn")?.addEventListener("click", closeInspectorModal);
  document.getElementById("btnCloseCriticalModal")?.addEventListener("click", closeCriticalModal);
  document.getElementById("btnCancelCritical")?.addEventListener("click", closeCriticalModal);

  // Checkbox critical confirmation toggle
  document.getElementById("chkCriticalConfirm")?.addEventListener("change", (e) => {
    const proceedBtn = document.getElementById("btnProceedCritical");
    if (e.target.checked) {
      proceedBtn.style.opacity = "1";
      proceedBtn.style.pointerEvents = "auto";
    } else {
      proceedBtn.style.opacity = "0.5";
      proceedBtn.style.pointerEvents = "none";
    }
  });

  // Critical proceed button
  document.getElementById("btnProceedCritical")?.addEventListener("click", () => {
    if (state.pendingCriticalToggle) {
      const { itemId, targetState, checkboxEl } = state.pendingCriticalToggle;
      closeCriticalModal();
      executeToggle(itemId, targetState, checkboxEl, true);
    }
  });

  // Search & Filters for User Software
  document.getElementById("searchUserSoftware")?.addEventListener("input", (e) => {
    state.activeFilters.searchUser = e.target.value.trim();
    renderUserSoftwareList();
  });

  document.querySelectorAll("#view-user-software [data-filter]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#view-user-software [data-filter]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilters.userRisk = btn.getAttribute("data-filter");
      renderUserSoftwareList();
    });
  });

  document.querySelectorAll("#view-user-software [data-state]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#view-user-software [data-state]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilters.userState = btn.getAttribute("data-state");
      renderUserSoftwareList();
    });
  });

  // Search & Filters for System Processes
  document.getElementById("searchSystemProcesses")?.addEventListener("input", (e) => {
    state.activeFilters.searchSystem = e.target.value.trim();
    renderSystemProcessesList();
  });

  document.querySelectorAll("#view-system-processes [data-filter]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#view-system-processes [data-filter]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilters.systemRisk = btn.getAttribute("data-filter");
      renderSystemProcessesList();
    });
  });

  // Search Tasks
  document.getElementById("searchScheduledTasks")?.addEventListener("input", (e) => {
    state.activeFilters.searchTasks = e.target.value.trim();
    renderScheduledTasksList();
  });

  // Search Deobfuscate
  document.getElementById("searchDeobf")?.addEventListener("input", (e) => {
    state.activeFilters.searchDeobf = e.target.value.trim();
    renderDeobfuscateList();
  });

  // Export JSON & HTML
  document.getElementById("btnExportJson")?.addEventListener("click", () => {
    window.open("/api/export?format=json", "_blank");
  });
  document.getElementById("btnExportHtml")?.addEventListener("click", () => {
    window.open("/api/export?format=html", "_blank");
  });

  // Clear Logs
  document.getElementById("btnClearLog")?.addEventListener("click", () => {
    document.getElementById("terminalLogs").innerHTML = "";
  });
  document.getElementById("btnClearLogFull")?.addEventListener("click", () => {
    document.getElementById("terminalLogsFull").innerHTML = "";
  });

  // Theme Toggle Buttons
  document.getElementById("btnThemeToggle")?.addEventListener("click", toggleTheme);
  document.getElementById("btnThemeQuick")?.addEventListener("click", toggleTheme);

  // External Links (YouTube, GitHub, etc.)
  document.querySelectorAll(".about-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const url = link.getAttribute("href");
      if (url) {
        fetch("/api/open-external", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: url })
        }).catch(() => {
          window.open(url, "_blank");
        });
      }
    });
  });
}

// ========================================================
// THEME MANAGEMENT (Dark / Light Mode)
// ========================================================
function initTheme() {
  const saved = localStorage.getItem("initcontrol_theme") || "dark";
  applyTheme(saved, false);
}

function applyTheme(theme, logChange = true) {
  const isLight = (theme === "light");
  if (isLight) {
    document.body.classList.add("theme-light");
  } else {
    document.body.classList.remove("theme-light");
  }
  localStorage.setItem("initcontrol_theme", theme);

  const icon = document.getElementById("themeToggleIcon");
  const label = document.getElementById("themeToggleLabel");
  if (icon) icon.innerText = isLight ? "☀️" : "🌙";
  if (label) label.innerText = isLight ? "Chiaro" : "Scuro";

  const quickBtn = document.getElementById("btnThemeQuick");
  if (quickBtn) quickBtn.title = isLight ? "Passa al Tema Scuro" : "Passa al Tema Chiaro";

  if (logChange) {
    addLog(`Tema interfaccia impostato su: ${isLight ? "Chiaro (Light)" : "Scuro (Dark)"}`, "info");
    showToast(`Tema ${isLight ? "Chiaro" : "Scuro"} attivato`, "info");
  }
}

function toggleTheme() {
  const current = document.body.classList.contains("theme-light") ? "light" : "dark";
  const next = current === "light" ? "dark" : "light";
  applyTheme(next, true);
}

// ========================================================
// TOAST NOTIFICATIONS & UTILITIES
// ========================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const icon = type === "success" ? "✅" : (type === "error" ? "❌" : "ℹ️");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
