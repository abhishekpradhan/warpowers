// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sanitizeSettings, readSettings, applyBindings, renderOptions, recordResult, sanitizeProgress, emptyProgress,
  serializeOperationRecord, restoreOperationRecord, OPERATION_RECORD_MAX_BYTES, OPERATION_RECORD_MAX_LABEL,
  mergeProgressRecords, canonicalizeProgress, missionRecord, formatTime, mapLeaf,
  QUALITY_PRESETS, SETTING_RANGES, DEFAULT_SETTINGS, BINDINGS, BINDING_KEYS } from '../web/core.js';

test('blocked or damaged storage never prevents a game boot', () => {
  assert.equal(readSettings({ getItem() { throw new Error('blocked'); } }).master, 80);
  assert.equal(readSettings({ getItem() { return '{broken'; } }).quality, 'balanced');
  assert.equal(sanitizeSettings({ master: NaN, music: 400, effects: -10, quality: '__proto__' }).master, 80);
  assert.equal(sanitizeSettings({ music: 400 }).music, 100);
  assert.equal(sanitizeSettings({ effects: -10 }).effects, 0);
});
test('key remapping changes only the requested single-key commands', () => {
  const source = readFileSync(new URL('../data/Data/INI/CommandMap.ini', import.meta.url), 'utf8');
  const bindings = { ...sanitizeSettings({}).bindings, STOP: 'J' };
  const result = applyBindings(source, bindings);
  assert.match(result, /CommandMap STOP\s+Key = KEY_J/);
  assert.match(result, /CommandMap CREATE_TEAM1\s+Key = KEY_1/);
  assert.match(result, /CommandMap OPTIONS\s+Key = KEY_ESC/);
});
test('a damaged or conflicting stored binding falls back alone; other custom keys survive', () => {
  const defaults = sanitizeSettings({}).bindings;
  const conflicting = sanitizeSettings({ bindings: { ...defaults, STOP: 'J', SCATTER: 'J' } }).bindings;
  assert.equal(conflicting.STOP, 'J');
  assert.equal(conflicting.SCATTER, 'X', 'the later duplicate returns to its default');
  const damaged = sanitizeSettings({ bindings: { STOP: 'J', SCATTER: 'F1', VIEW_COMMAND_CENTER: 'Q', TOGGLE_PAUSE: 7 } }).bindings;
  assert.equal(damaged.STOP, 'J');
  assert.equal(damaged.SCATTER, 'X');
  assert.equal(damaged.VIEW_COMMAND_CENTER, 'Q');
  assert.equal(damaged.TOGGLE_PAUSE, 'P');
  assert.equal(damaged.SELECT_ALL, 'B', 'a default taken by a custom key moves to the first free key');
  assert.deepEqual(Object.keys(damaged), Object.keys(BINDINGS));
  assert.equal(new Set(Object.values(damaged)).size, Object.keys(BINDINGS).length, 'bindings stay unique');
  assert.ok(Object.values(damaged).every(key => BINDING_KEYS.includes(key)));
  assert.deepEqual(sanitizeSettings({ bindings: [] }).bindings, defaults);
});
test('shared preset and range tables drive settings, options and their bounds', () => {
  assert.deepEqual(Object.keys(QUALITY_PRESETS), ['performance', 'balanced', 'high']);
  assert.match(renderOptions({ quality: 'performance' }), /Resolution = 1280 720\nStaticGameLOD = Low/);
  assert.equal(sanitizeSettings({ quality: 'ultra' }).quality, DEFAULT_SETTINGS.quality);
  for (const [key, [min, max]] of Object.entries(SETTING_RANGES)) {
    assert.ok(DEFAULT_SETTINGS[key] >= min && DEFAULT_SETTINGS[key] <= max, key);
    assert.equal(sanitizeSettings({ [key]: max + 50 })[key], max, key);
    assert.equal(sanitizeSettings({ [key]: 'x' })[key], DEFAULT_SETTINGS[key], key);
  }
  assert.equal(OPERATION_RECORD_MAX_LABEL, '64 KiB');
  assert.throws(() => restoreOperationRecord(emptyProgress(), ' '.repeat(OPERATION_RECORD_MAX_BYTES + 1)), /64 KiB/);
});
test('engine options use bounded supported values', () => {
  assert.match(renderOptions({ quality: 'high', cameraSpeed: 999 }), /Resolution = 1920 1080/);
  assert.match(renderOptions({ cameraSpeed: 999 }), /ScrollFactor = 120/);
  assert.match(renderOptions({ rightClickOrders: true }), /UseAlternateMouse = yes/);
  assert.doesNotMatch(renderOptions({ quality: 'high\nMalicious = yes' }), /Malicious/);
});
test('only explicit victories complete missions; retries preserve best result', () => {
  let progress = recordResult(null, { operationId: 'corridor', won: false, seconds: 20 });
  assert.equal(progress.missions.corridor.wins, 0);
  progress = recordResult(progress, { operationId: 'corridor', won: true, seconds: 300, difficulty: 1 });
  progress = recordResult(progress, { operationId: 'corridor', won: true, seconds: 400, difficulty: 2 });
  assert.equal(progress.missions.corridor.attempts, 3);
  assert.equal(progress.missions.corridor.bestSeconds, 300);
  assert.equal(progress.missions.corridor.bestDifficulty, 2);
  assert.equal(recordResult(progress, { operationId: 'corridor', won: 'true' }).missions.corridor.wins, 2);
});
test('progress rejects invalid versions and unsafe identifiers', () => {
  assert.deepEqual(sanitizeProgress({ version: 7, missions: {} }).missions, {});
  assert.deepEqual(recordResult(null, { map: '__proto__', won: true }).missions, {});
  assert.deepEqual(sanitizeProgress(JSON.parse('{"version":1,"missions":{"__proto__":{"wins":5}}}')).missions, {});
});
test('time and map normalization support engine paths', () => {
  assert.equal(formatTime(125), '2:05'); assert.equal(formatTime(-9), '0:00');
  assert.equal(mapLeaf('Maps\\WPOp01\\WPOp01.map'), 'WPOp01');
});

const result = (overrides = {}) => ({ attempts: 3, wins: 1, bestSeconds: 300, bestDifficulty: 1,
  completedAt: '2026-09-05T12:00:00.000Z', ...overrides });
const progressWith = missions => ({ version: 1, missions });
const backupText = mutate => {
  const backup = JSON.parse(serializeOperationRecord(progressWith({ op01: result() })));
  mutate(backup);
  return JSON.stringify(backup);
};

test('operation records round-trip results only and repeated restore is idempotent', () => {
  const progress = progressWith({ op01: result(), op02: result({ attempts: 2, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' }) });
  const text = serializeOperationRecord(progress);
  const parsed = JSON.parse(text);
  assert.equal(parsed.format, 'war-powers-operation-record');
  assert.deepEqual(Object.keys(parsed).sort(), ['format', 'progress', 'version']);
  const restored = restoreOperationRecord(emptyProgress(), text);
  assert.deepEqual(restored, progress);
  assert.deepEqual(restoreOperationRecord(restored, text), progress);
  assert.deepEqual(restoreOperationRecord(emptyProgress(), serializeOperationRecord(emptyProgress())), emptyProgress());
});

test('record merge preserves both missions and combines better stats without summing attempts or wins', () => {
  const current = progressWith({ op01: result({ attempts: 8, wins: 4, bestDifficulty: 2 }), op02: result() });
  const incoming = progressWith({ op01: result({ attempts: 6, wins: 5, bestSeconds: 240, completedAt: '2026-09-06T12:00:00.000Z' }), op03: result() });
  const before = structuredClone(current);
  const text = serializeOperationRecord(incoming);
  const merged = restoreOperationRecord(current, text);
  assert.deepEqual(merged.missions.op01, result({ attempts: 8, wins: 5, bestSeconds: 240, bestDifficulty: 2, completedAt: '2026-09-06T12:00:00.000Z' }));
  assert.deepEqual(merged.missions.op02, current.missions.op02);
  assert.deepEqual(merged.missions.op03, incoming.missions.op03);
  assert.deepEqual(restoreOperationRecord(merged, text), merged);
  assert.deepEqual(restoreOperationRecord(incoming, serializeOperationRecord(current)), merged);
  merged.missions.op02.wins = 0;
  assert.deepEqual(current, before, 'returned entries must not alias existing progress');
});

test('unknown winning time and losses never replace a measured winning time', () => {
  const current = progressWith({ op01: result() });
  const unknownTime = progressWith({ op01: result({ bestSeconds: 0 }) });
  assert.equal(restoreOperationRecord(current, serializeOperationRecord(unknownTime)).missions.op01.bestSeconds, 300);
  const losses = progressWith({ op01: result({ attempts: 9, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' }) });
  assert.deepEqual(restoreOperationRecord(current, serializeOperationRecord(losses)).missions.op01, result({ attempts: 9 }));
});

test('malformed or unsupported backups fail without overwriting current records', () => {
  const current = progressWith({ op01: result() });
  const before = structuredClone(current);
  const cases = [
    ['{broken', /valid JSON/], ['null', /must be an object/], ['[]', /must be an object/],
    [backupText(b => { b.format = 'another-game'; }), /not a War Powers/],
    [backupText(b => { b.version = 2; }), /Unsupported operation-record version/],
    [backupText(b => { b.progress.version = 2; }), /Unsupported operation progress version/],
    [backupText(b => { delete b.progress.missions.op01.wins; }), /missing fields/],
    [backupText(b => { b.settings = {}; }), /unexpected/],
    [backupText(b => { b.progress.checkpoint = 'payload'; }), /unexpected/],
    [backupText(b => { b.progress.missions.op01.extra = '<script>alert(1)</script>'; }), /unexpected/],
  ];
  for (const [text, message] of cases) {
    assert.throws(() => restoreOperationRecord(current, text), message);
    assert.deepEqual(current, before);
  }
});

test('record validation rejects unsafe identifiers and inconsistent or unbounded statistics', () => {
  for (const id of ['__proto__', 'constructor', 'prototype', '<script>', 'x'.repeat(65)]) {
    const text = backupText(b => { b.progress.missions = Object.fromEntries([[id, result()]]); });
    assert.throws(() => restoreOperationRecord(emptyProgress(), text), /invalid mission identifier/);
  }
  for (const patch of [
    { attempts: -1 }, { attempts: 1000001 }, { wins: 4 }, { wins: 1.5 }, { wins: '1' },
    { bestSeconds: Infinity }, { bestSeconds: -1 }, { bestSeconds: 86401 }, { bestDifficulty: 3 },
    { wins: 0 }, { completedAt: '2026-02-30T12:00:00.000Z' }, { completedAt: '<script>' },
  ]) {
    const text = backupText(b => { Object.assign(b.progress.missions.op01, patch); });
    assert.throws(() => restoreOperationRecord(emptyProgress(), text), /Mission op01:/);
  }
  assert.equal(Object.prototype.wins, undefined);
});

test('file and mission bounds reject oversized imports including the merged union', () => {
  assert.throws(() => restoreOperationRecord(emptyProgress(), ' '.repeat(OPERATION_RECORD_MAX_BYTES + 1)), /too large/);
  assert.throws(() => restoreOperationRecord(emptyProgress(), 'é'.repeat(OPERATION_RECORD_MAX_BYTES / 2 + 1)), /too large/);
  const many = count => progressWith(Object.fromEntries(Array.from({ length: count }, (_, n) => [`mission${n}`, result()])));
  assert.throws(() => serializeOperationRecord(many(129)), /too many missions/);
  const oversized = backupText(b => { b.progress = many(129); });
  assert.throws(() => restoreOperationRecord(emptyProgress(), oversized), /too many missions/);
  const current = many(128), before = structuredClone(current);
  assert.throws(() => restoreOperationRecord(current, serializeOperationRecord(progressWith({ extra: result() }))), /too many missions/);
  assert.deepEqual(current, before);
});

test('local merging preserves independent tab records and best stats in stable order', () => {
  const tabA = progressWith({ op03: result(), op01: result({ attempts: 7, wins: 3, bestDifficulty: 2 }) });
  const tabB = progressWith({ op02: result(), op01: result({ attempts: 5, wins: 4, bestSeconds: 220, completedAt: '2026-09-06T12:00:00.000Z' }) });
  const beforeA = structuredClone(tabA), beforeB = structuredClone(tabB);
  const merged = mergeProgressRecords(tabA, null, tabB);
  assert.deepEqual(Object.keys(merged.missions), ['op01', 'op02', 'op03']);
  assert.deepEqual(merged.missions.op01, result({ attempts: 7, wins: 4, bestSeconds: 220, bestDifficulty: 2, completedAt: '2026-09-06T12:00:00.000Z' }));
  assert.equal(JSON.stringify(merged), JSON.stringify(mergeProgressRecords(tabB, tabA)));
  assert.deepEqual(mergeProgressRecords(merged, tabA, tabB), merged);
  assert.deepEqual(mergeProgressRecords(), emptyProgress());
  assert.deepEqual(tabA, beforeA); assert.deepEqual(tabB, beforeB);
});

test('legacy map win survives canonical loss and repeated canonicalization', () => {
  const mission = { id: 'op01', map: 'WPOp01' };
  const legacy = progressWith({ WPOp01: result({ bestSeconds: 190, bestDifficulty: 2 }),
    op01: result({ attempts: 5, wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' }),
    unknown_map: result() });
  const before = structuredClone(legacy);
  const expected = result({ attempts: 5, bestSeconds: 190, bestDifficulty: 2 });
  assert.deepEqual(missionRecord(legacy, mission), expected);
  const canonical = canonicalizeProgress(legacy, [mission]);
  assert.deepEqual(canonical.missions.op01, expected);
  assert.equal(Object.hasOwn(canonical.missions, 'WPOp01'), false);
  assert.deepEqual(canonical.missions.unknown_map, legacy.missions.unknown_map);
  assert.deepEqual(canonicalizeProgress(canonical, [mission]), canonical);
  assert.deepEqual(missionRecord(recordResult(canonical, { operationId: 'op01', won: false }), mission), { ...expected, attempts: 6 });
  assert.deepEqual(legacy, before);
});

test('canonical aliases share the same better-stat merge as imported records', () => {
  const mission = { id: 'op01', map: 'WPOp01' };
  const canonical = result({ attempts: 9, wins: 5, bestSeconds: 280, bestDifficulty: 2 });
  const alias = result({ attempts: 6, wins: 4, bestSeconds: 230, completedAt: '2026-09-06T12:00:00.000Z' });
  const normalized = canonicalizeProgress(progressWith({ op01: canonical, WPOp01: alias }), [mission]);
  const imported = restoreOperationRecord(progressWith({ op01: canonical }), serializeOperationRecord(progressWith({ op01: alias })));
  assert.deepEqual(normalized, imported);
  assert.deepEqual(canonicalizeProgress(progressWith({ unknown: result() }), [{ id: '__proto__', map: 'unknown' }]), progressWith({ unknown: result() }));
});

test('damaged local storage is repaired without weakening imported-file validation', () => {
  const local = progressWith({ old: { attempts: 1, wins: 3, bestSeconds: 250, bestDifficulty: 2, completedAt: '2026-02-30T12:00:00.000Z' },
    loss: result({ wins: 0 }), legacy_date: result({ completedAt: '2026-09-05T12:00:00Z' }) });
  const normalized = sanitizeProgress(local);
  assert.deepEqual(normalized.missions.old, result({ attempts: 3, wins: 3, bestSeconds: 250, bestDifficulty: 2, completedAt: '' }));
  assert.deepEqual(normalized.missions.loss, result({ wins: 0, bestSeconds: 0, bestDifficulty: 0, completedAt: '' }));
  assert.equal(normalized.missions.legacy_date.completedAt, '2026-09-05T12:00:00.000Z');
  const text = serializeOperationRecord(progressWith({ op01: result() }));
  const restored = restoreOperationRecord(local, text);
  assert.deepEqual(restored, mergeProgressRecords(normalized, progressWith({ op01: result() })));
  assert.throws(() => restoreOperationRecord(emptyProgress(), backupText(b => { b.progress = local; })), /Mission (?:legacy_date|loss|old):/);
  assert.deepEqual(restoreOperationRecord({ version: 5 }, text), progressWith({ op01: result() }));
});

test('unknown valid mission IDs never read inherited object properties', () => {
  const progress = progressWith({ toString: result(), valueOf: result() });
  assert.deepEqual(mergeProgressRecords(emptyProgress(), progress), progress);
  assert.deepEqual(canonicalizeProgress(progress, [{ id: 'op01', map: 'WPOp01' }]), progress);
  assert.deepEqual(restoreOperationRecord(emptyProgress(), serializeOperationRecord(progress)), progress);
  assert.equal(recordResult(emptyProgress(), { operationId: 'toString', won: true }).missions.toString.wins, 1);
  assert.equal(missionRecord(emptyProgress(), { id: 'toString', map: 'valueOf' }).wins, 0);
});
