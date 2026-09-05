import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import * as core from '../web/core.js';

// Execute the actual app and listeners. Only module loading and the network
// bootstrap are replaced; recovery/control logic is never copied into tests.
const source = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');
const bootstrap = "bootGame().catch(error => fail(error.message, 'WP-START'));";
assert.ok(source.endsWith(`${bootstrap}\n`));
const application = source.replace(/^import\s*\{[\s\S]*?\}\s*from '\.\/core\.js';/, '')
  .replace(bootstrap, '');

function appFixture() {
  const elements = new Map(), events = new Map(), timers = [];
  let nativeCalls = 0, storageWrites = 0, focus = '';
  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, {
        hidden: true, open: false, textContent: '', attributes: {},
        classList: { add: name => classes.add(name), remove: name => classes.delete(name),
          toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name) },
        style: { setProperty() {} },
        addEventListener(type, callback) { events.set(`${id}:${type}`, callback); },
        setAttribute(name, value) { this.attributes[name] = value; },
        focus() { focus = id; }, close() { this.open = false; }, showModal() { this.open = true; },
        replaceChildren() {}, append() {}, querySelectorAll() { return []; },
      });
    }
    return elements.get(id);
  }
  const brokenNative = () => { nativeCalls++; throw new Error('native bridge unavailable'); };
  const context = vm.createContext({
    ...core, URLSearchParams, structuredClone,
    window: { localStorage: { getItem() { return null; }, setItem() { storageWrites++; } },
      Module: { _wpSetWebPause: brokenNative, _wpSetAudioLevels: brokenNative,
        _wpSaveGame: brokenNative, _wpLoadGame: brokenNative },
      addEventListener(type, callback) { events.set(`window:${type}`, callback); } },
    document: { getElementById: element, documentElement: element('root'),
      addEventListener(type, callback) { events.set(`document:${type}`, callback); },
      createElement: element },
    navigator: { userAgent: 'test', clipboard: { async writeText() { throw new Error('clipboard denied'); } } },
    location: { search: '', reload() {} }, matchMedia() { return { matches: false }; },
    performance: { now: () => 100 }, console: { log() {} },
    setTimeout(callback) { timers.push(callback); return timers.length; }, clearTimeout() {},
    setInterval() { return 1; }, clearInterval() {},
  });
  vm.runInContext(`${application}\n;globalThis.testApp = {
    fail, closePanel, setPause, applyAudio, saveCheckpoint, loadCheckpoint,
    updateGameState, handleResult, copyDiagnostics, showBriefing, showDebrief,
    prime() {
      runtimeReady = true; build = { id: 'fixture' };
      gameState = { inGame: true, map: 'WPTraining', frame: 300, objectiveStage: 1 };
      panelKind = 'settings'; panel.open = true; pauseReasons.add('panel');
      pendingResult = { won: true }; $('guide').hidden = false; $('missionHud').hidden = false;
    },
    snapshot() { return { failed, runtimeReady, panelKind, pauseCount: pauseReasons.size, pendingResult }; }
  };`, context);
  context.testApp.prime();
  return { app: context.testApp, element, events, timers,
    nativeCalls: () => nativeCalls, storageWrites: () => storageWrites, focus: () => focus };
}

test('native failure renders recovery without re-entering a throwing bridge', () => {
  const fixture = appFixture();
  assert.doesNotThrow(() => fixture.events.get('window:error')({ message: 'Original engine failure' }));
  assert.equal(fixture.nativeCalls(), 0);
  const state = fixture.app.snapshot();
  assert.equal(state.failed, true); assert.equal(state.runtimeReady, false);
  assert.equal(state.pauseCount, 0); assert.equal(state.pendingResult, null);
  assert.equal(fixture.element('panel').open, false);
  assert.equal(fixture.element('boot').hidden, false);
  assert.equal(fixture.element('bootError').hidden, false);
  assert.match(fixture.element('errorCode').textContent, /WP-SCRIPT/);
  assert.equal(fixture.element('guide').hidden, true);
  assert.equal(fixture.element('missionHud').hidden, true);
  assert.equal(fixture.focus(), 'reloadButton');
  const original = fixture.element('errorMessage').textContent;
  fixture.app.fail('Later failure');
  assert.equal(fixture.element('errorMessage').textContent, original);
});

test('late callbacks and diagnostics keep recovery usable after native failure', async () => {
  const fixture = appFixture();
  fixture.app.fail('Engine stopped');
  fixture.app.updateGameState({ inGame: true, map: 'WPTraining', frame: 0 });
  fixture.app.handleResult({ won: true, map: 'WPTraining' });
  fixture.app.showBriefing(); fixture.app.showDebrief();
  fixture.app.applyAudio(); fixture.app.setPause('hidden', true);
  await fixture.app.saveCheckpoint(); fixture.app.loadCheckpoint();
  assert.equal(fixture.timers.length, 0, 'late telemetry must not schedule a pausing briefing');
  assert.equal(fixture.storageWrites(), 0, 'late results must not change the operation record');
  await assert.doesNotReject(() => fixture.app.copyDiagnostics());
  assert.equal(fixture.element('panel').open, true, 'clipboard fallback remains available');
  fixture.app.closePanel();
  assert.equal(fixture.element('panel').open, false);
  assert.equal(fixture.element('guide').hidden, true);
  assert.equal(fixture.element('boot').hidden, false);
  assert.equal(fixture.focus(), 'reloadButton');
  assert.equal(fixture.nativeCalls(), 0);
});
