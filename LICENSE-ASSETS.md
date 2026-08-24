# Licensing

War Powers uses the most permissive licenses its dependency chain allows,
in a two-tier scheme chosen for clarity:

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
were relicensed to CC BY 4.0 by their sole author. No third-party ShareAlike
inputs exist in the tree (see the ledger), so nothing forces the SA clause.*

## Third-party inputs (unchanged)
- Quaternius model packs: **CC0 1.0** (conversion sources; adaptations ship
  under our CC BY 4.0)
- Liberation Sans: **SIL OFL 1.1** (license file alongside the font)

## The engine chain (upstream licenses; not ours to change)
- `engine/` (GeneralsX fork): **GPL-3.0** — inherited from EA's source
  release. Our engine modifications are GPL-3.0.
- dvijoke / d8web (D3D8→WebGL2 layer): **MIT** (upstream license).
- DXVK fork: **zlib** (upstream license).

## Why this is harmonious
The GPL engine *executes* our data and content the way a compiler runs a
program: game data is not linked, compiled in, or derived from GPL code, so
the CC/MIT tiers are unaffected by the engine's GPL. One nuance is recorded
in the ledger: our WND files follow a file *format* learned from a GPL
example file; formats are not copyrightable and the content is original.
