# War Powers — Licensing

The licensing map for the whole project. War Powers ships as a collection of
individually licensed files (policy D019: legality is the only exclusion bar —
our terms flex to fit what we legally use, not the other way around).

Authority chain: **ASSETS.md** is the authoritative per-file license ledger,
**CREDITS.md** carries the attributions, and this file explains the tiers and
how they fit together. Four tiers: our code, our content, imported content,
and the code we ship from others.

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

## 3. Imported content — keeps its upstream license, per file

Third-party assets ship under whatever license they came with, tracked
per-file in ASSETS.md. Adaptations we make of an import carry the import's
license where that license requires it (CC BY-SA and GPL do; CC0 adaptations
ship under our CC BY 4.0). A ShareAlike or GPL file never affects any sibling
file — a collection is not a derivative work.

Acceptable inbound: CC0/public domain, CC BY, CC BY-SA, GPL-licensed art,
SIL OFL (fonts). Not acceptable: EA-derived content in any form (unlicensed
derivative works — this is the rule that makes "no game files needed" legal),
unlicensed assets, and ND-encumbered assets (the style pipeline modifies
everything; ND bars derivatives). NC only by explicit per-case decision
recorded in the ledger (NC permanently bars commercial use of that asset).

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

`GeneralsXZH.wasm/.js` compiles together the GPL engine, the MIT d8web layer,
and emscripten's MIT runtime — MIT is GPL-compatible, so the **combined
binary is distributed under GPL-3.0** while the MIT files themselves stay
MIT. When the game is deployed publicly, the corresponding source for that
binary is the public engine repo plus the vendored `dvijoke/` in the public
workspace (publish-checklist §6 makes both public at go-time).

The game data files ride *alongside* the binary under their own per-file
licenses: the GPL engine executes game data the way a compiler runs a
program — data is not linked into, compiled into, or derived from GPL code,
so the content tiers are untouched by the engine's GPL, and symmetrically a
GPL-licensed art file in the data set would not touch the MIT/CC files
beside it. One nuance is recorded in the ledger: our WND files follow a file
*format* learned from a GPL example file; formats are not copyrightable and
the content is original.
