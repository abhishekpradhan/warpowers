# Contributing to War Powers

War Powers is a desktop browser RTS with an original, swappable dataset.
Read [the vision](docs/vision.md), [creative direction](docs/creative.md)
and [current quality plan](docs/product-polish.md) before changing its scope.
The repository is being prepared for public collaboration; publication and
hosting still require the project owner's explicit decision.

## Build and check

Use Python 3.10+, Node.js 20+ for the dependency-free tests, CMake, Ninja,
and an activated Emscripten SDK. The current build is verified with
Emscripten 6.0.8. Blender is needed only to regenerate model/portrait art;
checked-in assets are sufficient to build and play.

```sh
git submodule update --init --recursive
cd engine
emcmake cmake --preset wasm
cmake --build build/wasm --target GeneralsXZH.js
cd ..
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 engine/scripts/qa/test-keyboard-modifiers.py
python3 tools/lint_voices.py
python3 tools/validate_gameplay.py
python3 tools/check_content.py
python3 tools/genwebstage.py
python3 tools/serve.py
```

Open http://localhost:8322. Start with Field Orientation from Operations.
Changes to data, the engine, or web sources need a new staging run; an
engine source change also needs a rebuild. Refresh the browser afterward.
The server is local-only and staging never publishes the game.
Reuse this server and URL across playtests. A different hostname or port has
separate browser storage; do not start a second server to work around an
already occupied port. Browser QA can use a separate browser profile instead.

## A useful change

Keep a patch focused on a player outcome. Describe the trigger, the changed
behavior, and the checks performed. A UI change needs a browser walkthrough;
a balance or map change needs a playable scenario, not only valid INI.
Report remaining uncertainties explicitly. Use existing diagnostic harnesses
as regression evidence, and identify when they inject state or force a win.

- Edit generators alongside generated outputs. Generate into the repository
  or an explicit scratch directory; native deployment is a separate action.
- Add readable tooltips, hotkeys and failure feedback for new commands.
- Every new asset needs provenance in [ASSETS.md](ASSETS.md). Update the
  machine-readable registry with `python3 tools/check_content.py --write-registry`.
- Never add retail game assets, extracted data, unlicensed downloads,
  credentials, personal save files, build trees, or local SDKs.
- Keep inherited notices. Root tooling is MIT; project content is CC BY 4.0;
  imported files retain their recorded license. Engine work follows
  [its contribution guide](engine/CONTRIBUTING.md) and license.
- Add meaningful tests where behavior can regress. Do not add heavyweight
  dependencies or hosted CI solely for a small change.

## Repository boundaries

The root repo contains the dataset, web shell and vendored browser renderer.
The engine is a separate Git submodule; its native DXVK fork is another.
Work on `codex/…` branches (or a clearly named contributor branch). Commit
and push changed child repositories before committing their updated gitlinks
in the parent. Push only to the intended `origin`; upstream mirrors are
fetch-only. See [WORKSPACE.md](docs/WORKSPACE.md).

Inherited GitHub Actions are disabled to avoid running unrelated, costly
upstream workflows. All required local commands are above. Enabling hosted
workflows or changing publication settings is a separate project decision.

## Reporting problems

Include the build identifier (Settings → Copy diagnostics), browser/OS,
mission/faction/difficulty, exact steps and observed result. Remove private
information before sharing a report. For save problems, say whether storage
was available and whether the game was upgraded since the save. Saves stay
on that browser/device and are version-checked; they are not cloud accounts.
