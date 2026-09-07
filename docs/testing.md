# Testing

What the local gates prove, how to build the diagnostic harness, the scripted
modes it provides and the traces every build carries. Run commands from the
repository root.
The engine's own inherited replay tests (`engine/TESTING.md`) target retail
compatibility and do not apply to the War Powers dataset.

## Automated local gates

| Command | Covers | Does not cover |
|---|---|---|
| `node --test tests/*.test.mjs` | Web-state logic: malformed or blocked storage, settings bounds, command remapping, training guidance requirements and native-stage authority, battle identity across restarts, operation-record merge/round-trip/limits, engine-failure recovery | Anything rendered; the engine |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | Packaging and tool tests (35): `test_staging.py` covers repeatable hashes, content references and notices, UI/save compatibility identity, engine-glue release identity, protected output paths, oversized-candidate rejection and release source-URL rules; `test_tools.py` covers the TGA, W3D and map readers, the generators failing closed on a name collision, and CLI conflicts | The engine build itself |
| `python3 tools/check_content.py` | Native model, texture, icon and window references; operations metadata; Body modules on drawable objects; the asset registry (`--write-registry` rewrites `data/asset-registry.json`) | Visual correctness |
| `python3 tools/validate_gameplay.py` | Independent decode of all 17 map binaries: the seven mission success/failure/tie branches, native condition and action signatures, paid AI responses, supply/counter/budget contracts, traversable routes with cliff clearance, wheel locomotor turn speeds | Balance, pathing in play |
| `python3 tools/lint_voices.py` | Distinct voice ownership across templates and shared pools; every event defined; every WAV present | Intelligibility, mix |
| `python3 engine/scripts/qa/test-keyboard-modifiers.py` | Production event-state handling for left/right Ctrl/Shift/Alt, chord ordering, release and repeat | Browser key delivery |
| `python3 engine/scripts/qa/test-sentence-hotkeys.py` | Sentence layout and glyph handling under ASan/UBSan, including trailing ampersands and optional hotkey coordinates | Font rendering |
| `python3 engine/scripts/qa/test-mip-filter.py` | Mip-filter reference ownership and error propagation in the production `D3DXFilterTexture` | Pixel output |
| `python3 engine/scripts/qa/test-surface-copy.py` | Surface-copy bounds, pitches, block rows and self-copy rejection on the manual path (`--gli-root PATH` adds the Linux GLI path) | GPU behaviour |
| `python3 dvijoke/d8web/tests/test_resources.py` | The `d8web` frontend with a CPU-only backend under ASan/UBSan: surface copies, rectangle rejection, mip-level surface ownership and texture lifetime | WebGL2 itself |

The four engine fixtures and the renderer test compile small native programs;
`CXX` selects the compiler (default `c++`), which needs C++17 (engine) or
C++20 (renderer) with AddressSanitizer and UndefinedBehaviorSanitizer. The
four engine fixtures accept `--baseline REV` to prove that the previous
revision still fails; `dvijoke/d8web/tests/test_resources.py` takes no
arguments.

A green gate list is evidence for what the table says and nothing more. A
gameplay, UI or map change also needs a browser walkthrough, and the scripted
modes below inject state or force outcomes — say so when citing them.

## The harness build

Scripted self-play (`WP_AUTOTEST`, including the `mission` verdicts), click
tests (`WP_CLICKTEST`) and the review and stress scenes (`WP_REVIEW_SCENE`)
are compiled only when the CMake option `WP_HARNESS=ON` is set. The
`wasm-harness` preset does that and builds into `engine/build/wasm-harness`.
Stage it into its own directory and serve that directory:

```sh
cd engine
emcmake cmake --preset wasm-harness
cmake --build build/wasm-harness --target GeneralsXZH.js
cd ..
python3 tools/genwebstage.py webstage-harness --build-dir engine/build/wasm-harness/GeneralsMD
python3 tools/serve.py --directory webstage-harness
```

Production builds from the `wasm` preset ignore the harness variables. The
traces are different: they stay in every build, production included, behind
runtime environment switches, so a `?debug=1` session on a production stage
still produces `IG_TRACE`, AI, dozer, surface and scene-dump output. The shell
forwards the URL parameters below to the engine environment only when the
page is opened with `?debug=1`, which also enables the log panel, `IG_TRACE`
and the in-game frame counters. Keep a harness stage out of `webstage/`, and
never stage a harness build with `--release`.

Diagnostic outcomes never write the player's persistent operation record.

## Modes and traces

"Harness build?" says whether the switch exists only in a build configured
with `WP_HARNESS=ON` (the `wasm-harness` preset, or a native build configured
with that option); every other row is present in production builds as well.
"URL" is the query parameter the shell maps to the variable when `?debug=1`
is present; "—" means the shell never sets it.

| Variable | URL | Values | Harness build? | What it does |
|---|---|---|---|---|
| `WP_AUTOTEST` | `autotest` | `build`, `base`, `wedge`, `strike`, `ghost`, `husk`, `defeat`, `win`, `cycle`, `economy`, `powers`, `mission`, `mission-defeat`, `retry` | yes | Scripted self-play regressions once a match is running: `build` queues a unit; `base` drives the dozer/production loop; `wedge` reproduces the dozer approach wedge; `strike` kills a forward tower to trip AI retaliation; `ghost` and `husk` exercise fog memory and placement previews; `defeat` destroys the player's headquarters to exercise the defeat screen and `win` the enemy's; `cycle` runs match → shell → redeploy; `economy` measures hauling for one minute; `powers` fires the faction power; `mission`/`mission-defeat` satisfy or break the map's objectives and assert the native result callback; `retry` runs defeat → score → Retry cycles |
| `WP_AUTOTEST_UNIT` | — | template name | yes | Which unit the `build` mode queues |
| `WP_RETRY_RUNS`, `WP_RETRY_FRAMES` | `retryruns`, `retryframes` | integers | yes | How many Retry cycles the `retry` mode runs and at which logic frame each injects the headquarters loss |
| `WP_CLICKTEST` | — | `1`, `ui` | yes | Native only: synthetic SDL input; `1` selects a unit and orders a move, `ui` drives the command-bar build button |
| `WP_REVIEW_SCENE` | `review` | `1`, `stress` | yes | `1` spawns the faction roster review scene; `stress` adds the bounded 120-unit attack-move encounter and reports cadence and heap capacity |
| `WP_SCENE_DUMP` | `scenedump` | frame, or `+N` to re-arm per match | no | One-shot render-object census (name, class, position, draw info) for orphan hunting |
| `WP_AI_TRACE` | `aitrace` | `1` | no | Computer-player economy and army every ten seconds, per-team production gates, factory split, named-object destruction backtraces |
| `WP_DOZER_TRACE` | `doztrace` | `1` | no | Dozer task and approach-point tracing |
| `WP_SURFACE_TRACE` | `surfacetrace` | `1` | no | Surface and texture ownership tracing in the renderer bridge; the shell forwards it only in a diagnostic session |
| `IG_TRACE` | set by `?debug=1` | `1` | no | The permanent bring-up traces (`[MOUSE]`, `[WINHIT]`, `[AUDIO*]`, `[DEATH]`, `[WPAIR]`, …); verbose |
| `WP_FRAME_DUMP` | — | `<path.tga>` | no | Native: writes the back buffer to that file as a top-down TGA every 60th frame |
| `WP_PRESENT_SKIP` | — | frame count | no | Native: bypass presentation for unattended runs (an occluded window blocks presenting forever) |
| `WP_BOOT_MAP` | — | map path (`Maps\X\X.map`) | no | Native runs: boot straight into a map through the `-file` path and return to the in-engine shell at match end instead of quitting. Nothing in the shell sets it; browser deploys go through the in-engine shell and the `_wpShowMission` export |
| `WP_DIFFICULTY` | — | `0`, `1`, `2` | no | Native `-file` runs: override the difficulty the menu would have set |
| `WP_VOLUME` | set by the shell on every boot | `0`–`100` | no | Backend master volume at boot; the shell sets 100 and applies channel levels itself |

Native launches take the same variables in the environment, for example
`WP_PRESENT_SKIP=1 WP_AUTOTEST=base ./run.sh -win -noshellmap -file Maps/WPTest.map`
(the harness rows need a native build configured with `-DWP_HARNESS=ON`).
Without `-file` the native engine idles at the shell; the autotest acts only
once a match is running.

## Reproduce focused diagnostics

After staging and serving the harness build, with `?debug=1` on every URL:

- `/?debug=1&map=Maps/WPTest.map&autotest=economy` — Meridian hauling.
- `/?debug=1&map=Maps/WPTestJ.map&autotest=economy` — Jackal hauling.
- `/?debug=1&map=Maps/WPTest.map&autotest=powers` — Precision Strike.
- `/?debug=1&map=Maps/WPTestJ.map&autotest=powers` — Tunnel Ambush.
- `/?debug=1&autotest=retry&retryruns=2&retryframes=14400` — two eight-minute
  matches with defeat → score → Retry, in one runtime.
- `/?debug=1&autotest=defeat` — deploy Field Orientation through the menu and
  walk the ordinary debrief → battle report → Retry path.

The page keeps a visible diagnostic report; ordinary play never shows one.
Direct-map (`map=`) sessions exit after a result; for menu, debrief and report
testing open `/?debug=1&autotest=mission` and deploy through the menu.

Mission branches: `/?debug=1&map=Maps/<map>.map&autotest=mission` for success
and `autotest=mission-defeat` for failure. Require `MISSION_RESULT PASS` and
no `MISSION_CHECK FAIL` in the report.

| Map | Mission | Additional failure case |
|---|---|---|
| `WPTraining` | Field Orientation | — |
| `WPOp01` | First Light | — |
| `WPOp02` | Cut the Wire | — |
| `WPOp03` | The Long Watch | `mission-defeat-hq` |
| `WPOp04` | War Powers | — |
| `WPChallengeM` | Glass Rampart | `mission-defeat-hq` |
| `WPChallengeJ` | Hostile Takeover | `mission-defeat-hq` |

The fixtures create prerequisites, destroy named targets and advance timers
while asserting intermediate counters and the actual result callback.

Roster scenes: `/?debug=1&map=Maps/WPTest.map&review=1` (Meridian) or the
`WPTestJ` map (Jackal); `review=stress` is the performance fixture described
in [perf.md](perf.md). Run it separately from other game tabs.

## Browser walkthrough notes

- Storage is per origin: reuse `http://localhost:8322` and use a separate
  browser profile for a clean record instead of another port.
- A hidden tab suspends the engine; front the tab, deliver one input event,
  wait a beat, then screenshot before concluding anything about a "frozen"
  game.
- Avoid `debug=1` in ordinary playtests: the logs are verbose and the boot
  beacon goes to the local server's access log.
- Copy the build identifier from Settings → Copy diagnostics into every
  report.
