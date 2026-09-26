// SPDX-License-Identifier: MIT
/** Browser-independent preferences and progress rules. No game state is simulated here. */
export const SETTINGS_KEY = 'wpSettings.v2';
export const PROGRESS_KEY = 'wpProgress.v1';
/** Remappable CommandMap commands: [label, default key, default key while WASD pans the camera]. */
export const BINDINGS = Object.freeze({
  TOGGLE_ATTACKMOVE: ['Attack move', 'A', 'F'],
  GUARD: ['Guard', 'G', 'G'],
  STOP: ['Stop', 'S', 'H'],
  SCATTER: ['Scatter', 'X', 'X'],
  SELECT_MATCHING_UNITS: ['Select matching units', 'E', 'E'],
  SELECT_ALL: ['Select army', 'Q', 'Q'],
  SELECT_NEXT_IDLE_WORKER: ['Next idle builder', 'I', 'I'],
  VIEW_COMMAND_CENTER: ['View headquarters', 'H', 'J'],
  TOGGLE_PAUSE: ['Pause battle', 'P', 'P'],
});
export const BINDING_KEYS = Object.freeze('ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''));
export const CAMERA_KEY_MODES = Object.freeze({
  arrows: 'Arrow keys',
  wasd: 'W A S D (moves Attack move to F, Stop to H, View headquarters to J)',
});
/** Letters the engine consumes as camera keys while the WASD option is on. */
const WASD_KEYS = Object.freeze(['W', 'A', 'S', 'D']);
/** Rendering presets. The canvas size, Options.ini resolution and the Settings menu all read this table. */
export const QUALITY_PRESETS = Object.freeze({
  performance: Object.freeze({ label: 'Performance', width: 1280, height: 720 }),
  balanced: Object.freeze({ label: 'Balanced', width: 1600, height: 900 }),
  high: Object.freeze({ label: 'High resolution', width: 1920, height: 1080 }),
});
/** Inclusive slider ranges shared by sanitizeSettings and the Settings panel. */
export const SETTING_RANGES = Object.freeze({
  master: [0, 100],
  music: [0, 100],
  effects: [0, 100],
  voice: [0, 100],
  cameraSpeed: [0, 100],
  zoomSpeed: [1, 8],
  uiScale: [85, 125],
});
const BOOLEAN_SETTINGS = ['rightClickOrders', 'edgeScroll', 'cameraRotation', 'reducedMotion', 'highContrast', 'guide',
  'pauseWhenHidden'];
export const DEFAULT_SETTINGS = Object.freeze({
  version: 2,
  master: 80,
  music: 45,
  effects: 80,
  voice: 90,
  quality: 'balanced',
  uiScale: 100,
  cameraSpeed: 50,
  cameraKeys: 'arrows',
  edgeScroll: true,
  cameraRotation: false,
  zoomSpeed: 3,
  rightClickOrders: true,
  reducedMotion: false,
  highContrast: false,
  guide: true,
  pauseWhenHidden: true,
  bindings: Object.fromEntries(Object.entries(BINDINGS).map(([name, entry]) => [name, entry[1]])),
});
const record = value => value && typeof value === 'object' && !Array.isArray(value);
const bounded = (value, min, max, fallback) => (typeof value === 'number' && Number.isFinite(value)
  ? Math.min(max, Math.max(min, Math.round(value)))
  : fallback);

/** The default key of a command for a camera-key mode. */
export function defaultBinding(command, cameraKeys = 'arrows') {
  const entry = BINDINGS[command];
  return cameraKeys === 'wasd' ? entry[2] : entry[1];
}

/** Keep every valid, unique custom key; only invalid, reserved or duplicated entries fall back to a free default.
 *  A stored key that equals the arrow-mode default is not a customization, so switching the camera keys moves
 *  the affected commands to their WASD defaults instead of leaving them on letters the camera now owns. */
function sanitizeBindings(custom, cameraKeys = 'arrows') {
  const reserved = new Set(cameraKeys === 'wasd' ? WASD_KEYS : []);
  const chosen = {};
  const taken = new Set(reserved);
  for (const command of Object.keys(BINDINGS)) {
    const key = custom[command];
    if (!BINDING_KEYS.includes(key) || taken.has(key)) continue;
    if (cameraKeys === 'wasd' && key === BINDINGS[command][1] && key !== BINDINGS[command][2]) continue;
    chosen[command] = key;
    taken.add(key);
  }
  for (const command of Object.keys(BINDINGS)) {
    if (Object.hasOwn(chosen, command)) continue;
    const fallback = defaultBinding(command, cameraKeys);
    const key = taken.has(fallback) ? BINDING_KEYS.find(candidate => !taken.has(candidate)) : fallback;
    chosen[command] = key;
    taken.add(key);
  }
  return Object.fromEntries(Object.keys(BINDINGS).map(command => [command, chosen[command]]));
}

export function sanitizeSettings(value) {
  const data = record(value) ? value : {};
  const out = { ...DEFAULT_SETTINGS, bindings: { ...DEFAULT_SETTINGS.bindings } };
  for (const [key, [min, max]] of Object.entries(SETTING_RANGES)) out[key] = bounded(data[key], min, max, out[key]);
  if (typeof data.quality === 'string' && Object.hasOwn(QUALITY_PRESETS, data.quality)) out.quality = data.quality;
  if (typeof data.cameraKeys === 'string' && Object.hasOwn(CAMERA_KEY_MODES, data.cameraKeys)) {
    out.cameraKeys = data.cameraKeys;
  }
  for (const key of BOOLEAN_SETTINGS) {
    if (typeof data[key] === 'boolean') out[key] = data[key];
  }
  out.bindings = sanitizeBindings(record(data.bindings) ? data.bindings : {}, out.cameraKeys);
  return out;
}

export function readSettings(storage, reducedMotion = false) {
  try {
    const stored = storage.getItem(SETTINGS_KEY);
    if (stored) return sanitizeSettings(JSON.parse(stored));
    const legacyVolume = storage.getItem('wpVolume');
    return sanitizeSettings({ master: legacyVolume === null ? 80 : Number(legacyVolume), reducedMotion });
  } catch {
    return sanitizeSettings({ reducedMotion });
  }
}

/** Rewrite the Key of every remappable CommandMap entry; the engine reads the result before it starts. */
export function applyBindings(ini, bindings, cameraKeys = 'arrows') {
  const validated = sanitizeSettings({ bindings, cameraKeys }).bindings;
  return ini.replace(/(CommandMap\s+(\w+)[^\n]*\n)([\s\S]*?)(^End\s*$)/gm, (block, opening, name, body, end) => {
    if (!Object.hasOwn(validated, name)) return block;
    return opening + body.replace(/(\bKey\s*=\s*)KEY_\w+/, `$1KEY_${validated[name]}`) + end;
  });
}

/** Options.ini for the engine. Screen-edge scrolling stays off here: the page drives it with the
 *  arrow keys, which also works while the pointer rests in the letterbox beside the canvas. */
export function renderOptions(settings, debug = false) {
  const value = sanitizeSettings(settings);
  const preset = QUALITY_PRESETS[value.quality];
  const performance = value.quality === 'performance';
  const debugFontSize = debug ? 8 : 0;
  return [
    `Resolution = ${preset.width} ${preset.height}`,
    `StaticGameLOD = ${performance ? 'Low' : 'Medium'}`,
    'UseShadowVolumes = no',
    `UseShadowDecals = ${performance ? 'no' : 'yes'}`,
    `UseAlternateMouse = ${value.rightClickOrders ? 'yes' : 'no'}`,
    `ScrollFactor = ${20 + value.cameraSpeed}`,
    'ScreenEdgeScrollEnabledInWindowedApp = no',
    `LockCameraRotation = ${value.cameraRotation ? 'no' : 'yes'}`,
    `CameraKeysWASD = ${value.cameraKeys === 'wasd' ? 'yes' : 'no'}`,
    `WheelZoomFactor = ${value.zoomSpeed * 100}`,
    `RenderFpsFontSize = ${debugFontSize}`,
    `SystemTimeFontSize = ${debugFontSize}`,
    `GameTimeFontSize = ${debugFontSize}`,
    '',
  ].join('\n');
}

export function emptyProgress() {
  return { version: 1, missions: {} };
}

const GUIDANCE_TIPS = [
  ['builders', 'builder', 'Keep a builder in the field', controls =>
    `Select headquarters and train a builder. ${controls.bindings.VIEW_COMMAND_CENTER} returns your camera home.`],
  ['incomeBuildings', 'income', 'Secure your income', () =>
    'Build an Exchange or Racket beside a supply cache, then train a Porter or Scavenger there. '
    + 'Replace a lost hub to keep reinforcements funded.'],
  ['productionBuildings', 'production', 'Build your fighting force', () =>
    'Train infantry at headquarters. Build a Vehicle Plant or Chop Shop for armor. '
    + 'Hover a locked order to see its prerequisites.'],
  ['', 'advance', 'Scout. Support. Advance.', () =>
    'Combine anti-infantry and anti-armor units. Use Attack Move when advancing, '
    + 'and retain a reserve to protect your headquarters.'],
];
const BUILDER_LOST_TEXT = 'Your builder was lost. Train a Fabricator at headquarters, '
  + 'or wait for one already queued, then resume construction.';

/** Native objective stages remain authoritative, including checkpoint restores. */
export function fieldGuidance(mission, state, controls = DEFAULT_SETTINGS) {
  const objectives = mission?.objectives?.filter(objective => !objective.optional) || [];
  const orderText = text => (controls.rightClickOrders === false
    ? text.replace(/Right-click open ground/gi, 'Left-click open ground')
      .replace(/with a right click/gi, 'with a left click')
    : text);
  if (objectives.length) {
    const stage = bounded(state.objectiveStage, 0, objectives.length - 1, 0);
    const objective = objectives[stage];
    const checklist = (objective.requirements || []).map(requirement => {
      const count = bounded(state.trainingCounts?.[requirement.template], 0, requirement.count, 0);
      return { ...requirement, current: count, complete: count >= requirement.count };
    });
    const missing = checklist.find(item => !item.complete);
    const needsReplacementBuilder = mission.category === 'training'
      && missing?.requiresBuilder === true && state.builders === 0;
    const body = needsReplacementBuilder ? BUILDER_LOST_TEXT : orderText(missing?.hint || objective.hint || '');
    let note = '';
    if (checklist.length) {
      note = missing
        ? 'Completed units and structures count. Steps advance automatically.'
        : 'Requirements met. Moving to the next step…';
    }
    return {
      id: `${mission.id}:${stage}`,
      stage,
      total: objectives.length,
      title: objective.label,
      body,
      overview: orderText(objective.hint || ''),
      checklist,
      note,
    };
  }
  for (const [field, id, title, body] of GUIDANCE_TIPS) {
    if (field && state[field]) continue;
    return { id, title, body: body(controls), checklist: [] };
  }
  return undefined;
}

export function beginsNewBattle(previous, next) {
  if (!next.inGame) return false;
  if (!previous.inGame || mapLeaf(previous.map) !== mapLeaf(next.map)) return true;
  return Number.isFinite(next.frame) && Number.isFinite(previous.frame) && next.frame < previous.frame;
}

/** Upper bounds for stored mission statistics; sanitizing, recording and import validation share them. */
const RESULT_LIMITS = Object.freeze({ attempts: 1000000, wins: 1000000, bestSeconds: 86400, bestDifficulty: 2 });
const validMissionId = id => typeof id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(id)
  && !['__proto__', 'constructor', 'prototype'].includes(id);
const emptyMissionRecord = () => ({ attempts: 0, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' });
const ownMission = (missions, id) => (Object.hasOwn(missions, id) ? missions[id] : undefined);
function normalizeCompletionDate(value) {
  if (typeof value !== 'string') return '';
  const match = /^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,3}))?Z$/.exec(value);
  if (!match) return '';
  const canonical = `${match[1]}.${(match[2] || '').padEnd(3, '0')}Z`;
  const valid = Number.isFinite(Date.parse(canonical)) && new Date(canonical).toISOString() === canonical;
  return valid ? canonical : '';
}

function mergeMissionStats(old = emptyMissionRecord(), next = emptyMissionRecord()) {
  const times = [old.bestSeconds, next.bestSeconds].filter(seconds => seconds > 0);
  return {
    attempts: Math.max(old.attempts, next.attempts),
    wins: Math.max(old.wins, next.wins),
    bestSeconds: times.length ? Math.min(...times) : 0,
    bestDifficulty: Math.max(old.bestDifficulty, next.bestDifficulty),
    completedAt: old.completedAt > next.completedAt ? old.completedAt : next.completedAt,
  };
}

export function sanitizeProgress(value) {
  const out = emptyProgress();
  if (!record(value) || value.version !== 1 || !record(value.missions)) return out;
  for (const id of Object.keys(value.missions).sort()) {
    const entry = value.missions[id];
    if (!validMissionId(id) || !record(entry)) continue;
    const wins = bounded(entry.wins, 0, RESULT_LIMITS.wins, 0);
    out.missions[id] = {
      attempts: Math.max(wins, bounded(entry.attempts, 0, RESULT_LIMITS.attempts, 0)),
      wins,
      bestSeconds: wins ? bounded(entry.bestSeconds, 0, RESULT_LIMITS.bestSeconds, 0) : 0,
      bestDifficulty: wins ? bounded(entry.bestDifficulty, 0, RESULT_LIMITS.bestDifficulty, 0) : 0,
      completedAt: wins ? normalizeCompletionDate(entry.completedAt) : '',
    };
  }
  return out;
}

/** Combine local records without counting the same result twice. */
export function mergeProgressRecords(...values) {
  const out = emptyProgress();
  for (const value of values) {
    for (const [id, next] of Object.entries(sanitizeProgress(value).missions)) {
      out.missions[id] = mergeMissionStats(ownMission(out.missions, id), next);
    }
  }
  return sanitizeProgress(out);
}

/** Fold known legacy map keys into mission IDs, preserving unrelated records. */
export function canonicalizeProgress(progress, missions) {
  const out = sanitizeProgress(progress);
  for (const mission of Array.isArray(missions) ? missions : []) {
    if (!validMissionId(mission?.id) || !validMissionId(mission?.map) || mission.id === mission.map) continue;
    const alias = ownMission(out.missions, mission.map);
    if (!alias) continue;
    out.missions[mission.id] = mergeMissionStats(ownMission(out.missions, mission.id), alias);
    delete out.missions[mission.map];
  }
  return sanitizeProgress(out);
}

export function recordResult(progress, result, timestamp = new Date().toISOString()) {
  const out = sanitizeProgress(progress);
  const id = result.operationId || result.map;
  if (!validMissionId(id)) return out;
  const old = ownMission(out.missions, id) || emptyMissionRecord();
  const seconds = bounded(result.seconds ?? result.stats?.seconds, 0, RESULT_LIMITS.bestSeconds, 0);
  const won = result.won === true;
  let bestSeconds = old.bestSeconds;
  if (won && seconds > 0) bestSeconds = old.bestSeconds > 0 ? Math.min(old.bestSeconds, seconds) : seconds;
  out.missions[id] = {
    ...old,
    attempts: Math.min(RESULT_LIMITS.attempts, old.attempts + 1),
    wins: Math.min(RESULT_LIMITS.wins, old.wins + (won ? 1 : 0)),
    bestSeconds,
    bestDifficulty: won
      ? Math.max(old.bestDifficulty, bounded(result.difficulty, 0, RESULT_LIMITS.bestDifficulty, 0))
      : old.bestDifficulty,
    completedAt: won ? normalizeCompletionDate(timestamp) || old.completedAt : old.completedAt,
  };
  return out;
}

export function missionRecord(progress, mission) {
  const clean = sanitizeProgress(progress);
  const byId = validMissionId(mission?.id) ? ownMission(clean.missions, mission.id) : undefined;
  const byMap = validMissionId(mission?.map) ? ownMission(clean.missions, mission.map) : undefined;
  return mergeMissionStats(byId, byMap);
}

export const OPERATION_RECORD_MAX_BYTES = 65536;
export const OPERATION_RECORD_MAX_LABEL = `${OPERATION_RECORD_MAX_BYTES / 1024} KiB`;
const RECORD_FORMAT = 'war-powers-operation-record';
const MAX_RECORD_MISSIONS = 128;
const RESULT_FIELDS = ['attempts', 'wins', 'bestSeconds', 'bestDifficulty', 'completedAt'];
const plainObject = value => record(value) && [Object.prototype, null].includes(Object.getPrototypeOf(value));

function requireRecordFields(value, fields, label) {
  if (!plainObject(value)) throw new Error(`${label} must be an object.`);
  if (Object.keys(value).length !== fields.length || fields.some(key => !Object.hasOwn(value, key))) {
    throw new Error(`${label} has unexpected or missing fields.`);
  }
}

function validateOperationProgress(value) {
  requireRecordFields(value, ['version', 'missions'], 'Operation progress');
  if (value.version !== 1) throw new Error('Unsupported operation progress version.');
  if (!plainObject(value.missions)) throw new Error('Operation missions must be an object.');
  const ids = Object.keys(value.missions).sort();
  if (ids.length > MAX_RECORD_MISSIONS) {
    throw new Error(`Operation record contains too many missions (maximum ${MAX_RECORD_MISSIONS}).`);
  }
  const out = emptyProgress();
  for (const id of ids) {
    if (!validMissionId(id)) throw new Error('Operation record contains an invalid mission identifier.');
    const entry = value.missions[id];
    requireRecordFields(entry, RESULT_FIELDS, `Mission ${id}`);
    for (const [field, limit] of Object.entries(RESULT_LIMITS)) {
      if (!Number.isInteger(entry[field]) || entry[field] < 0 || entry[field] > limit) {
        throw new Error(`Mission ${id}: ${field} must be a whole number from 0 to ${limit}.`);
      }
    }
    if (entry.wins > entry.attempts) throw new Error(`Mission ${id}: wins cannot exceed attempts.`);
    if (typeof entry.completedAt !== 'string' || normalizeCompletionDate(entry.completedAt) !== entry.completedAt) {
      throw new Error(`Mission ${id}: completion date must be an ISO UTC timestamp or empty.`);
    }
    if (!entry.wins && (entry.bestSeconds || entry.bestDifficulty || entry.completedAt)) {
      throw new Error(`Mission ${id}: winning statistics require a recorded win.`);
    }
    out.missions[id] = { ...entry };
  }
  return out;
}

const recordTooLarge = () => new Error(`Operation record is too large (maximum ${OPERATION_RECORD_MAX_LABEL}).`);

/** A bounded, account-free backup of results only; no settings or saved game. */
export function serializeOperationRecord(progress) {
  const payload = { format: RECORD_FORMAT, version: 1, progress: validateOperationProgress(progress) };
  const text = JSON.stringify(payload, null, 2);
  if (new TextEncoder().encode(text).byteLength > OPERATION_RECORD_MAX_BYTES) throw recordTooLarge();
  return text;
}

/** Validate first, then return a non-destructive, idempotent merge. */
export function restoreOperationRecord(currentProgress, text) {
  if (typeof text !== 'string') throw new Error('Choose a JSON operation-record file.');
  if (text.length > OPERATION_RECORD_MAX_BYTES) throw recordTooLarge();
  if (new TextEncoder().encode(text).byteLength > OPERATION_RECORD_MAX_BYTES) throw recordTooLarge();
  let backup;
  try {
    backup = JSON.parse(text);
  } catch {
    throw new Error('Operation record is not valid JSON.');
  }
  requireRecordFields(backup, ['format', 'version', 'progress'], 'Operation record');
  if (backup.format !== RECORD_FORMAT) throw new Error('This file is not a War Powers operation record.');
  if (backup.version !== 1) throw new Error('Unsupported operation-record version.');
  const incoming = validateOperationProgress(backup.progress);
  return validateOperationProgress(mergeProgressRecords(currentProgress, incoming));
}

export function formatTime(seconds) {
  const n = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
}

export function mapLeaf(path) {
  const leaf = String(path || '').replace(/\\/g, '/').split('/').filter(Boolean).pop();
  return leaf?.replace(/\.map$/i, '') || '';
}
