#!/usr/bin/env python3
"""War Powers web staging: assemble a static dir that serves the wasm build.

Layout produced:
  stage/
    index.html            (boot harness; fetches the manifest, stages MEMFS)
    GeneralsXZH.js/.wasm  (engine build)
    gamedata/...          (our loose dataset, copied from the game dir)
    gamedata/manifest.json
    fonts/default.ttf     (Liberation Sans, OFL — fontconfig stub target)

Serve with any static server, e.g.:  python3 -m http.server -d stage 8080
"""
import json
import os
import shutil
import datetime
import subprocess
import sys

# data-quality gates: a failed lint fails the stage
subprocess.run([sys.executable,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lint_voices.py')],
               check=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Stage game data from the REPO (data/ is the single source of truth for the
# web build). The native runtime dir (~/GeneralsX/GeneralsZH) is a deploy
# TARGET synced from data/, never a staging source - staging from it shipped
# five-day-old data once (engine-notes, 2026-08-31).
GAME = os.path.join(ROOT, "data")
BUILD = os.path.join(ROOT, "engine", "build", "wasm", "GeneralsMD")
STAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "webstage")

DATA_DIRS = ["Data", "Maps", "Art", "Window"]

os.makedirs(STAGE, exist_ok=True)

# engine build artifacts
for f in ["GeneralsXZH.js", "GeneralsXZH.wasm"]:
    src = os.path.join(BUILD, f)
    if not os.path.exists(src):
        sys.exit(f"missing build artifact: {src} — build the wasm target first")
    shutil.copy2(src, os.path.join(STAGE, f))

# game data — manifest entries carry byte sizes for byte-accurate progress
manifest = []
dst_root = os.path.join(STAGE, "gamedata")
shutil.rmtree(dst_root, ignore_errors=True)
for d in DATA_DIRS:
    for dirpath, _, files in os.walk(os.path.join(GAME, d)):
        for fn in files:
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, GAME)
            dst = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
            manifest.append({"p": rel, "s": os.path.getsize(full)})
manifest.sort(key=lambda e: e["p"])
with open(os.path.join(dst_root, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=0)

# font for the wasm fontconfig stub
os.makedirs(os.path.join(STAGE, "fonts"), exist_ok=True)
shutil.copy2(os.path.join(ROOT, "data", "Fonts", "LiberationSans-Regular.ttf"),
             os.path.join(STAGE, "fonts", "default.ttf"))

# boot page
# stage the page with a build stamp injected (staging time + engine wasm mtime)
# so "which build is this session running" is answerable at a glance
wasm_mtime = os.path.getmtime(os.path.join(STAGE, "GeneralsXZH.wasm"))
stamp = "staged %s / engine %s" % (
    datetime.datetime.now().strftime("%m-%d %H:%M"),
    datetime.datetime.fromtimestamp(wasm_mtime).strftime("%m-%d %H:%M"))
page = open(os.path.join(ROOT, "web", "index.html")).read()
badge = ('<div style="position:fixed;right:8px;bottom:6px;font:10px monospace;'
         'color:#5a616c;z-index:9;pointer-events:none">' + stamp + '</div>'
         '<script>console.log("[build] ' + stamp + '")</script></body>')
page = page.replace("</body>", badge)
with open(os.path.join(STAGE, "index.html"), "w") as f:
    f.write(page)

total = sum(os.path.getsize(os.path.join(dp, f))
            for dp, _, fs in os.walk(STAGE) for f in fs)
print(f"staged {len(manifest)} data files -> {STAGE} ({total/1048576:.1f} MB total)")
