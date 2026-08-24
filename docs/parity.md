# Content parity — ZH skirmish experience vs the bundled pack

Companion to roadmap section 0 (D018). Parity target is the **skirmish
experience** (what wasm-generals players actually play), not the campaign.
Per class: where we are, the bar, and the **sourcing strategy** — because we
do not have to generate everything ourselves.

## Sourcing tiers (license-vetted 2026-08-24)

| Tier | What | License rule |
|---|---|---|
| **A. Generate** | Our pipeline: genw3d/gentex/gensfx/genmap/genwnd, Blender hero passes | ours, CC BY 4.0 |
| **B. Import CC0** | Kenney (models+audio+UI), Quaternius (proven in our pipeline), KayKit (characters **with rigs/animations**), itch.io CC0 tag, Poly Pizza; always through the retint/re-UV/bake pipeline so it looks native | CC0 → ships under our CC BY |
| **C. Import CC-BY** | Kevin MacLeod / incompetech (2000+ tracks, CC BY 4.0 — solves music), OpenGameArt CC0/CC-BY (e.g. military-orchestral tracks), Free Music Archive, freesound (CC0 filter) | attribution rows in ASSETS.md + CREDITS.md |
| **D. Community (post-publish)** | Nobody has built open replacement assets for the Generals GPL engine — OpenSAGE explicitly lists it as an unstarted "very long-term goal." **Our pack can be that project.** Publishing CC BY on a swappable data layer invites the OpenRA-style contribution dynamic | contributions accepted CC0/CC-BY only (ledger rule) |
| **✗ Unusable** | Classic C&C mods (EA-derivative, nearly all of them), Synty/paid packs, CC-BY-SA / NC / ND, GPL-licensed art (license mixing) | never |

## The matrix

| Class | ZH (approx) | Pack today | Parity bar (2 factions) | Source |
|---|---|---|---|---|
| Vehicles | ~12/faction ×3 | 7 total | 8/faction | A + B (military CC0 packs via conversion pipeline) |
| Infantry | ~7/faction | 2 total | 4/faction | B first (KayKit rigs → animation pipeline), then A |
| Aircraft | ~5/faction | 0 | 2/faction | A + B |
| Structures | ~13/faction | 7 total | 10/faction | A (Blender kit is strong here) |
| Unit animations | walk/attack/build/turret | turrets only | walk cycles, buildups | B (rigged CC0 chars) + Blender |
| Maps | ~40 MP | 2 (mirrored) | 8–10 varied | A (genmap: cheap; needs biome/layout variety) |
| Unit VO | ~10 lines/unit, acted | 4–7 lines/unit, synth | keep synth (D014), 8+ lines/unit | A (gensfx scales) |
| EVA/announcer | full set | 6 events | +unit-ready, +superweapon set later | A |
| Music | ~30 tracks | 1 stub loop | 6–8 track rotation | **C (CC-BY solves this)** |
| SFX | hundreds | ~12 | ~40 | A + B (Kenney audio CC0, freesound CC0) |
| Shell UI | full menu suite | page-as-menu + result banners | roadmap §0 | A (genwnd) |
| General powers | 15+/faction | 0 | parked (D018) | A |
| Superweapons | 3 | 0 | parked (D018) | A |
| AI | 3 difficulties | scripted opponent | parked (D018) | A |
| Balance | 20 yrs of patches | first-pass numbers | playtested self-consistency | playtesting |

## How the gap actually closes

1. **The engine is ~half the nostalgia** (feel, controls, construction,
   combat rhythm) and it's already ours.
2. **Tooling makes breadth cheap** — a new unit (model, texture, portrait,
   voice set, INI) is hours, not days; lints keep it shippable.
3. **CC0/CC-BY imports cover the expensive classes** — rigged characters
   (animations!), music, SFX bulk.
4. **Community finishes the tail** — post-publish, position the pack as
   *the* open asset replacement for the Generals GPL engine; the niche is
   explicitly empty and named as a community wish.
