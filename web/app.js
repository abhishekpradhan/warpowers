import {
  SETTINGS_KEY, PROGRESS_KEY, BINDINGS, BINDING_KEYS, DEFAULT_SETTINGS,
  sanitizeSettings, readSettings, applyBindings, renderOptions,
  emptyProgress, sanitizeProgress, recordResult, missionRecord, formatTime, mapLeaf,
  serializeOperationRecord, restoreOperationRecord, OPERATION_RECORD_MAX_BYTES,
  mergeProgressRecords, canonicalizeProgress,
} from './core.js';

const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const params = new URLSearchParams(location.search);
const DEBUG = params.get('debug') === '1';
const DIAGNOSTIC = params.has('autotest') || params.has('review');
const USER_DIR = '/home/web_user/.local/share/GeneralsX/GeneralsZH';
const SAVE_PATH = `${USER_DIR}/Save/wp-checkpoint.sav`;
const SAVE_META = `${USER_DIR}/wp-checkpoint.json`;
const pauseReasons = new Set();
const logLines = [];
const testLines = [];
let storage;
try { storage = window.localStorage; } catch { storage = { getItem: () => null, setItem: () => { throw new Error('Storage is unavailable'); } }; }
let settings = readSettings(storage, matchMedia('(prefers-reduced-motion: reduce)').matches);
const bootSettings = structuredClone(settings);
let progress = readStoredProgress();
let operations = { missions: [] };
let build;
let gameState = { inGame: false, map: '', seconds: 0 };
let currentMap = '';
let currentMission = null;
let guideDismissed = false;
let runtimeReady = false;
let persistenceReady = false;
let checkpointBusy = false;
let settingsPersistent = true;
let failed = false;
let pendingResult = null;
let lastResultKey = '';
let toastTimer;
let activeToasts = [];
let lastActivity = performance.now();
let loadedBytes = 0;
let totalBytes = 1;
let panelKind = '';
const canvas = $('canvas');
const panel = $('panel');

function log(message) {
  const text = String(message);
  logLines.push(text);
  if (logLines.length > 120) logLines.shift();
  console.log(text);
  // Keep bounded, visible diagnostic evidence even after verbose native frame
  // logs roll out of the browser console. Never shown during ordinary play.
  if (DIAGNOSTIC && (/\[WP_(?:AUTO|TEST)\].*(?:ECONOMY|POWERS|MISSION|MECHANICS|PASS|FAIL|MATCH_RESULT)/.test(text) || text.includes('[WP_REVIEW]'))) {
    testLines.push(text); if (testLines.length > 80) testLines.shift();
    $('testReport').hidden = false; $('testReport').textContent = testLines.join('\n');
  }
  if (DEBUG) { $('debugLog').hidden = false; $('debugLog').textContent = logLines.slice(-25).join('\n'); }
}
function renderToasts() {
  clearTimeout(toastTimer);
  const now = performance.now();
  activeToasts = activeToasts.filter(notice => notice.expires > now);
  $('toast').textContent = activeToasts.map(notice => notice.text).join('\n');
  $('toast').hidden = !activeToasts.length;
  if (activeToasts.length)
    toastTimer = setTimeout(renderToasts, Math.max(1, Math.min(...activeToasts.map(notice => notice.expires)) - now));
}
function toast(text) {
  // Keep a few concurrent announcements visible without delaying a fresh alert
  // behind production chatter. Repeated text refreshes its existing notice.
  activeToasts = activeToasts.filter(notice => notice.text !== text);
  activeToasts.push({ text, expires: performance.now() + 5500 });
  activeToasts = activeToasts.slice(-3);
  renderToasts();
}
function writeStorage(key, value) {
  try { storage.setItem(key, JSON.stringify(value)); return true; }
  catch {
    settingsPersistent = false;
    $('storageStatus').textContent = 'Browser storage is unavailable. Preferences and progress last for this tab only.';
    return false;
  }
}
function readStoredProgress() {
  try { return sanitizeProgress(JSON.parse(storage.getItem(PROGRESS_KEY))); }
  catch { return emptyProgress(); }
}
function mergeLatestProgress(value = progress) {
  return canonicalizeProgress(mergeProgressRecords(value, readStoredProgress()), operations.missions);
}
function persistProgress(value) {
  progress = mergeLatestProgress(value);
  const persisted = !DIAGNOSTIC && writeStorage(PROGRESS_KEY, progress);
  updateRecordDisplay();
  return persisted;
}
function missionStatusText(record) {
  return record.wins ? `COMPLETED${record.bestSeconds ? ` · ${formatTime(record.bestSeconds)}` : ''}` : 'UNPLAYED';
}
function updateRecordDisplay() {
  updateCompletionCount();
  if (panelKind !== 'journal') return;
  for (const status of $('panelBody').querySelectorAll('[data-record-mission]')) {
    const mission = operations.missions.find(mission => mission.id === status.dataset.recordMission);
    if (!mission) continue;
    const record = missionRecord(progress, mission);
    status.textContent = missionStatusText(record);
    status.classList.toggle('isComplete', record.wins > 0);
  }
}
window.addEventListener('storage', event => {
  if (DIAGNOSTIC || (event.key !== PROGRESS_KEY && event.key !== null)) return;
  if (event.newValue === null) { progress = emptyProgress(); updateRecordDisplay(); return; }
  let incoming;
  try { incoming = JSON.parse(event.newValue); } catch { return; }
  const stored = canonicalizeProgress(readStoredProgress(), operations.missions);
  progress = canonicalizeProgress(mergeProgressRecords(progress, incoming, stored), operations.missions);
  // Converge overlapping writes from other tabs without an event/write loop.
  if (JSON.stringify(progress) !== JSON.stringify(stored)) writeStorage(PROGRESS_KEY, progress);
  updateRecordDisplay();
});
function applyAppearance() {
  document.documentElement.style.setProperty('--ui-scale', settings.uiScale / 100);
  document.documentElement.classList.toggle('reducedMotion', settings.reducedMotion);
  document.documentElement.classList.toggle('highContrast', settings.highContrast);
  $('muteButton').classList.toggle('isMuted', settings.master === 0);
  $('muteButton').textContent = settings.master === 0 ? '×♪' : '♪';
  $('muteButton').setAttribute('aria-label', settings.master === 0 ? 'Unmute audio' : 'Mute audio');
}
function applyAudio() {
  if (runtimeReady && typeof window.Module?._wpSetAudioLevels === 'function')
    window.Module._wpSetAudioLevels(settings.master, settings.music, settings.effects, settings.voice);
  else if (runtimeReady && typeof window.Module?._wpSetMasterVolume === 'function')
    window.Module._wpSetMasterVolume(settings.master);
}
function saveSettings() {
  settings = sanitizeSettings(settings);
  writeStorage(SETTINGS_KEY, settings);
  applyAppearance(); applyAudio();
}
function setPause(reason, active) {
  if (active) pauseReasons.add(reason); else pauseReasons.delete(reason);
  if (runtimeReady && window.Module?._wpSetWebPause) window.Module._wpSetWebPause(pauseReasons.size ? 1 : 0);
}
function closePanel() {
  if (panel.open) panel.close();
  panelKind = ''; setPause('panel', false); canvas.focus({ preventScroll: true });
}
function openPanel(kind, title, eyebrow = 'COMMAND NETWORK') {
  panelKind = kind;
  $('panelTitle').textContent = title; $('panelEyebrow').textContent = eyebrow;
  $('panelBody').replaceChildren();
  if (!panel.open) { setPause('panel', true); panel.showModal(); }
  panel.scrollTop = 0;
}
function appendHTML(html) { $('panelBody').insertAdjacentHTML('beforeend', html); }
function section(title) { appendHTML(`<h3 class="sectionLabel">${escapeHTML(title)}</h3>`); }
function needRestart() {
  return ['quality', 'rightClickOrders', 'cameraSpeed', 'bindings'].some(key => JSON.stringify(settings[key]) !== JSON.stringify(bootSettings[key]));
}
function updateRestartNote() {
  const note = $('restartNote');
  if (!note) return;
  note.classList.toggle('pending', needRestart());
  note.textContent = needRestart()
    ? 'Display, camera and key changes take effect when the game restarts. The current battle continues with its original controls.'
    : 'Audio and overlay settings apply immediately. Display and control changes apply on the next game launch.';
  $('applyRestart').hidden = !needRestart();
}
function rangeSetting(key, label, min = 0, max = 100) {
  appendHTML(`<div class="settingRow"><label for="setting-${key}">${escapeHTML(label)}</label><div class="rangeWrap"><input id="setting-${key}" type="range" min="${min}" max="${max}" value="${settings[key]}"><output id="value-${key}" for="setting-${key}">${settings[key]}%</output></div></div>`);
  $(`setting-${key}`).addEventListener('input', event => {
    settings[key] = Number(event.target.value); $(`value-${key}`).textContent = `${settings[key]}%`;
    saveSettings(); updateRestartNote();
  });
}
function checkboxSetting(key, label) {
  appendHTML(`<div class="settingRow"><label for="setting-${key}">${escapeHTML(label)}</label><input id="setting-${key}" type="checkbox" ${settings[key] ? 'checked' : ''}></div>`);
  $(`setting-${key}`).addEventListener('change', event => {
    settings[key] = event.target.checked; saveSettings(); updateRestartNote(); updateGuide();
    if (key === 'pauseWhenHidden') setPause('hidden', settings.pauseWhenHidden && document.hidden && !DIAGNOSTIC);
  });
}
function checkpointMeta() {
  if (!runtimeReady || !window.FS) return null;
  try {
    if (!window.FS.analyzePath(SAVE_PATH).exists) return null;
    return JSON.parse(window.FS.readFile(SAVE_META, { encoding: 'utf8' }));
  } catch { return null; }
}
function syncSaves() {
  return new Promise((resolve, reject) => {
    if (!persistenceReady) { reject(new Error('Persistent save storage is unavailable in this browser session.')); return; }
    window.FS.syncfs(false, error => error ? reject(error) : resolve());
  });
}
async function saveCheckpoint() {
  if (checkpointBusy || !gameState.inGame || !window.Module?._wpSaveGame) return;
  checkpointBusy = true;
  const button = $('saveCheckpoint'); if (button) button.disabled = true;
  const fs = window.FS;
  let previous, previousMeta, captured = false;
  try {
    previous = fs.analyzePath(SAVE_PATH).exists ? fs.readFile(SAVE_PATH) : null;
    previousMeta = fs.analyzePath(SAVE_META).exists ? fs.readFile(SAVE_META) : null;
    captured = true;
    const result = window.Module._wpSaveGame();
    if (result !== 0) throw new Error(`The current battle could not be saved (code ${result}).`);
    const metadata = { version: 1, compatibility: build.compatibility, map: mapLeaf(gameState.map), mission: currentMission?.id || '', title: currentMission?.title || mapTitle(currentMap), savedAt: new Date().toISOString() };
    window.FS.writeFile(SAVE_META, JSON.stringify(metadata));
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
  }
  finally {
    checkpointBusy = false;
    if (panelKind === 'settings') showSettings();
  }
}
function loadCheckpoint() {
  if (checkpointBusy || gameState.inGame) return;
  const metadata = checkpointMeta();
  if (!metadata || metadata.compatibility !== build.compatibility) { toast('This checkpoint belongs to another game version. Start a new battle.'); return; }
  closePanel();
  const result = window.Module._wpLoadGame?.();
  if (result !== 0) toast(`Could not restore the checkpoint (code ${result ?? 'unavailable'}).`);
  else { currentMap = ''; lastResultKey = ''; toast('Checkpoint restored.'); }
}
function showSettings() {
  openPanel('settings', 'Settings');
  section('Audio');
  rangeSetting('master', 'Master volume'); rangeSetting('music', 'Music');
  rangeSetting('effects', 'Effects & ambience'); rangeSetting('voice', 'Unit voices & announcer');
  section('Display & camera');
  appendHTML(`<div class="settingRow"><label for="quality">Rendering</label><select id="quality"><option value="performance">Performance · 1280 × 720</option><option value="balanced">Balanced · 1600 × 900</option><option value="high">High resolution · 1920 × 1080</option></select></div>`);
  $('quality').value = settings.quality;
  $('quality').addEventListener('change', event => { settings.quality = event.target.value; saveSettings(); updateRestartNote(); });
  rangeSetting('uiScale', 'Overlay text size', 85, 125); rangeSetting('cameraSpeed', 'Camera scroll speed');
  checkboxSetting('rightClickOrders', 'Right-click to issue orders');
  checkboxSetting('highContrast', 'High-contrast overlays'); checkboxSetting('reducedMotion', 'Reduce interface motion');
  checkboxSetting('pauseWhenHidden', 'Pause when this tab is hidden'); checkboxSetting('guide', 'Show field guidance');
  section('Keyboard');
  for (const [key, [label]] of Object.entries(BINDINGS)) {
    appendHTML(`<div class="settingRow"><label for="key-${key}">${escapeHTML(label)}</label><select id="key-${key}">${BINDING_KEYS.map(k => `<option value="${k}">${k}</option>`).join('')}</select></div>`);
    const input = $(`key-${key}`); input.value = settings.bindings[key];
    input.addEventListener('change', () => {
      if (Object.entries(settings.bindings).some(([other, value]) => other !== key && value === input.value)) {
        input.value = settings.bindings[key]; toast('That key already has an assignment. Choose another key.'); return;
      }
      settings.bindings[key] = input.value; saveSettings(); updateRestartNote();
    });
  }
  appendHTML('<p id="restartNote" class="settingsNote"></p><button id="applyRestart" hidden>Restart game to apply</button>');
  updateRestartNote();
  $('applyRestart').addEventListener('click', () => {
    if (!gameState.inGame) { location.reload(); return; }
    $('restartNote').textContent = 'Restarting ends the current battle. Save a checkpoint first, or choose Restart now to discard unsaved progress.';
    $('applyRestart').textContent = 'Restart now';
    $('applyRestart').onclick = () => location.reload();
  }, { once: true });
  section('Battle checkpoint');
  const metadata = checkpointMeta();
  const compatible = metadata?.compatibility === build?.compatibility;
  appendHTML(`<div class="saveRow"><button id="saveCheckpoint" ${checkpointBusy || !gameState.inGame || !persistenceReady ? 'disabled' : ''}>${checkpointBusy ? 'Saving…' : 'Save checkpoint'}</button><button id="loadCheckpoint" ${checkpointBusy || !compatible || gameState.inGame ? 'disabled' : ''}>Resume checkpoint</button><p class="settingsNote">${metadata ? `${escapeHTML(metadata.title)} · ${escapeHTML(new Date(metadata.savedAt).toLocaleString())}${compatible ? '' : ' · saved in a different game version'}` : 'One checkpoint per device. Return to the menu to resume a saved battle.'}${!persistenceReady ? ' Persistent save storage is unavailable.' : ''}</p></div>`);
  $('saveCheckpoint').addEventListener('click', saveCheckpoint); $('loadCheckpoint').addEventListener('click', loadCheckpoint);
  appendHTML(`<p class="settingsNote">Build ${escapeHTML(build?.id || 'loading')}. <button class="textButton" id="copyBuild">Copy diagnostics</button></p>`);
  $('copyBuild').addEventListener('click', copyDiagnostics);
}
function showHelp() {
  openPanel('help', 'Field manual', 'KNOW YOUR TOOLS');
  appendHTML('<p class="manualIntro">Build a working economy, scout before committing your army, and protect your headquarters. In skirmish, destroying the enemy headquarters wins the battle. Operations display their own objectives.</p>');
  section('Command');
  const controls = [
    ['Select unit or building', 'Left click'], ['Select a group', 'Drag a selection box'],
    ['Move, attack or set a rally point', bootSettings.rightClickOrders ? 'Right click' : 'Left click on the destination'],
    ['Cancel an order or build placement', 'Right click'],
    ['Deselect', bootSettings.rightClickOrders ? 'Left click open ground' : 'Right click'],
    ['Attack while advancing', 'Attack Move button, then choose a destination'], ['Guard a position', 'Guard button, then choose a position'],
    ['Stop', bootSettings.bindings.STOP], ['Scatter', bootSettings.bindings.SCATTER],
    ['Select army', bootSettings.bindings.SELECT_ALL], ['Select matching units', bootSettings.bindings.SELECT_MATCHING_UNITS],
    ['Next idle builder', bootSettings.bindings.SELECT_NEXT_IDLE_WORKER], ['View headquarters', bootSettings.bindings.VIEW_COMMAND_CENTER],
    ['Create / recall group', 'Ctrl + 1–9 / 1–9'], ['Add group to selection / view group', 'Shift + 1–9 / Alt + 1–9'],
    ['View last radar alert', 'Space'], ['Rotate camera', ', / .'], ['Zoom camera', 'Wheel / Page Up / Page Down'],
    ['Reset camera', 'Home'], ['Pause / battle menu', `${bootSettings.bindings.TOGGLE_PAUSE} / Escape`],
  ];
  appendHTML(`<dl class="controlList">${controls.map(([name, key]) => `<div><dt>${escapeHTML(name)}</dt><dd>${escapeHTML(key)}</dd></div>`).join('')}</dl>`);
  appendHTML('<div class="manualColumns"><section><h3>Meridian Combine</h3><p>Precise, expensive hardware with a power grid to protect. Establish a Power Array and Exchange, then a Vehicle Plant. Mix Vectors with infantry support and use Outriders to find safe approaches.</p><ul><li>Wardens suppress infantry.</li><li>Lancers threaten armor and aircraft.</li><li>Zenith artillery attacks from range.</li></ul></section><section><h3>Jackal Front</h3><p>Cheap, mobile raiders with independent infrastructure. Scavengers haul supplies to Rackets without a power grid. Use Vultures to strike exposed targets, and preserve your raiding force for the next opening.</p><ul><li>Scrappers clear hostile infantry.</li><li>Stings cover armor and air threats.</li><li>Mongrels absorb pressure for raiders.</li></ul></section></div>');
  section('Supply lines');
  appendHTML('<p class="muted">Build an Exchange or Racket near a supply cache, then train a Porter or Scavenger there. Haulers collect crates and return them to the hub for money. Protect this route and expand to the contested caches before your home supply runs out. Hubs also provide a small income trickle for recovery.</p>');
  section('Faction powers');
  appendHTML('<p class="muted">A Directorate unlocks Meridian’s Precision Strike: a visible targeting beacon followed by a concentrated blast. A Jackal Den unlocks Tunnel Ambush: a mixed infantry squad at a scouted target. Select the completed structure, choose its power and target revealed ground. Each power must recharge before it can be used again.</p>');
  section('Production & survival');
  appendHTML('<p class="muted">Select a production building to view its units. A padlock marks unavailable orders; hover a portrait for cost, role and prerequisites. Queue units by clicking their available portraits; click a queued item to cancel it. Select a builder to place structures on revealed ground. Keep your income defended, watch the power meter, and leave a reserve at headquarters.</p>');
}
function recordStatus(message, failed = false) {
  if (panelKind !== 'journal') { toast(message); return; }
  const status = $('recordStatus');
  status.hidden = false;
  status.classList.toggle('error', failed);
  status.textContent = message;
}
function downloadRecord() {
  try {
    progress = mergeLatestProgress();
    updateRecordDisplay();
    const file = new Blob([serializeOperationRecord(progress)], { type: 'application/json' });
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url; link.download = `war-powers-record-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    recordStatus('Record download started. Keep the file to restore your completions and best times.');
  } catch (error) { recordStatus(`Record could not be downloaded: ${error.message}`, true); }
}
async function restoreRecord(file) {
  if (!file) return;
  const button = $('restoreRecord');
  button.disabled = true; button.textContent = 'Restoring…';
  try {
    if (file.size > OPERATION_RECORD_MAX_BYTES) throw new Error('Choose an operation record smaller than 64 KB.');
    const text = await file.text();
    // Read progress after the file resolves, preserving any intervening result.
    const restored = restoreOperationRecord(mergeLatestProgress(), text);
    const persisted = persistProgress(restored);
    recordStatus(persisted
      ? 'Record restored. Your existing completions and better results are kept.'
      : 'Record restored for this tab only. Keep your backup; this record has not been saved in the browser.');
  } catch (error) { recordStatus(`Record not restored: ${error.message}`, true); }
  finally { button.disabled = false; button.textContent = 'Restore record'; }
}
function showJournal() {
  progress = mergeLatestProgress();
  updateCompletionCount();
  openPanel('journal', 'Operations', 'THE MERIDIAN STRIP');
  appendHTML(`<p class="manualIntro">${escapeHTML(operations.campaign?.description || 'Training, operations and commander trials. Your record stays on this device.')}</p>`);
  appendHTML('<p class="muted">Every mission is available from the start. Follow the order below for the story, or start anywhere. Skirmish lets you choose either side.</p><div class="recordTools"><div class="actions"><button id="downloadRecord">Download record</button><button id="restoreRecord">Restore record</button><input id="recordFile" type="file" accept=".json,application/json" aria-label="Operation record backup" hidden></div><p class="settingsNote">Completions and best times stay in this browser and may be cleared. Keep a backup to restore them or move browsers. Battle checkpoints are separate.</p><p id="recordStatus" class="settingsNote" role="status" hidden></p></div>');
  $('downloadRecord').addEventListener('click', downloadRecord);
  $('restoreRecord').addEventListener('click', () => $('recordFile').click());
  $('recordFile').addEventListener('change', event => {
    const file = event.target.files[0]; event.target.value = '';
    restoreRecord(file);
  });
  for (const [index, mission] of operations.missions.entries()) {
    const record = missionRecord(progress, mission);
    appendHTML(`<article class="missionEntry"><span class="missionIndex">${String(index + 1).padStart(2, '0')}</span><div><span class="missionFaction">Play as ${escapeHTML(mission.faction === 'jackal' ? 'Jackal Front' : 'Meridian Combine')} · ${escapeHTML(mission.duration)}</span><h3>${escapeHTML(mission.title)}</h3><p>${escapeHTML(mission.briefing)}</p><button class="textButton" data-mission="${index}" style="margin-top:12px" ${gameState.inGame ? 'disabled' : ''}>Review deployment ↗</button></div><span class="missionStatus${record.wins ? ' isComplete' : ''}" data-record-mission="${escapeHTML(mission.id)}">${missionStatusText(record)}</span></article>`);
  }
  if (gameState.inGame) appendHTML('<p class="settingsNote">Return to the main menu before choosing another operation.</p>');
  for (const button of $('panelBody').querySelectorAll('[data-mission]')) button.addEventListener('click', () => {
    const index = Number(button.dataset.mission); closePanel();
    if (window.Module?._wpShowMission) window.Module._wpShowMission(index);
    else toast('Choose this operation on the Deployment screen.');
  });
}
function showBriefing() {
  if (!currentMission) { showHelp(); return; }
  const mission = currentMission;
  openPanel('briefing', mission.title, mission.faction === 'jackal' ? 'JACKAL FRONT · OPERATIONS' : 'MERIDIAN COMBINE · OPERATIONS');
  appendHTML(`<p class="operationTag">${escapeHTML(mission.duration)} · ${escapeHTML(mission.category)}</p><p class="briefingLead">${escapeHTML(mission.briefing)}</p>`);
  section('Objectives');
  appendHTML(`<ol class="objectiveList">${mission.objectives.map(o => `<li>${escapeHTML(o.label)}${o.optional ? ' <span class="muted">(Optional)</span>' : ''}</li>`).join('')}</ol><div class="actions"><button id="beginMission" class="primary">Return to battlefield</button></div>`);
  $('beginMission').addEventListener('click', closePanel);
}
function showDebrief() {
  const result = pendingResult; if (!result) return;
  const mission = operations.missions.find(m => m.id === result.operationId || m.map === mapLeaf(result.map));
  if (!mission) return;
  openPanel('debrief', mission.title, result.won ? 'OPERATION COMPLETE' : 'OPERATION FAILED');
  const stats = result.stats || {};
  appendHTML(`<p class="briefingLead">${escapeHTML(result.won ? mission.debriefWin : mission.debriefLoss)}</p><div class="resultStats"><div><strong>${formatTime(stats.durationSeconds)}</strong><span>BATTLE TIME</span></div><div><strong>${Number(stats.unitsBuilt) || 0}</strong><span>UNITS FIELDED</span></div><div><strong>${Number(stats.unitsLost) || 0}</strong><span>UNITS LOST</span></div></div>`);
  const next = operations.missions.find(m => m.id === mission.nextMission);
  if (result.won && next) appendHTML(`<p class="muted">Next operation: ${escapeHTML(next.title)}. Select it from Operations when you return to the menu.</p>`);
  appendHTML('<div class="actions"><button id="returnScore" class="primary">Continue to battle report</button></div>');
  $('returnScore').addEventListener('click', closePanel);
  pendingResult = null;
}
function mapTitle(id) {
  const base = id.replace(/J$/, '');
  return ({ WPTest: 'The Flats', WPRidge: 'Ridge Divide', WPScrap: 'Scrapyard', WPBasin: 'The Basin', WPRange: 'Trench Range' })[base] || 'The Meridian Strip';
}
function updateGuide() {
  if (!gameState.inGame || !settings.guide || guideDismissed || panel.open) { $('guide').hidden = true; return; }
  let title = '', body = '';
  if (currentMission) {
    const objectives = currentMission.objectives.filter(o => !o.optional);
    const objective = objectives[Math.max(0, Math.min(objectives.length - 1, gameState.objectiveStage || 0))];
    title = currentMission.category === 'training' ? 'Your next order' : 'Operations officer'; body = objective?.hint || '';
    if (!bootSettings.rightClickOrders) body = body.replace(/Right-click open ground/gi, 'Left-click open ground').replace(/with a right click/gi, 'with a left click');
  } else if (gameState.seconds < 30 && !gameState.builders) {
    title = 'Establish your foothold'; body = `Select headquarters and train a builder. ${bootSettings.bindings.VIEW_COMMAND_CENTER} returns your camera home; Field manual explains the controls.`;
  } else if (!gameState.incomeBuildings) {
    title = 'Fund the next wave'; body = 'Build an Exchange or Racket beside a supply cache, then train a Porter or Scavenger at that hub. Haulers bring crates home to fund reinforcements.';
  } else if (!gameState.productionBuildings) {
    title = 'Bring in the armor'; body = 'A Vehicle Plant or Chop Shop unlocks armored units. Keep infantry nearby and scout before sending the army into the shroud.';
  } else if (gameState.seconds < 150) {
    title = 'Scout. Support. Advance.'; body = 'Combine anti-infantry and anti-armor units. Use Attack Move when advancing, and retain a reserve to protect your headquarters.';
  }
  $('guide').hidden = !body;
  $('guideTitle').textContent = title; $('guideBody').textContent = body;
}
function updateGameState(state) {
  gameState = state;
  const leaf = mapLeaf(state.map);
  $('missionHud').hidden = !state.inGame;
  if (!state.inGame) {
    $('guide').hidden = true; currentMap = '';
    // Let native victory/defeat cleanup reach the score screen before opening
    // a pausing web dialog. The result callback can precede that by seconds.
    if (pendingResult && panelKind !== 'debrief') setTimeout(showDebrief, 0);
    return;
  }
  if (leaf !== currentMap) {
    currentMap = leaf; currentMission = operations.missions.find(m => m.map === leaf) || null;
    guideDismissed = false; lastResultKey = '';
    $('missionTitle').textContent = currentMission?.title || mapTitle(leaf);
    $('missionType').textContent = (currentMission?.category || 'skirmish').toUpperCase();
    $('briefingButton').textContent = currentMission ? 'Mission briefing ↗' : 'Field manual ↗';
    if (currentMission && !DIAGNOSTIC) setTimeout(() => { if (gameState.inGame && currentMap === leaf && !panel.open) showBriefing(); }, 0);
    if (pauseReasons.size) setTimeout(() => setPause('panel', panel.open), 0);
  }
  const required = currentMission?.objectives.filter(o => !o.optional) || [];
  const objective = required[Math.max(0, Math.min(required.length - 1, state.objectiveStage || 0))];
  $('objectiveText').textContent = objective?.label.replace(/\s*\(0\/\d+\)/, '') || 'Destroy the enemy headquarters. Protect your own.';
  $('matchClock').textContent = formatTime(state.seconds);
  $('objectiveProgress').textContent = state.objectiveTarget > 0 ? `${state.objectiveProgress || 0} / ${state.objectiveTarget}` : '';
  $('objectiveTimer').textContent = state.objectiveSeconds >= 0 ? `${formatTime(state.objectiveSeconds)} remaining` : '';
  updateGuide();
}
function handleResult(result) {
  if (params.has('autotest')) log(`[WP_TEST] MATCH_RESULT ${JSON.stringify(result)}`);
  const key = `${result.map}:${result.stats?.durationSeconds}:${result.won}`;
  if (lastResultKey === key) return; lastResultKey = key;
  const mission = operations.missions.find(m => m.id === result.operationId || m.map === mapLeaf(result.map));
  if (mission) {
    persistProgress(recordResult(mergeLatestProgress(), { ...result, operationId: mission.id, seconds: result.stats?.durationSeconds }));
    pendingResult = result;
    if (!gameState.inGame) setTimeout(showDebrief, 0);
  }
}
function updateCompletionCount() {
  const campaign = operations.missions.filter(m => m.category === 'operation');
  $('completionCount').textContent = campaign.length ? `${campaign.filter(m => missionRecord(progress, m).wins > 0).length}/${campaign.length}` : '';
}
function diagnostics() {
  return JSON.stringify({ build: build?.id, compatibility: build?.compatibility, browser: navigator.userAgent,
    display: bootSettings.quality, map: currentMap, boot: window.wpBootReport, persistenceReady, settingsPersistent,
    logs: logLines.slice(-35), }, null, 2);
}
async function copyDiagnostics() {
  try { await navigator.clipboard.writeText(diagnostics()); toast('Diagnostics copied.'); }
  catch { openPanel('diagnostics', 'Diagnostics'); const pre = document.createElement('pre'); pre.textContent = diagnostics(); pre.style.cssText = 'white-space:pre-wrap;word-break:break-word;font-size:11px'; $('panelBody').append(pre); }
}
function fail(message, code = 'WP-RUNTIME') {
  if (failed) return; failed = true;
  log(`${code}: ${message}`);
  closePanel(); $('boot').hidden = false; $('boot').classList.remove('departing');
  $('bootError').hidden = false; $('bootPhase').textContent = 'Command connection interrupted';
  $('errorMessage').textContent = message; $('errorCode').textContent = `${code} · ${build?.id || 'initializing'}`;
  $('bootHint').textContent = 'Your saved operation record is preserved. Reload to return to command.';
  $('utilityBar').hidden = true;
}
function setPhase(phase) { if (!failed) { $('bootPhase').textContent = phase; lastActivity = performance.now(); } }
function progressBytes(bytes) {
  loadedBytes += bytes; lastActivity = performance.now();
  const percent = Math.min(99, Math.floor(loadedBytes / Math.max(1, totalBytes) * 100));
  $('bootFill').style.width = `${percent}%`; $('bootPercent').textContent = `${percent}%`;
}
async function fetchBytes(url, track = true) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error(`${url.split('?')[0]}: HTTP ${response.status}`);
    if (!track || !response.body) {
      const bytes = new Uint8Array(await response.arrayBuffer()); if (track) progressBytes(bytes.length); return bytes;
    }
    const reader = response.body.getReader(); const chunks = []; let size = 0;
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      chunks.push(value); size += value.length; progressBytes(value.length);
    }
    const result = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
    return result;
  } finally { clearTimeout(timeout); }
}
async function fetchJSON(url) { return JSON.parse(new TextDecoder().decode(await fetchBytes(url, false))); }
async function stageFiles(files) {
  const queue = files.slice();
  await Promise.all(Array.from({ length: Math.min(12, queue.length) }, async () => {
    while (queue.length) {
      const file = queue.shift(); let bytes = await fetchBytes(file.u);
      if (bytes.length !== file.s) throw new Error(`Incomplete asset: ${file.p}`);
      if (file.p === 'Data/INI/CommandMap.ini') bytes = new TextEncoder().encode(applyBindings(new TextDecoder().decode(bytes), bootSettings.bindings));
      const path = `/game/${file.p}`;
      window.FS.mkdirTree(path.slice(0, path.lastIndexOf('/'))); window.FS.writeFile(path, bytes);
    }
  }));
}
function restorePersistence() {
  return new Promise(resolve => {
    const fs = window.FS;
    fs.mkdirTree(USER_DIR);
    try {
      if (!window.IDBFS) throw new Error('Persistent filesystem was not linked into this engine build.');
      fs.mount(window.IDBFS, {}, USER_DIR);
      fs.syncfs(true, error => {
        if (error) { log(`Save storage unavailable: ${error.message || error}`); persistenceReady = false; }
        else persistenceReady = true;
        resolve();
      });
    } catch (error) { log(`Save storage unavailable: ${error.message}`); resolve(); }
  });
}

// UI listeners are registered before SDL. Modal keystrokes must never command units.
$('closePanel').addEventListener('click', closePanel);
panel.addEventListener('cancel', event => { event.preventDefault(); closePanel(); });
document.addEventListener('keydown', event => {
  if (panel.open) {
    event.stopImmediatePropagation();
    if (event.key === 'Escape') { event.preventDefault(); closePanel(); }
  }
}, true);
canvas.addEventListener('contextmenu', event => event.preventDefault());
$('settingsButton').addEventListener('click', showSettings); $('helpButton').addEventListener('click', showHelp);
$('journalButton').addEventListener('click', showJournal); $('briefingButton').addEventListener('click', showBriefing);
$('dismissGuide').addEventListener('click', () => { guideDismissed = true; $('guide').hidden = true; });
$('reloadButton').addEventListener('click', () => location.reload());
$('diagnosticsButton').addEventListener('click', copyDiagnostics);
let volumeBeforeMute = settings.master || 80;
$('muteButton').addEventListener('click', () => {
  if (settings.master) { volumeBeforeMute = settings.master; settings.master = 0; } else settings.master = volumeBeforeMute;
  saveSettings();
});
$('fullscreenButton').addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen(); else await $('stage').requestFullscreen();
  } catch { toast('Fullscreen is unavailable here. You can still play in this window.'); }
});
document.addEventListener('fullscreenchange', () => $('fullscreenButton').setAttribute('aria-label', document.fullscreenElement ? 'Exit fullscreen' : 'Enter fullscreen'));
document.addEventListener('visibilitychange', () => setPause('hidden', settings.pauseWhenHidden && document.hidden && !DIAGNOSTIC));
canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); fail('The graphics connection was lost. Reload to reconnect, then resume your last checkpoint.', 'WP-GRAPHICS'); });
window.addEventListener('error', event => { log(`UNCAUGHT: ${event.error?.stack || event.message}`); if (runtimeReady) fail('The game encountered an unexpected error. Reload to recover.', 'WP-SCRIPT'); });
window.addEventListener('unhandledrejection', event => { log(`UNHANDLED: ${event.reason?.message || event.reason}`); if (!failed) fail('A game operation could not complete. Reload to reconnect.', 'WP-ASYNC'); });
applyAppearance();

async function bootGame() {
  if (!window.WebAssembly) throw new Error('This browser does not support WebAssembly. Use a current desktop browser.');
  const probe = document.createElement('canvas');
  const gl = probe.getContext('webgl2');
  if (!gl) throw new Error('WebGL2 is unavailable. Enable browser graphics acceleration or use another desktop browser.');
  gl.getExtension('WEBGL_lose_context')?.loseContext();
  performance.mark('wpBoot:deploy');
  build = await fetchJSON('build.json');
  const [manifest, missionData] = await Promise.all([fetchJSON(build.manifest), fetchJSON(build.operations)]);
  operations = missionData; progress = mergeLatestProgress(); updateCompletionCount();
  totalBytes = build.engine.wasm.size + build.font.size + manifest.reduce((sum, entry) => sum + entry.s, 0);
  const dimensions = { performance: [1280, 720], balanced: [1600, 900], high: [1920, 1080] }[bootSettings.quality];
  [canvas.width, canvas.height] = dimensions;
  const directMap = params.get('map');
  const argumentsList = ['-win', '-noshellmap'];
  // Native -file expands a map stem into Maps/<stem>/<stem>.map itself.
  // Accept a complete dataset path too, without duplicating its directory.
  if (directMap) {
    const leaf = mapLeaf(directMap);
    if (!/^[A-Za-z0-9_]+$/.test(leaf) || !manifest.some(file => file.p.toLowerCase() === `maps/${leaf}/${leaf}.map`.toLowerCase()))
      throw new Error('That battlefield is unavailable in this build. Remove the map from the URL and reload.');
    argumentsList.push('-file', `Maps/${leaf}.map`);
  }
  if (DEBUG && params.get('args')) argumentsList.push(...params.get('args').split(',').filter(Boolean));
  window.Module = {
    canvas, arguments: argumentsList,
    locateFile: path => path.endsWith('.wasm') ? build.engine.wasm.url : path,
    print: log, printErr: log,
    onGameState: updateGameState,
    onMatchResult: handleResult,
    onGameMessage: message => { if (message?.text) toast(message.text); },
    onAbort: reason => fail(`The engine stopped unexpectedly: ${String(reason).slice(0, 150)}`, 'WP-ENGINE'),
    onEngineRunning() {
      runtimeReady = true; performance.mark('wpBoot:running');
      if (failed) return;
      const measures = [['deploy', 'engineReady', 'engineDownloadMs'], ['engineReady', 'dataReady', 'dataStageMs'], ['dataReady', 'running', 'engineInitMs'], ['deploy', 'running', 'totalMs']];
      window.wpBootReport = {};
      for (const [start, end, name] of measures) {
        try { window.wpBootReport[name] = Math.round(performance.measure(`wpBoot:${name}`, `wpBoot:${start}`, `wpBoot:${end}`).duration); }
        catch { log(`Boot measurement unavailable: ${name}`); }
      }
      log(`[BOOT] ${JSON.stringify(window.wpBootReport)}`);
      $('bootFill').style.width = '100%'; $('bootPercent').textContent = '100%';
      $('boot').classList.add('departing');
      setTimeout(() => { if (!failed) $('boot').hidden = true; }, 500);
      $('utilityBar').hidden = false; applyAudio();
      setPause('hidden', settings.pauseWhenHidden && document.hidden && !DIAGNOSTIC);
      canvas.focus({ preventScroll: true });
      if (DEBUG) fetch(`/wp-boot-ok?total=${window.wpBootReport.totalMs}&build=${encodeURIComponent(build.id)}`).catch(error => log(`Diagnostic beacon unavailable: ${error.message}`));
    },
    onGameExit() {
      if (gameState.inGame && !lastResultKey) { fail('The battle was interrupted. Reload and resume your last checkpoint.', 'WP-EXIT'); return; }
      $('boot').hidden = false; $('boot').classList.remove('departing');
      $('bootPhase').textContent = 'Session complete'; $('bootHint').textContent = 'Your operation record is saved on this device.';
      $('bootError').hidden = false; $('errorMessage').textContent = ''; $('errorCode').textContent = '';
      $('reloadButton').textContent = 'Return to command'; $('utilityBar').hidden = true;
    },
    instantiateWasm(imports, callback) {
      setPhase('Downloading engine…');
      fetchBytes(build.engine.wasm.url).then(bytes => { setPhase('Preparing engine…'); return WebAssembly.instantiate(bytes, imports); })
        .then(result => { performance.mark('wpBoot:engineReady'); callback(result.instance, result.module); })
        .catch(error => fail(`Engine download failed. ${error.message}`, 'WP-DOWNLOAD'));
      return {};
    },
    preRun: [function () {
      const fs = window.FS; const env = window.ENV;
      setPhase('Preparing the battlefield…'); window.addRunDependency('war-powers-content');
      env.CNC_GENERALS_ZH_PATH = '/game'; env.CNC_GENERALS_PATH = '/game-base'; env.HOME = '/home/web_user';
      // Channel API applies the persisted master; keep the backend master at unity.
      env.WP_VOLUME = '100';
      if (DEBUG) { env.IG_TRACE = '1'; window.IG_TRACE = 1; }
      for (const [parameter, key] of [['autotest', 'WP_AUTOTEST'], ['review', 'WP_REVIEW_SCENE'], ['scenedump', 'WP_SCENE_DUMP'], ['aitrace', 'WP_AI_TRACE'], ['doztrace', 'WP_DOZER_TRACE']])
        if (params.has(parameter)) env[key] = params.get(parameter) || '1';
      fs.mkdirTree('/game'); fs.mkdirTree('/game-base'); fs.mkdirTree('/fonts'); fs.chdir('/game'); fs.symlink('/game/Data', '/game/data');
      Promise.all([
        stageFiles(manifest),
        fetchBytes(build.font.url).then(bytes => fs.writeFile('/fonts/default.ttf', bytes)),
        restorePersistence(),
      ]).then(() => {
        fs.writeFile(`${USER_DIR}/Options.ini`, renderOptions(bootSettings, DEBUG));
        performance.mark('wpBoot:dataReady'); setPhase('Starting command network…');
        setTimeout(() => { if (!failed) window.removeRunDependency('war-powers-content'); }, 30);
      }).catch(error => fail(`Battlefield preparation failed. ${error.message}`, 'WP-DATA'));
    }],
  };
  const script = document.createElement('script'); script.src = build.engine.js.url;
  script.onerror = () => fail('The engine script could not be downloaded. Check your connection and reload.', 'WP-SCRIPT-DOWNLOAD');
  document.body.append(script);
}
const bootWatchdog = setInterval(() => {
  if (runtimeReady || failed) { clearInterval(bootWatchdog); return; }
  if (performance.now() - lastActivity > 45000) fail('Loading stopped responding. Check your connection and reload.', 'WP-TIMEOUT');
}, 5000);
bootGame().catch(error => fail(error.message, 'WP-START'));
