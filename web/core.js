/** Browser-independent preferences and progress rules. No game state is simulated here. */
export const SETTINGS_KEY = 'wpSettings.v2';
export const PROGRESS_KEY = 'wpProgress.v1';
export const BINDINGS = Object.freeze({
  STOP: ['Stop', 'S'], SCATTER: ['Scatter', 'X'],
  SELECT_MATCHING_UNITS: ['Select matching units', 'E'], SELECT_ALL: ['Select army', 'Q'],
  SELECT_NEXT_IDLE_WORKER: ['Next idle builder', 'I'], VIEW_COMMAND_CENTER: ['View headquarters', 'H'],
  TOGGLE_PAUSE: ['Pause battle', 'P'],
});
export const BINDING_KEYS = Object.freeze('B E H I J K L M N O P Q R S T U V X Y Z'.split(' '));
export const DEFAULT_SETTINGS = Object.freeze({
  version: 2, master: 80, music: 45, effects: 80, voice: 90,
  quality: 'balanced', uiScale: 100, cameraSpeed: 50, rightClickOrders: true,
  reducedMotion: false, highContrast: false, guide: true, pauseWhenHidden: true,
  bindings: Object.fromEntries(Object.entries(BINDINGS).map(([name, entry]) => [name, entry[1]])),
});
const record = value => value && typeof value === 'object' && !Array.isArray(value);
const bounded = (value, min, max, fallback) => typeof value === 'number' && Number.isFinite(value)
  ? Math.min(max, Math.max(min, Math.round(value))) : fallback;

export function sanitizeSettings(value) {
  const data = record(value) ? value : {};
  const out = { ...DEFAULT_SETTINGS, bindings: { ...DEFAULT_SETTINGS.bindings } };
  for (const key of ['master', 'music', 'effects', 'voice', 'cameraSpeed'])
    out[key] = bounded(data[key], 0, 100, out[key]);
  out.uiScale = bounded(data.uiScale, 85, 125, 100);
  if (['performance', 'balanced', 'high'].includes(data.quality)) out.quality = data.quality;
  for (const key of ['rightClickOrders', 'reducedMotion', 'highContrast', 'guide', 'pauseWhenHidden'])
    if (typeof data[key] === 'boolean') out[key] = data[key];
  if (record(data.bindings)) {
    const proposed = Object.fromEntries(Object.keys(BINDINGS).map(key =>
      [key, BINDING_KEYS.includes(data.bindings[key]) ? data.bindings[key] : out.bindings[key]]));
    if (new Set(Object.values(proposed)).size === Object.keys(BINDINGS).length) out.bindings = proposed;
  }
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

export function applyBindings(ini, bindings) {
  const validated = sanitizeSettings({ bindings }).bindings;
  return ini.replace(/(CommandMap\s+(\w+)[^\n]*\n)([\s\S]*?)(^End\s*$)/gm,
    (block, opening, name, body, end) => Object.hasOwn(validated, name)
      ? opening + body.replace(/(\bKey\s*=\s*)KEY_\w+/, `$1KEY_${validated[name]}`) + end : block);
}

export function renderOptions(settings, debug = false) {
  const value = sanitizeSettings(settings);
  const resolution = { performance: '1280 720', balanced: '1600 900', high: '1920 1080' }[value.quality];
  return [
    `Resolution = ${resolution}`, `StaticGameLOD = ${value.quality === 'performance' ? 'Low' : 'Medium'}`,
    'UseShadowVolumes = no', `UseShadowDecals = ${value.quality === 'performance' ? 'no' : 'yes'}`,
    `UseAlternateMouse = ${value.rightClickOrders ? 'yes' : 'no'}`,
    `ScrollFactor = ${20 + value.cameraSpeed}`,
    `RenderFpsFontSize = ${debug ? 8 : 0}`, `SystemTimeFontSize = ${debug ? 8 : 0}`,
    `GameTimeFontSize = ${debug ? 8 : 0}`, '',
  ].join('\n');
}

export function emptyProgress() { return { version: 1, missions: {} }; }
const validMissionId = id => typeof id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(id)
  && !['__proto__', 'constructor', 'prototype'].includes(id);
const emptyMissionRecord = () => ({ attempts: 0, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' });
const ownMission = (missions, id) => Object.hasOwn(missions, id) ? missions[id] : undefined;
function normalizeCompletionDate(value) {
  if (typeof value !== 'string') return '';
  const match = /^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,3}))?Z$/.exec(value);
  if (!match) return '';
  const canonical = `${match[1]}.${(match[2] || '').padEnd(3, '0')}Z`;
  return Number.isFinite(Date.parse(canonical)) && new Date(canonical).toISOString() === canonical ? canonical : '';
}

function mergeMissionStats(old = emptyMissionRecord(), next = emptyMissionRecord()) {
  const times = [old.bestSeconds, next.bestSeconds].filter(seconds => seconds > 0);
  return {
    attempts: Math.max(old.attempts, next.attempts), wins: Math.max(old.wins, next.wins),
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
    const wins = bounded(entry.wins, 0, 1000000, 0);
    out.missions[id] = {
      attempts: Math.max(wins, bounded(entry.attempts, 0, 1000000, 0)), wins,
      bestSeconds: wins ? bounded(entry.bestSeconds, 0, 86400, 0) : 0,
      bestDifficulty: wins ? bounded(entry.bestDifficulty, 0, 2, 0) : 0,
      completedAt: wins ? normalizeCompletionDate(entry.completedAt) : '',
    };
  }
  return out;
}

/** Combine local records without counting the same result twice. */
export function mergeProgressRecords(...values) {
  const out = emptyProgress();
  for (const value of values)
    for (const [id, next] of Object.entries(sanitizeProgress(value).missions))
      out.missions[id] = mergeMissionStats(ownMission(out.missions, id), next);
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
  const seconds = bounded(result.seconds ?? result.stats?.seconds, 0, 86400, 0);
  const won = result.won === true;
  out.missions[id] = {
    ...old, attempts: Math.min(1000000, old.attempts + 1), wins: Math.min(1000000, old.wins + (won ? 1 : 0)),
    bestSeconds: won && seconds > 0 ? (old.bestSeconds > 0 ? Math.min(old.bestSeconds, seconds) : seconds) : old.bestSeconds,
    bestDifficulty: won ? Math.max(old.bestDifficulty, bounded(result.difficulty, 0, 2, 0)) : old.bestDifficulty,
    completedAt: won ? normalizeCompletionDate(timestamp) || old.completedAt : old.completedAt,
  };
  return out;
}

export function missionRecord(progress, mission) {
  const clean = sanitizeProgress(progress);
  return mergeMissionStats(validMissionId(mission?.id) ? ownMission(clean.missions, mission.id) : undefined,
    validMissionId(mission?.map) ? ownMission(clean.missions, mission.map) : undefined);
}

export const OPERATION_RECORD_MAX_BYTES = 65536;
const RECORD_FORMAT = 'war-powers-operation-record';
const MAX_RECORD_MISSIONS = 128;
const resultFields = ['attempts', 'wins', 'bestSeconds', 'bestDifficulty', 'completedAt'];

function requireRecordFields(value, fields, label) {
  if (!record(value) || ![Object.prototype, null].includes(Object.getPrototypeOf(value)))
    throw new Error(`${label} must be an object.`);
  if (Object.keys(value).length !== fields.length || fields.some(key => !Object.hasOwn(value, key)))
    throw new Error(`${label} has unexpected or missing fields.`);
}

function validateOperationProgress(value) {
  requireRecordFields(value, ['version', 'missions'], 'Operation progress');
  if (value.version !== 1) throw new Error('Unsupported operation progress version.');
  if (!record(value.missions) || ![Object.prototype, null].includes(Object.getPrototypeOf(value.missions)))
    throw new Error('Operation missions must be an object.');
  const ids = Object.keys(value.missions).sort();
  if (ids.length > MAX_RECORD_MISSIONS) throw new Error('Operation record contains too many missions (maximum 128).');
  const out = emptyProgress();
  for (const id of ids) {
    if (!validMissionId(id))
      throw new Error('Operation record contains an invalid mission identifier.');
    const entry = value.missions[id];
    requireRecordFields(entry, resultFields, `Mission ${id}`);
    for (const [field, limit] of [['attempts', 1000000], ['wins', 1000000], ['bestSeconds', 86400], ['bestDifficulty', 2]]) {
      if (!Number.isInteger(entry[field]) || entry[field] < 0 || entry[field] > limit)
        throw new Error(`Mission ${id}: ${field} must be a whole number from 0 to ${limit}.`);
    }
    if (entry.wins > entry.attempts) throw new Error(`Mission ${id}: wins cannot exceed attempts.`);
    if (typeof entry.completedAt !== 'string' || normalizeCompletionDate(entry.completedAt) !== entry.completedAt)
      throw new Error(`Mission ${id}: completion date must be an ISO UTC timestamp or empty.`);
    if (!entry.wins && (entry.bestSeconds || entry.bestDifficulty || entry.completedAt))
      throw new Error(`Mission ${id}: winning statistics require a recorded win.`);
    out.missions[id] = { ...entry };
  }
  return out;
}

/** A bounded, account-free backup of results only; no settings or saved game. */
export function serializeOperationRecord(progress) {
  const text = JSON.stringify({ format: RECORD_FORMAT, version: 1, progress: validateOperationProgress(progress) }, null, 2);
  if (new TextEncoder().encode(text).byteLength > OPERATION_RECORD_MAX_BYTES)
    throw new Error('Operation record is too large (maximum 64 KiB).');
  return text;
}

/** Validate first, then return a non-destructive, idempotent merge. */
export function restoreOperationRecord(currentProgress, text) {
  if (typeof text !== 'string') throw new Error('Choose a JSON operation-record file.');
  if (text.length > OPERATION_RECORD_MAX_BYTES || new TextEncoder().encode(text).byteLength > OPERATION_RECORD_MAX_BYTES)
    throw new Error('Operation record is too large (maximum 64 KiB).');
  let backup;
  try { backup = JSON.parse(text); }
  catch { throw new Error('Operation record is not valid JSON.'); }
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
export function mapLeaf(path) { return String(path || '').replace(/\\/g, '/').split('/').filter(Boolean).pop()?.replace(/\.map$/i, '') || ''; }
