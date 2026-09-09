# War Powers

A free real-time strategy game that runs in a desktop browser. Nothing to install, no game files to supply, no account.

[![Play in the browser](https://img.shields.io/badge/play-warpowers.vercel.app-1a7f37?style=flat)](https://warpowers.vercel.app)
[![Release](https://img.shields.io/github/v/release/abhishekpradhan/warpowers?style=flat)](https://github.com/abhishekpradhan/warpowers/releases/latest)
[![License: MIT (code)](https://img.shields.io/badge/license-MIT%20%28code%29-2b6cb0?style=flat)](LICENSE)
[![License: CC BY 4.0 (content)](https://img.shields.io/badge/license-CC%20BY%204.0%20%28content%29-2b6cb0?style=flat)](LICENSING.md)
[![CI](https://github.com/abhishekpradhan/warpowers/actions/workflows/ci.yml/badge.svg)](https://github.com/abhishekpradhan/warpowers/actions/workflows/ci.yml)

![Original War Powers models on the Meridian Strip: tanks, a hauler, infantry and a relay station](docs/media/warpowers-panorama.jpg)

## Play now

**<https://warpowers.vercel.app>** — open it in a current desktop browser with WebGL2 (Chrome, Edge, Firefox or Safari), with a keyboard and mouse. It boots in a few seconds on a normal connection. Choose **Operations → Field Orientation** for the guided first battle.

Release [v0.1.0](https://github.com/abhishekpradhan/warpowers/releases/tag/v0.1.0) (2026-09-09) is the first public build. The release page carries the web bundle; the [changelog](CHANGELOG.md) lists what is in it.

## What it is

War Powers is a browser RTS in the *Command & Conquer: Generals* idiom. It runs on the engine Electronic Arts released under the GPL, as continued by [TheSuperHackers](https://github.com/TheSuperHackers/GeneralsGameCode) and ported to macOS and Linux by [GeneralsX](https://github.com/fbraz3/GeneralsX); the project's [engine fork](https://github.com/abhishekpradhan/warpowers-engine) compiles it to WebAssembly. Everything on top of the engine is original and freely licensed — two fictional factions, models, textures, maps, missions, voices and interface — so no game files are needed and none of EA's ship. Establish a base, protect your supply line, scout the shroud and command a combined army as the precise, power-hungry **Meridian Combine** or the scrappy, mobile **Jackal Front** across the contested Meridian Strip. Settings, checkpoints and records stay in your browser: no account, no server-side state, no telemetry.

## Features

- **Two asymmetric factions.** Meridian fields expensive, accurate hardware on a fragile power grid; Jackal fields cheap raiders and power-independent salvage infrastructure. One signature power each: Precision Strike and Tunnel Ambush.
- **Seven authored missions, all open from the start.** The Field Orientation training battle, a four-operation campaign (First Light, Cut the Wire, The Long Watch, War Powers) and two timed commander trials (Glass Rampart, Hostile Takeover). Story order is a recommendation, never a lock.
- **Skirmish on five battlefields**, from either faction's side, at three opposition levels, against an opponent that builds, expands, escalates, raids the economy and retaliates.
- **A hauling economy.** Finite supply caches, physical hauler trucks and raidable supply lines; tech prerequisites, layered defences, artillery, two aircraft per faction and eight infantry roles.
- **A modern command experience.** 16:9 layouts, selected-unit information, a production queue, placement previews, attack-move, guard, rally points, control groups, remappable keys, a field manual and live training guidance.
- **Original art, voices and interface.** 54 original models and their textures come from reproducible Blender pipelines; maps, layouts, icons and processed radio barks come from generators; 44 rendered portraits; six attributed CC BY music tracks.
- **Browser-local persistence.** Settings, key remapping, audio channels, one checkpoint slot and an operation record with optional JSON backup, restore and merge. Nothing phones home.

![An early Field Orientation opening: the Meridian headquarters, the first units and the shroud beyond](docs/media/readme-battle.jpg)

## How it works

| Layer | What happens |
|---|---|
| Engine | The GeneralsX fork in `engine/` (the *Zero Hour* engine, `GeneralsMD/` tree) is compiled with Emscripten to `GeneralsXZH.wasm`, with SDL3 for windowing and input and miniaudio for sound. |
| Rendering | The engine's Direct3D 8 calls go through the vendored `d8web` renderer in `dvijoke/` (MIT) to WebGL2. |
| Content | Rules, units, weapons and powers are INI data; models are W3D, textures TGA, layouts WND and maps binary `.map` files, all under `data/`. The engine names no War Powers asset; retail behaviour it used to hard-code is switchable in `GameData.ini`. |
| Pipeline | Generators in `tools/` build maps, layouts, icons, portrait sheets and voices; scripted Blender pipelines build the models and textures byte-for-byte reproducibly; validators check content references, gameplay contracts and voice ownership, and the stager runs them before it writes a stage. |
| Shell | `web/` loads the content-addressed bundle that `tools/genwebstage.py` stages, boots the engine, and provides the HUD, settings, field manual, operation record and credits. |
| Persistence | Settings live in `localStorage`, the checkpoint slot in an IDBFS-mounted directory, the operation record in the browser with optional JSON download and restore. Nothing leaves the browser. |
| Hosting | Static files with immutable content-hashed assets; every stage carries `build.json` (the build identifier) and `source.json` (the corresponding source for that build, linked from the credits page). |

<a name="play-it"></a>

## Run it locally

**Browser:** a current desktop browser with WebGL2 and WebAssembly (Chrome, Edge, Firefox or Safari); keyboard and mouse. No mobile or touch support.

**Toolchain:** Python 3.10+ (standard library only), CMake 3.25+, Ninja and an activated [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html) — 6.0.8 is the tested version. Node.js 20+ runs the web tests. Blender 5.x is needed only to regenerate art; the checked-in art is complete.

```sh
git clone https://github.com/abhishekpradhan/warpowers.git
cd warpowers
git submodule update --init engine
cd engine
emcmake cmake --preset wasm
cmake --build build/wasm --target GeneralsXZH.js
cd ..
python3 tools/genwebstage.py
python3 tools/serve.py
```

Open **http://localhost:8322**. The first configure downloads the engine's dependencies and the first build takes a while; staging and serving take seconds. Always configure with `emcmake`: plain CMake may pick the host compiler. The `engine` submodule is all the browser build needs; `git submodule update --init --recursive` also fetches the engine's nested DXVK fork and OpenSAGE.BlenderPlugin checkouts, which only native development and art regeneration use. Keep one server and URL across sessions: browser storage belongs to the origin.

The local gates — the same list [CI](.github/workflows/ci.yml) runs on every push and pull request — take a couple of minutes from the repository root:

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

`npm run test:all` runs the first five without installing anything. The engine and renderer fixtures compile small native programs with AddressSanitizer and UndefinedBehaviorSanitizer (`CXX` selects the compiler). What each gate proves, and the diagnostic harness build (`wasm-harness` preset), are in [docs/testing.md](docs/testing.md). A scheduled workflow rebuilds the WebAssembly engine weekly, and a release workflow deploys a published GitHub release.

## Project layout

| Path | Contents |
|---|---|
| `data/` | Game rules (INI), maps, models, textures, audio, layouts, strings and operation metadata — CC BY 4.0 for project content |
| `web/` | The loader page, HUD, settings, field manual, operation record, checkpoints and credits — MIT |
| `tools/` | Content generators, validators, the stager and the local server; `tools/blender/` holds the model and texture pipelines ([tools/README.md](tools/README.md)) |
| `tests/` | Dependency-free web-state tests (`*.test.mjs`) and the packaging and tool tests (`test_*.py`) |
| `engine/` | The [GeneralsX engine fork](https://github.com/abhishekpradhan/warpowers-engine) compiled with Emscripten — Git submodule, GPL-3.0 with EA's additional terms |
| `dvijoke/` | Vendored `d8web` D3D8 → WebGL2 renderer — MIT |
| `licenses/` | Browser dependency inventory (`third-party.json`) and notice files |
| `docs/` | Vision, creative bible, roadmap, decision log, testing, engine notes, web bridge, art pipeline ([index](docs/README.md)) |
| `.github/` | Issue and pull-request templates; the CI, weekly WebAssembly build and release-deploy workflows |

## Contributing

Bug reports and feature requests go through the issue templates; questions are welcome as issues too. [CONTRIBUTING.md](CONTRIBUTING.md) has the toolchain, the build loop, the gate list and what a good pull request looks like. The [code of conduct](CODE_OF_CONDUCT.md) applies everywhere in the project, and vulnerabilities go through the [security policy](SECURITY.md), not public issues.

Good first areas:

- **Content** — unit rules, balance, maps and missions are data and generators (`data/`, `tools/`). Read the [creative bible](docs/creative.md) first, and never hand-edit a generated file.
- **Tools and tests** — Python 3 standard library and `node --test`, no packages; every tool is an `argparse` CLI.
- **Engine** — C++ in the [engine fork](https://github.com/abhishekpradhan/warpowers-engine); its [contributing guide](https://github.com/abhishekpradhan/warpowers-engine/blob/main/CONTRIBUTING.md) says where a change belongs and which fixtures to run.

Retail EA assets, extracted game data or anything derived from them never enter the repository, in any form.

## Roadmap

[docs/roadmap.md](docs/roadmap.md) says what ships today, what is being worked on (human playtests, the browser matrix, balance from match evidence) and what is deliberately out of scope: multiplayer, replays, mobile input, accounts and telemetry. The [decision log](docs/decisions.md) explains why. Notable changes are in [CHANGELOG.md](CHANGELOG.md).

## License and credits

Code in this repository is [MIT](LICENSE). Project-authored game content — models, textures, audio, maps, layouts, strings and INI data — is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); imported files keep their own licenses, recorded per file in [ASSETS.md](ASSETS.md) and credited in [CREDITS.md](CREDITS.md). The engine fork in `engine/` is GPL-3.0 with EA's additional terms, so the compiled browser game ships under the GPL together with its corresponding source; [LICENSING.md](LICENSING.md) maps the boundaries and obligations.

War Powers is not affiliated with or endorsed by Electronic Arts. No EA assets or game data are included, and EA names appear only to identify the engine's source lineage.
