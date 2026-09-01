# War Powers — Licensing

**The whole story in one sentence: everything in this repository is free to
reuse with attribution — MIT code, CC BY 4.0 content, CC0/OFL imports — and
the only copyleft in the project is the engine, which lives in its own GPL
repository and is what the compiled game ships under.**

Authority chain: **[ASSETS.md](ASSETS.md)** is the authoritative per-file
license ledger, **[CREDITS.md](CREDITS.md)** carries the attributions, and
this file is the map. Policy: D019 (per-file licensing; legality is the only
exclusion bar) as narrowed by D022 (permissive-only workspace) — see
[docs/decisions.md](docs/decisions.md).

## 1. Our code — MIT

Everything authored in this repository that is code, tooling, or
documentation — `tools/`, `web/`, build/generator scripts, `docs/` — is MIT
licensed (see [LICENSE](LICENSE)).

## 2. Our content — CC BY 4.0

All original War Powers game content — models, textures, audio, maps, UI
layouts, strings, and the INI data set under `data/` — is licensed under
**Creative Commons Attribution 4.0 International (CC BY 4.0)** unless a row
in ASSETS.md says otherwise.

- Full text: https://creativecommons.org/licenses/by/4.0/legalcode
- Attribution: "War Powers project", linking to the project repository once
  public.

## 3. Imported content — permissive-with-attribution, per file

Imports ship under whatever license they came with, tracked per-file in
ASSETS.md and credited in CREDITS.md. Pre-approved inbound licenses (D022):
**CC0 / public domain, CC BY, SIL OFL** — the same
permissive-with-attribution family as our own terms, so imports never change
what a reuser may do with the collection. Adaptations of CC0 sources ship
under our CC BY 4.0.

Anything outside that family — ShareAlike, GPL-licensed art, NC — requires a
fresh decision-log entry *before* import (none has ever been needed). Never
acceptable regardless: EA-derived content in any form (unlicensed derivative
works — the rule that makes "no game files needed" legal), unlicensed
assets, and ND-encumbered assets (the style pipeline modifies everything;
ND bars derivatives).

Current imports (complete as of 2026-08-31; the ledger is the authority):

| Import | License | Notes |
|---|---|---|
| Music — six tracks by Kevin MacLeod (incompetech.com) | **CC BY 4.0** | Re-encoded/trimmed for the web build; attribution in CREDITS.md |
| Quaternius model packs (`refs/quaternius-tanks/`) | **CC0 1.0** | Conversion sources only; our adaptations ship under CC BY 4.0 |
| Liberation Sans (`data/Fonts/`) | **SIL OFL 1.1** | License at `data/Fonts/LICENSE-LiberationFonts` |

## 4. Code we ship from others

- `engine/` (submodule; our GeneralsX fork): **GPL-3.0 with EA's additional
  terms** — from Electronic Arts' 2025 source release of the Generals engine
  (full terms in `engine/LICENSE.md`). Our engine modifications are GPL-3.0.
- `dvijoke/` (vendored inline, upstream meerzulee/dvijoke): **MIT** — the
  D3D8→WebGL2 layer the web build compiles in. Carries its own copyright
  notice and license text at `dvijoke/LICENSE` (decision D020).
- DXVK fork (engine submodule, `engine/references/fbraz3-dxvk`): **zlib** —
  used only by the native macOS development build; never part of the web
  bundle.

## What the shipped web bundle is, license-wise

`GeneralsXZH.wasm/.js` compiles together the GPL engine, the MIT d8web
layer, and emscripten's MIT runtime — MIT is GPL-compatible, so the
**combined binary is distributed under GPL-3.0** while the MIT files
themselves stay MIT. When the game is deployed publicly, the corresponding
source for that binary is the public engine repo plus the vendored
`dvijoke/` in the public workspace (publish-checklist §6 makes both public
at go-time).

The game data files ride *alongside* the binary under their own per-file
licenses: the GPL engine executes game data the way a compiler runs a
program — data is not linked into, compiled into, or derived from GPL code,
so the content tiers are untouched by the engine's GPL. One nuance is
recorded in the ledger: our WND files follow a file *format* learned from a
GPL example file; formats are not copyrightable and the content is original.
