# Web bridge: the shell ↔ engine contract

The browser shell (`web/index.html`, `web/app.js`, `web/core.js`,
`web/styles.css`) loads a content-addressed release produced by
`tools/genwebstage.py` and drives the Emscripten build of the engine
(`engine/build/wasm/GeneralsMD/GeneralsXZH.{js,wasm}`). The engine side of the
contract lives in `WPShell.cpp` (`GeneralsMD/Code/GameEngine/Source/GameClient/
GUI/GUICallbacks/Menus/`) and the `igrotekaFrameTick` main loop in
`GeneralsMD/Code/GameEngine/Source/Common/GameEngine.cpp`. This page records
what crosses that seam today; it is not a design proposal.

## Boot sequence

1. `index.html` runs an inline classic feature gate (modules, WebAssembly,
   `structuredClone`, `Object.hasOwn`, `<dialog>`, a WebGL2 probe). A failure
   sets `window.wpUnsupported`, shows `#bootError` with code `WP-BROWSER`, and
   `app.js` refuses to run.
2. `app.js` fetches `build.json`, then the manifest and `operations.json` it
   names, sizes the canvas from `QUALITY_PRESETS[settings.quality]`, defines
   `window.Module` and appends the glue `<script>` with a subresource-integrity
   hash from `build.json`.
3. The glue calls `Module.instantiateWasm`: the shell downloads the `.wasm`,
   verifies size and SHA-256, compiles it and hands the instance back.
4. The glue runs `Module.preRun`: the shell sets the environment, lays out
   MEMFS, stages every manifest file (12 parallel streams, each verified),
   writes the font, mounts IDBFS and restores saves, writes `Options.ini`, then
   releases the `war-powers-content` run dependency.
5. `main()` runs synchronously (engine init and the first map load can block
   the thread for tens of seconds on slow devices). The first animation-frame
   tick calls `Module.onEngineRunning`; the loader fades and the utility bar
   appears.

The stall watchdog has two modes: while transferring it fails after 45 s
without bytes or a phase change; while the engine compiles or starts it counts
free event-loop ticks instead (about a minute), because a blocked thread cannot
tick and a hidden tab suspends animation frames. Hidden tabs are never judged.

## `Module` callbacks (engine → shell)

| Callback | Source | Payload |
|---|---|---|
| `onEngineRunning()` | first `igrotekaFrameTick` | none; the loader is dismissed and audio levels/pause are applied |
| `onGameExit()` | `igrotekaFrameTick` when the engine quits (EXIT_RUNTIME=0, the loop just stops) | none; the shell shows its "Session complete" state, or `WP-EXIT` if a battle was interrupted without a result |
| `onAbort(reason)` | Emscripten `abort()` | string; fails with `WP-ENGINE` |
| `onGameState(state)` | `WPUpdatePlayerExperience` every 8 ticks | `{version: 1, inGame, paused, map, operationId, frame, seconds, money, powerProduced, powerConsumed, units, structures, builders, productionBuildings, incomeBuildings, selected:{count,name,template,health,maxHealth}, objectiveStage, objectiveProgress, objectiveTarget, objectiveSeconds, unitsBuilt, unitsLost, unitsDestroyed, buildingsBuilt, moneyEarned, idleWorkers, difficulty, headquartersHealth, headquartersMaxHealth, trainingCounts:{…}}` |
| `onMatchResult(result)` | `WPRecordMatchResult` at VICTORY/DEFEAT | `{map, operationId, won, difficulty, stats:{unitsBuilt, unitsLost, unitsDestroyed, buildingsBuilt, moneyEarned, durationSeconds}}` plus the same numbers flattened for older readers |
| `onGameMessage(message)` | `WPDisplayMissionText` (`WP:` string keys) and `WPDisplayPlayerMessage` | `{id, text, map}`; the shell shows `text` as a toast |
| `onMatchLoadBegin(json)`, `onMatchLoadEnd()`, `onLobbyReached()` | `GameLogic::startNewGame` (map/slot payload) and the LAN lobby | emitted by the engine but not consumed by the shell today; available for a future map-loading indicator |
| `print` / `printErr` | Emscripten stdout/stderr | engine lines go to `console.debug`; `printErr` lines starting with `WARNING` go to `console.warn`, `ERROR`/`FATAL` to `console.error` |

Telemetry is observational: native map scripts decide objectives and results.
`beginsNewBattle()` in `core.js` detects a fresh battle from `inGame`, the map
leaf and a frame counter that moved backwards (restart or checkpoint).

## `EMSCRIPTEN_KEEPALIVE` exports (shell → engine)

| Export | Effect |
|---|---|
| `_wpSetWebPause(paused)` | Acquire or release the web pause; returns whether the game is paused. The engine only releases a pause the web acquired, so native Escape/P pauses survive closing a panel |
| `_wpSetAudioLevels(master, music, effects, voice)` | Percentages 0–100 applied as system-setting volumes per channel |
| `_wpSetMasterVolume(pct)` | Older single-volume path, used only when the channel export is missing |
| `_wpSaveGame()` | Writes `Save/wp-checkpoint.sav`; returns a `SaveCode` (0 = OK). Durable only after the shell's `FS.syncfs` |
| `_wpLoadGame()` | Loads that slot; returns a `SaveCode`. The shell suppresses the automatic briefing for the restored battle |
| `_wpShowMission(index)` | Opens the deployment screen for `operations.json` mission `index`; refused during a battle |

The shell calls exports only while `runtimeReady` and not `failed`. `fail()`
makes one best-effort pause and mute call, then never touches the engine again.

## Environment set by the shell (`preRun`)

Always: `CNC_GENERALS_ZH_PATH=/game`, `CNC_GENERALS_PATH=/game-base`,
`HOME=/home/web_user`, `WP_VOLUME=100` (the channel API applies the real
master). Options that need a restart are written to
`/home/web_user/.local/share/GeneralsX/GeneralsZH/Options.ini` by
`renderOptions()` (resolution from `QUALITY_PRESETS`, LOD, shadows,
`UseAlternateMouse`, `ScrollFactor`, debug font sizes).

Only with `?debug=1`: `IG_TRACE=1` (and `window.IG_TRACE = 1` for the
`EM_ASM` traces) plus the variables below. The production `wasm` preset,
built without `WP_HARNESS`, ignores the harness variables (`WP_AUTOTEST`,
`WP_RETRY_*`, `WP_REVIEW_SCENE`); the traces (`WP_SCENE_DUMP`, `WP_AI_TRACE`,
`WP_DOZER_TRACE`, `WP_SURFACE_TRACE`) still apply, because they are runtime
switches in every build.

| URL parameter | Engine variable | Notes |
|---|---|---|
| `autotest=<mode>` | `WP_AUTOTEST` | also marks the session diagnostic: no progress persistence, no hidden-tab pause, no automatic briefing, `[WP_TEST] MATCH_RESULT` lines |
| `review=<1\|stress>` | `WP_REVIEW_SCENE` | diagnostic session as above |
| `scenedump=<frame>` | `WP_SCENE_DUMP` | |
| `aitrace=1` | `WP_AI_TRACE` | |
| `doztrace=1` | `WP_DOZER_TRACE` | |
| `retryruns=<n>`, `retryframes=<n>` | `WP_RETRY_RUNS`, `WP_RETRY_FRAMES` | only with `autotest=retry`, which also skips the pausing web debrief |
| `surfacetrace=1` | `WP_SURFACE_TRACE` | only in a diagnostic session |
| `args=a,b` | extra `Module.arguments` | appended after `-win -noshellmap` |
| `debug=1` alone | | shows `#debugLog`, `Options.ini` debug font sizes, and sends `GET /wp-boot-ok?total=&build=` (answered by `tools/serve.py`) |

`?map=<stem>` is not debug-only: it validates the stem against the manifest
and starts the engine with `-file Maps/<stem>.map`. The `#testReport` pane
shows `[WP_AUTO]`/`[WP_TEST]`/`[WP_REVIEW]`/`[WP_SURFACE]` lines and any
sanitizer report during a diagnostic session.

## Filesystem layout

| Path | Backing | Contents |
|---|---|---|
| `/game` | MEMFS, engine cwd | every manifest file under its `p` path (`Data/…`, `Maps/…`, `Art/…`, `Window/…`); `/game/data` is a symlink to `/game/Data` because MEMFS is case-sensitive. `Data/INI/CommandMap.ini` is rewritten with the player's key bindings before it is written |
| `/game-base` | MEMFS | empty base-game root |
| `/fonts/default.ttf` | MEMFS | the font from `build.json` |
| `/home/web_user/.local/share/GeneralsX/GeneralsZH` | IDBFS (`-lidbfs.js`) | `Options.ini`, `Save/wp-checkpoint.sav`, and the sidecar `wp-checkpoint.json` = `{version: 1, compatibility, map, mission, title, savedAt}` written by the shell after a successful save |

`FS.syncfs(true)` restores the directory before `main()`; `FS.syncfs(false)`
flushes after a save. A checkpoint whose `compatibility` differs from the
running `build.json` cannot be resumed.

## Release records

`build.json` (mutable, `no-cache`):
`{schemaVersion: 1, id, compatibility, engine: {js: {url, size, sha256}, wasm: {url, size, sha256}}, font: {url, size, sha256}, manifest, operations, dataFiles, dataBytes, source}`.
`compatibility` hashes the data manifest and the wasm; `id` also covers the
shell, notices and credits, so UI-only releases keep saves compatible.

Manifest (`assets/manifest.<hash>.json`): an array of `{p, s, u, h}` = engine
path, size, immutable asset URL, SHA-256 hex. `source.json`:
`{schemaVersion: 1, build, status: 'development'|'provided', url, engine: {js: {sha256, size}, wasm: {sha256, size}}, dependencies}`.

Integrity: the shell checks `s`/`h` for every staged file and `size`/`sha256`
for the wasm and font with `crypto.subtle.digest` (hashing the whole set adds
well under a second on a desktop; WebCrypto needs a secure origin, so plain
`http://` on a LAN address only checks sizes). The manifest and
`operations.json` are content-addressed too (`assets/manifest.<16 hex>.json`,
`assets/<24 hex>.json`); their bytes must hash to the address. The glue script uses the
`integrity` attribute. Once the loader has failed, in-flight transfers are
abandoned: no retry wakes and no late download is hashed, staged or handed to
the engine. A mismatch fails with `WP-INTEGRITY`. Immutable files
(`assets/`, engine, font, manifest, operations) are retried up to three times
with backoff after network errors or 5xx, never after 4xx; `build.json` is
fetched once.

## The `trainingCounts` coupling

`WPUpdatePlayerExperience` counts a fixed template list on `WPTraining` only:
`WP_Fabricator, WP_Exchange, WP_PowerArray, WP_Porter, WP_VehiclePlant,
WP_Tank, WP_Vigil` (`trainingNames` in `WPShell.cpp`), reported as
`state.trainingCounts[template]`. `fieldGuidance()` in `core.js` reads the
same keys through `objectives[].requirements[].template` in
`data/operations.json`. A new training requirement template must be added to
both, or its checklist stays at 0.

## Failure codes

`WP-BROWSER` (feature gate), `WP-START` (unreadable `build.json`/manifest or an
unknown `?map=`; a failed fetch of those files reports `WP-DOWNLOAD`), `WP-DOWNLOAD`,
`WP-INTEGRITY`, `WP-SCRIPT-DOWNLOAD` (glue script or its SRI check),
`WP-ENGINE` (compile, abort), `WP-DATA` (staging), `WP-TIMEOUT` (watchdog),
`WP-GRAPHICS` (`webglcontextlost`), `WP-SCRIPT` (uncaught error while
running), `WP-ASYNC` (unhandled rejection), `WP-EXIT` (engine quit mid-battle),
`WP-RUNTIME` (default). Settings → Copy diagnostics includes the build id,
boot timings (`window.wpBootReport`) and the last log lines.

## Runtime globals and how to tighten them

The glue is not modularized, so the shell relies on globals the generated
script leaks: `Module`, `FS`, `IDBFS`, `ENV`, `addRunDependency` and
`removeRunDependency` (read as `window.FS`, `window.ENV`, …). To stop depending
on leaks, add
`-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,ENV,addRunDependency,removeRunDependency`
to the link options in `engine/cmake/wasm-deps.cmake` and read
`window.Module.FS` etc. in `prepareBattlefield`/`restorePersistence`; the
`_wp*` exports are already attached to `Module`. Going further to
`-sMODULARIZE` would replace `window.Module = {…}` plus a `<script>` tag with a
factory call (`GeneralsXZH(moduleArg)`), which the stager's `build.json` would
need to describe; it is not required for the export change.

## Test seam

Under node with `globalThis.__wpTestHarness = true`, `app.js` skips its boot
and exposes `globalThis.__wpTest` (shell `state`, `diagnostics`, the loader
and watchdog objects, and the functions `tests/recovery.test.mjs` drives).
Browsers never define `process`, so the seam does not exist there.
