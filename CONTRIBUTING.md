# Contributing to War Powers

Thanks for helping. War Powers is a desktop-browser RTS built from a GPL engine
fork and an original, freely licensed dataset. Before changing its scope, read
[the vision](docs/vision.md), the [creative bible](docs/creative.md) and the
[roadmap](docs/roadmap.md); the [decision log](docs/decisions.md) explains why
things are the way they are. Bug reports and feature requests go through the
issue templates; questions are welcome as issues too.

## Toolchain

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.10 or newer, standard library only | generators, validators, staging, the local server and the Python tests |
| Node.js | 20 or newer, no npm packages | the web-state tests (`node --test`) |
| CMake + Ninja | CMake 3.25 or newer | configuring and building the engine |
| Emscripten SDK | 6.0.8 (the tested version) | the WebAssembly engine build |
| A native C++17/C++20 compiler with AddressSanitizer and UndefinedBehaviorSanitizer (clang or gcc) | — | the focused engine and renderer fixtures; `CXX` selects it, default `c++` |
| Blender + [OpenSAGE.BlenderPlugin](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin) | Blender 5.x; the plugin checkout at `engine/references/OpenSAGE.BlenderPlugin` | regenerating models, textures and portraits only — checked-in art is complete |
| eSpeak NG | any recent release | regenerating unit voices only (`tools/gensfx.py`) |

Nothing is installed with a package manager and nothing phones home.

## Build, stage, serve

The full quick start is in the [README](README.md#play-it). In short:
`emcmake cmake --preset wasm` and `cmake --build build/wasm --target
GeneralsXZH.js` inside `engine/`, then `python3 tools/genwebstage.py` and
`python3 tools/serve.py` from the root.

- An **engine** source change needs a rebuild, then a restage.
- A **data** or **web** change needs a restage (`tools/genwebstage.py` runs
  the content gates first).
- Refresh the browser afterwards; `build.json` is never cached.
- Always configure with `emcmake`: plain CMake may pick the host compiler, and
  a build directory configured that way must be deleted.

**Reuse the same server URL.** Browser storage — settings, the checkpoint and
the operation record — belongs to the origin, so `http://localhost:8322` and
`http://127.0.0.1:8322` are different games. Keep one `tools/serve.py` running
and use a separate browser profile for QA instead of a second port.

## Tests and gates

Run everything from the repository root. Together these take a couple of
minutes; the sanitizer fixtures compile small native programs.

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_content.py
python3 tools/validate_gameplay.py
python3 tools/lint_voices.py
python3 engine/scripts/qa/test-keyboard-modifiers.py
python3 engine/scripts/qa/test-sentence-hotkeys.py
python3 engine/scripts/qa/test-mip-filter.py
python3 engine/scripts/qa/test-surface-copy.py
python3 dvijoke/d8web/tests/test_resources.py
```

`npm run test:all` runs the first five (no packages are installed; the
`package.json` scripts only spell out the commands). What they cover, and what
they do not, is in [docs/testing.md](docs/testing.md).
A generator, validator or fixture passing is evidence for that fixture only;
a change to gameplay, UI or maps also needs a browser walkthrough.

## Diagnostic runs

The scripted self-play modes, click tests and review scenes are compiled only
into the harness build (CMake option `WP_HARNESS`, preset `wasm-harness`).
Stage it into its own directory and serve that directory:

```sh
cd engine
emcmake cmake --preset wasm-harness
cmake --build build/wasm-harness --target GeneralsXZH.js
cd ..
python3 tools/genwebstage.py webstage-harness --build-dir engine/build/wasm-harness/GeneralsMD
python3 tools/serve.py --directory webstage-harness
```

The engine traces (`IG_TRACE`, `WP_AI_TRACE`, `WP_DOZER_TRACE`,
`WP_SURFACE_TRACE`, `WP_SCENE_DUMP`, `WP_FRAME_DUMP`, `WP_PRESENT_SKIP`) are
different: they stay in production builds behind runtime environment
switches. The shell forwards diagnostic URL parameters only with `?debug=1`,
for example `/?debug=1&map=Maps/WPTest.map&autotest=economy`; production
builds from the `wasm` preset ignore the harness variables, while the traces
still apply. The modes and traces, and which of them need the harness build,
are tabulated in [docs/testing.md](docs/testing.md).

## Branches and pull requests

- Work on a feature branch from `main`; keep pull requests small and focused
  on one player-visible outcome or one engineering change.
- In the description, state the **trigger** (what was wrong or missing), the
  **changed behaviour** and the **checks performed** — which tests, which
  browser walkthrough, which diagnostic mode. Say what remains unverified.
- Edit generators alongside their generated outputs; never hand-edit a
  generated map, layout, model or texture.
- New commands need readable tooltips, hotkeys and failure feedback. A balance
  or map change needs a playable scenario, not only valid INI.
- Add tests where behaviour can regress. Do not add heavyweight dependencies
  or a build framework for a small change.

## Asset provenance

Every asset family needs a row in [ASSETS.md](ASSETS.md) — path, what it is,
source, author, license, date, notes — and the machine-readable registry must
be regenerated:

```sh
python3 tools/check_content.py --write-registry
```

Pre-approved inbound licenses are CC0/public domain, CC BY and SIL OFL.
Anything else needs a decision-log entry before import. See
[LICENSING.md](LICENSING.md).

## What never goes in

- Retail EA assets, extracted or converted game data, or anything derived
  from them, in any form and at any resolution.
- Unlicensed downloads, or files whose license you cannot name.
- Credentials, tokens, personal save files, browser profiles.
- Build trees, staged output (`webstage/`), local SDKs, editor state.

## Licenses

Root code is MIT; project-authored content is CC BY 4.0; imported files keep
their recorded license. Contributions to `engine/` follow
[its contribution guide](engine/CONTRIBUTING.md) and are GPL-3.0 with EA's
additional terms. Keep every inherited notice intact. By contributing you
agree that your contribution is licensed under the license of the file or
directory it lands in.

## Repository boundaries

- The **root** repository holds the dataset, the web shell, the tools and the
  vendored `dvijoke/` renderer.
- `engine/` is a **Git submodule** (the GeneralsX fork).
- The engine carries two **nested submodules**: `engine/references/fbraz3-dxvk`
  (DXVK, used only by the native macOS development build) and
  `engine/references/OpenSAGE.BlenderPlugin` (used only for art regeneration).
  The browser build needs neither.

Commit and push a child repository before committing its updated gitlink in
the parent, so a recursive clone always resolves. The layout, remotes and push
order are in [docs/WORKSPACE.md](docs/WORKSPACE.md).

## Continuous integration

Workflows for the gate list above and for a scheduled WebAssembly build exist
in `.github/workflows/`; the gate workflow runs on pushes and pull requests.
Run the gate list locally before opening a pull request so the workflow only
confirms what you already checked.

## Reporting problems

Use the bug report template. Include the build identifier from **Settings →
Copy diagnostics**, your browser and OS, the mission, faction and difficulty,
the exact steps and what you observed. Remove personal information from
diagnostics before posting. For checkpoint problems, say whether storage was
available and whether the game was updated since the save; checkpoints stay on
that browser and device and are version-checked.
