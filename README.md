# War Powers (working title)

A free, browser-playable RTS in the Command & Conquer: Generals / Zero Hour idiom — built on the GPL-released engine lineage with **fully original replacement assets**, so players need no game files, no install, no launcher.

**Status:** Stage 0 — native engine bring-up on macOS. Nothing playable yet.

## Layout

- `docs/` — all planning and decisions
  - [brainstorm.md](docs/brainstorm.md) — original vision & nostalgia pillars (v0.1, partly superseded)
  - [port-vs-greenfield.md](docs/port-vs-greenfield.md) — the fork-vs-scratch trade study
  - [fork-plan.md](docs/fork-plan.md) — **the active plan**: base choice (§1a) + staged roadmap
  - [decisions.md](docs/decisions.md) — append-only decision log (D001–D008)
- `ASSETS.md` — asset provenance ledger (every asset, source, license)
- `engine/` — *not in this repo*: clone of [fbraz3/GeneralsX](https://github.com/fbraz3/GeneralsX) (GPL v3 + EA §7 terms) with `upstream` and `superhackers` remotes
- `data/` — our original game data (INI, maps) — the zero-retail dataset *(coming in Stage 1)*

## Hard rules

1. **No EA bytes.** No EA code copied into anything we author; no EA assets, INI text, or data files in any repo or deployment — ever. (One violation relicenses/poisons the project.)
2. **No EA trademarks** in branding — per the engine license's additional terms.
3. **Every asset has a ledger row** in `ASSETS.md` before it's used. Shipped assets: our own work, CC0, or CC-BY (with credit). Nothing else.
