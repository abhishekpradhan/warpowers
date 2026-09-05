# Workspace map — what lives where

One page to answer "where is that and where does it push." The workspace is
one git repo with one submodule (the engine); everything on disk that git
does not track is generated output.

## Directory layout (this repo: `warpowers`)

| Path | What it is | Tracked? |
|---|---|---|
| `data/` | All original game content: INI, maps, models, textures, audio, UI layouts, strings | yes (CC BY 4.0) |
| `tools/` | Generators + gates: genmap, genwnd, genw3d, genrig, gentex, gensfx, genicons2, gencmdicons, genportraitsheet, genwebstage, lint_voices, tgadiff; `tools/blender/` hero-asset scripts | yes (MIT) |
| `web/` | Loader + browser HUD, settings, field manual, operation record and persistent checkpoints | yes (MIT) |
| `docs/` | vision, roadmap, decisions, engine-notes (landmine log), publish-checklist, parity, creative, perf, this file | yes |
| `engine/` | **Submodule** → GeneralsX fork (GPL-3.0). Native + wasm engine source and build trees | gitlink |
| `dvijoke/` | **Vendored inline** (MIT, upstream meerzulee/dvijoke; full history subtree-merged 2026-08-31 from warpowers-dvijoke @ ba6791de). `d8web/` is the D3D8→WebGL2 layer the wasm build compiles in (`engine/cmake/wasm-deps.cmake` references `../dvijoke/d8web`) | yes (MIT; its own LICENSE) |
| `refs/` | Historical third-party source packs; retained provenance/reference inputs, excluded from web staging | yes |
| `webstage/` | **Generated** web bundle (engine wasm + gamedata + page), output of `tools/genwebstage.py`. Serve this dir to play | ignored |

Inside the engine submodule:
- `engine/references/fbraz3-dxvk` — DXVK fork (zlib), used by the native
  macOS build when `SAGE_DXVK_USE_LOCAL_FORK` is on. Tracked by the engine
  repo as a gitlink.
- `engine/references/OpenSAGE.BlenderPlugin` — W3D Blender exporter used by
  `tools/blender/` scripts. Reference checkout (gitlink).
- `engine/build/macos-vulkan/`, `engine/build/wasm/` — build trees (ignored).

## Native development

The browser build and all content checks run from a fresh recursive clone;
no runtime directory under a developer's home is required. Native macOS
setup is documented in the engine README. Choose an explicit runtime path,
then copy the repository's `Data`, `Maps`, `Art` and `Window` directories
there. Generators write repository data or a requested output directory;
deployment is a separate, deliberate action.

## GitHub repos (all private, all under abhishekpradhan)

| Repo | Local path | Default branch | Purpose |
|---|---|---|---|
| `warpowers` | workspace root | `main` | primary repo |
| `warpowers-engine` | `engine/` | `main` | engine fork |
| `warpowers-dxvk` | `engine/references/fbraz3-dxvk` | `main` | DXVK fork (native dev path only) |

(`warpowers-dvijoke` is **archived** read-only — its content and history now
live inline at `dvijoke/`, decision D020.)

Remote scheme, every checkout (normalized 2026-08-31): `origin` = our private
repo and what local branches track; fork parents/upstreams are fetch-only
remotes with their push URL set to `DISABLED`, so **never push upstream** is
enforced by git itself. Engine carries `upstream` (fbraz3/GeneralsX),
`superhackers`, `generalsxweb`; dxvk carries `upstream` (doitsujin) and
`fbraz3`.

**GitHub Actions: DISABLED at repo level on every repo (2026-08-31).** The
engine/dxvk forks inherited upstream CI workflows that billed private-repo
runner minutes (Windows/macOS at 2x/10x multipliers) on every push and
drained the account's monthly Actions budget (2026-08-24). The workflow
files are stripped from our branches AND Actions is switched off in each
repo's settings, so even an upstream-sync branch that reintroduces
`.github/workflows/` cannot run anything. Re-enable per-repo only if we
ever add CI of our own.

## Push routine

Use the active feature branch, not a hardcoded `main`. If all three
repositories changed, publish their commits from the deepest child outward:

```sh
git -C engine/references/fbraz3-dxvk push -u origin HEAD
# Commit the DXVK gitlink in engine, then:
git -C engine push -u origin HEAD
# Commit the engine gitlink in the root, then:
git push -u origin HEAD
```

Verify each referenced child commit is reachable on its remote before
pushing its parent. Do not push to disabled upstream remotes. A regular
push does not deploy this game or change repository visibility.

## Fresh clone

```
git clone --recursive https://github.com/abhishekpradhan/warpowers.git
```
brings the workspace (dvijoke included inline) + the engine submodule.
Build + play (matches the README quick start; needs emsdk active):

```
cd engine
emcmake cmake --preset wasm
cmake --build build/wasm --target GeneralsXZH.js
cd ..
python3 tools/genwebstage.py
python3 tools/serve.py
```

The native runtime dir is only needed for the native macOS build path.

Use `emcmake` for initial configuration: plain CMake may select the host compiler.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for prerequisite versions and local tests.
