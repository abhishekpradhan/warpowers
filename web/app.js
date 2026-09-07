// SPDX-License-Identifier: MIT
import {
  SETTINGS_KEY, PROGRESS_KEY, BINDINGS, BINDING_KEYS, QUALITY_PRESETS, SETTING_RANGES,
  sanitizeSettings, readSettings, applyBindings, renderOptions,
  emptyProgress, sanitizeProgress, recordResult, missionRecord, formatTime, mapLeaf,
  serializeOperationRecord, restoreOperationRecord, OPERATION_RECORD_MAX_BYTES, OPERATION_RECORD_MAX_LABEL,
  mergeProgressRecords, canonicalizeProgress,
  fieldGuidance, beginsNewBattle,
} from './core.js';

// The inline feature gate in index.html runs before this module and leaves its
// message on the loader. An unsupported browser must not paint over it.
if (window.wpUnsupported) throw new Error(window.wpUnsupported);

// ============================================================================
// Constants and DOM helpers
// ============================================================================
const $ = id => document.getElementById(id);
const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, character => HTML_ESCAPES[character]);
const params = new URLSearchParams(location.search);
const DEBUG = params.get('debug') === '1';
// MEMFS layout. USER_DIR is mounted on IDBFS so checkpoints survive reloads.
const HOME_DIR = '/home/web_user';
const USER_DIR = `${HOME_DIR}/.local/share/GeneralsX/GeneralsZH`;
const SAVE_PATH = `${USER_DIR}/Save/wp-checkpoint.sav`;
const SAVE_META = `${USER_DIR}/wp-checkpoint.json`;
const DATA_ROOT = '/game';
const BASE_ROOT = '/game-base';
const FONT_DIR = '/fonts';
const FONT_PATH = `${FONT_DIR}/default.ttf`;
const COMMAND_MAP = 'Data/INI/CommandMap.ini';
const CONTENT_DEPENDENCY = 'war-powers-content';
// Loader tuning.
const STAGE_STREAMS = 12; // parallel asset downloads
const FETCH_ATTEMPTS = 3; // immutable assets only; never after a 4xx
const RETRY_DELAY_MS = 750; // doubled after each failed attempt
const BOOT_FADE_MS = 500; // must outlast #boot's opacity transition (.45s in styles.css)
const RUN_RELEASE_DELAY_MS = 30; // lets the final progress frame paint before the synchronous engine start
const WATCHDOG_TICK_MS = 5000;
const TRANSFER_STALL_MS = 45000; // no bytes and no phase change while downloading
const ENGINE_START_TICKS = 12; // free event-loop ticks (about a minute) while the engine compiles or starts
// Interface tuning.
const TOAST_MS = 5500;
const MAX_TOASTS = 3;
const LOG_LINES = 120;
const DEBUG_LOG_LINES = 25;
const REPORT_LINES = 80;
const DIAGNOSTIC_LOG_LINES = 35;
const RECORD_URL_TTL_MS = 30000;
const RESTART_KEYS = ['quality', 'rightClickOrders', 'cameraSpeed', 'bindings'];
const MAP_TITLES = {
  WPTest: 'The Flats', WPRidge: 'Ridge Divide', WPScrap: 'Scrapyard', WPBasin: 'The Basin', WPRange: 'Trench Range',
};
const DEFAULT_OBJECTIVE = 'Destroy the enemy headquarters. Protect your own.';
const DEFAULT_CAMPAIGN_TEXT = 'Training, operations and commander trials. Your record stays on this device.';
const RESTART_NOTES = {
  idle: 'Audio and overlay settings apply immediately. Display and control changes apply on the next game launch.',
  pending: 'Display, camera and key changes take effect when the game restarts. '
    + 'The current battle continues with its original controls.',
  armed: 'Restarting ends the current battle. Save a checkpoint first, '
    + 'or choose Restart now to discard unsaved progress.',
};
const BOOT_MEASURES = [
  ['deploy', 'engineReady', 'engineDownloadMs'],
  ['engineReady', 'dataReady', 'dataStageMs'],
  ['dataReady', 'running', 'engineInitMs'],
  ['deploy', 'running', 'totalMs'],
];

// ============================================================================
// Diagnostics: test-harness plumbing (debug sessions only)
// ----------------------------------------------------------------------------
// Everything the native harness needs from the page lives here so the seam is
// visible in one place: URL switches, engine ENV forwarding, extra engine
// arguments, the on-page report panes, the local boot beacon and the few
// behaviours a diagnostic run turns off (progress persistence, hidden-tab
// pause, the automatic briefing and the pausing debrief). All of it requires
// `?debug=1`. An ordinary visit forwards nothing to the engine, and engine
// builds without -DWP_HARNESS=ON ignore these variables anyway.
// ============================================================================
const HARNESS_ENV = [
  ['autotest', 'WP_AUTOTEST'],
  ['review', 'WP_REVIEW_SCENE'],
  ['scenedump', 'WP_SCENE_DUMP'],
  ['aitrace', 'WP_AI_TRACE'],
  ['doztrace', 'WP_DOZER_TRACE'],
];
const RETRY_ENV = [['retryruns', 'WP_RETRY_RUNS'], ['retryframes', 'WP_RETRY_FRAMES']];
const REPORT_PATTERN = /\[WP_(?:AUTO|TEST)\].*(?:RETRY|ECONOMY|POWERS|MISSION|MECHANICS|PASS|FAIL|MATCH_RESULT)/;
const SANITIZER_PATTERN = /ERROR: AddressSanitizer|runtime error:/;
const diagnostics = {
  debug: DEBUG,
  /** A native harness session (`?autotest=` or `?review=`): no persistence, hidden pause or briefing. */
  active: DEBUG && (params.has('autotest') || params.has('review')),
  /** The native Retry fixture must reach the score screen without the pausing web debrief. */
  retry: DEBUG && params.get('autotest') === 'retry',
  sanitizerReport: false,
  reportLines: [],
  /** Engine environment variables for this session; empty outside debug. */
  engineEnv() {
    const env = {};
    if (!DEBUG) return env;
    env.IG_TRACE = '1';
    for (const [parameter, key] of HARNESS_ENV) {
      if (params.has(parameter)) env[key] = params.get(parameter) || '1';
    }
    if (this.retry) {
      for (const [parameter, key] of RETRY_ENV) {
        if (params.has(parameter)) env[key] = params.get(parameter);
      }
    }
    if (this.active && params.get('surfacetrace') === '1') env.WP_SURFACE_TRACE = '1';
    return env;
  },
  /** Apply the session environment before the engine's main() reads it. */
  configureEngine(env) {
    Object.assign(env, this.engineEnv());
    // Engine EM_ASM traces read window.IG_TRACE directly.
    if (DEBUG) window.IG_TRACE = 1;
  },
  /** Extra engine command-line arguments (`?args=a,b`), debug only. */
  engineArguments() {
    return DEBUG ? (params.get('args') || '').split(',').filter(Boolean) : [];
  },
  /** Mirror engine output into the on-page panes: the harness report and the rolling debug log. */
  observe(text, lines) {
    if (this.active) {
      if (SANITIZER_PATTERN.test(text)) this.sanitizerReport = true;
      const relevant = this.sanitizerReport || REPORT_PATTERN.test(text)
        || text.includes('[WP_REVIEW]') || text.includes('[WP_SURFACE]');
      if (relevant) {
        this.reportLines.push(text);
        if (this.reportLines.length > REPORT_LINES) this.reportLines.shift();
        $('testReport').hidden = false;
        $('testReport').textContent = this.reportLines.join('\n');
      }
    }
    if (DEBUG) {
      $('debugLog').hidden = false;
      $('debugLog').textContent = lines.slice(-DEBUG_LOG_LINES).join('\n');
    }
  },
  /** Local harness beacon (tools/serve.py answers /wp-boot-ok); debug only. */
  bootBeacon(report, buildId) {
    if (!DEBUG) return;
    fetch(`/wp-boot-ok?total=${report.totalMs}&build=${encodeURIComponent(buildId)}`)
      .catch(error => log(`Diagnostic beacon unavailable: ${error.message}`, 'warn'));
  },
};

// ============================================================================
// Shell state
// ============================================================================
let storage;
try {
  storage = window.localStorage;
} catch {
  storage = {
    getItem: () => null,
    setItem() {
      throw new Error('Storage is unavailable');
    },
  };
}
const settings = readSettings(storage, matchMedia('(prefers-reduced-motion: reduce)').matches);
/** The settings the running engine started with; display and control changes need a restart. */
const bootSettings = structuredClone(settings);
/** Mutable shell state, kept in one object so the node test seam can read and prime it by name. */
const state = {
  failed: false,
  runtimeReady: false,
  persistenceReady: false,
  settingsPersistent: true,
  checkpointBusy: false,
  restoringCheckpoint: false,
  restartArmed: false,
  build: null,
  operations: { missions: [] },
  progress: readStoredProgress(),
  game: { inGame: false, map: '', seconds: 0 },
  currentMap: '',
  currentMission: null,
  pendingResult: null,
  lastResultKey: '',
  panelKind: '',
  guideDismissed: false,
  guideRenderKey: '',
  integrityWarned: false,
  pauseReasons: new Set(),
  volumeBeforeMute: settings.master || 80,
};
const loader = { loadedBytes: 0, totalBytes: 1, percent: 0 };
/** 'transfer' judges silence on the wire; 'engine' counts free event-loop ticks instead, because
 *  compiling and the synchronous engine start block timers without meaning a stall. */
const watchdog = { timer: 0, mode: 'transfer', lastActivity: performance.now(), idleTicks: 0 };
const toasts = { active: [], timer: 0 };
const logLines = [];
const canvas = $('canvas');
const panel = $('panel');

// ============================================================================
// Logging and notices
// ============================================================================
const ENGINE_LEVELS = [[/^(?:ERROR|FATAL)\b/, 'error'], [/^WARNING\b/, 'warn']];
/** Keep a bounded transcript for Copy diagnostics. Shell notices are info; engine output is debug unless flagged. */
function log(message, level = 'info') {
  const text = String(message);
  logLines.push(text);
  if (logLines.length > LOG_LINES) logLines.shift();
  console[level](text);
  diagnostics.observe(text, logLines);
}
const enginePrint = text => log(text, 'debug');
function engineError(text) {
  const line = String(text);
  const match = ENGINE_LEVELS.find(([pattern]) => pattern.test(line));
  log(line, match ? match[1] : 'debug');
}
function renderToasts() {
  clearTimeout(toasts.timer);
  const now = performance.now();
  toasts.active = toasts.active.filter(notice => notice.expires > now);
  $('toast').textContent = toasts.active.map(notice => notice.text).join('\n');
  $('toast').hidden = !toasts.active.length;
  if (!toasts.active.length) return;
  const nextExpiry = Math.min(...toasts.active.map(notice => notice.expires));
  toasts.timer = setTimeout(renderToasts, Math.max(1, nextExpiry - now));
}
/** Keep a few concurrent announcements visible without delaying a fresh alert behind chatter. */
function toast(text) {
  toasts.active = toasts.active.filter(notice => notice.text !== text);
  toasts.active.push({ text, expires: performance.now() + TOAST_MS });
  toasts.active = toasts.active.slice(-MAX_TOASTS);
  renderToasts();
}

// ============================================================================
// Storage and operation record
// ============================================================================
function writeStorage(key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    state.settingsPersistent = false;
    $('storageStatus').textContent = 'Browser storage is unavailable. Preferences and progress last for this tab only.';
    return false;
  }
}
function readStoredProgress() {
  try {
    return sanitizeProgress(JSON.parse(storage.getItem(PROGRESS_KEY)));
  } catch {
    return emptyProgress();
  }
}
function mergeLatestProgress(value = state.progress) {
  return canonicalizeProgress(mergeProgressRecords(value, readStoredProgress()), state.operations.missions);
}
function persistProgress(value) {
  state.progress = mergeLatestProgress(value);
  const persisted = !diagnostics.active && writeStorage(PROGRESS_KEY, state.progress);
  updateRecordDisplay();
  return persisted;
}
function missionStatusText(record) {
  if (!record.wins) return 'UNPLAYED';
  return `COMPLETED${record.bestSeconds ? ` · ${formatTime(record.bestSeconds)}` : ''}`;
}
function updateCompletionCount() {
  const campaign = state.operations.missions.filter(mission => mission.category === 'operation');
  const completed = campaign.filter(mission => missionRecord(state.progress, mission).wins > 0).length;
  $('completionCount').textContent = campaign.length ? `${completed}/${campaign.length}` : '';
}
function updateRecordDisplay() {
  updateCompletionCount();
  if (state.panelKind !== 'journal') return;
  for (const status of $('panelBody').querySelectorAll('[data-record-mission]')) {
    const mission = state.operations.missions.find(entry => entry.id === status.dataset.recordMission);
    if (!mission) continue;
    const record = missionRecord(state.progress, mission);
    status.textContent = missionStatusText(record);
    status.classList.toggle('isComplete', record.wins > 0);
  }
}
/** Converge overlapping writes from other tabs without an event/write loop. */
function handleStorageEvent(event) {
  if (diagnostics.active || (event.key !== PROGRESS_KEY && event.key !== null)) return;
  if (event.newValue === null) {
    state.progress = emptyProgress();
    updateRecordDisplay();
    return;
  }
  let incoming;
  try {
    incoming = JSON.parse(event.newValue);
  } catch {
    return;
  }
  const stored = canonicalizeProgress(readStoredProgress(), state.operations.missions);
  const merged = mergeProgressRecords(state.progress, incoming, stored);
  state.progress = canonicalizeProgress(merged, state.operations.missions);
  if (JSON.stringify(state.progress) !== JSON.stringify(stored)) writeStorage(PROGRESS_KEY, state.progress);
  updateRecordDisplay();
}
function recordStatus(message, isError = false) {
  if (state.panelKind !== 'journal') {
    toast(message);
    return;
  }
  const status = $('recordStatus');
  status.hidden = false;
  status.classList.toggle('error', isError);
  status.textContent = message;
}
function downloadRecord() {
  try {
    state.progress = mergeLatestProgress();
    updateRecordDisplay();
    const file = new Blob([serializeOperationRecord(state.progress)], { type: 'application/json' });
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url;
    link.download = `war-powers-record-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), RECORD_URL_TTL_MS);
    recordStatus('Record download started. Keep the file to restore your completions and best times.');
  } catch (error) {
    recordStatus(`Record could not be downloaded: ${error.message}`, true);
  }
}
async function restoreRecord(file) {
  if (!file) return;
  const button = $('restoreRecord');
  button.disabled = true;
  button.textContent = 'Restoring…';
  try {
    if (file.size > OPERATION_RECORD_MAX_BYTES) {
      throw new Error(`Choose an operation record smaller than ${OPERATION_RECORD_MAX_LABEL}.`);
    }
    const text = await file.text();
    // Read progress after the file resolves, preserving any intervening result.
    const restored = restoreOperationRecord(mergeLatestProgress(), text);
    const persisted = persistProgress(restored);
    recordStatus(persisted
      ? 'Record restored. Your existing completions and better results are kept.'
      : 'Record restored for this tab only. Keep your backup; this record has not been saved in the browser.');
  } catch (error) {
    recordStatus(`Record not restored: ${error.message}`, true);
  } finally {
    button.disabled = false;
    button.textContent = 'Restore record';
  }
}

// ============================================================================
// Appearance, audio and pause ownership
// ============================================================================
function applyAppearance() {
  const root = document.documentElement;
  root.style.setProperty('--ui-scale', settings.uiScale / 100);
  root.classList.toggle('reducedMotion', settings.reducedMotion);
  // An explicit "full motion" choice overrides the prefers-reduced-motion fallback in styles.css.
  root.classList.toggle('fullMotion', !settings.reducedMotion);
  root.classList.toggle('highContrast', settings.highContrast);
  const muted = settings.master === 0;
  $('muteButton').classList.toggle('isMuted', muted);
  $('muteButton').textContent = muted ? '×♪' : '♪';
  $('muteButton').setAttribute('aria-label', muted ? 'Unmute audio' : 'Mute audio');
}
/** A live engine export, or null once the runtime is unavailable or has failed. */
function engineExport(name) {
  if (state.failed || !state.runtimeReady) return null;
  const method = window.Module?.[name];
  return typeof method === 'function' ? method : null;
}
function applyAudio() {
  const setLevels = engineExport('_wpSetAudioLevels');
  if (setLevels) {
    setLevels(settings.master, settings.music, settings.effects, settings.voice);
    return;
  }
  engineExport('_wpSetMasterVolume')?.(settings.master);
}
function saveSettings() {
  Object.assign(settings, sanitizeSettings(settings));
  writeStorage(SETTINGS_KEY, settings);
  applyAppearance();
  applyAudio();
}
/** Web panels acquire and release only their own pause; native Escape/P pauses stay untouched. */
function setPause(reason, active) {
  if (active) state.pauseReasons.add(reason);
  else state.pauseReasons.delete(reason);
  engineExport('_wpSetWebPause')?.(state.pauseReasons.size ? 1 : 0);
}
function hiddenPauseWanted() {
  return settings.pauseWhenHidden && document.hidden && !diagnostics.active;
}
function toggleMute() {
  if (settings.master) {
    state.volumeBeforeMute = settings.master;
    settings.master = 0;
  } else {
    settings.master = state.volumeBeforeMute;
  }
  saveSettings();
}
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await $('stage').requestFullscreen();
  } catch {
    toast('Fullscreen is unavailable here. You can still play in this window.');
  }
}

// ============================================================================
// Panels (one modal dialog)
// ============================================================================
function closePanel() {
  if (panel.open) panel.close();
  state.panelKind = '';
  setPause('panel', false);
  (state.failed ? $('reloadButton') : canvas).focus({ preventScroll: true });
  updateGuide();
}
function openPanel(kind, title, eyebrow = 'COMMAND NETWORK') {
  state.panelKind = kind;
  $('panelTitle').textContent = title;
  $('panelEyebrow').textContent = eyebrow;
  $('panelBody').replaceChildren();
  if (!panel.open) {
    setPause('panel', true);
    panel.showModal();
  }
  updateGuide();
  panel.scrollTop = 0;
}
function appendHTML(html) {
  $('panelBody').insertAdjacentHTML('beforeend', html);
}
/** Static panel markup lives in <template> elements in index.html. */
function appendTemplate(id) {
  $('panelBody').append($(id).content.cloneNode(true));
}
function section(title) {
  appendHTML(`<h3 class="sectionLabel">${escapeHTML(title)}</h3>`);
}

// ============================================================================
// Settings panel
// ============================================================================
function needRestart() {
  return RESTART_KEYS.some(key => JSON.stringify(settings[key]) !== JSON.stringify(bootSettings[key]));
}
/** Any settings change disarms a pending restart, so a reload never happens without its warning. */
function updateRestartNote(arm = false) {
  const note = $('restartNote');
  const button = $('applyRestart');
  if (!note || !button) return;
  const pending = needRestart();
  state.restartArmed = arm && pending;
  note.classList.toggle('pending', pending);
  if (state.restartArmed) note.textContent = RESTART_NOTES.armed;
  else note.textContent = pending ? RESTART_NOTES.pending : RESTART_NOTES.idle;
  button.hidden = !pending;
  button.textContent = state.restartArmed ? 'Restart now' : 'Restart game to apply';
}
function requestRestart() {
  if (!state.game.inGame || state.restartArmed) {
    location.reload();
    return;
  }
  updateRestartNote(true);
}
function rangeSetting(key, label) {
  const [min, max] = SETTING_RANGES[key];
  appendHTML(`<div class="settingRow"><label for="setting-${key}">${escapeHTML(label)}</label><div class="rangeWrap">`
    + `<input id="setting-${key}" type="range" min="${min}" max="${max}" value="${settings[key]}">`
    + `<output id="value-${key}" for="setting-${key}">${settings[key]}%</output></div></div>`);
  $(`setting-${key}`).addEventListener('input', event => {
    settings[key] = Number(event.target.value);
    $(`value-${key}`).textContent = `${settings[key]}%`;
    saveSettings();
    updateRestartNote();
  });
}
function checkboxSetting(key, label) {
  appendHTML(`<div class="settingRow"><label for="setting-${key}">${escapeHTML(label)}</label>`
    + `<input id="setting-${key}" type="checkbox"${settings[key] ? ' checked' : ''}></div>`);
  $(`setting-${key}`).addEventListener('change', event => {
    settings[key] = event.target.checked;
    if (key === 'guide') state.guideDismissed = !settings.guide;
    saveSettings();
    updateRestartNote();
    updateGuide();
    if (key === 'pauseWhenHidden') setPause('hidden', hiddenPauseWanted());
  });
}
function qualityOption([id, preset]) {
  return `<option value="${id}">${escapeHTML(preset.label)} · ${preset.width} × ${preset.height}</option>`;
}
function qualitySetting() {
  const options = Object.entries(QUALITY_PRESETS).map(qualityOption).join('');
  appendHTML('<div class="settingRow"><label for="quality">Rendering</label>'
    + `<select id="quality">${options}</select></div>`);
  $('quality').value = settings.quality;
  $('quality').addEventListener('change', event => {
    settings.quality = event.target.value;
    saveSettings();
    updateRestartNote();
  });
}
function bindingSetting(command, label) {
  const options = BINDING_KEYS.map(key => `<option value="${key}">${key}</option>`).join('');
  appendHTML(`<div class="settingRow"><label for="key-${command}">${escapeHTML(label)}</label>`
    + `<select id="key-${command}">${options}</select></div>`);
  const input = $(`key-${command}`);
  input.value = settings.bindings[command];
  input.addEventListener('change', () => {
    const conflict = Object.entries(settings.bindings).some(([other, key]) => other !== command && key === input.value);
    if (conflict) {
      input.value = settings.bindings[command];
      toast('That key already has an assignment. Choose another key.');
      return;
    }
    settings.bindings[command] = input.value;
    saveSettings();
    updateRestartNote();
  });
}
function checkpointMeta() {
  if (!state.runtimeReady || !window.FS) return null;
  try {
    if (!window.FS.analyzePath(SAVE_PATH).exists) return null;
    return JSON.parse(window.FS.readFile(SAVE_META, { encoding: 'utf8' }));
  } catch {
    return null;
  }
}
function checkpointCompatible(metadata) {
  return !!metadata && metadata.compatibility === state.build?.compatibility;
}
/** Refresh the checkpoint buttons and note in place; the panel keeps its scroll position and focus. */
function updateCheckpointControls() {
  if (state.panelKind !== 'settings') return;
  const save = $('saveCheckpoint');
  const load = $('loadCheckpoint');
  if (!save || !load) return;
  const metadata = checkpointMeta();
  const compatible = checkpointCompatible(metadata);
  save.disabled = state.checkpointBusy || !state.game.inGame || !state.persistenceReady;
  save.textContent = state.checkpointBusy ? 'Saving…' : 'Save checkpoint';
  load.disabled = state.checkpointBusy || !compatible || state.game.inGame;
  let note = 'One checkpoint per device. Return to the menu to resume a saved battle.';
  if (metadata) {
    const saved = new Date(metadata.savedAt).toLocaleString();
    note = `${metadata.title} · ${saved}${compatible ? '' : ' · saved in a different game version'}`;
  }
  if (!state.persistenceReady) note += ' Persistent save storage is unavailable.';
  $('checkpointNote').textContent = note;
}
function syncSaves() {
  return new Promise((resolve, reject) => {
    if (!state.persistenceReady) {
      reject(new Error('Persistent save storage is unavailable in this browser session.'));
      return;
    }
    window.FS.syncfs(false, error => (error ? reject(error) : resolve()));
  });
}
async function saveCheckpoint() {
  const save = engineExport('_wpSaveGame');
  if (!save || state.checkpointBusy || !state.game.inGame) return;
  state.checkpointBusy = true;
  updateCheckpointControls();
  const fs = window.FS;
  let previous;
  let previousMeta;
  let captured = false;
  try {
    previous = fs.analyzePath(SAVE_PATH).exists ? fs.readFile(SAVE_PATH) : null;
    previousMeta = fs.analyzePath(SAVE_META).exists ? fs.readFile(SAVE_META) : null;
    captured = true;
    const result = save();
    if (result !== 0) throw new Error(`The current battle could not be saved (code ${result}).`);
    const metadata = {
      version: 1,
      compatibility: state.build?.compatibility,
      map: mapLeaf(state.game.map),
      mission: state.currentMission?.id || '',
      title: state.currentMission?.title || mapTitle(state.currentMap),
      savedAt: new Date().toISOString(),
    };
    fs.writeFile(SAVE_META, JSON.stringify(metadata));
    await syncSaves();
    toast('Checkpoint saved on this device.');
  } catch (error) {
    // Preserve the preceding slot if serialization or the durable flush fails.
    if (captured) {
      if (previous) fs.writeFile(SAVE_PATH, previous);
      else if (fs.analyzePath(SAVE_PATH).exists) fs.unlink(SAVE_PATH);
      if (previousMeta) fs.writeFile(SAVE_META, previousMeta);
      else if (fs.analyzePath(SAVE_META).exists) fs.unlink(SAVE_META);
    }
    toast(`Checkpoint not saved: ${error.message}`);
  } finally {
    state.checkpointBusy = false;
    updateCheckpointControls();
  }
}
function loadCheckpoint() {
  if (state.failed || state.checkpointBusy || state.game.inGame) return;
  const metadata = checkpointMeta();
  if (!metadata) {
    toast('No checkpoint is saved on this device. Start a new battle.');
    return;
  }
  if (!checkpointCompatible(metadata)) {
    toast('This checkpoint belongs to another game version. Start a new battle.');
    return;
  }
  const load = engineExport('_wpLoadGame');
  closePanel();
  // The restored battle continues where it stopped; only a fresh mission opens its briefing.
  state.restoringCheckpoint = true;
  const result = load ? load() : undefined;
  if (result !== 0) {
    state.restoringCheckpoint = false;
    toast(`Could not restore the checkpoint (code ${result ?? 'unavailable'}).`);
    return;
  }
  state.currentMap = '';
  state.lastResultKey = '';
  toast('Checkpoint restored.');
}
function showSettings() {
  openPanel('settings', 'Settings');
  section('Audio');
  rangeSetting('master', 'Master volume');
  rangeSetting('music', 'Music');
  rangeSetting('effects', 'Effects & ambience');
  rangeSetting('voice', 'Unit voices & announcer');
  section('Display & camera');
  qualitySetting();
  rangeSetting('uiScale', 'Overlay text size');
  rangeSetting('cameraSpeed', 'Camera scroll speed');
  checkboxSetting('rightClickOrders', 'Right-click to issue orders');
  checkboxSetting('highContrast', 'High-contrast overlays');
  checkboxSetting('reducedMotion', 'Reduce interface motion');
  checkboxSetting('pauseWhenHidden', 'Pause when this tab is hidden');
  checkboxSetting('guide', 'Open field guidance automatically');
  section('Keyboard');
  for (const [command, [label]] of Object.entries(BINDINGS)) bindingSetting(command, label);
  appendTemplate('settingsTailTemplate');
  updateRestartNote();
  $('applyRestart').addEventListener('click', requestRestart);
  $('saveCheckpoint').addEventListener('click', saveCheckpoint);
  $('loadCheckpoint').addEventListener('click', loadCheckpoint);
  updateCheckpointControls();
  $('buildId').textContent = state.build?.id || 'loading';
  $('copyBuild').addEventListener('click', copyDiagnostics);
}

// ============================================================================
// Field manual
// ============================================================================
function controlRows() {
  const keys = bootSettings.bindings;
  const rightClick = bootSettings.rightClickOrders;
  return [
    ['Select unit or building', 'Left click'],
    ['Select a group', 'Drag a selection box'],
    ['Move, attack or set a rally point', rightClick ? 'Right click' : 'Left click on the destination'],
    ['Cancel an order or build placement', 'Right click'],
    ['Deselect', rightClick ? 'Left click open ground' : 'Right click'],
    ['Attack while advancing', 'Attack Move button, then choose a destination'],
    ['Guard a position', 'Guard button, then choose a position'],
    ['Stop', keys.STOP],
    ['Scatter', keys.SCATTER],
    ['Select army', keys.SELECT_ALL],
    ['Select matching units', keys.SELECT_MATCHING_UNITS],
    ['Next idle builder', keys.SELECT_NEXT_IDLE_WORKER],
    ['View headquarters', keys.VIEW_COMMAND_CENTER],
    ['Create / recall group', 'Ctrl + 1–9 / 1–9'],
    ['Add group to selection / view group', 'Shift + 1–9 / Alt + 1–9'],
    ['View last radar alert', 'Space'],
    ['Rotate camera', ', / .'],
    ['Zoom camera', 'Wheel / Page Up / Page Down'],
    ['Reset camera', 'Home'],
    ['Pause / battle menu', `${keys.TOGGLE_PAUSE} / Escape`],
  ];
}
function showHelp() {
  openPanel('help', 'Field manual', 'KNOW YOUR TOOLS');
  appendTemplate('manualTemplate');
  $('controlList').innerHTML = controlRows()
    .map(([name, key]) => `<div><dt>${escapeHTML(name)}</dt><dd>${escapeHTML(key)}</dd></div>`)
    .join('');
}

// ============================================================================
// Operations journal, briefing, debrief and field guidance
// ============================================================================
function findMission(result) {
  return state.operations.missions.find(m => m.id === result.operationId || m.map === mapLeaf(result.map));
}
function mapTitle(id) {
  return MAP_TITLES[id.replace(/J$/, '')] || 'The Meridian Strip';
}
function missionEntry(index, mission) {
  const record = missionRecord(state.progress, mission);
  const faction = mission.faction === 'jackal' ? 'Jackal Front' : 'Meridian Combine';
  const disabled = state.game.inGame ? ' disabled' : '';
  return `<article class="missionEntry"><span class="missionIndex">${String(index + 1).padStart(2, '0')}</span><div>`
    + `<span class="missionFaction">Play as ${escapeHTML(faction)} · ${escapeHTML(mission.duration)}</span>`
    + `<h3>${escapeHTML(mission.title)}</h3><p>${escapeHTML(mission.briefing)}</p>`
    + `<button class="textButton reviewButton" data-mission="${index}"${disabled}>`
    + 'Review deployment <span aria-hidden="true">↗</span></button></div>'
    + `<span class="missionStatus${record.wins ? ' isComplete' : ''}" data-record-mission="${escapeHTML(mission.id)}">`
    + `${missionStatusText(record)}</span></article>`;
}
function chooseRecordFile(event) {
  const file = event.target.files[0];
  event.target.value = '';
  restoreRecord(file);
}
function reviewMission(index) {
  if (state.failed) return;
  closePanel();
  const show = engineExport('_wpShowMission');
  if (show) show(index);
  else toast('Choose this operation on the Deployment screen.');
}
function showJournal() {
  state.progress = mergeLatestProgress();
  updateCompletionCount();
  openPanel('journal', 'Operations', 'THE MERIDIAN STRIP');
  const intro = state.operations.campaign?.description || DEFAULT_CAMPAIGN_TEXT;
  appendHTML(`<p class="manualIntro">${escapeHTML(intro)}</p>`);
  appendTemplate('recordToolsTemplate');
  $('downloadRecord').addEventListener('click', downloadRecord);
  $('restoreRecord').addEventListener('click', () => $('recordFile').click());
  $('recordFile').addEventListener('change', chooseRecordFile);
  for (const [index, mission] of state.operations.missions.entries()) appendHTML(missionEntry(index, mission));
  if (state.game.inGame) {
    appendHTML('<p class="settingsNote">Return to the main menu before choosing another operation.</p>');
  }
  for (const button of $('panelBody').querySelectorAll('[data-mission]')) {
    button.addEventListener('click', () => reviewMission(Number(button.dataset.mission)));
  }
}
function showBriefing() {
  if (state.failed) return;
  const mission = state.currentMission;
  if (!mission) {
    showHelp();
    return;
  }
  const eyebrow = mission.faction === 'jackal' ? 'JACKAL FRONT · OPERATIONS' : 'MERIDIAN COMBINE · OPERATIONS';
  openPanel('briefing', mission.title, eyebrow);
  appendHTML(`<p class="operationTag">${escapeHTML(mission.duration)} · ${escapeHTML(mission.category)}</p>`
    + `<p class="briefingLead">${escapeHTML(mission.briefing)}</p>`);
  section('Objectives');
  const objectives = mission.objectives
    .map(o => `<li>${escapeHTML(o.label)}${o.optional ? ' <span class="muted">(Optional)</span>' : ''}</li>`)
    .join('');
  appendHTML(`<ol class="objectiveList">${objectives}</ol>`
    + '<div class="actions"><button id="beginMission" class="primary">Return to battlefield</button></div>');
  $('beginMission').addEventListener('click', closePanel);
}
const resultStat = (value, label) => `<div><strong>${value}</strong><span>${label}</span></div>`;
function showDebrief() {
  if (state.failed) return;
  const result = state.pendingResult;
  if (!result) return;
  const mission = findMission(result);
  if (!mission) return;
  openPanel('debrief', mission.title, result.won ? 'OPERATION COMPLETE' : 'OPERATION FAILED');
  const stats = result.stats || {};
  appendHTML(`<p class="briefingLead">${escapeHTML(result.won ? mission.debriefWin : mission.debriefLoss)}</p>`);
  appendHTML(`<div class="resultStats">${resultStat(formatTime(stats.durationSeconds), 'BATTLE TIME')}`
    + `${resultStat(Number(stats.unitsBuilt) || 0, 'UNITS FIELDED')}`
    + `${resultStat(Number(stats.unitsLost) || 0, 'UNITS LOST')}</div>`);
  const next = state.operations.missions.find(entry => entry.id === mission.nextMission);
  if (result.won && next) {
    appendHTML(`<p class="muted">Next operation: ${escapeHTML(next.title)}. `
      + 'Select it from Operations when you return to the menu.</p>');
  }
  appendHTML('<div class="actions"><button id="returnScore" class="primary">Continue to battle report</button></div>');
  $('returnScore').addEventListener('click', closePanel);
  state.pendingResult = null;
}
function checklistItem(item) {
  const mark = item.complete ? '✓' : '○';
  const done = item.complete ? '<span class="srOnly"> complete</span>' : '';
  const progress = `${Number(item.current) || 0}/${Number(item.count) || 0}`;
  return `<li class="${item.complete ? 'complete' : ''}">`
    + `<span class="requirementMark" aria-hidden="true">${mark}</span><span>${escapeHTML(item.label)}</span>`
    + `<span class="requirementCount">${progress}${done}</span></li>`;
}
function updateGuide() {
  const visible = !state.failed && state.game.inGame && !state.guideDismissed && !panel.open;
  $('guide').hidden = !visible;
  $('guidanceButton').setAttribute('aria-expanded', String(!!visible));
  if (state.failed || !state.game.inGame) return;
  const guide = fieldGuidance(state.currentMission, state.game, bootSettings);
  const step = guide.total ? `Step ${guide.stage + 1} of ${guide.total}` : 'Battle tip';
  $('guidanceButton').textContent = guide.total ? `Guidance · ${guide.stage + 1}/${guide.total}` : 'Guidance';
  // Keep focus and DOM stable across native telemetry polls and selections.
  const key = JSON.stringify(guide);
  if (key === state.guideRenderKey) return;
  state.guideRenderKey = key;
  $('guideStep').textContent = step;
  $('guideTitle').textContent = guide.title;
  $('guideBody').textContent = guide.body;
  $('guideNote').textContent = guide.note || '';
  $('guideNote').hidden = !guide.note;
  $('guideChecklist').hidden = !guide.checklist.length;
  $('guideChecklist').innerHTML = guide.checklist.map(checklistItem).join('');
  $('guideOverviewLabel').textContent = state.currentMission ? 'All steps' : 'Field manual';
}
function guidanceStep(mission, guide, objective, index, total) {
  let status = 'UPCOMING';
  if (index < guide.stage) status = 'COMPLETED';
  else if (index === guide.stage) status = 'CURRENT STEP';
  const overview = fieldGuidance(mission, { ...state.game, objectiveStage: index }, bootSettings).overview;
  const current = index === guide.stage ? ' aria-current="step"' : '';
  return `<li${current}><span class="eyebrow">${status} · ${index + 1}/${total}</span>`
    + `<h3>${escapeHTML(objective.label)}</h3><p>${escapeHTML(overview)}</p></li>`;
}
function resumeGuidance() {
  state.guideDismissed = false;
  closePanel();
}
function showGuidanceOverview() {
  const mission = state.currentMission;
  if (!mission) {
    showHelp();
    return;
  }
  const guide = fieldGuidance(mission, state.game, bootSettings);
  openPanel('guidance', 'Field guidance', mission.title);
  appendHTML('<p class="muted">Steps follow the battlefield automatically. Collapse the guidance panel at any time; '
    + 'Guidance beside the mission briefing brings it back.</p>');
  const objectives = mission.objectives.filter(objective => !objective.optional);
  const steps = objectives.map((objective, index) => guidanceStep(mission, guide, objective, index, objectives.length));
  appendHTML(`<ol class="guidanceSteps">${steps.join('')}</ol>`
    + '<div class="actions"><button id="returnGuidance" class="primary">Show current guidance</button></div>');
  $('returnGuidance').addEventListener('click', resumeGuidance);
}
function dismissGuide() {
  state.guideDismissed = true;
  updateGuide();
  $('guidanceButton').focus({ preventScroll: true });
}
function toggleGuide() {
  state.guideDismissed = !state.guideDismissed;
  updateGuide();
}

// ============================================================================
// Engine telemetry (Module.onGameState / Module.onMatchResult)
// ============================================================================
/** A new battlefield: HUD labels, guidance and, for a fresh mission, its briefing. */
function beginBattle(leaf) {
  const restored = state.restoringCheckpoint;
  state.restoringCheckpoint = false;
  state.currentMap = leaf;
  state.currentMission = state.operations.missions.find(mission => mission.map === leaf) || null;
  state.guideDismissed = !settings.guide;
  state.guideRenderKey = '';
  state.lastResultKey = '';
  $('missionTitle').textContent = state.currentMission?.title || mapTitle(leaf);
  $('missionType').textContent = (state.currentMission?.category || 'skirmish').toUpperCase();
  $('briefingLabel').textContent = state.currentMission ? 'Mission briefing' : 'Field manual';
  // A restored checkpoint returns straight to the battle; a diagnostic run must not be paused by a dialog.
  if (state.currentMission && !diagnostics.active && !restored) {
    setTimeout(() => {
      if (state.game.inGame && state.currentMap === leaf && !panel.open) showBriefing();
    }, 0);
  }
  if (state.pauseReasons.size) setTimeout(() => setPause('panel', panel.open), 0);
}
function updateGameState(next) {
  if (state.failed) return;
  const newBattle = beginsNewBattle(state.game, next);
  state.game = next;
  const leaf = mapLeaf(next.map);
  $('missionHud').hidden = !next.inGame;
  if (!next.inGame) {
    updateGuide();
    state.currentMap = '';
    state.currentMission = null;
    // Let native victory/defeat cleanup reach the score screen before opening
    // a pausing web dialog. The result callback can precede that by seconds.
    if (state.pendingResult && state.panelKind !== 'debrief') setTimeout(showDebrief, 0);
    return;
  }
  if (newBattle || leaf !== state.currentMap) beginBattle(leaf);
  const required = state.currentMission?.objectives.filter(o => !o.optional) || [];
  const objective = required[Math.max(0, Math.min(required.length - 1, next.objectiveStage || 0))];
  $('objectiveText').textContent = objective?.label.replace(/\s*\(0\/\d+\)/, '') || DEFAULT_OBJECTIVE;
  $('matchClock').textContent = formatTime(next.seconds);
  const counted = next.objectiveTarget > 0;
  $('objectiveProgress').textContent = counted ? `${next.objectiveProgress || 0} / ${next.objectiveTarget}` : '';
  $('objectiveTimer').textContent = next.objectiveSeconds >= 0 ? `${formatTime(next.objectiveSeconds)} remaining` : '';
  updateGuide();
}
function handleResult(result) {
  if (state.failed) return;
  if (diagnostics.active) log(`[WP_TEST] MATCH_RESULT ${JSON.stringify(result)}`);
  const key = `${result.map}:${result.stats?.durationSeconds}:${result.won}`;
  if (state.lastResultKey === key) return;
  state.lastResultKey = key;
  const mission = findMission(result);
  if (!mission) return;
  const seconds = result.stats?.durationSeconds;
  persistProgress(recordResult(mergeLatestProgress(), { ...result, operationId: mission.id, seconds }));
  // The native Retry fixture must reach and render the score screen without this modal pausing it.
  if (diagnostics.retry) return;
  state.pendingResult = result;
  if (!state.game.inGame) setTimeout(showDebrief, 0);
}
function handleGameMessage(message) {
  if (message?.text) toast(message.text);
}

// ============================================================================
// Failure, exit and diagnostics report
// ============================================================================
function diagnosticReport() {
  return JSON.stringify({
    build: state.build?.id,
    compatibility: state.build?.compatibility,
    browser: navigator.userAgent,
    display: bootSettings.quality,
    map: state.currentMap,
    boot: window.wpBootReport,
    persistenceReady: state.persistenceReady,
    settingsPersistent: state.settingsPersistent,
    logs: logLines.slice(-DIAGNOSTIC_LOG_LINES),
  }, null, 2);
}
async function copyDiagnostics() {
  try {
    await navigator.clipboard.writeText(diagnosticReport());
    toast('Diagnostics copied.');
  } catch {
    openPanel('diagnostics', 'Diagnostics');
    const pre = document.createElement('pre');
    pre.textContent = diagnosticReport();
    pre.style.cssText = 'white-space:pre-wrap;word-break:break-word;font-size:11px';
    $('panelBody').append(pre);
  }
}
function showBootOverlay(phase, hint) {
  $('boot').hidden = false;
  $('boot').classList.remove('departing');
  $('bootPhase').textContent = phase;
  $('bootHint').textContent = hint;
  $('utilityBar').hidden = true;
}
/** Stop driving a broken engine: pause and mute it once, best effort, then never call it again. */
function quiesceEngine() {
  if (!state.runtimeReady) return;
  const module = window.Module;
  for (const [name, args] of [['_wpSetWebPause', [1]], ['_wpSetAudioLevels', [0, 0, 0, 0]]]) {
    try {
      if (typeof module?.[name] === 'function') module[name](...args);
    } catch (error) {
      log(`${name} unavailable after failure: ${error.message}`, 'warn');
    }
  }
}
function fail(message, code = 'WP-RUNTIME') {
  if (state.failed) return;
  state.failed = true;
  quiesceEngine();
  // Recovery stays entirely in the browser from here, including later telemetry and dialog cleanup.
  state.runtimeReady = false;
  state.pauseReasons.clear();
  state.pendingResult = null;
  state.panelKind = '';
  if (panel.open) panel.close();
  log(`${code}: ${message}`, 'error');
  $('guide').hidden = true;
  $('missionHud').hidden = true;
  $('guidanceButton').setAttribute('aria-expanded', 'false');
  showBootOverlay('Command connection interrupted',
    'Your saved operation record is preserved. Reload to return to command.');
  $('bootExit').hidden = true;
  $('bootError').hidden = false;
  $('errorMessage').textContent = message;
  $('errorCode').textContent = `${code} · ${state.build?.id || 'initializing'}`;
  $('reloadButton').focus({ preventScroll: true });
}
/** EXIT GAME never unwinds the runtime (EXIT_RUNTIME=0); the page returns to its own landing state. */
function handleGameExit() {
  if (state.failed) return;
  if (state.game.inGame && !state.lastResultKey) {
    fail('The battle was interrupted. Reload and resume your last checkpoint.', 'WP-EXIT');
    return;
  }
  showBootOverlay('Session complete', 'Your operation record is saved on this device.');
  $('bootError').hidden = true;
  $('bootExit').hidden = false;
  $('returnButton').focus({ preventScroll: true });
}
function handleWindowError(event) {
  log(`UNCAUGHT: ${event.error?.stack || event.message}`, 'error');
  if (state.runtimeReady) fail('The game encountered an unexpected error. Reload to recover.', 'WP-SCRIPT');
}
function handleRejection(event) {
  log(`UNHANDLED: ${event.reason?.message || event.reason}`, 'error');
  if (!state.failed) fail('A game operation could not complete. Reload to reconnect.', 'WP-ASYNC');
}
function handleContextLost(event) {
  event.preventDefault();
  fail('The graphics connection was lost. Reload to reconnect, then resume your last checkpoint.', 'WP-GRAPHICS');
}

// ============================================================================
// Loader: progress, stall watchdog, transfers and integrity
// ============================================================================
function noteActivity() {
  watchdog.lastActivity = performance.now();
  watchdog.idleTicks = 0;
}
function setWatchdogMode(mode) {
  watchdog.mode = mode;
  noteActivity();
}
function watchdogTick() {
  if (state.runtimeReady || state.failed) {
    clearInterval(watchdog.timer);
    watchdog.timer = 0;
    return;
  }
  // Background tabs throttle timers and fetches and suspend animation frames; judge only visible sessions.
  if (document.hidden) return;
  watchdog.idleTicks += 1;
  if (watchdog.mode === 'transfer' && performance.now() - watchdog.lastActivity > TRANSFER_STALL_MS) {
    fail('Loading stopped responding. Check your connection and reload.', 'WP-TIMEOUT');
  } else if (watchdog.mode === 'engine' && watchdog.idleTicks >= ENGINE_START_TICKS) {
    fail('The engine did not start. Reload to try again.', 'WP-TIMEOUT');
  }
}
function setPhase(phase) {
  if (state.failed) return;
  $('bootPhase').textContent = phase;
  noteActivity();
}
function paintProgress(percent) {
  $('bootFill').style.width = `${percent}%`;
  $('bootPercent').textContent = `${percent}%`;
  $('bootProgress').setAttribute('aria-valuenow', String(percent));
}
/** Account transferred bytes (negative when a retry discards a partial download) and repaint on change. */
function progressBytes(delta) {
  // Transfers still draining behind the recovery page must not repaint over it.
  if (state.failed) return;
  loader.loadedBytes = Math.max(0, loader.loadedBytes + delta);
  noteActivity();
  const percent = Math.min(99, Math.floor(loader.loadedBytes / Math.max(1, loader.totalBytes) * 100));
  if (percent === loader.percent) return;
  loader.percent = percent;
  paintProgress(percent);
}
class TransferError extends Error {
  constructor(message, { code = 'WP-DOWNLOAD', retryable = false } = {}) {
    super(message);
    this.code = code;
    this.retryable = retryable;
  }
}
/** fetch() reports a network failure as a TypeError carrying one of these texts (Chromium, Firefox, WebKit). */
const NETWORK_TEXT = /Failed to fetch|NetworkError|Load failed|network/i;
const FETCH_MESSAGES = {
  network: 'The connection to the game server was interrupted',
  AbortError: 'A download was cancelled before it completed',
};
/** Turn fetch's own errors into player-facing copy; only network interruptions are worth retrying. */
function describeFetchError(error, label) {
  if (error instanceof TransferError) return error;
  const name = `${error?.name}`;
  // Any other TypeError is a shell defect, not a flaky link: surface its message instead of retrying it.
  const kind = name === 'TypeError' && NETWORK_TEXT.test(`${error.message}`) ? 'network' : name;
  if (!Object.hasOwn(FETCH_MESSAGES, kind)) return new TransferError(`${label}: ${error?.message || error}`);
  return new TransferError(`${FETCH_MESSAGES[kind]} (${label}).`, { retryable: kind === 'network' });
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function concatChunks(chunks, size) {
  const out = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  return out;
}
async function fetchOnce(url, label, track) {
  let received = 0;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      const retryable = response.status >= 500;
      try {
        // Release the failed response's connection before any retry reuses it.
        await response.body?.cancel();
      } catch {
        // A locked or already closed body holds nothing worth releasing.
      }
      throw new TransferError(`${label}: the server answered HTTP ${response.status}.`, { retryable });
    }
    if (!track || !response.body) {
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (track) progressBytes(bytes.length);
      return bytes;
    }
    const reader = response.body.getReader();
    const chunks = [];
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      progressBytes(value.length);
    }
    return concatChunks(chunks, received);
  } catch (error) {
    if (received) progressBytes(-received);
    throw describeFetchError(error, label);
  }
}
/** A transfer that starts, retries or finishes behind the recovery page is dropped instead of staged. */
const abandoned = label => new TransferError(`${label}: loading stopped after an earlier failure.`);
/** Immutable content-addressed files are retried after network errors or 5xx; 4xx and mutable files fail at once.
 *  Once the boot has failed, every caller (stage workers, font, engine, records) is stopped here: no new attempt
 *  starts, no retry wakes, and a download that completes late is never hashed, written or instantiated. */
async function fetchBytes(url, { track = true, immutable = false } = {}) {
  const label = url.split('?')[0];
  const attempts = immutable ? FETCH_ATTEMPTS : 1;
  for (let attempt = 1; ; attempt += 1) {
    try {
      if (state.failed) throw abandoned(label);
      const bytes = await fetchOnce(url, label, track);
      if (state.failed) throw abandoned(label);
      return bytes;
    } catch (error) {
      if (state.failed || !error.retryable || attempt >= attempts) throw error;
      log(`Retrying ${label}: ${error.message}`, 'warn');
      await sleep(RETRY_DELAY_MS * 2 ** (attempt - 1));
    }
  }
}
const toHex = buffer => Array.from(new Uint8Array(buffer), byte => byte.toString(16).padStart(2, '0')).join('');
const hexToBase64 = hex => btoa(String.fromCharCode(...hex.match(/../g).map(pair => parseInt(pair, 16))));
function integrityError(label, detail) {
  const message = `A downloaded file did not match this build (${label}: ${detail}). Reload to download it again.`;
  return new TransferError(message, { code: 'WP-INTEGRITY' });
}
/** SHA-256 hex of `bytes`, or '' where WebCrypto is unavailable: it needs a secure origin (https or localhost). */
async function digestBytes(bytes) {
  const subtle = globalThis.crypto?.subtle;
  if (subtle) return toHex(await subtle.digest('SHA-256', bytes));
  if (!state.integrityWarned) log('Integrity hashes are not checked on this insecure origin.', 'warn');
  state.integrityWarned = true;
  return '';
}
/** Reject a download that does not match the build's content address; the size check needs no WebCrypto. */
async function verifyAsset(bytes, { size, sha256, label }) {
  if (Number.isInteger(size) && bytes.length !== size) throw integrityError(label, `${bytes.length} of ${size} bytes`);
  if (!sha256) return bytes;
  const digest = await digestBytes(bytes);
  if (digest && digest !== sha256) throw integrityError(label, 'checksum mismatch');
  return bytes;
}
/** tools/genwebstage.py names build.json's records by a SHA-256 prefix: assets/manifest.<16 hex>.json for the
 *  manifest and assets/<24 hex>.json for the operations file. Those prefixes are the only hash the records carry. */
const CONTENT_ADDRESS = /(?:^|\/)(?:manifest\.)?([0-9a-f]{16,64})\.json$/;
/** Fetch a JSON record; a content-addressed name is checked against its bytes like any other asset. */
async function fetchJSON(url, options = {}) {
  const label = url.split('?')[0];
  const bytes = await fetchBytes(url, { ...options, track: false });
  // Untracked transfers report no bytes; a completed record is the watchdog's only sign of a flowing link.
  noteActivity();
  const address = CONTENT_ADDRESS.exec(label)?.[1];
  if (address) {
    const digest = await digestBytes(bytes);
    if (digest && !digest.startsWith(address)) throw integrityError(label, 'checksum mismatch');
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}
async function stageFiles(manifest) {
  const queue = manifest.slice();
  const fs = window.FS;
  const worker = async () => {
    while (queue.length) {
      const file = queue.shift();
      const downloaded = await fetchBytes(file.u, { immutable: true });
      let bytes = await verifyAsset(downloaded, { size: file.s, sha256: file.h, label: file.p });
      if (file.p === COMMAND_MAP) {
        bytes = new TextEncoder().encode(applyBindings(new TextDecoder().decode(bytes), bootSettings.bindings));
      }
      const path = `${DATA_ROOT}/${file.p}`;
      fs.mkdirTree(path.slice(0, path.lastIndexOf('/')));
      fs.writeFile(path, bytes);
    }
  };
  await Promise.all(Array.from({ length: Math.min(STAGE_STREAMS, queue.length) }, worker));
}
async function stageFont(build) {
  const { url, size, sha256 } = build.font;
  const bytes = await verifyAsset(await fetchBytes(url, { immutable: true }), { size, sha256, label: 'font' });
  window.FS.writeFile(FONT_PATH, bytes);
}
function restorePersistence() {
  return new Promise(resolve => {
    const fs = window.FS;
    fs.mkdirTree(USER_DIR);
    try {
      if (!window.IDBFS) throw new Error('Persistent filesystem was not linked into this engine build.');
      fs.mount(window.IDBFS, {}, USER_DIR);
      fs.syncfs(true, error => {
        if (error) log(`Save storage unavailable: ${error.message || error}`, 'warn');
        state.persistenceReady = !error;
        resolve();
      });
    } catch (error) {
      log(`Save storage unavailable: ${error.message}`, 'warn');
      resolve();
    }
  });
}

// ============================================================================
// Boot
// ============================================================================
function engineArguments(manifest) {
  const argumentsList = ['-win', '-noshellmap'];
  const directMap = params.get('map');
  // Native -file expands a map stem into Maps/<stem>/<stem>.map itself. Accept a complete dataset path too.
  if (directMap) {
    const leaf = mapLeaf(directMap);
    const known = /^[A-Za-z0-9_]+$/.test(leaf)
      && manifest.some(file => file.p.toLowerCase() === `maps/${leaf}/${leaf}.map`.toLowerCase());
    if (!known) {
      throw new Error('That battlefield is unavailable in this build. Remove the map from the URL and reload.');
    }
    argumentsList.push('-file', `Maps/${leaf}.map`);
  }
  argumentsList.push(...diagnostics.engineArguments());
  return argumentsList;
}
function bootReport() {
  const report = {};
  for (const [start, end, name] of BOOT_MEASURES) {
    try {
      report[name] = Math.round(performance.measure(`wpBoot:${name}`, `wpBoot:${start}`, `wpBoot:${end}`).duration);
    } catch {
      log(`Boot measurement unavailable: ${name}`, 'warn');
    }
  }
  return report;
}
/** First engine frame: the synchronous main() has finished and the battlefield is live. */
function handleEngineRunning() {
  if (state.failed) return;
  state.runtimeReady = true;
  performance.mark('wpBoot:running');
  window.wpBootReport = bootReport();
  log(`[BOOT] ${JSON.stringify(window.wpBootReport)}`);
  paintProgress(100);
  $('boot').classList.add('departing');
  setTimeout(() => {
    if (!state.failed) $('boot').hidden = true;
  }, BOOT_FADE_MS);
  $('utilityBar').hidden = false;
  applyAudio();
  setPause('hidden', hiddenPauseWanted());
  canvas.focus({ preventScroll: true });
  diagnostics.bootBeacon(window.wpBootReport, state.build.id);
}
async function instantiateEngine(build, imports, callback) {
  let bytes;
  try {
    setPhase('Downloading engine…');
    const { url, size, sha256 } = build.engine.wasm;
    bytes = await verifyAsset(await fetchBytes(url, { immutable: true }), { size, sha256, label: 'engine' });
  } catch (error) {
    fail(`Engine download failed. ${error.message}`, error.code || 'WP-DOWNLOAD');
    return;
  }
  try {
    setPhase('Preparing engine…');
    setWatchdogMode('engine');
    const result = await WebAssembly.instantiate(bytes, imports);
    // A boot that failed while compiling stays on its recovery page; the glue never receives this instance.
    if (state.failed) return;
    performance.mark('wpBoot:engineReady');
    callback(result.instance, result.module);
  } catch (error) {
    fail(`The engine could not be prepared. ${error.message}`, 'WP-ENGINE');
  }
}
/** Emscripten preRun: MEMFS layout, engine environment, data staging and save restore before main(). */
function prepareBattlefield(build, manifest) {
  const fs = window.FS;
  setPhase('Preparing the battlefield…');
  setWatchdogMode('transfer');
  window.addRunDependency(CONTENT_DEPENDENCY);
  const env = window.ENV;
  env.CNC_GENERALS_ZH_PATH = DATA_ROOT;
  env.CNC_GENERALS_PATH = BASE_ROOT;
  env.HOME = HOME_DIR;
  // The channel API applies the persisted master volume; keep the backend master at unity.
  env.WP_VOLUME = '100';
  diagnostics.configureEngine(env);
  for (const directory of [DATA_ROOT, BASE_ROOT, FONT_DIR]) fs.mkdirTree(directory);
  fs.chdir(DATA_ROOT);
  // MEMFS is case-sensitive; the engine asks for both spellings.
  fs.symlink(`${DATA_ROOT}/Data`, `${DATA_ROOT}/data`);
  Promise.all([stageFiles(manifest), stageFont(build), restorePersistence()])
    .then(() => {
      if (state.failed) return;
      fs.writeFile(`${USER_DIR}/Options.ini`, renderOptions(bootSettings, diagnostics.debug));
      performance.mark('wpBoot:dataReady');
      setPhase('Starting command network…');
      setWatchdogMode('engine');
      setTimeout(() => {
        if (!state.failed) window.removeRunDependency(CONTENT_DEPENDENCY);
      }, RUN_RELEASE_DELAY_MS);
    })
    .catch(error => fail(`Battlefield preparation failed. ${error.message}`, error.code || 'WP-DATA'));
}
function createModule(build, manifest) {
  return {
    canvas,
    arguments: engineArguments(manifest),
    locateFile: path => (path.endsWith('.wasm') ? build.engine.wasm.url : path),
    print: enginePrint,
    printErr: engineError,
    onGameState: updateGameState,
    onMatchResult: handleResult,
    onGameMessage: handleGameMessage,
    onAbort: reason => fail(`The engine stopped unexpectedly: ${String(reason).slice(0, 150)}`, 'WP-ENGINE'),
    onEngineRunning: handleEngineRunning,
    onGameExit: handleGameExit,
    instantiateWasm(imports, callback) {
      instantiateEngine(build, imports, callback);
      return {};
    },
    preRun: [() => prepareBattlefield(build, manifest)],
  };
}
/** The glue is a classic script; subresource integrity pins it to the build record. */
function loadEngineScript(build) {
  const script = document.createElement('script');
  script.src = build.engine.js.url;
  if (build.engine.js.sha256) script.integrity = `sha256-${hexToBase64(build.engine.js.sha256)}`;
  // The glue is an untracked transfer; its arrival keeps a slow but flowing link clear of the stall watchdog.
  script.onload = noteActivity;
  script.onerror = () => fail('The engine script could not be downloaded or did not match this build. '
    + 'Check your connection and reload.', 'WP-SCRIPT-DOWNLOAD');
  document.body.append(script);
}
async function bootGame() {
  performance.mark('wpBoot:deploy');
  const build = await fetchJSON('build.json');
  state.build = build;
  const [manifest, missions] = await Promise.all([
    fetchJSON(build.manifest, { immutable: true }),
    fetchJSON(build.operations, { immutable: true }),
  ]);
  state.operations = missions;
  state.progress = mergeLatestProgress();
  updateCompletionCount();
  loader.totalBytes = build.engine.wasm.size + build.font.size + manifest.reduce((sum, entry) => sum + entry.s, 0);
  const preset = QUALITY_PRESETS[bootSettings.quality];
  canvas.width = preset.width;
  canvas.height = preset.height;
  window.Module = createModule(build, manifest);
  loadEngineScript(build);
}
function startBoot() {
  watchdog.timer = setInterval(watchdogTick, WATCHDOG_TICK_MS);
  bootGame().catch(error => fail(error.message, error.code || 'WP-START'));
}

// ============================================================================
// Listeners (registered before the engine's SDL handlers) and start
// ============================================================================
$('closePanel').addEventListener('click', closePanel);
panel.addEventListener('cancel', event => {
  event.preventDefault();
  closePanel();
});
// Modal keystrokes must never command units.
document.addEventListener('keydown', event => {
  if (!panel.open) return;
  event.stopImmediatePropagation();
  if (event.key === 'Escape') {
    event.preventDefault();
    closePanel();
  }
}, true);
canvas.addEventListener('contextmenu', event => event.preventDefault());
$('settingsButton').addEventListener('click', showSettings);
$('helpButton').addEventListener('click', showHelp);
$('journalButton').addEventListener('click', showJournal);
$('briefingButton').addEventListener('click', showBriefing);
$('dismissGuide').addEventListener('click', dismissGuide);
$('guidanceButton').addEventListener('click', toggleGuide);
$('guideOverview').addEventListener('click', showGuidanceOverview);
$('reloadButton').addEventListener('click', () => location.reload());
$('returnButton').addEventListener('click', () => location.reload());
$('diagnosticsButton').addEventListener('click', copyDiagnostics);
$('muteButton').addEventListener('click', toggleMute);
$('fullscreenButton').addEventListener('click', toggleFullscreen);
document.addEventListener('fullscreenchange', () => {
  $('fullscreenButton').setAttribute('aria-label', document.fullscreenElement ? 'Exit fullscreen' : 'Enter fullscreen');
});
document.addEventListener('visibilitychange', () => setPause('hidden', hiddenPauseWanted()));
canvas.addEventListener('webglcontextlost', handleContextLost);
window.addEventListener('storage', handleStorageEvent);
window.addEventListener('error', handleWindowError);
window.addEventListener('unhandledrejection', handleRejection);
applyAppearance();

// tests/recovery.test.mjs runs this module under node with a fake DOM and
// `globalThis.__wpTestHarness = true`; it drives the shell through this seam
// instead of the network boot. Browsers never define `process`.
const TEST_HARNESS = typeof process === 'object' && process !== null
  && typeof process.versions?.node === 'string' && globalThis.__wpTestHarness === true;
if (TEST_HARNESS) {
  globalThis.__wpTest = {
    state, settings, bootSettings, loader, watchdog, diagnostics, logLines,
    fail, closePanel, openPanel, setPause, applyAudio, saveCheckpoint, loadCheckpoint,
    updateGameState, handleResult, handleGameMessage, copyDiagnostics, showBriefing, showDebrief,
    showSettings, showHelp, showJournal, updateRestartNote, requestRestart,
    handleEngineRunning, handleGameExit, watchdogTick, setWatchdogMode, noteActivity, setPhase,
    progressBytes, fetchBytes, fetchJSON, verifyAsset, instantiateEngine, loadEngineScript, engineArguments,
    quiesceEngine,
  };
} else {
  startBoot();
}
