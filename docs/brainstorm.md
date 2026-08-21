# War Powers — Brainstorm v0.1

> A browser RTS that feels like 2003's *Command & Conquer: Generals / Zero Hour*, built like it's 2026.
> This is a strawman for discussion — argue with everything. Last updated 2026-08-21.

---

## 1. Vision

**Open a link, and 90 seconds later you're plopping down a base, hearing radio chatter, and dreading a superweapon timer.** No install, no launcher, no account, no 1.9GB asset import. A new game — not a clone — that hits the exact nerve Generals hit, with the friction of a modern web app (i.e., none).

## 2. Pillars

Decisions get tested against these:

1. **Nostalgia through feel, not imitation.** We're chasing the *sensations* — dozer plop, supply chinook loop, promotion powers, superweapon dread, chunky explosions — not a 1:1 recreation. This is also what keeps us legally clean and creatively free.
2. **90 seconds to fun.** The web's superpower is zero friction. Cold load to playable skirmish must stay brutally fast.
3. **Readable chaos.** Big armies, big explosions, still legible: strong silhouettes, faction color trims, disciplined VFX.
4. **One deterministic sim.** The same sim core drives single-player, multiplayer, replays, and automated tests. Determinism is a day-one architectural property, not a retrofit (every port that deferred netcode ended up cutting it — see §5).
5. **Data-driven everything.** Units, weapons, powers, build trees live in data files — the spiritual successor to the `rules.ini` modding culture. Balance patches are data edits; community modding becomes possible later for free.

## 3. The nostalgia checklist

What specifically made Generals feel like Generals (our design backlog, roughly grouped):

**Economy**
- Finite supply piles + a visible gatherer loop (chinook/truck/worker analogs); supply lines you can raid
- No population cap — money is the only cap
- Alternate income: capturable derrick-style tech buildings, black-market/hacker-style passive income
- Sell-back on buildings

**Base building**
- Builder units construct anywhere on the map (no grid adjacency); scaffold/build-up animations
- Power grid with brownout penalties (defenses offline, production slowed) — and one faction that famously *doesn't need power*
- Base defenses that genuinely hold ground; garrisonable civilian buildings

**Combat**
- Hard-ish counters; tooltips that say so
- Projectiles are physical: missiles fly, can be dodged, can be shot down by point-defense
- Aircraft sortie from airfields and come home; artillery arcs; ground scarring
- Veterancy chevrons; husks left behind; salvage crates from wrecks (guerrilla-faction signature)
- Area denial: toxin trails, fire, radiation patches

**Meta layer**
- Promotion points → general powers on cooldowns (paradrops, artillery barrages, bombing runs)
- Superweapons on **globally visible timers** — the shared dread clock is the single most Generals mechanic there is
- Capturable neutral tech buildings

**Presentation**
- Bottom command bar + radar minimap + unit portrait; classic RTS camera (top-down, rotate, zoom)
- Unit acknowledgment VO with personality; a battle announcer; orchestral-industrial score
- Desert/urban theaters; particle-heavy explosions, decals, screen shake (toggleable)

**Deliberately NOT nostalgic:** 2003's input latency, pathfinding derps, and UI clunk. We keep the fantasy, not the jank.

## 4. The modern half

- **Instant:** <5s cold load to menu; assets stream behind the menu; playable skirmish underway while low-priority assets keep streaming.
- **QoL:** control groups with on-screen UI, rally points + queued waypoints, attack-move + stances, smart-cast powers, edge pan + MMB drag, camera bookmarks, full replays with timeline scrub, observer mode, tactical pings.
- **Onboarding:** guided first skirmish, counter tooltips, build advisor for new players.
- **Accessibility:** colorblind-safe faction palettes, remappable keys, UI scale, runs on integrated GPUs.
- **Social:** a lobby is a URL — share the link, friend clicks, you're playing. Replays shareable the same way. Later: Discord Activity embed as a distribution hack.
- **Session shape:** 15–30 minute matches; later a "Boss Ladder" solo mode (our homage to Generals Challenge — a gauntlet of boss commanders with personalities and taunts, far cheaper to build than a campaign).

## 5. Landscape — what exists, and our gap

Surveyed 2026-08-21 (all links in §13). Short version: **it's all ports; the lane we want is empty.**

| Project | What it is | Status |
|---|---|---|
| [EA source release](https://github.com/electronicarts/CnC_Generals_Zero_Hour) | Original C++ (VC6/DX8), GPL v3 + EA §7 terms, **no assets**, archived read-only Feb 2025 | Frozen; preservation only |
| [GeneralsGameCode](https://github.com/TheSuperHackers/GeneralsGameCode) | Community mainline: VS2022/C++20/CMake modernization | Very active; the base everything else forks |
| [GeneralsX](https://github.com/fbraz3/GeneralsX) / [Fighter19](https://github.com/Fighter19/CnC_Generals_Zero_Hour) | Native cross-platform ports (macOS/Linux/SDL3) | Active; playable with owned game files |
| [NewShoes](https://newshoes.gg/) | WASM port of EA trees; WebGL2, pthreads, OPFS; explicitly "not a new game or reimplementation" | ZH skirmish works; 4-player WebRTC P2P in testing |
| [wasm-generals](https://generals.wasm.ltd/) | WASM port of GeneralsX via D3D8→WebGPU layer | Claims full ZH incl. LAN MP (self-reported) |
| [Generals-Web](https://github.com/TheodoryLabs/Generals-Web) | WASM port of SuperHackers via custom GLES3 backend | Skirmish boots; perf degrades as bases grow; no audio wiring, no netcode |
| [GeneralsXWeb](https://github.com/meerzulee/GeneralsXWeb) ([write-up](https://mrz.sh/posts/porting-generals-zero-hour-to-the-browser/)) | WASM port, single-threaded, D3D8→WebGL2 (`d8web`) | ZH skirmish fully playable in-browser, no networking |
| [generals-2026](https://github.com/koltregaskes/generals-2026) | Despite the name: a native **iOS/iPadOS** port, not web | Functional fan project |

**Lessons the ports paid for (so we don't have to):**
- Their #1 cost was D3D8→WebGL/WebGPU translation layers — four teams built one independently. A new game starts on WebGL2/WebGPU natively and skips that entire cost center.
- A 2003-scale RTS runs fine single-threaded in a browser (GeneralsXWeb: whole engine at 30fps logic, no SharedArrayBuffer, static hosting) — but **sim scale, not rendering, is the perf ceiling** (Generals-Web drops frames as bases grow). Budget the sim, not the draw calls.
- Engine code size is a non-issue (~2.7MB gzipped WASM for the whole 2003 engine); **the asset pipeline dominates load experience** — 1.9GB imports and ~1 minute of INI parsing at first boot. We ship compiled binary data over a CDN and stream it.
- Everyone converges on **deterministic lockstep** for netcode (it "maps beautifully onto WebRTC") — and it's also the feature most often cut because it was deferred. Determinism from day one.
- Browser audio/time are silent killers in C++ ports (audio-thread failures, missing clocks). Native Web Audio + `performance.now()` fixed timestep avoids the class entirely.

**Gap thesis:** every project above is a preservation play, gated on a Steam purchase and a multi-GB local import, forever unable to distribute assets or reach beyond the retro audience. **Nobody has built the modern, legally clean, instantly loadable, link-to-play Generals-idiom RTS with its own assets.** That's our lane, and the ports are our friends — they serve the "I want *literally* Zero Hour" audience; we serve "I want that *feeling* again, right now, in one click."

## 6. Strategy: greenfield, not port

**Recommendation: from-scratch, web-native TypeScript game.** Rationale:

- **Assets are the wall.** EA's release excludes all art/audio/data; ports can never offer link-to-play. Our own assets are the unlock for pillar #2 — and most of the nostalgia lives in *design* (mechanics, pacing, audio identity), which we can honor with original work.
- **The port lane is crowded and duplicated** (four browser ports of the same lineage); the greenfield lane is empty.
- **A 2003 single-threaded C++ engine is a bad foundation** for the modern half: netcode, streaming, mobile-touch-later, modding.
- **GPL v3 + EA §7 additional terms** attach to all engine code in that lineage. We read it for *understanding* (it's a superb reference for how mechanics actually worked — locomotors, weapon logic, AI templates) but copy nothing. Our numbers and code are our own — which we want anyway, since this isn't a clone.
- Decide **our own license** early: MIT (max community/contributors) vs GPL (share-alike) vs closed. Leaning open source, flavor TBD.

**Legal guardrails (standing checklist):**
- No EA code, no ripped assets, no recreated audio recordings, no trademarks in product branding ("Command & Conquer", "Generals", "Zero Hour", faction names/logos). Nominative references in docs/marketing comparisons are fine.
- Mechanics and stat *ideas* aren't protectable, but express everything in our own names, numbers, and data.
- Original VO and music only — homage in style, not in recording.

## 7. Architecture & stack (proposed)

TypeScript monorepo (pnpm workspaces), strict separation between deterministic sim and everything else:

```
packages/
  sim/       Pure TS deterministic core. ECS over typed arrays (bitecs/koota or
             hand-rolled SoA — pick in M0). Fixed timestep 15–20Hz. Fixed-point
             integer positions. Seeded PCG RNG. Custom trig tables (JS float
             +-*/ and sqrt are IEEE-deterministic; Math.sin/cos are NOT).
             Command-pattern inputs only. Per-tick state hash. Zero DOM/engine
             imports — runs in a worker, on a server, or in a test equally.
  renderer/  Three.js, WebGPU renderer with WebGL2 fallback. Instanced/batched
             unit rendering, heightmap terrain + splat shader, texture-space
             fog of war, GPU particles, decal pools, outline/selection pass.
             Interpolates between sim snapshots.
  ui/        React overlay: command bar, build menus, minimap (canvas), power
             bar, superweapon timers. Signals/zustand for per-frame data.
             Pointer input → intents → sim commands.
  net/       Lockstep client: input-delay ticks, command batching, hash
             comparison for desync detection, replay writer/reader (replays
             ARE the input log — free feature).
  data/      Typed unit/weapon/power/upgrade defs. The "rules.ini" of the
             project. Compiled to binary at build time — no runtime INI-style
             parsing (the ports' 1-minute boot lesson).
server/      Cloudflare Worker + Durable Object per match: WebSocket relay,
             tick ordering, lobby links, replay storage in R2. No accounts in
             MVP. (Alternative: tiny Bun service on Fly.io.)
```

- **Sim in a Web Worker**, render thread interpolates. Start with structured-clone snapshots; upgrade to SharedArrayBuffer ring buffer only if profiling demands (needs COOP/COEP headers — a hosting constraint to note, not a day-one cost).
- **Pathfinding:** coarse nav grid A* for routes + per-order **flow fields** (great group movement feel) + RVO-style local avoidance. Deterministic integer grid. This is the highest-risk system — it gets the M0 spike.
- **Skirmish AI:** data-driven build templates + attack-wave scripting with utility scoring — the original's AI was scripted-but-fun; that's cheap and matches the fantasy.
- **Tooling from day one:** Vitest with **golden-replay determinism tests in CI** (same inputs → same final hash, across browsers), perf budget test (headless 500-unit sim), tweakpane dev panel, replay-driven debugging.
- **Assets:** Blender → glTF, KTX2 compressed textures, meshopt; Web Audio; CC0 kitbash placeholders (Kenney/Quaternius) until the bespoke set exists.

**Perf budget (honest targets):** 400–600 live units at 60fps render / 20Hz sim on a 2020 integrated-GPU laptop; <150MB streamed for a match; <5s cold TTI.

## 8. Faction sketch

Three asymmetric factions eventually; **MVP ships two** (the most mechanically opposed pair). Names are pure placeholders:

| | **"Coalition"** (superpower-tech) | **"Uprising"** (guerrilla) | **"Directorate"** (industrial horde — post-MVP) |
|---|---|---|---|
| Fantasy | Expensive, elite, air-dominant | Cheap, sneaky, everywhere | Mass armor, overwhelming |
| Economy | Supply drops, high-value gatherers | Scavenge, salvage from husks, black-market passives | Bulk gatherers, hacker-style passives |
| Power | Full grid dependency | **No power grid at all** | Grid + overcharge risk |
| Signature | Drones, point-defense lasers, precision strikes | Tunnels, stealth, ambushes, dirty weapons | Horde bonuses, napalm, EMP, nuke endgame |
| Superweapon | Steerable orbital/beam | Missile storm | Nuke |

The asymmetry axes (econ style, power dependency, cost curve, map presence) matter more than any individual unit — that's where Generals' faction identity actually lived. Tone question (real-world-adjacent vs fictionalized) is open — §12.

## 9. Milestones

Every milestone ends in a **playable URL** — the web means every build is shippable, which is also the motivation engine for a project this size.

- **M0 — Feel spike** *(the "is this fun to touch" gate)*: terrain + camera, box select, 200 units flow-field marching, fog of war, one tank shooting one thing with real juice (tracer, impact, husk, decal, shake). No economy. Iterate until drag-select + attack-move feels *great*. If this isn't fun, nothing downstream matters.
- **M1 — Vertical slice**: 1 map, 2 factions × ~8 units/6 buildings, full economy + power loop, win/lose, one skirmish AI difficulty, sound pass v1. Send the link to friends.
- **M2 — The Generals layer**: promotion powers, one superweapon each with global timers, garrisons, veterancy, capturable tech buildings, juice pass 2 (VO, announcer, music loop).
- **M3 — Multiplayer**: lobby links, lockstep 1v1 over the relay, replays, desync tooling, observer seat. (Sim was deterministic since M0, so this is plumbing, not surgery.)
- **M4 — Depth**: third faction, Boss Ladder solo mode, 3–5 map pool, balance via data patches, maybe in-browser map editor.

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **Scope** — RTS is pathfinding + netcode + AI + dense UI + balance, all at once | Strict milestone gates; no campaign; 1v1 focus; data-driven content; M0 kills the project cheap if the core isn't fun |
| **Desyncs** — lockstep's classic tax | Per-tick hashes from day one; golden-replay CI across browsers; sim quarantined from float chaos (fixed-point, custom trig, seeded RNG, no `Date`/`Math.random`) |
| **Browser perf** — sim scale is the ceiling (proven by the ports) | SoA/typed-array sim, object pools (GC discipline), instanced rendering, perf tests in CI with hard budgets |
| **Art cost** — the biggest nostalgia lever is audiovisual | Tight low-poly style guide (silhouette + palette carry identity); CC0 placeholders now, bespoke set later; audio identity (VO/announcer/music) is cheaper than model fidelity and carries huge nostalgia weight — invest there early |
| **Lockstep maphacks** | Accept for casual/friends play; document honestly; server-authoritative sim only if ranked play ever matters |
| **Legal drift** | §6 checklist; periodic self-audit; original names/numbers/assets everywhere |
| **Motivation (hobby-scale project)** | Every milestone is a URL friends can play; feel-first M0 |

## 11. Name

✅ **War Powers** (decided 2026-08-21) — names the signature mechanic (your general powers) and the era's satire (the War Powers Resolution). Collision-checked against existing games; formal trademark + domain check happens before the repo goes public at M1. Runners-up: Top Brass, Thunder Run. Rejected for collisions: Arclight, Zero Sum, Warpath. Details in [decisions.md](decisions.md) D006.

## 12. Decisions & open questions

**Decided 2026-08-21:**
1. ✅ **First playable target: single-player skirmish vs AI.** Sim is still built deterministic/lockstep-ready from day one; MP lands in M3 as plumbing.
2. ✅ **Art direction: stylized low-poly 3D.** Silhouette + faction palette + the classic camera carry the identity.
3. ✅ **Faction tone: thinly-veiled fictional.** Modern-warfare satire energy, no real nation names.

4. ✅ **Name: War Powers.** (§11, [decisions.md](decisions.md) D006)
5. ✅ **License: MIT code + CC BY-NC 4.0 assets** — possible only because we're 100% from scratch with zero EA/GPL code (D001/D007). **Repo private until M1**, then public.
6. ✅ **Stack locked** — see [decisions.md](decisions.md) D005 (20Hz tick, hand-rolled SoA ECS, Q24.8 fixed-point, Three.js WebGPU/WebGL2, React HUD, Cloudflare).

**Still open at the high level:** nothing. Remaining technical details (flow-field design, snapshot format, camera feel targets) get specced in the M0 plan; creative details (factions, rosters, art style, audio identity) are the next brainstorm round.

## 13. Reference links

**Original source**
- EA source release: https://github.com/electronicarts/CnC_Generals_Zero_Hour
- EA modding FAQ: https://www.ea.com/games/command-and-conquer/news/modding-faq

**Community modernization (native)**
- GeneralsGameCode (community mainline): https://github.com/TheSuperHackers/GeneralsGameCode
- GeneralsX: https://github.com/fbraz3/GeneralsX
- Fighter19 fork: https://github.com/Fighter19/CnC_Generals_Zero_Hour

**Browser/WASM ports**
- Project New Shoes: https://github.com/Agusx1211/NewShoes · https://newshoes.gg/
- wasm-generals: https://github.com/origami-ltd/wasm-generals · https://generals.wasm.ltd/
- Generals-Web: https://github.com/TheodoryLabs/Generals-Web
- GeneralsXWeb: https://github.com/meerzulee/GeneralsXWeb · https://igroteka.mrz.sh/ · write-up: https://mrz.sh/posts/porting-generals-zero-hour-to-the-browser/

**Other ports**
- generals-2026 (iOS/iPadOS, despite the name): https://github.com/koltregaskes/generals-2026

**Lineage:** EA → TheSuperHackers/GeneralsGameCode → fbraz3/GeneralsX → {GeneralsXWeb, wasm-generals}; independent browser ports: NewShoes (from EA trees), Generals-Web (from TheSuperHackers).
