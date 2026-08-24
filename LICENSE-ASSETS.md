# Licensing

War Powers ships as a collection of individually licensed files (D019:
legality is the only exclusion bar — our terms flex to fit what we legally
use, not the other way around). Three tiers:

## Our code — MIT
Everything authored in this repository that is code or tooling — `tools/`,
`web/`, build/generator scripts, and documentation — is MIT licensed (see
`LICENSE`).

## Our content — CC BY 4.0
All original War Powers game content — models, textures, audio, maps, UI
layouts, strings, and the INI data set under `data/` — is licensed under
**Creative Commons Attribution 4.0 International (CC BY 4.0)** unless a row
in ASSETS.md says otherwise.

Full text: https://creativecommons.org/licenses/by/4.0/legalcode
Attribution: "War Powers project", linking to the project repository once
public.

*Relicensing note (2026-08-23): content rows previously marked CC BY-SA 4.0
were relicensed to CC BY 4.0 by their sole author.*

## Imported content — keeps its upstream license, per file
Third-party assets ship under whatever license they came with; **ASSETS.md is
the authoritative per-file license map** and CREDITS.md carries the credits.
Acceptable inbound licenses: CC0/public domain, CC-BY, CC-BY-SA, GPL-licensed
art, SIL OFL (fonts). Adaptations we make of an import carry the import's
license where that license requires it (BY-SA and GPL do; CC0 adaptations
ship under our CC BY 4.0). A ShareAlike or GPL file does not affect any
sibling file — collection ≠ derivative work.

Current imports:
- Quaternius model packs: **CC0 1.0** (conversion sources; adaptations ship
  under our CC BY 4.0)
- Liberation Sans: **SIL OFL 1.1** (license file alongside the font)

Not acceptable: EA-derived content in any form (unlicensed derivative works
— this is the rule that makes "no game files needed" legal), unlicensed
assets, ND-encumbered assets (the style pipeline modifies everything; ND bars
derivatives). NC assets only by explicit per-case decision recorded in the
ledger (NC permanently bars commercial use of that asset).

## The engine chain (upstream licenses; not ours to change)
- `engine/` (GeneralsX fork): **GPL-3.0** — inherited from EA's source
  release. Our engine modifications are GPL-3.0.
- dvijoke / d8web (D3D8→WebGL2 layer): **MIT** (upstream license).
- DXVK fork: **zlib** (upstream license).

## Why this is harmonious
The GPL engine *executes* game data the way a compiler runs a program: data
is not linked, compiled in, or derived from GPL code, so the content tiers
are unaffected by the engine's GPL — and symmetrically, a GPL-licensed art
file in the data set does not touch the MIT/CC files beside it. One nuance
is recorded in the ledger: our WND files follow a file *format* learned from
a GPL example file; formats are not copyrightable and the content is
original.
