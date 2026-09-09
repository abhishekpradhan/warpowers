// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';
import * as core from '../web/core.js';

// Execute the real shell under node. Only module loading and the browser are
// replaced: app.js exposes `globalThis.__wpTest` (and skips its network boot)
// when it runs under node with `__wpTestHarness` set, so recovery, loader and
// control logic are never copied into these tests.
const source = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');
const IMPORT = /^\/\/ SPDX-License-Identifier: MIT\nimport \{[^}]*\} from '\.\/core\.js';\n/;
assert.match(source, IMPORT, 'app.js must start with its SPDX line and one import from ./core.js');
const application = source.replace(IMPORT, '');
const page = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');

function appFixture(search = '', options = {}) {
  const elements = new Map();
  const events = new Map();
  const timers = [];
  const counters = { nativeCalls: 0, storageWrites: 0, reloads: 0 };
  let focus = '';
  let now = 100;
  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, {
        id, hidden: true, open: false, disabled: false, textContent: '', innerHTML: '', value: '', attributes: {},
        classes,
        classList: {
          add: name => classes.add(name),
          remove: name => classes.delete(name),
          toggle: (name, enabled) => (enabled ? classes.add(name) : classes.delete(name)),
          contains: name => classes.has(name),
        },
        style: { setProperty() {} },
        content: { cloneNode: () => ({}) },
        addEventListener(type, callback) { events.set(`${id}:${type}`, callback); },
        setAttribute(name, value) { this.attributes[name] = value; },
        getAttribute(name) { return this.attributes[name]; },
        focus() { focus = id; },
        close() { this.open = false; },
        showModal() { this.open = true; },
        replaceChildren() {}, append() {}, insertAdjacentHTML() {}, querySelectorAll() { return []; },
      });
    }
    return elements.get(id);
  }
  const brokenNative = () => { counters.nativeCalls++; throw new Error('native bridge unavailable'); };
  const document = {
    hidden: false, getElementById: element, documentElement: element('root'), body: element('body'),
    addEventListener(type, callback) { events.set(`document:${type}`, callback); },
    createElement: element,
  };
  const context = vm.createContext({
    ...core, URLSearchParams, structuredClone, TextEncoder, TextDecoder, btoa,
    // `crypto: undefined` models an insecure origin without WebCrypto.
    crypto: Object.hasOwn(options, 'crypto') ? options.crypto : crypto,
    WebAssembly: options.WebAssembly || WebAssembly,
    process, __wpTestHarness: true,
    window: {
      localStorage: { getItem() { return null; }, setItem() { counters.storageWrites++; } },
      Module: options.module || {
        _wpSetWebPause: brokenNative, _wpSetAudioLevels: brokenNative,
        _wpSaveGame: brokenNative, _wpLoadGame: brokenNative,
      },
      FS: options.fs,
      addEventListener(type, callback) { events.set(`window:${type}`, callback); },
    },
    document,
    navigator: { userAgent: 'test', clipboard: { async writeText() { throw new Error('clipboard denied'); } } },
    location: { search, reload() { counters.reloads++; } },
    matchMedia() { return { matches: false }; },
    performance: { now: () => now, mark() {}, measure() { return { duration: 5 }; } },
    console: { log() {}, info() {}, debug() {}, warn() {}, error() {} },
    // Zero-delay UI scheduling is recorded; longer delays run on a virtual clock so retries and toasts settle.
    setTimeout(callback, delay = 0) {
      if (delay > 0) {
        setTimeout(() => { now += delay; callback(); }, 0);
        return -1;
      }
      timers.push(callback);
      return timers.length;
    },
    clearTimeout() {}, setInterval() { return 1; }, clearInterval() {},
    fetch: options.fetch,
  });
  vm.runInContext(application, context);
  const seam = context.__wpTest;
  assert.ok(seam, 'app.js must expose its node test seam');
  return { seam, element, events, timers, counters, document, setNow: value => { now = value; }, focus: () => focus };
}

/** Prime shell state by field name; a renamed field fails here instead of silently doing nothing. */
function prime(fixture, patch) {
  for (const [key, value] of Object.entries(patch)) {
    assert.ok(key in fixture.seam.state, `app.js shell state has no "${key}" field`);
    fixture.seam.state[key] = value;
  }
}
function primeBattle(fixture) {
  prime(fixture, {
    runtimeReady: true, build: { id: 'fixture', compatibility: 'c1' },
    game: { inGame: true, map: 'WPTraining', frame: 300, objectiveStage: 1 },
    panelKind: 'settings', pendingResult: { won: true },
  });
  fixture.seam.state.pauseReasons.add('panel');
  fixture.element('panel').open = true;
  fixture.element('guide').hidden = false;
  fixture.element('missionHud').hidden = false;
}
const trainingMission = {
  id: 'training', map: 'WPTraining', title: 'Field Orientation', category: 'training', objectives: [],
};

test('native failure renders recovery, quiesces the engine once and never re-enters the bridge', () => {
  const fixture = appFixture();
  primeBattle(fixture);
  assert.doesNotThrow(() => fixture.events.get('window:error')({ message: 'Original engine failure' }));
  assert.equal(fixture.counters.nativeCalls, 2, 'fail() tries to pause and mute the engine exactly once each');
  const { state } = fixture.seam;
  assert.equal(state.failed, true);
  assert.equal(state.runtimeReady, false);
  assert.equal(state.pauseReasons.size, 0);
  assert.equal(state.pendingResult, null);
  assert.equal(fixture.element('panel').open, false);
  assert.equal(fixture.element('boot').hidden, false);
  assert.equal(fixture.element('bootError').hidden, false);
  assert.equal(fixture.element('bootExit').hidden, true);
  assert.match(fixture.element('errorCode').textContent, /WP-SCRIPT/);
  assert.equal(fixture.element('guide').hidden, true);
  assert.equal(fixture.element('missionHud').hidden, true);
  assert.equal(fixture.focus(), 'reloadButton');
  const original = fixture.element('errorMessage').textContent;
  fixture.seam.fail('Later failure');
  assert.equal(fixture.element('errorMessage').textContent, original);
  assert.equal(fixture.counters.nativeCalls, 2, 'later failures never call the engine again');
});

test('a failing shell pauses and mutes a working engine before it stops driving it', () => {
  const calls = [];
  const module = {
    _wpSetWebPause: value => { calls.push(['pause', value]); return 1; },
    _wpSetAudioLevels: (...levels) => calls.push(['audio', ...levels]),
  };
  const fixture = appFixture('', { module });
  primeBattle(fixture);
  fixture.seam.fail('Graphics gone', 'WP-GRAPHICS');
  assert.deepEqual(calls, [['pause', 1], ['audio', 0, 0, 0, 0]]);
  fixture.seam.setPause('hidden', true);
  fixture.seam.applyAudio();
  assert.equal(calls.length, 2, 'after failure the bridge is never used again');
});

test('late callbacks and diagnostics keep recovery usable after native failure', async () => {
  const fixture = appFixture();
  primeBattle(fixture);
  fixture.seam.fail('Engine stopped');
  const quiesced = fixture.counters.nativeCalls;
  fixture.seam.updateGameState({ inGame: true, map: 'WPTraining', frame: 0 });
  fixture.seam.handleResult({ won: true, map: 'WPTraining' });
  fixture.seam.showBriefing();
  fixture.seam.showDebrief();
  fixture.seam.applyAudio();
  fixture.seam.setPause('hidden', true);
  await fixture.seam.saveCheckpoint();
  fixture.seam.loadCheckpoint();
  assert.equal(fixture.timers.length, 0, 'late telemetry must not schedule a pausing briefing');
  assert.equal(fixture.counters.storageWrites, 0, 'late results must not change the operation record');
  await assert.doesNotReject(() => fixture.seam.copyDiagnostics());
  assert.equal(fixture.element('panel').open, true, 'clipboard fallback remains available');
  fixture.seam.closePanel();
  assert.equal(fixture.element('panel').open, false);
  assert.equal(fixture.element('guide').hidden, true);
  assert.equal(fixture.element('boot').hidden, false);
  assert.equal(fixture.focus(), 'reloadButton');
  assert.equal(fixture.counters.nativeCalls, quiesced);
});

test('harness switches change behaviour only with ?debug=1, and only Retry bypasses the web debrief', () => {
  const cases = [
    ['', true, 1, false],
    ['?autotest=retry', true, 1, false],
    ['?autotest=defeat&debug=1', true, 0, true],
    ['?debug=1&autotest=retry', false, 0, true],
  ];
  for (const [query, expectedDebrief, expectedWrites, expectedReport] of cases) {
    const fixture = appFixture(query);
    primeBattle(fixture);
    prime(fixture, { operations: { missions: [trainingMission] }, pendingResult: null, panelKind: '' });
    fixture.element('panel').open = false;
    fixture.seam.state.pauseReasons.clear();
    fixture.seam.handleResult({
      operationId: 'training', map: 'WPTraining', won: false, stats: { durationSeconds: 180 },
    });
    assert.equal(!!fixture.seam.state.pendingResult, expectedDebrief, query);
    assert.equal(fixture.counters.storageWrites, expectedWrites, query);
    assert.equal(fixture.counters.nativeCalls, 0, 'result handling waits for the native score transition');
    assert.equal(/MATCH_RESULT/.test(fixture.element('testReport').textContent), expectedReport, query);
  }
});

test('engine environment and extra arguments are forwarded only in debug sessions', () => {
  const switches = 'autotest=retry&retryruns=2&retryframes=900&review=1&scenedump=5&aitrace=1&doztrace=1'
    + '&surfacetrace=1&args=-quickstart,-x';
  // Values come from the vm realm; copy them so deepEqual compares content, not prototypes.
  const env = fixture => ({ ...fixture.seam.diagnostics.engineEnv() });
  const args = fixture => [...fixture.seam.engineArguments([])];
  const plain = appFixture(`?${switches}`);
  assert.deepEqual(env(plain), {});
  assert.equal(plain.seam.diagnostics.active, false);
  assert.equal(plain.seam.diagnostics.retry, false);
  assert.deepEqual(args(plain), ['-win', '-noshellmap']);
  const debug = appFixture(`?debug=1&${switches}`);
  assert.deepEqual(env(debug), {
    IG_TRACE: '1', WP_AUTOTEST: 'retry', WP_REVIEW_SCENE: '1', WP_SCENE_DUMP: '5', WP_AI_TRACE: '1',
    WP_DOZER_TRACE: '1', WP_RETRY_RUNS: '2', WP_RETRY_FRAMES: '900', WP_SURFACE_TRACE: '1',
  });
  assert.equal(debug.seam.diagnostics.active, true);
  assert.equal(debug.seam.diagnostics.retry, true);
  assert.deepEqual(args(debug), ['-win', '-noshellmap', '-quickstart', '-x']);
  assert.deepEqual(env(appFixture('?debug=1&autotest=defeat&retryruns=2')), { IG_TRACE: '1', WP_AUTOTEST: 'defeat' });
  assert.deepEqual(env(appFixture('?debug=1')), { IG_TRACE: '1' });
});

test('a restored checkpoint returns to the battle without reopening the briefing', () => {
  const metadata = { compatibility: 'c1', title: 'Field Orientation', savedAt: '2026-09-05T12:00:00.000Z' };
  const fs = { analyzePath: () => ({ exists: true }), readFile: () => JSON.stringify(metadata) };
  let loads = 0;
  const module = { _wpLoadGame: () => { loads++; return 0; }, _wpSetWebPause: () => 0, _wpSetAudioLevels() {} };
  const fixture = appFixture('', { fs, module });
  prime(fixture, {
    runtimeReady: true, build: { id: 'b', compatibility: 'c1' },
    operations: { missions: [trainingMission] }, game: { inGame: false, map: '' },
  });
  fixture.seam.loadCheckpoint();
  assert.equal(loads, 1);
  assert.match(fixture.element('toast').textContent, /Checkpoint restored/);
  fixture.seam.updateGameState({ inGame: true, map: 'WPTraining', frame: 4000, objectiveStage: 2 });
  assert.equal(fixture.timers.length, 0, 'no briefing is scheduled after a restore');
  assert.equal(fixture.element('missionTitle').textContent, 'Field Orientation');
  assert.equal(fixture.seam.state.restoringCheckpoint, false);
  // Back in the menu, a fresh start of the same mission opens its briefing again.
  fixture.seam.updateGameState({ inGame: false, map: '' });
  fixture.seam.updateGameState({ inGame: true, map: 'WPTraining', frame: 0, objectiveStage: 0 });
  assert.equal(fixture.timers.length, 1, 'a fresh mission schedules its briefing');
  fixture.timers[0]();
  assert.equal(fixture.seam.state.panelKind, 'briefing');
  assert.equal(fixture.element('panel').open, true);
});

test('resume explains a missing or incompatible checkpoint without touching the engine', () => {
  let loads = 0;
  const module = { _wpLoadGame: () => { loads++; return 0; }, _wpSetWebPause: () => 0 };
  const missing = appFixture('', { module, fs: { analyzePath: () => ({ exists: false }) } });
  prime(missing, { runtimeReady: true, build: { id: 'b', compatibility: 'c1' }, game: { inGame: false, map: '' } });
  missing.seam.loadCheckpoint();
  assert.match(missing.element('toast').textContent, /No checkpoint is saved/);
  const foreign = { compatibility: 'other', title: 'Old', savedAt: '2026-09-05T12:00:00.000Z' };
  const fs = { analyzePath: () => ({ exists: true }), readFile: () => JSON.stringify(foreign) };
  const incompatible = appFixture('', { module, fs });
  prime(incompatible, {
    runtimeReady: true, build: { id: 'b', compatibility: 'c1' }, game: { inGame: false, map: '' },
  });
  incompatible.seam.loadCheckpoint();
  assert.match(incompatible.element('toast').textContent, /another game version/);
  assert.equal(loads, 0);
  assert.equal(incompatible.seam.state.restoringCheckpoint, false);
});

test('the boot watchdog separates a silent transfer from a busy engine start and ignores hidden tabs', () => {
  const transfer = appFixture();
  transfer.seam.setWatchdogMode('transfer');
  transfer.setNow(100 + 44000);
  transfer.seam.watchdogTick();
  assert.equal(transfer.seam.state.failed, false, 'progress within the stall window is fine');
  transfer.setNow(100 + 46000);
  transfer.seam.watchdogTick();
  assert.equal(transfer.seam.state.failed, true);
  assert.match(transfer.element('errorCode').textContent, /WP-TIMEOUT/);

  const engine = appFixture();
  engine.seam.setWatchdogMode('engine');
  engine.setNow(10 ** 7);
  for (let tick = 0; tick < 11; tick++) engine.seam.watchdogTick();
  assert.equal(engine.seam.state.failed, false, 'wall-clock silence is not a stall while the engine works');
  engine.document.hidden = true;
  for (let tick = 0; tick < 30; tick++) engine.seam.watchdogTick();
  assert.equal(engine.seam.state.failed, false, 'hidden tabs suspend animation frames and are never judged');
  engine.document.hidden = false;
  engine.seam.watchdogTick();
  assert.equal(engine.seam.state.failed, true, 'a free event loop without an engine frame eventually fails');
  assert.match(engine.element('errorMessage').textContent, /engine did not start/);

  const busy = appFixture();
  busy.seam.setWatchdogMode('engine');
  for (let tick = 0; tick < 11; tick++) busy.seam.watchdogTick();
  busy.seam.setPhase('Starting command network…');
  for (let tick = 0; tick < 11; tick++) busy.seam.watchdogTick();
  assert.equal(busy.seam.state.failed, false, 'a phase change restarts the count');

  const running = appFixture();
  prime(running, { runtimeReady: true });
  running.seam.setWatchdogMode('transfer');
  running.setNow(10 ** 7);
  running.seam.watchdogTick();
  assert.equal(running.seam.state.failed, false, 'a running engine is never timed out');
});

const payload = new TextEncoder().encode('war powers');
const okResponse = body => ({
  ok: true, status: 200, body: null,
  arrayBuffer: async () => body.buffer.slice(body.byteOffset, body.byteOffset + body.byteLength),
});

test('immutable downloads retry network errors and 5xx with bounded attempts, never 4xx or mutable files', async () => {
  let released = 0;
  const failure = status => ({ ok: false, status, body: { cancel: async () => { released += 1; } } });
  const calls = [];
  const attempt = url => calls.filter(entry => entry === url).length;
  const chunk = new Uint8Array(4);
  const fetchStub = async url => {
    calls.push(url);
    switch (url) {
      case 'flaky': if (attempt(url) < 3) throw new TypeError('Failed to fetch'); return okResponse(payload);
      case 'down': throw new TypeError('NetworkError when attempting to fetch resource.');
      case 'server': if (attempt(url) < 2) return failure(503); return okResponse(payload);
      case 'missing': return failure(404);
      case 'mutable': throw new TypeError('Load failed');
      case 'broken': throw new TypeError("Cannot read properties of undefined (reading 'u')");
      case 'cancelled': throw Object.assign(new Error('The operation was aborted.'), { name: 'AbortError' });
      case 'stream': {
        if (attempt(url) > 1) return okResponse(payload);
        let reads = 0;
        const read = async () => {
          reads += 1;
          if (reads === 1) return { done: false, value: chunk };
          throw new TypeError('network error');
        };
        return { ok: true, status: 200, body: { getReader: () => ({ read }) } };
      }
      default: throw new Error(`unexpected ${url}`);
    }
  };
  const fixture = appFixture('', { fetch: fetchStub });
  const { seam } = fixture;
  const interrupted = /connection to the game server was interrupted/;
  assert.deepEqual([...await seam.fetchBytes('flaky', { immutable: true })], [...payload]);
  assert.equal(attempt('flaky'), 3);
  await assert.rejects(seam.fetchBytes('down', { immutable: true }), interrupted);
  assert.equal(attempt('down'), 3, 'a dead link is given exactly FETCH_ATTEMPTS tries');
  await seam.fetchBytes('server', { immutable: true });
  assert.equal(attempt('server'), 2);
  await assert.rejects(seam.fetchBytes('missing', { immutable: true }), /HTTP 404/);
  assert.equal(attempt('missing'), 1, '4xx is never retried');
  assert.equal(released, 2, 'every failed response body is cancelled');
  await assert.rejects(seam.fetchBytes('mutable'), interrupted);
  assert.equal(attempt('mutable'), 1, 'mutable files are fetched once');
  await assert.rejects(seam.fetchBytes('broken', { immutable: true }), /broken: Cannot read properties of undefined/);
  assert.equal(attempt('broken'), 1, 'a TypeError from the shell itself is not a network interruption');
  await assert.rejects(seam.fetchBytes('cancelled', { immutable: true }), /download was cancelled before it completed/);
  assert.equal(attempt('cancelled'), 1, 'an aborted download is not retried');
  await assert.rejects(seam.fetchBytes('unknown', { immutable: true }), /unknown: unexpected unknown/);
  assert.equal(attempt('unknown'), 1);
  const before = seam.loader.loadedBytes;
  await seam.fetchBytes('stream', { immutable: true });
  assert.equal(seam.loader.loadedBytes - before, payload.length, 'a discarded partial download does not count');
  assert.equal(seam.state.failed, false);
});

test('a failed boot abandons its transfers: nothing starts, retries, repaints or reaches the engine', async () => {
  let seam;
  const calls = [];
  let finish;
  const fetchStub = async url => {
    calls.push(url);
    if (url === 'inflight') await new Promise(resolve => { finish = resolve; });
    if (url === 'retrying') {
      seam.fail('Command connection interrupted');
      throw new TypeError('Failed to fetch');
    }
    return okResponse(payload);
  };
  const fixture = appFixture('', { fetch: fetchStub });
  ({ seam } = fixture);
  const inflight = seam.fetchBytes('inflight', { immutable: true });
  await assert.rejects(seam.fetchBytes('retrying', { immutable: true }), /connection to the game server/);
  assert.equal(seam.state.failed, true);
  assert.equal(calls.filter(url => url === 'retrying').length, 1, 'a failure ends the retry bound early');
  const loaded = seam.loader.loadedBytes;
  seam.progressBytes(500);
  assert.equal(seam.loader.loadedBytes, loaded);
  assert.equal(fixture.element('bootPercent').textContent, '', 'progress never repaints over the recovery page');
  finish();
  await assert.rejects(inflight, /loading stopped after an earlier failure/);
  await assert.rejects(seam.fetchBytes('later', { immutable: true }), /loading stopped after an earlier failure/);
  assert.deepEqual(calls, ['inflight', 'retrying'], 'no transfer starts behind the recovery page');

  // An engine compiled after the failure is never handed to the glue.
  const wasm = new Uint8Array([0, 0x61, 0x73, 0x6d, 1, 0, 0, 0]);
  const handed = [];
  const WebAssembly = {
    instantiate: async () => {
      compiling.seam.fail('Command connection interrupted');
      return { instance: {}, module: {} };
    },
  };
  const compiling = appFixture('', { fetch: async () => okResponse(wasm), WebAssembly });
  const sha256 = createHash('sha256').update(wasm).digest('hex');
  const build = { engine: { wasm: { url: 'assets/engine.wasm', size: wasm.length, sha256 } } };
  await compiling.seam.instantiateEngine(build, {}, instance => handed.push(instance));
  assert.equal(compiling.seam.state.failed, true);
  assert.deepEqual(handed, []);
  assert.match(compiling.element('errorCode').textContent, /WP-RUNTIME/, 'the original failure is kept');
});

test('records named by a content address are verified, and each completed record is watchdog activity', async () => {
  const manifest = new TextEncoder().encode('[{"p":"Data/x","s":1,"u":"assets/a.json","h":"00"}]\n');
  const sha256 = createHash('sha256').update(manifest).digest('hex');
  const bodies = {
    'build.json': new TextEncoder().encode('{"id":"b"}'),
    [`assets/manifest.${sha256.slice(0, 16)}.json`]: manifest,
    [`assets/${sha256.slice(0, 24)}.json`]: manifest,
    [`assets/manifest.${'0'.repeat(16)}.json`]: manifest,
    [`assets/${'0'.repeat(24)}.json`]: manifest,
  };
  const fixture = appFixture('', { fetch: async url => okResponse(bodies[url]) });
  const { seam } = fixture;
  fixture.setNow(5000);
  assert.equal((await seam.fetchJSON('build.json')).id, 'b');
  assert.equal(seam.watchdog.lastActivity, 5000, 'an untracked record counts as activity when it lands');
  const addressed = url => seam.fetchJSON(url, { immutable: true });
  assert.equal((await addressed(`assets/manifest.${sha256.slice(0, 16)}.json`)).length, 1);
  assert.equal((await addressed(`assets/${sha256.slice(0, 24)}.json`)).length, 1);
  const integrity = error => error.code === 'WP-INTEGRITY' && /did not match this build/.test(error.message);
  await assert.rejects(addressed(`assets/manifest.${'0'.repeat(16)}.json`), integrity);
  await assert.rejects(addressed(`assets/${'0'.repeat(24)}.json`), integrity);
  assert.equal(seam.state.failed, false, 'verification reports; the boot decides how to fail');
});

test('the engine glue is pinned by subresource integrity and its arrival counts as activity', () => {
  const fixture = appFixture();
  const glue = new TextEncoder().encode('var Module = {};');
  const sha256 = createHash('sha256').update(glue).digest('hex');
  fixture.seam.loadEngineScript({ engine: { js: { url: 'assets/glue.js', sha256 } } });
  const script = fixture.element('script');
  assert.equal(script.src, 'assets/glue.js');
  assert.equal(script.integrity, `sha256-${createHash('sha256').update(glue).digest('base64')}`);
  fixture.setNow(7000);
  script.onload();
  assert.equal(fixture.seam.watchdog.lastActivity, 7000);
  delete script.integrity;
  fixture.seam.loadEngineScript({ engine: { js: { url: 'assets/glue.js' } } });
  assert.equal(script.integrity, undefined, 'a record without a hash gets no integrity attribute');
  script.onerror();
  assert.match(fixture.element('errorCode').textContent, /WP-SCRIPT-DOWNLOAD/);
});

test('an insecure origin skips hash checks with one warning while size checks still apply', async () => {
  const record = new TextEncoder().encode('{"unchecked":true}');
  const fixture = appFixture('', { crypto: undefined, fetch: async () => okResponse(record) });
  const { seam } = fixture;
  const wrongHash = { size: payload.length, sha256: 'ab'.repeat(32), label: 'x' };
  assert.equal(await seam.verifyAsset(payload, wrongHash), payload);
  assert.equal(await seam.verifyAsset(payload, wrongHash), payload);
  assert.equal((await seam.fetchJSON(`assets/${'0'.repeat(24)}.json`, { immutable: true })).unchecked, true);
  assert.equal(seam.logLines.filter(line => /not checked on this insecure origin/.test(line)).length, 1);
  assert.equal(seam.state.integrityWarned, true);
  await assert.rejects(seam.verifyAsset(payload, { size: 3, sha256: 'ab'.repeat(32), label: 'short' }), error => (
    error.code === 'WP-INTEGRITY' && /3 bytes/.test(error.message)
  ));
  assert.equal(seam.state.failed, false);
});

test('integrity checks reject a wrong size or checksum with the WP-INTEGRITY code', async () => {
  const fixture = appFixture();
  const payload = new TextEncoder().encode('war powers');
  const sha256 = createHash('sha256').update(payload).digest('hex');
  const verified = await fixture.seam.verifyAsset(payload, { size: payload.length, sha256, label: 'ok' });
  assert.equal(verified, payload);
  const integrity = error => error.code === 'WP-INTEGRITY' && /did not match this build/.test(error.message);
  const wrongHash = { size: payload.length, sha256: 'ab'.repeat(32), label: 'x' };
  await assert.rejects(fixture.seam.verifyAsset(payload, wrongHash), integrity);
  await assert.rejects(fixture.seam.verifyAsset(payload, { size: 3, label: 'short' }), integrity);
  assert.equal(fixture.seam.state.failed, false, 'verification reports; the caller decides how to fail');
});

test('a completed session shows its own return state, while an interrupted battle is a failure', () => {
  const fixture = appFixture();
  prime(fixture, { runtimeReady: true, game: { inGame: false, map: '' } });
  fixture.seam.handleGameExit();
  assert.equal(fixture.seam.state.failed, false);
  assert.equal(fixture.element('bootExit').hidden, false);
  assert.equal(fixture.element('bootError').hidden, true);
  assert.equal(fixture.element('bootPhase').textContent, 'Session complete');
  assert.equal(fixture.element('utilityBar').hidden, true);
  assert.equal(fixture.focus(), 'returnButton');
  const interrupted = appFixture();
  prime(interrupted, { runtimeReady: true, game: { inGame: true, map: 'WPTraining' }, lastResultKey: '' });
  interrupted.seam.handleGameExit();
  assert.equal(interrupted.seam.state.failed, true);
  assert.match(interrupted.element('errorCode').textContent, /WP-EXIT/);
  assert.equal(interrupted.element('bootExit').hidden, true);
  assert.equal(interrupted.element('bootError').hidden, false);
});

test('a restart needs a confirming click and any later settings change withdraws it', () => {
  const module = { _wpSetWebPause: () => 0, _wpSetAudioLevels() {} };
  const fixture = appFixture('', { module });
  prime(fixture, { runtimeReady: true, game: { inGame: true, map: 'WPTraining', frame: 300 } });
  fixture.seam.showSettings();
  const button = fixture.element('applyRestart');
  const note = fixture.element('restartNote');
  assert.equal(button.hidden, true);
  fixture.events.get('setting-cameraSpeed:input')({ target: { value: '70' } });
  assert.equal(button.hidden, false);
  assert.equal(button.textContent, 'Restart game to apply');
  fixture.events.get('applyRestart:click')();
  assert.equal(fixture.counters.reloads, 0);
  assert.equal(button.textContent, 'Restart now');
  assert.match(note.textContent, /ends the current battle/);
  fixture.events.get('setting-master:input')({ target: { value: '40' } });
  assert.equal(button.textContent, 'Restart game to apply', 'a later change withdraws the confirmation');
  fixture.events.get('applyRestart:click')();
  assert.equal(fixture.counters.reloads, 0);
  fixture.events.get('applyRestart:click')();
  assert.equal(fixture.counters.reloads, 1);
  const menu = appFixture('', { module });
  prime(menu, { runtimeReady: true, game: { inGame: false, map: '' } });
  menu.seam.showSettings();
  menu.events.get('setting-cameraSpeed:input')({ target: { value: '70' } });
  menu.events.get('applyRestart:click')();
  assert.equal(menu.counters.reloads, 1, 'outside a battle the restart is immediate');
});

test('saving a checkpoint updates the settings controls in place instead of rebuilding the panel', async () => {
  const written = {};
  const fs = {
    analyzePath: () => ({ exists: false }),
    writeFile: (path, data) => { written[path] = data; },
    syncfs: (populate, done) => done(null),
  };
  const module = { _wpSaveGame: () => 0, _wpSetWebPause: () => 0, _wpSetAudioLevels() {} };
  const fixture = appFixture('', { fs, module });
  prime(fixture, {
    runtimeReady: true, persistenceReady: true, build: { id: 'b', compatibility: 'c1' },
    operations: { missions: [trainingMission] }, game: { inGame: true, map: 'WPTraining', frame: 300 },
  });
  fixture.seam.showSettings();
  let rebuilt = 0;
  fixture.element('panelBody').replaceChildren = () => { rebuilt++; };
  await fixture.seam.saveCheckpoint();
  assert.equal(rebuilt, 0);
  assert.equal(fixture.element('saveCheckpoint').textContent, 'Save checkpoint');
  assert.equal(fixture.element('saveCheckpoint').disabled, false);
  assert.match(fixture.element('toast').textContent, /Checkpoint saved/);
  const metadata = JSON.parse(Object.entries(written).find(([path]) => path.endsWith('wp-checkpoint.json'))[1]);
  assert.equal(metadata.compatibility, 'c1');
  assert.equal(metadata.mission, '');
});

test('the inline feature gate reports unsupported browsers before the module loads', () => {
  const match = /<script>([\s\S]*?)<\/script>/.exec(page);
  assert.ok(match, 'index.html must carry an inline classic feature gate');
  assert.ok(page.indexOf(match[0]) < page.indexOf('<script type="module" src="app.js">'), 'the gate runs first');
  assert.match(page, /<noscript>/);
  function runGate({
    modules = true, webgl = true, clone = true, dialog = true, wasm = true,
    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/152.0', media = {}, search = '',
    session = {},
  } = {}) {
    const elements = new Map();
    let reloads = 0;
    const events = [];
    const element = id => {
      if (!elements.has(id)) elements.set(id, { hidden: true, textContent: '' });
      return elements.get(id);
    };
    const Dialog = function () {};
    Dialog.prototype.showModal = function () {};
    const gl = { getExtension: () => ({ loseContext() {} }) };
    const context = vm.createContext({
      window: { dispatchEvent(event) { events.push(event.type); }, getSelection: () => ({ removeAllRanges() {}, addRange() {} }) },
      location: { reload() { reloads++; }, search, origin: 'https://example.test' },
      navigator: { userAgent: agent },
      matchMedia: query => ({ matches: Boolean(media[query]) }),
      sessionStorage: { getItem: key => session[key] ?? null, setItem(key, value) { session[key] = value; } },
      Event: class { constructor(type) { this.type = type; } },
      document: {
        getElementById: element,
        createElement(tag) {
          if (tag === 'script') return modules ? { noModule: false } : {};
          if (tag === 'canvas') return { getContext: () => (webgl ? gl : null) };
          return {};
        },
      },
      structuredClone: clone ? structuredClone : undefined,
      HTMLDialogElement: dialog ? Dialog : undefined,
      WebAssembly: wasm ? WebAssembly : undefined,
    });
    vm.runInContext(match[1], context);
    return {
      message: context.window.wpUnsupported, desktopOnly: context.window.wpDesktopOnly === true,
      element, reload: () => reloads, events, session,
    };
  }
  const supported = runGate();
  assert.equal(supported.message, undefined);
  assert.equal(supported.element('bootError').hidden, true);
  const noGraphics = runGate({ webgl: false });
  assert.match(noGraphics.message, /WebGL2 is unavailable/);
  assert.equal(noGraphics.element('bootError').hidden, false);
  assert.equal(noGraphics.element('errorCode').textContent, 'WP-BROWSER');
  assert.equal(noGraphics.element('diagnosticsButton').hidden, true);
  const old = runGate({ clone: false, dialog: false, modules: false, wasm: false });
  assert.match(old.message, /JavaScript modules, WebAssembly, structuredClone, dialog elements/);
  assert.equal(old.element('bootPhase').textContent, 'Browser not supported');
  old.element('reloadButton').onclick();
  assert.equal(old.reload(), 1);
  // The module itself defers to the gate's verdict instead of painting over it.
  const context = vm.createContext({ ...core, window: { wpUnsupported: 'unsupported here' } });
  assert.throws(() => vm.runInContext(application, context), /unsupported here/);
});

test('the desktop gate holds phones and touch-only devices before any download', () => {
  const match = /<script>([\s\S]*?)<\/script>/.exec(page);
  const runGate = options => {
    const elements = new Map();
    const events = [];
    const session = options.session ?? {};
    const element = id => {
      if (!elements.has(id)) elements.set(id, { hidden: true, textContent: id === 'deviceLink' ? '{{PUBLIC_URL}}' : '' });
      return elements.get(id);
    };
    const Dialog = function () {};
    Dialog.prototype.showModal = function () {};
    const gl = { getExtension: () => ({ loseContext() {} }) };
    const context = vm.createContext({
      window: { dispatchEvent(event) { events.push(event.type); } },
      location: { reload() {}, search: options.search ?? '', origin: 'https://example.test' },
      navigator: { userAgent: options.agent ?? 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/152.0' },
      matchMedia: query => ({ matches: Boolean((options.media ?? {})[query]) }),
      sessionStorage: { getItem: key => session[key] ?? null, setItem(key, value) { session[key] = value; } },
      Event: class { constructor(type) { this.type = type; } },
      document: {
        getElementById: element,
        createElement(tag) {
          if (tag === 'script') return { noModule: false };
          if (tag === 'canvas') return { getContext: () => gl };
          return {};
        },
      },
      structuredClone, HTMLDialogElement: Dialog, WebAssembly,
    });
    vm.runInContext(match[1], context);
    return { desktopOnly: context.window.wpDesktopOnly === true, element, events, session };
  };
  const desktop = runGate({ media: { '(any-pointer: fine)': true, '(any-hover: hover)': true } });
  assert.equal(desktop.desktopOnly, false);
  assert.equal(desktop.element('deviceNotice').hidden, true);
  const phone = runGate({
    agent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1',
    media: { '(pointer: coarse)': true },
  });
  assert.equal(phone.desktopOnly, true);
  assert.equal(phone.element('deviceNotice').hidden, false);
  assert.equal(phone.element('bootProgress').hidden, true);
  assert.equal(phone.element('bootPhase').textContent, 'Desktop required');
  assert.equal(phone.element('deviceLink').textContent, 'https://example.test/', 'an unstaged page still shows a real address');
  const touchTablet = runGate({ agent: 'Mozilla/5.0 (X11; Linux; Tablet) Chrome/152.0', media: { '(pointer: coarse)': true } });
  assert.equal(touchTablet.desktopOnly, true, 'touch-only input holds even without a phone user agent');
  const tabletWithMouse = runGate({ agent: 'Mozilla/5.0 (X11; Linux; Tablet) Chrome/152.0',
    media: { '(pointer: coarse)': true, '(any-pointer: fine)': true } });
  assert.equal(tabletWithMouse.desktopOnly, false, 'a fine pointer anywhere passes the gate');
  const overridden = runGate({ agent: 'Mozilla/5.0 (iPhone) Mobile Safari', media: { '(pointer: coarse)': true }, search: '?desktop=1' });
  assert.equal(overridden.desktopOnly, false);
  const remembered = runGate({ agent: 'Mozilla/5.0 (iPhone) Mobile Safari', media: { '(pointer: coarse)': true },
    session: { wpDesktopOverride: '1' } });
  assert.equal(remembered.desktopOnly, false);
  // Continue anyway: remembers the choice for the session and releases the module without a reload.
  phone.element('continueAnywayButton').onclick();
  assert.equal(phone.session.wpDesktopOverride, '1');
  assert.deepEqual(phone.events, ['wp-continue']);
  assert.equal(phone.element('deviceNotice').hidden, true);
  assert.equal(phone.element('bootProgress').hidden, false);
  // The module waits for that event instead of booting behind the notice.
  assert.match(application, /else if \(window\.wpDesktopOnly\) \{[\s\S]*?addEventListener\('wp-continue', startBoot, \{ once: true \}\)/);
});
