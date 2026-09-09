# Workspace map

Where things live and where they push. The workspace is one Git repository
with one submodule (the engine), which in turn carries two nested submodules:
DXVK (native macOS) and OpenSAGE.BlenderPlugin (art regeneration). Everything
on disk that Git does not track is generated output.

## Directory layout

| Path | What it is | Tracked |
|---|---|---|
| `data/` | Original game rules (INI), maps, models, textures, audio, layouts and strings, plus the attributed music and font | yes — CC BY 4.0 for project content; imports keep their licenses |
| `web/` | Loader page, in-match HUD, settings, field manual, operation record, checkpoints, credits page | yes — MIT |
| `tools/` | Generators (maps, layouts, models, rigs, textures, audio, icons, portraits), validators, the stager and the local server; `tools/blender/` holds the asset scripts | yes — MIT |
| `tests/` | Web-state tests (`*.test.mjs`) and the packaging and tool tests (`test_*.py`) | yes — MIT |
| `docs/` | Design and engineering documents; see [README.md](README.md) | yes — MIT |
| `licenses/` | Browser dependency inventory (`third-party.json`) and notice files | yes |
| `dvijoke/` | Vendored `d8web` renderer (D3D8 → WebGL2), subtree-merged with its full history (decision D020); `engine/cmake/wasm-deps.cmake` references `../dvijoke/d8web` | yes — MIT, own `LICENSE` |
| `engine/` | The GeneralsX engine fork: native and WebAssembly sources, build presets, QA fixtures | submodule (gitlink) — GPL-3.0 with EA's additional terms |
| `webstage/` | Generated browser bundle from `tools/genwebstage.py`; the directory `tools/serve.py` serves | ignored |
| `webstage-*/` | Additional generated stages, for example a harness build | ignored |

Inside the engine submodule:

| Path | What it is | Tracked |
|---|---|---|
| `engine/references/fbraz3-dxvk` | DXVK fork (zlib) used by the native macOS build when `SAGE_DXVK_USE_LOCAL_FORK=ON`; not part of the browser build | nested submodule |
| `engine/references/OpenSAGE.BlenderPlugin` | W3D exporter used by `tools/blender/` | nested submodule |
| `engine/build/wasm/`, `engine/build/wasm-harness/`, `engine/build/macos-vulkan/` | Build trees | ignored |

## Repositories

| Repository | Path | Contents |
|---|---|---|
| `warpowers` | workspace root | dataset, web shell, tools, docs, vendored renderer |
| `warpowers-engine` | `engine/` | engine fork; tracks upstream GeneralsX through a fetch-only remote |
| `warpowers-dxvk` | `engine/references/fbraz3-dxvk` | DXVK fork; native development only |

`origin` is the project's own remote in every checkout. Upstream projects are
fetch-only remotes whose push URL is disabled, so upstream cannot be pushed to
by accident. GitHub Actions run the gate workflow on the root repository; see
[CONTRIBUTING.md](../CONTRIBUTING.md#continuous-integration).

## Push order

Push from the deepest child outward so that every gitlink a parent records is
reachable before the parent is pushed:

```sh
git -C engine/references/fbraz3-dxvk push -u origin HEAD
# commit the DXVK gitlink in engine, then
git -C engine push -u origin HEAD
# commit the engine gitlink in the root, then
git push -u origin HEAD
```

Verify each referenced child commit exists on its remote before pushing its
parent. A push never deploys the game.

## Fresh clone and native paths

`git clone https://github.com/abhishekpradhan/warpowers.git && cd warpowers
&& git submodule update --init engine` brings the workspace and the engine,
which is all the browser build needs; `git submodule update --init --recursive`
(or `git clone --recursive`) also fetches the nested DXVK and
OpenSAGE.BlenderPlugin checkouts for native development or art regeneration.
The build recipe is in the [README](../README.md#play-it). The browser build
and all content checks run from such a fresh clone with no runtime directory
outside the repository. The native macOS path is documented
in the engine README; choose an explicit runtime directory for it and copy the
repository's `Data`, `Maps`, `Art` and `Window` directories there. Generators
write repository data or a requested output directory; deploying to a runtime
directory is a separate, deliberate action.
