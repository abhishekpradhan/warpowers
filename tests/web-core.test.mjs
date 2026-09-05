import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sanitizeSettings, readSettings, applyBindings, renderOptions, recordResult, sanitizeProgress, formatTime, mapLeaf } from '../web/core.js';

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
  assert.equal(sanitizeSettings({ bindings: { ...bindings, SCATTER: 'J' } }).bindings.STOP, 'S');
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
