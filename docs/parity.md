# Bundled content and experience coverage

Updated 2026-09-05. War Powers targets a readable, complete two-faction RTS
experience on the ported engine. Matching another game's roster counts is
not the current release criterion. The owner-approved polish work extends
the original port-first baseline with supply, powers and authored missions.

| Area | Current implementation | Acceptance evidence required |
|---|---|---|
| Factions | Meridian Combine and Jackal Front; distinct power/economy/combat characteristics | Several viable openings and understandable counterplay |
| Vehicles | Builders, haulers, recon, gun truck, tanks and artillery | Every command, muzzle/turret, cargo and damage state exercised |
| Infantry | Four roles per faction: rifle, anti-armor, scout, heavy | Readable roles and animation; equal-budget counter encounters |
| Aircraft | Two per faction | Production, takeoff, attack, return and anti-air coverage |
| Structures | Headquarters, production, supply, technology and layered defense | Placement, queues, prerequisites, power, construction and destruction |
| Skirmish | Five layouts, each with both faction starts, three difficulties | Pathing, supply expansion, AI rebuilding, win/loss and replay |
| Authored content | Training + four campaign operations + two commander trials | Native objectives, deadlines, warnings, failure and unlock/replay |
| Powers | Precision Strike and Tunnel Ambush | Scouted targeting, warning/counterplay, effect and cooldown |
| HUD and help | Widescreen command bar, minimap, objective clock, field guidance, manual | Picking, queue cancel, control groups and readable overlays |
| Persistence | Device-local settings, mission record and checkpoint slot | Save → reload → resume; blocked storage and incompatible saves |
| Audio | Distinct unit voice pools, effects, ambience and six attributed tracks | Actual mix/listening pass; critical information also visible |
| Provenance | Original runtime models and textures, credited music/font imports | Generator/ledger consistency and staged notices |

`tools/validate_gameplay.py` independently decodes shipped map binaries and
checks mission branches, native script signatures, faction contracts,
paid AI responses and opening budgets. `tools/check_content.py` validates
model/texture/icon/window references and builds the asset registry.
`tools/lint_voices.py` checks distinct voice ownership. These complement,
rather than replace, browser and player verification.

Current art direction and roster names live in [creative.md](creative.md).
[ASSETS.md](../ASSETS.md) identifies actual per-file provenance. Suitable
openly licensed imports remain allowed; source history retains the earlier
prototype sourcing approach. A source mesh's availability does not establish
its license or permission to redistribute modified content.
