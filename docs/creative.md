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

| | **Meridian Combine** | **Jackal Front** | **Iron Pact** *(third)* |
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

## Current playable roster

`data/Data/Generals.str` supplies display names; object and command-set INI
files supply the authoritative available roster. Iron Pact remains internal.

| Role | Meridian Combine | Jackal Front |
|---|---|---|
| Builder / supply | Fabricator / Porter | Rigger / Scavenger |
| Rifle / anti-armor | Warden / Lancer | Scrapper / Sting |
| Scout / heavy infantry | Vigil / Bastion | Prowler / Bruiser |
| Armor / mobile fire support | Vector / Outrider / Zenith | Mongrel / Vulture |
| Aircraft | Kestrel / Shrike | Buzzard / Gnat |
| Economic identity | Larger cargo loads, precise costly armor, vulnerable power grid | Smaller fast supply runs, cheaper raiders, power-independent infrastructure |
| Signature | Directorate Precision Strike, visible warning beacon | Den Tunnel Ambush, mixed infantry reinforcement at scouted ground |

Both sides build supply hubs and protect physical haulers. Caches are finite;
contested lateral supplies create reasons to leave the starting base. Small
hub income supports recovery but does not replace a protected supply route.
Power, affordability, counter matchups and timings are gameplay contracts
checked by `tools/validate_gameplay.py`; final balance needs player evidence.

## Production art specification

Painted, stylized low-poly models are the standard. The current production
source is Blender and `tools/blender/`; the primitive part language remains
useful for rigs, effects, scaffolds and utility assets. Historical swatch-only
rules are superseded. Git history preserves earlier specifications.

- Readability at the actual RTS camera comes first. Recon reads as a scout
  car; the gun truck has an exposed weapon bed; infantry roles differ by
  silhouette, weapon and shoulder/pack shapes.
- Vehicles use textured hulls and distinct **HOUSECOLOR** mesh regions for
  ownership. Use named `TURRET` pivots and turret-relative `MUZZLE` attachments
  where the weapon traverses. Cargo vehicles use a separate `CARGO` mesh.
- Shared `WPINF1` infantry hierarchy preserves compatible walk, idle and
  fire animation. New lifecycle states must be wired in the object's draw
  block, not merely exported as unused files.
- New unit textures normally use 512-square painted atlases; small props
  use 256. Portraits render the runtime W3D model with consistent lighting,
  framing and background, then pack into the two command sheets.
- Model budgets are role-based and recorded with bounds/dependencies in
  `data/asset-registry.json`. The hard validator ceiling is 12,000 triangles;
  simple props should remain far below it. This is a ceiling, not a target.
- Terrain stays subdued with clear routes, supply sites, rubble and industrial
  landmarks. Units and order feedback own the strongest contrast.
- Effects must preserve silhouettes and explain direction, impact, damage
  and destruction. Test firing/construction/damage in the engine as well as
  close-up source renders. Do not mark an asset approved from a render alone.

See [ASSETS.md](../ASSETS.md) for provenance and the generator contracts in
`tools/blender/polish_assets.json`. Changing a production asset requires
updating its source and generated outputs together; legacy generators must
not silently replace it.

## Operations and tone

Field Orientation teaches commands, supply, production, scouting and the HQ
objective. The four-operation campaign alternates viewpoints through First
Light, Cut the Wire, The Long Watch and War Powers. Each has a specific tactical
pressure: establish a foothold, sabotage dispersed targets, hold a relay,
and dismantle defenses before a final assault. Commander trials add timed
holds and aggressive deadlines. `data/operations.json` owns briefings,
objective hints, unlocks and debrief writing; `tools/genmap.py` owns native
mission triggers. Validate both together.

Commanders speak through concise operational messages, with institutional
confidence or improvised pragmatism. Avoid lengthy interruption, real-world
national caricatures and lore that obscures the immediate order. Objectives
and warning timers must remain visible without relying on audio.

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
