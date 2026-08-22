# Creative bible

The taste document. Factions, naming, art, and audio all answer to this and to
[vision.md](vision.md)'s pillars (readable chaos; keep the fantasy, not the
jank). Decisions herein: D014.

## The war

A near-future proxy conflict over the **Meridian Strip** — a resource corridor
nobody's map agrees on. Three powers fight it, none of them named after a real
nation, all of them satire of a real way of waging war. The game's name is the
joke: everyone involved claims emergency *war powers*; nobody declared war.

## The trio

| | **Meridian Command** | **Jackal Front** | **Iron Pact** *(third)* |
|---|---|---|---|
| Fantasy | PR-managed superpower warfare | improvised guerrilla war economy | industrial mass and momentum |
| Satire | branded, networked, deniable | scrap-and-salvage ingenuity | propaganda-broadcast collectivism |
| Economy | expensive, few, excellent | cheap, fragile, everywhere | mid-cost, scales with mass |
| Power | deeply grid-dependent | **needs no power** | over-built grid, slow to start |
| Presence | concentrated, surgical | dispersed, ambush, tunnels | one big rolling front |
| Silhouette | angular, elevated, antennae/wings | asymmetric, welded, tarps, mismatched | low, wide, riveted slabs |
| Palette | steel `#B8C2CC` / white `#E8ECF0` | sand `#C9B08A` / rust `#8A5A3C` | graphite `#4A4E55` / charcoal `#2E3138` |
| Trim | signal gold `#D7B45A` | oxide green `#6F8F5A` | vermilion `#C3442E` |

Build order: **Meridian + Jackal first** (maximum asymmetry per match), Iron
Pact after the two-faction game is polished.

Trim colors differ in lightness, not just hue (colorblind-safe). Every unit
also carries a **player-color region** distinct from faction trim. Terrain
stays desaturated; units own the saturation.

## Naming rules

- **Never** an EA/C&C unit, structure, faction, or general name (Ranger,
  Crusader, Paladin, Raptor, Rebel, Technical, Scorpion, Battlemaster, Red
  Guard, Conscript, Stinger Site, …). When in doubt, search the C&C wiki
  before adopting a name.
- Generic military terms are fine (Barracks, Supply Depot, Command Center).
- Meridian units sound corporate-geometric (Vector, Zenith, Outrider).
  Jackal units sound scrappy-zoological (Vulture, Mongrel, Hornet).
  Iron Pact units sound heavy-mechanical (Ram, Anvil, Piston).
- Formal trademark pass on everything pre-public (D006).

## Slice rosters

### Meridian Command
| Role | Name | Notes |
|---|---|---|
| Builder | **Fabricator** | hover dozer, printing-scaffold build FX later |
| Gatherer | **Porter** | supply drone |
| Rifle infantry | **Warden** | |
| AT infantry | **Lancer** | dodgeable missile |
| MBT | **Vector** | the poster unit; raised chassis, gold canopy |
| Recon | **Outrider** | fast drone, sight range |
| Support | **Zenith** | artillery, arcing shells |
| Structures | Command Center, **Power Array**, Barracks, Vehicle Plant, Supply Depot, **Bulwark** turret | grid-dependent |

### Jackal Front
| Role | Name | Notes |
|---|---|---|
| Builder | **Rigger** | welded half-truck |
| Gatherer | **Scavenger** | |
| Rifle infantry | **Irregular** | cheap, fast |
| AT infantry | **Tankbuster** | |
| Gun truck | **Vulture** | fast raider, the faction icon |
| Tank | **Mongrel** | cheap, mismatched armor plates |
| Support | **Hornet** | rocket buggy, area saturation |
| Structures | Command Post, Hideout (barracks), **Chop Shop** (factory), Salvage Yard (supply), Watchpost (defense) | **no power structure** |

First **general powers** after the slice (the namesake mechanic): Meridian
*Precision Strike* (target beacon, air-delivered) vs Jackal *Tunnel Ambush*
(spawn a squad from anywhere previously scouted).

## Art spec

- Low-poly faceted: units **300–800 tris**, structures **500–1500**.
- **Palette atlas** texturing: one shared 64×64 swatch texture; every model
  UVs onto flat swatches (faction colors, trims, neutrals). No painted
  textures; identity from silhouette + palette (vision pillar 3).
- Hierarchy: W3D HLod with named subobjects (hull/turret/barrel) so turrets
  can traverse later.
- Two pipelines: `tools/genw3d.py` **part-language** for procedural slice
  models (reproducible, fast iteration), Blender + OpenSAGE plugin for
  hand-crafted heroes once validated (spike pending).
- VFX language: short-lived, high-contrast, silhouette-preserving; faction
  tinted (gold tracers vs green rocket trails).

## Audio identity

- **Score**: percussive industrial-orchestral. Meridian twist: synthetic
  pulses. Jackal twist: hand percussion, detuned strings. Interim tracks from
  CC-BY libraries (ledger rows), originals later.
- **VO**: *processed radio barks* (D014). Short phrases, any voice, through a
  fixed chain: band-pass ~300 Hz–3 kHz, saturation, squelch tail. Personality
  in writing, not casting: Meridian crisp and corporate ("Copy. Moving."),
  Jackal loose and wry ("Yeah yeah, going.").
- **Announcer**: same processing, neutral-ops tone ("Unit lost." "Power
  restored.").
- **UI**: tactile clicks, radar pings, low thud on build-complete.
