# Content tooling

Every generator, validator and helper that produces or checks the files under
`data/`. All of it is Python 3.10+ standard library: there are **no
third-party Python packages** to install. The Blender scripts additionally use
`bpy`, `bmesh` and `mathutils`, which only exist inside Blender.

Conventions: every script is an `argparse` CLI with a `main()` guarded by
`__main__`; nothing runs at import time; a generator writes into the
repository `data/` only when that is its documented purpose, and then always
has a `--data`/`--out`/`OUTPUT` override. Faction names are the Meridian
Combine and the Jackal Front.

## Tools

"Writes data/ by default" means running the script with no arguments changes
files under the repository `data/` tree.

| Script | Reads | Writes | Writes data/ by default? |
|---|---|---|---|
| `check_content.py` | `data/` INI, WND, W3D, textures, `Generals.str`, `operations.json`; `blender/polish_assets.json` | Report on stderr; `data/asset-registry.json` only with `--write-registry` | No (only with the flag) |
| `validate_gameplay.py` | `data/Maps/**/*.map`, INI, `operations.json`; `engine/.../ScriptEngine.cpp` (`--engine`) | Report | No |
| `lint_voices.py` | `Object.ini`, `SoundEffects.ini`, `data/Data/Audio/Sounds/*.wav` | Report | No |
| `genmap.py` | `data/operations.json` | `data/Maps/<Name>/<Name>.map` (17 with `--all`) | Yes (`--out DIR`, or an explicit `OUTPUT.map`) |
| `genwnd.py` | nothing | 11 `.wnd` layouts under `data/Window/` | Yes (`--out DIR`) |
| `gentex.py` | nothing | `data/Art/Terrain/{wp_ground,wp_ground_ash,wp_concrete}.tga`; `data/Art/Textures/` sprites (`shadow`, `wp_glow`, `wp_soft`, `wp_rallyline`, `wp_icons`, `EXScorch01`), the 11 engine-required placeholders, `wp_sky`, `wp_water`, `wp_box` | Yes (`--data DIR`) |
| `gencmdicons.py` | nothing | `data/Art/Textures/wp_cmdglyphs.tga` | Yes (`--data DIR` or `--out FILE`) |
| `genstatic.py` | `web/static/favicon.svg` | `web/static/` PNG icons (32/180/192/512) and `favicon.ico`; `--check` reports stale icons | No (writes `web/static/`) |
| `gentactical.py` | `data/Maps` | `data/Art/Textures/wp_map_previews.tga`, `MappedImages/HandCreated/WPMapPreviews.ini` | Yes (`--data DIR`) |
| `genportraitsheet.py` | `SOURCE/WPIco*.tga` renders from `blender/render_roster.py` | `data/Art/Textures/wp_cmdicons{,2}.tga`, `WPCmdIcons{,2}.ini` | Yes (`--data DIR`) |
| `genw3d.py` | `blender/polish_assets.json` (name-collision check) | 11 utility models in `data/Art/W3D/` (projectiles, markers, scaffolds, boot-slice troopers) | Yes (`OUTPUT_DIR`) |
| `genrig.py` | nothing | `data/Art/W3D/wpinf1*.w3d` (shared infantry skeleton + 4 animations) | Yes (`OUTPUT_DIR`) |
| `gensfx.py` | eSpeak NG binary | `data/Data/Audio/Sounds/*.wav` | Yes (`--data DIR`, optional `--runtime DIR`) |
| `optimize_art.py` | `data/Art/**/*.tga`, `blender/polish_assets.json` | Rewrites TGAs in place (RLE, alpha drop, contracted atlas halving) | Yes (`--data DIR`; `--check` writes nothing) |
| `genwebstage.py` | `data/`, `web/`, `licenses/`, the wasm engine build (`--build-dir`) | A content-addressed release in `webstage/` (or `DESTINATION`) | No (`webstage/` is not under `data/`) |
| `serve.py` | a staged `webstage/` | nothing | No |
| `tgadiff.py` | two `WP_FRAME_DUMP` TGAs | Report | No |
| `wp_tga.py`, `wp_w3d.py`, `w3dhierarchy.py` | libraries: TGA read/write, W3D chunk framing, pivot canonicalisation | — | — |
| `blender/build_polish.py` | `polish_assets.json`, `support_kit.py`, `base_kit.py` | 54 catalog models: `data/Art/W3D/*.w3d`, raw bakes in `data/Art/Textures/wp_*.tga`, portraits + manifest in `--review`; refreshes `polish_assets.json` only when `--data` is the repository `data/` | Yes (`--data DIR`; `--only a,b`; `--check` writes nothing) |
| `blender/render_roster.py` | `data/` models, textures, `Object.ini` | `WPIco*.tga` portraits in `--out` (default `/tmp/warpowers-portraits`) | No |
| `blender/render_menu.py` | `build_polish.py` model kit | `data/Art/Textures/wp_menu.tga`, `WPMenuArt.ini`, a JPEG contact in `--review` | Yes (`--data DIR`) |
| `blender/_bootstrap.py`, `wp_pipeline.py`, `support_kit.py`, `base_kit.py` | libraries: plugin registration and `--` args; modeling kit, bake and composite; support-kit and base-kit geometry with their ownership-panel contracts | — | — |

Raw bakes are written at `bake_size`; run `optimize_art.py` afterwards to
produce the committed form (`texture_size`, RLE, top-left origin). Every
Python-only generator already writes its committed form directly.

## External binaries

- **Blender 5.x** (verified with 5.2.0 LTS) with the **OpenSAGE Blender
  plugin** (0.7.4) from the engine checkout at
  `engine/references/OpenSAGE.BlenderPlugin`. It is a git submodule:
  `git submodule update --init --recursive`. The scripts register the plugin
  themselves; nothing needs to be installed into Blender's preferences.
  macOS locations: `/opt/homebrew/bin/blender` or
  `/Applications/Blender.app/Contents/MacOS/Blender`.
- **eSpeak NG** (`espeak-ng`), only for `gensfx.py`. Found via `--espeak PATH`,
  then `$ESPEAK_NG`, then `PATH`, then `/opt/homebrew/bin/espeak-ng`.

## Headless Blender

Always pass `--factory-startup` so user preferences and add-ons cannot change
the result; script arguments follow `--`.

```sh
BLENDER=/opt/homebrew/bin/blender
# All 54 catalog models into data/ (raw bakes; then optimize_art.py):
$BLENDER --background --factory-startup --python tools/blender/build_polish.py -- --data data --review /tmp/warpowers-art-review
# A bounded set, or a no-write reproducibility check against the committed files:
$BLENDER --background --factory-startup --python tools/blender/build_polish.py -- --only merout01,wprock01 --check
# Portraits, then the two command sheets:
$BLENDER --background --factory-startup --python tools/blender/render_roster.py -- --data data --out /tmp/warpowers-portraits
python3 tools/genportraitsheet.py /tmp/warpowers-portraits --data data
# Main-menu panorama:
$BLENDER --background --factory-startup --python tools/blender/render_menu.py -- --data data --review /tmp/warpowers-art-review
python3 tools/optimize_art.py --data data
```

## Full regeneration order

```sh
python3 tools/genmap.py --all
python3 tools/gentactical.py --data data
python3 tools/genwnd.py
python3 tools/gentex.py
python3 tools/gencmdicons.py
python3 tools/genrig.py
python3 tools/genw3d.py
# Blender steps above, then:
python3 tools/optimize_art.py --data data
python3 tools/check_content.py --write-registry
```

## Gates and tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/lint_voices.py
python3 tools/validate_gameplay.py
python3 tools/check_content.py
python3 tools/optimize_art.py --check
python3 -W error -m py_compile tools/*.py tools/blender/*.py
python3 tools/genwebstage.py /tmp/webstage-check   # runs the three content gates itself
```

`genwebstage.py` needs `engine/build/wasm/GeneralsMD/GeneralsXZH.{js,wasm}`
(or `--build-dir`).

## What is byte-reproducible

Verified on 2026-09-07 (macOS arm64, Python 3.14, Blender 5.2.0 LTS, CPU
Cycles) by regenerating into a scratch directory and comparing with the
committed files; the `build_polish.py` row was re-verified on 2026-09-08 after
the seven base-kit models joined the catalog:

| Generator | Result |
|---|---|
| `genmap.py --all` | 17/17 maps identical |
| `genwnd.py` | 11/11 layouts identical |
| `gentex.py` | 23/23 files identical (terrain, sprites, placeholders) |
| `gencmdicons.py`, `gentactical.py` | identical (sheet and INI) |
| `genw3d.py`, `genrig.py` | 11/11 and 5/5 models identical |
| `check_content.py --write-registry` | fixed point (registry unchanged) |
| `optimize_art.py --check` | nothing to rewrite |
| `build_polish.py --check` | 54/54 models: W3D and optimized TGA identical (includes the seven base-kit models, whose pre-catalog exports were not reproducible) |
| `render_roster.py` + `genportraitsheet.py` | both sheets and both INIs identical |
| `render_menu.py` + `optimize_art.py` | `wp_menu.tga` and `WPMenuArt.ini` identical |
| `gensfx.py` | **not** reproducible: eSpeak NG output depends on its version and voice data (the DSP sounds are seeded and stable) |

Equality across other Blender versions, GPU renderers or operating systems is
not promised for any Blender output.
