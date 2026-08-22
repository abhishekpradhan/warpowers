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

1. **No EA asset or data bytes ever ship** — no EA art, audio, INI text, maps, or archive contents in any repo or deployment. EA never granted redistribution rights to anyone; this rule is what makes "no files needed" legal. (GPL *code* from the engine lineage and its ports is fine to copy/adapt — the project is a GPL fork — with provenance noted in commits.)
2. **No EA trademarks** in branding — per the engine license's additional terms.
3. **Every asset has a ledger row** in `ASSETS.md` before it's used. Shipped assets: our own work (CC BY-SA 4.0), CC0, CC-BY, or CC-BY-SA (with credit). Nothing else.
