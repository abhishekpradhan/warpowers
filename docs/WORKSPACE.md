# Workspace map — what lives where

One page to answer "where is that and where does it push." The workspace is
one git repo with two submodules; everything else on disk is generated.

## Directory layout (this repo: `warpowers`)

| Path | What it is | Tracked? |
|---|---|---|
| `data/` | All original game content: INI, maps, models, textures, audio, UI layouts, strings | yes (CC BY 4.0) |
| `tools/` | Generators + gates: genmap, genwnd, genw3d, gentex, gensfx, genportraitsheet, genwebstage, lint_voices; `tools/blender/` hero-asset scripts; `tools/patches/` | yes (MIT) |
| `web/` | `index.html` — the page-as-menu + boot harness (faction picker, volume, build badge) | yes (MIT) |
| `docs/` | vision, roadmap, decisions, engine-notes (landmine log), publish-checklist, hosting, perf, this file | yes |
| `engine/` | **Submodule** → GeneralsX fork (GPL-3.0). Native + wasm engine source and build trees | gitlink |
| `dvijoke/` | **Submodule** → dvijoke fork (MIT). `d8web/` is the D3D8→WebGL2 layer the wasm build compiles in (`engine/cmake/wasm-deps.cmake` references `../dvijoke/d8web`) | gitlink |
| `refs/` | Third-party asset sources (Quaternius CC0 packs). Conversion inputs only; never shipped | yes |
| `webstage/` | **Generated** web bundle (engine wasm + gamedata + page), output of `tools/genwebstage.py`. Serve this dir to play | ignored |

Inside the engine submodule:
- `engine/references/fbraz3-dxvk` — DXVK fork (zlib), used by the native
  macOS build when `SAGE_DXVK_USE_LOCAL_FORK` is on. Tracked by the engine
  repo as a gitlink.
- `engine/references/OpenSAGE.BlenderPlugin` — W3D Blender exporter used by
  `tools/blender/` scripts. Reference checkout (gitlink).
- `engine/build/macos-vulkan/`, `engine/build/wasm/` — build trees (ignored).

## Outside the workspace

| Path | What it is |
|---|---|
| `~/GeneralsX/GeneralsZH/` | The native **runtime dir**: deployed binary (`GeneralsXZH` + `run.sh`), synced `Data/`, `Maps/`, `Art/`, `Window/`. Deploy = `rm -f` + `cp` + `codesign -s - -f`. Not a repo — everything in it comes from this workspace |
| `~/MoltenVK-src` | MoltenVK source checkout for GPU debugging (not shipped) |

## GitHub repos (all private, all under abhishekpradhan)

| Repo | Local path | Branch | Purpose |
|---|---|---|---|
| `warpowers` | workspace root | `main` | primary repo (origin) |
| `warpowers-engine` | `engine/` | `main` | engine fork backup (remote name: `backup`) |
| `warpowers-dvijoke` | `dvijoke/` | `main` | dvijoke fork backup (remote name: `backup`) |
| `warpowers-dxvk` | `engine/references/fbraz3-dxvk` | `main` | DXVK fork backup (remote name: `backup`) |

Upstreams (fetch-only in practice; **never push**): engine → `generalsxweb`
(meerzulee/GeneralsXWeb), dvijoke → `origin` (meerzulee/dvijoke), dxvk →
fbraz3 lineage.

## Push routine

```
git push origin main                                   # workspace
git -C engine push backup main:main                    # engine fork
git -C dvijoke push backup main:main                   # dvijoke fork
git -C engine/references/fbraz3-dxvk push backup       # dxvk fork (rarely changes)
```

Rule: after committing in a submodule, commit the updated gitlink in the
workspace and push both — a workspace push whose gitlinks reference unpushed
submodule commits breaks fresh clones.

## Fresh clone

```
git clone --recursive https://github.com/abhishekpradhan/warpowers.git
```
brings the workspace + engine + dvijoke. Build wasm:
`source ~/emsdk/emsdk_env.sh && cmake --build engine/build/wasm --target GeneralsXZH.js`
(configure presets first on a brand-new machine), then `python3
tools/genwebstage.py` and serve `webstage/`.
