# War Powers — product polish plan

Assessment baseline: 2026-09-04. The owner authorized implementing this plan, including preparing and pushing the private source repositories, later that day. This document records the problems and intended acceptance bar; [roadmap.md](roadmap.md) tracks current implementation and [publish-checklist.md](publish-checklist.md) tracks verified release readiness. Baseline observations below describe the pre-polish build, not current feature availability.

## Product direction

The existing objectives are sufficiently clear: deliver the classic Generals-style RTS experience through a browser link, with no supplied game files, a polished modern interface, readable battles and independently shippable content. Keep the engine foundation and its swappable dataset. Single-player skirmish comes first; Meridian Combine and Jackal Front are the playable faction scope. Desktop input is the target. Self-produced Blender assets are the established production path, with suitable imports available as accelerators.

These priorities follow D002, D003, D008, D013, D015, D017 and D018 in [decisions.md](decisions.md). [vision.md](vision.md) supplies the experience bar: quick entry, readable chaos, useful controls, guided onboarding and 15–30 minute matches. It places a boss ladder later. The present request brings asset quality, scenarios and campaigns into review; it does not require a large campaign to become the next release gate.

**Recommendation: finish one reference skirmish to the intended product standard, then extend that standard across the pack.** Prove authored missions with one operation before expanding into a commander ladder or campaign.

Gameplay-depth and authored-content milestones below are proposed extensions to the bundled pack beyond D018's port-first baseline. The existing deployment/publication gate in D013 and publish-checklist.md continues to apply.

## What is already valuable

- A running browser engine, shell/deployment flow, fog of war, production, dozer construction, combat orders, minimap and match-result infrastructure.
- An opponent that spends money, builds, produces teams, defends and raids. Improving its decisions and encounter pacing is more useful than replacing it wholesale.
- A coherent fictional premise and promising faction visual languages: institutional precision versus improvised salvage warfare.
- Reproducible generators for models, maps, textures, icons and audio, a Blender export path, provenance records and targeted engine regression hooks.
- Most content is already project-authored. The ledger identifies four adapted Quaternius meshes, six imported music tracks and the font. Replacing imports alone would affect only a portion of the presentation.

## Assessment evidence and limits

The local browser review used the existing staged build: engine stamp August 31, 16:38; stage stamp August 31, 18:31. Dataset files were compared with the source tree and matched; fonts are handled separately by staging. The browser CLI described by the review skill was unavailable, so the walkthrough used the available computer-use browser interface.

Observed: menu → deployment → Meridian/Standard/Flats; HQ selection; queueing three tanks and a builder; tooltips and queue feedback; placing and completing a vehicle plant; a selected tank moving to an order marker; Escape pause; abandon confirmation → menu. The boot log reported 969 ms on this local run. No warning/error entries were returned by the sampled browser log. This is not a cold-CDN, low-end hardware or cross-browser performance result.

The walkthrough showed small units on repetitive terrain, a largely empty black command area, inconsistent icon styles and little first-match instruction. Audio quality, a complete battle, late-game behavior, every unit, other browsers and all difficulties were not certified in this review. Balance conclusions below are hypotheses supported by data, to be tested in actual matches.

## Priority 1 — make commanding and reading a battle feel finished

### Battlefield, camera and HUD

The wrapper forces a 4:3 canvas and a 1024×768 internal resolution. Boot options select Low LOD and disable both shadow types ([web/index.html](../web/index.html), lines 54–59, 189, 432–439). Better textures will have limited impact until we establish how much detail the game actually displays.

Define a supported widescreen layout, render resolution and UI scale while preserving reliable world picking and camera behavior. Test shadow support in the browser renderer; choose a tested grounding treatment if full shadows are unsuitable. Use a compact, coherent command bar with a clear selected-unit identity, role, health, commands and production queue. Put economy, power, objectives and threats in predictable locations. Give the minimap a clear frame, legible ownership and alerts. Show hotkeys and explain unavailable commands, prerequisites and costs.

Maintain the RTS controls already working. Make their behavior discoverable, including selection versus orders, attack-move, rally points, groups, camera movement and cancel. Check browser shortcut/focus conflicts and full-screen input. Add visible group/idle-worker feedback and configurable camera sensitivity as part of the control specification.

The current command bar is generated in [tools/genwnd.py](../tools/genwnd.py), lines 90–166. This should become an intentional gameplay layout rather than an accumulation of engine-required windows.

### Guided entry and objectives

The deployment screen gives battlefield and opposition text, then immediately starts a match. It needs a map preview, faction playstyle summary, a clear win condition and a discoverable controls/help surface. “SKIRMISH” currently names the easiest difficulty; use language that distinguishes mode from difficulty.

All current maps win when the enemy HQ is destroyed and lose when the player's HQ is destroyed ([tools/genmap.py](../tools/genmap.py), lines 547–553). State that explicitly. A skippable first-skirmish guide should teach selection, builder use, production, income, scouting, counters, HQ defense and attack. Give instructions at the moment they matter, with generous early pressure. Introduce alerts before the player has to react to them.

The result screen should explain the outcome and offer an immediate next action: retry, change difficulty, change battlefield or later continue an operation. Avoid making a novice infer the loss condition from the destruction animation.

### Combat feedback and asset lifecycle

Finish one representative vehicle from idle through destruction before scaling production: a readable silhouette and player-color region, articulated turret, aligned muzzle/projectile origin, recoil, movement detail, impact reaction, damage smoke and a short-lived wreck. Infantry needs readable movement/attack transitions and death feedback; structures need construction, active, damaged and destroyed states.

The active object data does not wire turret or weapon-fire/launch-bone fields, or named damaged/rubble model conditions. Vector's draw block contains its default model ([data/Data/INI/Default/Object.ini](../data/Data/INI/Default/Object.ini), lines 165–179). Shared scaffolds and immediate destruction paths are widespread. The engine has capabilities that the content still needs to exercise.

Keep effects readable in groups: projectile direction, hit location, attack type and ownership should survive overlapping smoke and explosions. Align visual impact, weapon sound and damage timing. Use screen shake only when useful, with a toggle.

## Priority 2 — make the RTS decisions live up to the premise

### Economy and counters

The current tuning merits a dedicated balance pass:

| Data fact | Implication to investigate |
|---|---|
| Both sides start with $10,000. Basic tanks cost $600 and train in 3 seconds. | The starting bank can fund 16 tanks. Test whether early aggression crowds out building, economy and scouting. |
| Exchange costs $700 and produces $25 per 8 seconds; Racket costs $650 and produces $30 per 10 seconds. | Nominal payback is 3.73/3.61 minutes before construction time. Test investment value, reinforcement affordability and late-game starvation. |
| A tank shell deals 100 armor-piercing damage; infantry takes 120%; Lancer has 100 HP. | A direct shell kills the anti-armor infantry unit. Verify the intended counter through range, cost, terrain and mixed-army encounters. |

Sources: [genmap.py](../tools/genmap.py), lines 334/346; [Object.ini](../data/Data/INI/Default/Object.ini), lines 147–148, 1084, 1418–1497; [Weapon.ini](../data/Data/INI/Weapon.ini), lines 2–9; [Armor.ini](../data/Data/INI/Armor.ini), lines 12–16. These numbers do not establish a dominant strategy by themselves.

Test several viable openings and explicit equal-budget counter situations. Record first contact, first meaningful tech choice, economic recovery and match duration. A visible supply/gatherer loop is part of the documented ambition and would make raiding more tangible; treat it as a scoped gameplay milestone after the current economy is measured.

### Faction identity

Vector and Mongrel currently share the same cost, HP, build time, weapon, armor, movement and geometry settings (Object.ini, lines 131–245). Distinct names and skins therefore carry more differentiation than battlefield behavior.

Give each faction one clear economic/base-building distinction and one combat specialty before expanding its roster. Use the existing creative direction: Meridian concentrates costly, precise, power-dependent hardware; Jackal uses cheap raiding forces and dispersed infrastructure. Resolve the discrepancy between the creative bible's power-independent Jackal and the shipped Dynamo/power-consuming Den. That decision affects gameplay, tutorials and which structures deserve final art.

The already-proposed Precision Strike and Tunnel Ambush are suitable later experiments in faction powers. Prove targeting, warning, counterplay and cooldown communication for one power per faction before adding a progression tree or superweapon layer. Neither is required to begin the presentation pass.

### AI and map play

Retain the working economic AI. Its scripted team compositions, expansion recipe and escalation schedules repeat across maps ([genmap.py](../tools/genmap.py), lines 348–352, 401–423, 597–671). Add readable strategic variation: raiding, fortification or armor pressure, alternate routes and responses to player composition. Telegraph escalating threats through scouting opportunities and appropriate warnings.

Test rebuilding after losing economy, power, factory or builder. Test whether the permanent retaliation unlock after the first enemy building kill makes successful harassment feel disproportionately punishing. Do not assume this is broken without match evidence.

There are five geometries mirrored by faction, rather than ten distinct scenarios. They share the HQ objective and opponent recipe. Give each finished battlefield a tactical purpose, readable routes and landmarks. Verify traversability and fire lanes in play; visible ridges do not prove useful chokepoints.

## Original asset production plan

**Visual thesis:** a readable, stylized near-future conflict with painted material detail, weathered industrial ground and sharply different faction silhouettes. This follows D003/D015 and the existing creative bible.

Establish one current asset specification: model scale, camera/readability target, material and texture budgets, UV conventions, player-color masks, named attachments, animation states, export rules and performance limits. The pipeline currently defers team-color masks ([tools/blender/wp_pipeline.py](../tools/blender/wp_pipeline.py), lines 15–16). Replace the contradictory historical art rules in the creative bible when the new standard is adopted.

| Order | Asset work | Why this comes first |
|---|---|---|
| 1 | One environment kit: terrain transitions, rocks/cliffs, roads/tracks, damaged pavement, industrial walls/props and a few landmarks. | Terrain fills most of the screen. Current maps use ground, ash tint and concrete with little environmental placement. |
| 2 | One complete vehicle and one production structure per faction, including lifecycle states. | Establishes modeling, materials, animation, firing, construction and destruction standards together. |
| 3 | Builders, rifle/AT infantry, defenses and remaining units required by the reference skirmish. | Covers the interactions players encounter most often. |
| 4 | One portrait system for the whole active roster. | Current shaded 3D cameos and flat geometric icons visibly conflict. Use consistent framing, lighting and role readability. |
| 5 | Replace remaining placeholder assets by visibility and gameplay role. | Quality improves where players spend attention; new roster breadth waits until the workflow is proven. |

Among imported models, prioritize **Vulture and Outrider**: their source forms read as tanks despite gun-truck and recon roles ([convert_pack_units.py](../tools/blender/convert_pack_units.py), lines 44–53). Give them unmistakable role silhouettes. Mongrel and Zenith can remain until their own quality pass. Retain useful imports while they meet the chosen standard.

Audio should retain the processed-radio direction and faction writing. Audit the actual mix, then improve weapon layers, movement, production/completion, repair and objective cues, voice repetition and alert priority. Provide separate music/effects/voice levels and text for critical announcements. Source coverage is known, but audio quality was not auditioned in this review. Keep the six current music tracks while proving gameplay; original faction motifs and tension/combat cues become useful once encounter pacing is established.

Production needs an asset registry recording role, source, generator/export version, dependencies, budget, required states, provenance and approval status. Normalize generator output paths, use stable seeds and prevent older placeholder generators from overwriting approved assets. Extend staging checks beyond the working voice lint to model/texture/icon/animation references. Build a reusable in-engine review scene across terrain, fog, selection, firing, construction and damage. A close-up Blender render is not sufficient acceptance evidence.

## Scenarios, challenge ladder and campaign

The content files for Campaign, ChallengeMode, Science, Rank and SpecialPower are currently stubs. The engine's history does not constitute an authored mission system ready for this pack. Build content tools and player-facing progression deliberately.

1. **Reference skirmish:** one finished battlefield, both factions, a deliberately bounded roster, calibrated difficulty, a guided opening and complete result/retry loop. Preserve ordinary skirmish replayability.
2. **One authored operation:** use the same environment and roster to prove objective state, triggers, dialogue, pacing, failure/retry and persistent progress. A proposed “Corridor Control” operation could teach scouting and holding a contested route before a telegraphed counterattack and an HQ assault. It should use a different sequence of decisions from ordinary skirmish.
3. **Compact operation set or commander ladder:** add genuinely different pressures, such as surviving with a damaged base, raiding an income network, or breaking an artillery position. Reuse the art kit but vary objectives, routes and opponent behavior. The commander ladder fits vision.md's stated lower-cost solo ambition.
4. **Campaign:** expand only after an operation demonstrates acceptable production effort and replay value. A proposed first campaign could connect four to six operations across the Meridian Strip, with faction viewpoints, recurring commanders, short map briefings, restrained radio storytelling, optional objectives and debrief consequences. This is a scope proposal, not an existing project commitment.

The mission pipeline needs declarative objectives and triggers, stable mission IDs, debug start points, event logging, validation of success/failure paths, briefing/debrief content and unlock/replay rules. Before longer missions, prove browser save/checkpoint storage, versioning and reload recovery. Avoid making cinematics, a third faction or a large technology tree dependencies for the first operation.

## Product durability and release evidence

| Priority | Work | Current evidence / completion condition |
|---|---|---|
| Immediate | Visible failure and recovery states | `fail()` does not remove the overlay's hidden class after boot; `onAbort` calls it. Fix and reproduce a post-boot failure. Source finding at web/index.html:238–245, 343–365; not deliberately crash-tested here. |
| With HUD | Persistent settings and desktop accessibility | Pause currently offers Return/Restart/Abandon. Add readable UI scale, audio channels, key reference/remapping, camera controls, color-independent identification and critical alert text. |
| Before operations | Save/resume and mission progress | Boot creates a fresh MEMFS user directory. Define persistent storage, save compatibility, unavailable-storage behavior and interrupted-save recovery. Verify after closing/reopening the browser. |
| Before network validation | Asset reuse and loading | Timestamp cache-busting and staging the entire manifest precede engine start. Use content hashes and test repeat visits; evaluate deferring music and unused maps. |
| Before distribution | Credits and notices in the product | Repo credit/license documents are absent from the staged bundle. Add an accessible product surface and intended notices/source links. |
| Before release | Browser and hardware matrix | Existing checklist still lacks a Safari full match, Firefox, second-machine play, late-game stress and real-network measurements. |

Use the existing regression hooks, but distinguish them from player tests: some inject engine commands or destroy the enemy HQ directly. Add a small input-driven suite for selection, placement, queues/cancel, pause, restart, victory/defeat and repeat deployment. Test both factions and all maps. Keep local deterministic gates practical; the docs record that inherited GitHub Actions workflows were disabled.

Measure actual frame times, memory and responsiveness through a crowded 30–45 minute stress run. Declare minimum desktop hardware and network profiles before setting percentile targets. The existing ≤20-second boot budget and 15–30-minute ordinary match target remain useful; this assessment does not certify either across devices.

## Proposed execution sequence and exit gates

| Milestone | Concrete deliverable | Exit gate |
|---|---|---|
| A — Standard and baseline | Current creative spec, representative asset/HUD scene, roster inventory, reference map choice, baseline playtest observations. | Each priority has an observable player outcome; final asset roles and browser rendering constraints are known. |
| B — Reference skirmish | Finished battlefield and HUD; representative roster with animation/lifecycle/audio; guided entry; tuned opening and counters; visible failure recovery. | First-time testers complete the opening without coaching and can explain objectives, selected-unit role and what to do next. Both factions complete the match and retry cleanly. |
| C — Pack-wide polish | Remaining roster/maps brought to the same standard; meaningful faction differences, AI variety, settings and repeatable quality gates. | Every unit is built and used in the browser; all map/faction/difficulty combinations are exercised for completion, pathing and essential AI behavior; several openings are viable. |
| D — Authored operation | One mission with briefing, changing objectives, escalation, debrief and saved progress/checkpoint. | Objectives cannot softlock, failure and replay work, progression survives reload, and the mission creates decisions beyond the skirmish recipe. |
| E — Content expansion | Small operation set or commander ladder, followed by a campaign if the production evidence supports it. | Each addition has distinct tactical identity and meets the established presentation, pacing and reliability bar. |

Prioritize A/B next. Engine replacement, large new rosters, multiplayer infrastructure and a full campaign are separate tracks. This sequence protects the documented lightweight project scope while addressing the polish that is visible in every minute of play.

Update the active roadmap/parity/creative documents when adopting this plan: they currently mix old counts, completed implementation notes and superseded design specifications. Keep a single current acceptance bar based on the player experience, with evidence attached to completed gates.
