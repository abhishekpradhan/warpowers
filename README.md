# War Powers (working title)

A free, browser-playable RTS in the Command & Conquer: Generals / Zero Hour
idiom — built on the GPL-released engine lineage with **fully original
replacement assets**, so players need no game files, no install, no launcher.

**Direction (D018):** port-parity first — the product is the browser port
(the wasm-generals experience minus the "supply your own game files"
requirement); our content is the bundled default asset pack on a swappable
data layer. **Status:** full matches run in the browser on 100% original
data (base-building, combat, fog of war, win/lose, audio, two factions);
current work is the port surface (in-engine shell, boot time, QoL) and
content toward the parity bar ([docs/parity.md](docs/parity.md)).

**Licensing (D019):** per-file; legality is the only exclusion bar.
- Our code: **MIT** ([LICENSE](LICENSE)) · our content: **CC BY 4.0**
- Imports keep their upstream license (CC0/CC-BY/CC-BY-SA/GPL art/OFL),
  tracked per-file in [ASSETS.md](ASSETS.md)
- Engine chain: GPL-3.0 (engine fork) / MIT (dvijoke) / zlib (DXVK fork) —
  see [LICENSE-ASSETS.md](LICENSE-ASSETS.md)

## Layout

See [docs/WORKSPACE.md](docs/WORKSPACE.md) for the full map. Short version:

- `data/` — the complete original game dataset (INI, maps, art, audio, UI)
- `tools/` — generators and gates (models, textures, SFX/VO, maps, WND
  layouts, web staging, lints); `tools/blender/` hero-asset pipeline
- `web/` — the browser boot page
- `docs/` — vision, roadmap, decisions log, engine notes, parity matrix
- `engine/` — **submodule**: our GPL fork of the GeneralsX engine lineage
- `dvijoke/` — **vendored inline** (MIT, upstream meerzulee/dvijoke): the
  D3D8→WebGL2 layer the wasm build compiles in; carries its own LICENSE
- clone with `git clone --recursive`; build recipes in
  [docs/engine-notes.md](docs/engine-notes.md)

## Hard rules

1. **No EA asset or data bytes ever ship** — no EA art, audio, INI text,
   maps, or archive contents in any repo or deployment. EA never granted
   redistribution rights; this rule is what makes "no files needed" legal.
   (GPL *code* from the engine lineage is fine — the project is a GPL fork.)
2. **No EA trademarks** in branding — per the engine license's additional
   terms.
3. **Every asset has a ledger row** in [ASSETS.md](ASSETS.md) before it's
   used, with its license (per-file licensing per D019).
4. **Private until polished** — nothing deploys or publishes without an
   explicit go.
