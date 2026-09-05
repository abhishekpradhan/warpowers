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
export function sanitizeProgress(value) {
  const out = emptyProgress();
  if (!record(value) || value.version !== 1 || !record(value.missions)) return out;
  for (const [id, entry] of Object.entries(value.missions)) {
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(id) || ['__proto__', 'constructor', 'prototype'].includes(id) || !record(entry)) continue;
    out.missions[id] = {
      attempts: bounded(entry.attempts, 0, 1000000, 0), wins: bounded(entry.wins, 0, 1000000, 0),
      bestSeconds: bounded(entry.bestSeconds, 0, 86400, 0),
      bestDifficulty: bounded(entry.bestDifficulty, 0, 2, 0),
      completedAt: typeof entry.completedAt === 'string' && /^\d{4}-\d\d-\d\dT/.test(entry.completedAt)
        ? entry.completedAt.slice(0, 32) : '',
    };
  }
  return out;
}

export function recordResult(progress, result, timestamp = new Date().toISOString()) {
  const out = sanitizeProgress(progress);
  const id = result.operationId || result.map;
  if (typeof id !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(id) || ['__proto__', 'constructor', 'prototype'].includes(id)) return out;
  const old = out.missions[id] || { attempts: 0, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' };
  const seconds = bounded(result.seconds ?? result.stats?.seconds, 0, 86400, 0);
  const won = result.won === true;
  out.missions[id] = {
    ...old, attempts: Math.min(1000000, old.attempts + 1), wins: Math.min(1000000, old.wins + (won ? 1 : 0)),
    bestSeconds: won && seconds > 0 ? (old.bestSeconds > 0 ? Math.min(old.bestSeconds, seconds) : seconds) : old.bestSeconds,
    bestDifficulty: won ? Math.max(old.bestDifficulty, bounded(result.difficulty, 0, 2, 0)) : old.bestDifficulty,
    completedAt: won ? timestamp : old.completedAt,
  };
  return out;
}

export function missionRecord(progress, mission) {
  return progress.missions[mission.id] || progress.missions[mission.map] || { attempts: 0, wins: 0, bestSeconds: 0 };
}
export function formatTime(seconds) {
  const n = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
}
export function mapLeaf(path) { return String(path || '').replace(/\\/g, '/').split('/').filter(Boolean).pop()?.replace(/\.map$/i, '') || ''; }
