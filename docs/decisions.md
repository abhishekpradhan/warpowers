# Decision log

Append-only. Each entry: what we decided, why, and what would make us revisit.

---

## D001 — Greenfield, not a port (2026-08-21)

From-scratch web-native game; EA's GPL source is read for understanding only, never copied.
**Why:** assets are excluded from EA's release (ports can never be link-to-play); the port lane has four teams in it already; GPL v3 + EA §7 terms attach to that lineage; a 2003 single-threaded C++ engine is a bad foundation for the modern half.
**Reviewed 2026-08-21** at the user's challenge ("could be a very expensive decision") — full trade study written, later removed in the D011 doc cleanup (see git history). Key corrections to the original rationale: EA's license is clean GPL v3 that fully permits a standalone renamed total-conversion; faction-scale conversion needs INI + art only (no C++), so the fork path is more viable than v0.1 implied; and the dominant costs (assets, design, balance) are **path-independent and transfer between paths**, so this decision is smaller and more reversible than it looks. **Outcome:** direction shifted 2026-08-21 — user wants a much lighter project (weeks, not months), desktop-only, starting from the "ZH free in a browser, no files needed" experience and evolving from there. Base evaluation + staged roadmap in [fork-plan.md](fork-plan.md). **Final (user-accepted 2026-08-21): fork path confirmed per fork-plan §1a** — engine base GeneralsX (tracking TheSuperHackers), zero-retail dataset built natively first, web layer composed at Stage 2 from donor parts (d8web MIT, GeneralsXWeb audio fix, Generals-Web HTTP-Range VFS design). This supersedes D005's game-stack choices (the TS/React/Cloudflare pieces survive only for the site shell and hosting) and revises D007's code license to GPL v3 + EA §7 terms (our assets remain CC BY-NC).

## D008 — Desktop-only (2026-08-21)

No mobile or touch scope. User decision; simplifies input, UI, and testing matrices across all paths.

## D009 — Uniform copyleft; greenfield-era code guardrail retired (2026-08-21)

> **Superseded on licensing (by D019, 2026-08-23):** assets moved CC BY-SA →
> CC BY 4.0 and workspace code is MIT — the uniform-copyleft story below is
> historical. The guardrail retirement and the three load-bearing rules
> still stand.

User-initiated license review confirmed: the project's engineering complexity comes from EA's asset-redistribution restrictions (immovable under any license we pick), not from our license choices — no switch reduces the current work. Changes made:
- **Assets: CC BY-SA 4.0** (was CC BY-NC). One story project-wide: GPL v3 code + share-alike assets, OpenRA/0 A.D.-style. Anyone may reuse or sell, but must keep it open and credit.
- **Guardrail update:** the greenfield-era rule "never copy EA/GPL-lineage code" is obsolete — the project *is* a GPL fork now, so GPL ecosystem code (TheSuperHackers, GeneralsX, other ports' engine layers) may be freely copied/adapted with commit-level provenance. **Concrete unlock for Stage 2:** GeneralsXWeb's audio fix and Generals-Web's HTTP-Range VFS can be lifted as code rather than reimplemented.
- **Rules that remain (unchanged and load-bearing):** (1) no EA asset/data bytes ever ship — that's EA's redistribution right, not our license; (2) no EA trademarks in branding (§7 terms); (3) every asset gets a provenance ledger row.

## D010 — Repo topology: engine backed up + submoduled; two repos stay (2026-08-21)

User-initiated review of "not a fork / engine outside the repo." Findings and changes:
- **Engine patches had no remote backup** (laptop-only) — fixed: full history refetched (~79MB pack), pushed to private **`warpowers-engine`** (standalone private repo, not a GitHub-button fork, since those are always public; visibility flips at Stage 2).
- **`engine/` is now a git submodule of the workspace** — the workspace commit pins the exact engine SHA, so data ↔ engine-patch versions are always consistent, and `git clone --recursive` fetches the whole project. This delivers "engine in the repo" without sacrificing the thing two-repo protects: clean upstream rebasing onto GeneralsX/TheSuperHackers via real git remotes (the reason a vendored monorepo/subtree stays rejected — that's what made Generals-Web's upstream story painful).
- Upstreamable generic fixes (Vulkan-env build bug, transition null-guard, shroud fallback, deploy same-inode SIGKILL) can be cherry-picked to a clean public fork for PRs before Stage 2 without revealing the project — optional, user's call.
- Doc sweep same day: brainstorm.md and port-vs-greenfield.md banner-marked as historical/superseded records; D007 annotated; fork-plan and README licensing/status/layout statements refreshed.

## D011 — Living documents only; git history is the archive (2026-08-21)

User direction: keep the repo clean and ready for eventual open-sourcing. Policy: the repo carries only **living** documents — README, vision.md (distilled from the brainstorm's still-current sections: pillars, nostalgia checklist, modern bar), fork-plan.md (active plan + progress log), engine-notes.md (living engine reference), decisions.md (this compact why-trail), ASSETS.md (ledger). Superseded documents are **deleted, not banner-archived** — brainstorm.md and port-vs-greenfield.md removed; anyone needing them reads git history. Future doc rot gets the same treatment; docs polish is a standing item on the Stage 2 go-public checklist.

## D012 — Publish-time repo plan: GitHub org + real forks; multi-repo stays (2026-08-22)

User review: "repos aren't proper forks and aren't well organized; consider an org at publish; consider whether we still need multiple repos at all."

**Do we still need multiple repos?** Yes, for exactly two, and D010's reasons still hold: (1) the engine must rebase onto GeneralsX/TheSuperHackers via real git remotes — folding its ~80MB full history into the workspace as a subtree would make upstream tracking painful (the Generals-Web failure mode) and bloat every workspace clone; (2) the repo edge is the cleanest license boundary (engine = GPL v3 + EA §7; workspace assets = CC BY-SA 4.0; both repos are copyleft, but provenance stays legible). The **DXVK fork** is the marginal case: it exists only for the native macOS dev path (the web build won't use DXVK at all) and to upstream our three fixes. It stays a separate repo — but gets **formalized as a submodule of the engine repo** (today it's an untracked nested checkout at `engine/references/fbraz3-dxvk` with only a backup remote), so `clone --recursive` reproduces the full native build.

**Why the repos aren't GitHub forks today:** a GitHub fork of a public repo **cannot be private**, and "private until playable" (D007/D010) wins until Stage 2. Our engine history is a full clone of upstream, so fork-ability is preserved — pushing our branch to a real fork later is a plain `git push` (shared ancestry).

**At publish (Stage 2 go-public checklist):**
1. Create the GitHub **org** — name follows the D006 trademark check (do not squat a name that may change).
2. Fork `GeneralsX/GeneralsX` → `<org>/warpowers-engine` via the fork button (public, carries the "forked from" banner, enables upstream PRs), then `git push` our `warpowers` branch into it.
3. Fork `fbraz3/dxvk` → `<org>/warpowers-dxvk`, push `warpowers-dxvk` branch. (fbraz3 is the fork parent because our branch builds on their macOS patchset and they're the first PR target; dxvk-upstream PRs can still be opened cross-fork.)
4. Transfer the workspace repo to `<org>/warpowers`, make public; update the engine submodule URL to the org fork.
5. Retire the private standalones (`abhishekpradhan/warpowers-engine`, `-dxvk` backup) after verifying the org repos are complete.

Until then the private standalone repos remain the working truth, and the upstreamable-fixes PR option (D010) stays available via a clean public fork that cherry-picks only generic fixes.

**Addendum (2026-08-31, pre-deploy organization audit):** the layout D012
planned is now fully in place, plus one repo D012 predates. Current state:

| Repo (all private) | Role | Linked as | Fork parent |
|---|---|---|---|
| `warpowers` | workspace: docs, data, tools, web page | top-level; submodules → engine, dvijoke | none (ours from scratch) |
| `warpowers-engine` | GeneralsX engine fork (all WP engine work) | workspace submodule `engine/` | fbraz3/GeneralsX (+ TheSuperHackers, GeneralsXWeb as extra fetch remotes) |
| `warpowers-dvijoke` | DX8→web layer fork (emscripten path) — **new since D012**, add to the go-time fork list (parent meerzulee/dvijoke) | workspace submodule `dvijoke/` | meerzulee/dvijoke |
| `warpowers-dxvk` | DXVK fork (native macOS dev path only) | **engine submodule `references/fbraz3-dxvk` — the D012 formalization is DONE** | fbraz3/dxvk (true upstream doitsujin/dxvk kept as fetch remote) |

(OpenSAGE.BlenderPlugin rides along as a reference-only engine submodule
pointing at the public OpenSAGE repo — not our fork, nothing to publish.)

Normalized in every checkout: `origin` = our private repo and is what local
branches track; every foreign remote keeps its fetch URL but has its push URL
set to `DISABLED`, so the "never push upstream" rule is now enforced by git
itself. All four repos are pushed and every submodule pin is reachable on its
remote — a `git clone --recursive` of `warpowers` reproduces the whole tree.

**GitHub Actions are disabled at repo level on all four.** Inherited upstream
CI (GeneralsX CI on the engine mirror, DXVK's Windows build/package jobs) ran
17 runs against private-repo minutes on Aug 22–24 before the workflow files
were stripped; the repo-level switch also covers any future upstream-sync
branch that would reintroduce workflow files. Re-enable per-repo only when we
add CI of our own. At go-time, the public org forks get a fresh look at CI.

Vercel note: deploys go through the `vercel` CLI from the local tree
(`.vercelignore` restricts the upload to `webstage/` + `vercel.json`); no
GitHub↔Vercel integration is installed, so Vercel has no repo access and
nothing deploys on push.

*(Update, later the same day: dvijoke was vendored inline and its fork repo
archived — see D020; the go-time fork list is now engine + dxvk.)*

## D002 — Single-player skirmish first (2026-08-21)

First playable target is 1v1 vs scripted AI. Multiplayer lands in M3.
**Why:** fastest route to a fun shareable build. The sim is deterministic/lockstep-ready from day one regardless, so MP later is plumbing, not surgery.

## D003 — Stylized low-poly 3D (2026-08-21)

**Why:** keeps the real Generals feel (3D camera, arcing projectiles, terrain) at hobby-achievable asset cost; silhouettes + faction palettes carry identity; ages better than dated realism.

## D004 — Thinly-veiled fictional faction tone (2026-08-21)

**Why:** keeps the modern-warfare satire energy without naming real nations; shippable publicly without the controversy the original courted.

## D005 — Tech stack (2026-08-21)

TypeScript everywhere, no game engine, specialized deterministic sim + thin renderer:

| Layer | Choice | Why |
|---|---|---|
| Language | **TypeScript (strict)** — sim, renderer, UI, server, tooling | One language, one toolchain, web-native |
| Build/dev | **Vite** + **pnpm workspaces** monorepo, Node LTS | Boring, fast, standard |
| Renderer | **Three.js** — WebGPURenderer with automatic WebGL2 fallback; plain Three (no react-three-fiber), custom frame loop; instanced/BatchedMesh unit rendering | Full control over an RTS-shaped pipeline; the ports proved rendering isn't the hard part when you start web-native |
| UI/HUD | **React** DOM overlay + **zustand**; HUD reads interpolated snapshots, emits intents → sim commands | Command bar/menus are DOM's strength; keeps game loop out of React |
| Sim core | Dependency-free TS package. Hand-rolled **SoA typed-array ECS** (bitecs-inspired, small, owned). **20Hz fixed tick**. **Fixed-point Q24.8** positions, 16-bit binary angles + LUT trig, **PCG32** seeded RNG, per-tick state hash, command-pattern inputs only. Runs in a **Web Worker** | Determinism is the day-one property (lockstep, replays, CI). JS `+ - * / sqrt` are IEEE-deterministic but `Math.sin/cos` are not — so the sim owns its math. Worker keeps GC/jank away from render |
| Sim↔render | Structured-clone snapshots first; SharedArrayBuffer ring buffer only if profiling demands (COOP/COEP hosting note) | Don't pay complexity before it's needed |
| Pathfinding | Coarse-grid hierarchical A* + per-order **flow fields** + RVO-lite avoidance, all inside sim | Group movement feel is the game; highest-risk system, gets the M0 spike |
| Audio | Thin custom **Web Audio** mixer (voice pooling, priority, ducking, camera-relative pan) | Ports proved browser audio bites C++ engines; native Web Audio avoids the class. Small enough to own |
| Networking (M3) | Deterministic **lockstep**; **Cloudflare Durable Object** per match as WebSocket relay; replays = input logs in **R2** | Every port converged on lockstep; relay beats P2P WebRTC for simplicity/NAT; replays fall out free |
| Hosting | **Cloudflare Pages** — every push gets a preview URL | "Every milestone is a URL" is the motivation engine; previews make every commit shareable |
| Assets | Blender → **glTF + meshopt**; **KTX2/Basis** textures; game data authored as typed TS in `packages/data`, **compiled to a binary pack at build** | The ports' worst load cost was runtime text parsing (~1min INI parse). We never parse text at runtime |
| Quality | **Vitest** + **golden-replay determinism tests in CI** (same inputs → same hash), headless 600-unit perf budget test, **Biome** lint/format, GitHub Actions; Playwright smoke later | Desyncs and perf regressions are the two RTS-killers; both get CI gates from the start |
| Placeholder art | Kenney / Quaternius CC0 kits until the bespoke set | M0 feel work shouldn't wait on art |

**Why no engine (Godot/Unity/PlayCanvas/Babylon):** engines optimize for general 3D games and fight you on deterministic simulation, bundle size, and web-native integration. Our needs are a specialized sim (which no engine provides) plus a thin renderer (which Three.js covers). Babylon would also work; Three.js wins on ecosystem and control.

**Repo layout:** `packages/sim · renderer · ui · net · data` + `server/` + `docs/`.

## D006 — Name: **War Powers** (2026-08-21)

Names the signature mechanic (your general powers) and the era's satire (the War Powers Resolution). Shortlist collision-checked 2026-08-21: War Powers (clean), Top Brass (clean in games; obscure 2024 board game), Thunder Run (clean); rejected: Arclight (well-known Mechabellum unit), Zero Sum (multiple Steam games), Warpath (Lilith mobile war-strategy game).
**Before public branding (M1):** formal trademark search + domain grab (warpowers.gg or similar).

## D007 — License: MIT code + CC BY-NC 4.0 assets; repo private until M1 (2026-08-21)

> **Superseded in two steps:** the fork decision (D001 outcome) forced code to GPL v3 + EA §7 terms, and **D009** moved assets to **CC BY-SA 4.0**. "Private until playable" survives (now phrased as "private until Stage 2"). Original entry kept below for the record.

**This choice is only possible because of D001.** We are 100% from scratch — no forked code — so no license obligation flows in from the EA lineage. (Had we forked it, GPL v3 + EA §7 additional terms would apply to the whole project and MIT would be off the table.) Code is MIT for maximum contributor-friendliness; assets are CC BY-NC 4.0 so the game stays playable and moddable by anyone but not resellable. LICENSE files land with the first scaffold.
**Repo visibility:** private until the M1 vertical slice, then public with something playable to show.
**Standing guardrail either way:** zero EA/GPL-lineage code ever enters this repo — one copied file would relicense the project out from under us.

## D013 — Product bar: polished modern experience; private until polished (2026-08-22)

User direction after the first browser match: the objective is a **polished, modern product** — every aspect judged by that bar: in-game UX, the web shell around the canvas, loading experience, performance, and hosting. Explicitly: **nothing is shared until it is polished** — this supersedes any "rough but public" reading of Stage 2; the go-public gate is now product quality, not feature completeness. Hosting accounts available: **Vercel, Railway, Modal** (open to alternatives). Working posture:
- **Vercel** is the presumptive game host: static bundle + global CDN + brotli, per-commit preview deployments, and **Deployment Protection** so private iteration can still happen against a real CDN before anything is shareable. Custom domain at launch (D006 trademark/domain task).
- **Railway** reserved for future server-side needs (multiplayer signaling/relay — the merged web branch already carries a WebRTC UDP transport expecting a lobby service).
- **Modal** not needed for hosting; candidate for future asset-pipeline compute.
- No deployment of any kind until the web shell is a designed product (branded loading, error states, no debug chrome) and the EA-trademark window title is gone from every surface.

## D014 — Creative round: the trio, names, VO direction (2026-08-22)

User-selected from proposals: factions **Meridian Command** (superpower), **Jackal Front** (guerrilla), **Iron Pact** (industrial horde — designed now, built third); build order Meridian + Jackal first for maximum per-match asymmetry.
*[Names finalized 2026-08-31: **Meridian Combine** / **Jackal Front** — D021.]* VO direction: **processed radio barks** (short recorded phrases through a fixed comms chain — any voice usable, personality lives in the writing). Full taste document: [creative.md](creative.md) — palettes with colorblind-aware trims, naming rules (no EA/C&C names, ever), slice rosters, art spec (300–800 tri units, shared palette-atlas texturing, HLod subobject hierarchy), audio identity. First general powers after the slice: Precision Strike vs Tunnel Ambush.

## D015 — Asset quality bar: ZH-comparable; all self-produced (2026-08-22)

User review of the beauty target: the procedural part-language models are "nowhere close to the quality of Command and Conquer Zero Hour" — and the nostalgia pillar demands that bar. Recalibration: **"finished" assets mean ZH-comparable quality** — modeled forms (wheel wells, muzzle brakes, greebles), painted-detail textures (panel lines, weathering, baked AO — texture carries most of the look), team-color regions, and eventually animation (turret traverse, treads, build-ups). The part-language (`genw3d.py`) is demoted to **placeholder tier**: gameplay stand-ins until each asset's real replacement lands.

Production path: **Blender pipeline, everything self-produced** (user decision: no commissioned art). Model + UV + bake + texture in Blender via headless Python scripting; export W3D via the OpenSAGE Blender plugin (the unproven link — validated by spike before anything else). CC-licensed asset packs (Kenney/Quaternius/Sketchfab CC-BY) remain an opportunistic accelerator through the same pipeline, with ledger rows. Commissioned art: ruled out.

## D016 — Construction model: dozer-built (2026-08-22, overnight run; user delegated)

**Dozer-built, Generals-style.** The engine decides it: DozerAIUpdate, GUI_COMMAND_DOZER_CONSTRUCT buttons, the placement UI, and construction-percent rendering are native engine paths — while "build from Command Center" (C&C sidebar style) has no engine support and would need custom BuildAssistant/ControlBar changes that also pull away from the Generals nostalgia feel. Each faction gets a construction vehicle (Meridian: Surveyor; Jackal: Packrat — creative.md naming rules apply)
*[Names since revised: the shipped builders are Fabricator and Rigger.]*. Structures build where you place them; base layout stays a player skill.

## D017 — Publish faction scope: 2 playable, no tease (2026-08-22, user decision)

Meridian Combine vs Jackal Front are the publish bar (names per D021); **Iron Pact stays fully internal** — no roster, no teaser presence, nothing on public surfaces until after launch. All overnight/roster work targets the two factions only.

## D018 — Direction: port-parity first; content is the bundled pack (2026-08-23, user decision)

Drift review against the founding goal ("generals.wasm.ltd / wasm-generals,
without needing the game files") found the project had grown a new-game
ambition beyond the port objective. User chose **port-parity first**: the
product is the browser port with zero player-supplied files; today's
Meridian/Jackal content is the **bundled default asset pack** riding a
deliberately swappable data layer — not a new game under active design.

Consequences:
- Next milestones are the port surface wasm-generals is judged by: in-engine
  shell (main menu, skirmish setup, options, score screen, load screens),
  boot ≤20s, verification that native engine QoL (control groups, rally
  points, attack-move, stances, hotkeys) works in the browser build, and
  eventually multiplayer.
- Game-depth work (economy loop, general powers, superweapons, real AI,
  music) is parked until the port surface matches the reference project.
- vision.md is trimmed to reflect this framing; the nostalgia checklist
  survives as the asset-pack ambition backlog, not the near-term plan.

## D019 — License policy: legality is the bar; per-file licensing (2026-08-23, user decision)
Third-party assets are excluded only when using them would be illegal or
functionally impossible, never for license-mixing tidiness. Our terms adjust
to fit: the pack is a collection of individually licensed files. Ours stay
CC BY 4.0; imports keep their upstream license (CC0/CC-BY/CC-BY-SA/GPL art/
OFL all acceptable), tracked per-file in ASSETS.md and credited in CREDITS.md.
ShareAlike/GPL imports ship under their own terms without affecting sibling
files. NC assets only by explicit per-case decision (they permanently bar
commercial use of that asset). ND stays out on functional grounds (the
style-coherence pipeline modifies everything, and ND bars derivatives).
EA-derived content stays out on legality (unlicensed derivative works).
(This entry also records the licensing moves it implies: our assets
CC BY-SA 4.0 → CC BY 4.0, and workspace code MIT — superseding D009's
uniform-copyleft story.)

## D020 — Repo consolidation: dvijoke vendored inline; engine + dxvk stay forks (2026-08-31, user decision)

User asked whether four repos could be one. Mapped three endpoints (full
monorepo / 4→2 consolidation / status quo) with measured stakes: the engine
is the only fork with a **live** upstream (parents committed 2026-08-30 and
-31; we're 101 commits ahead, 45 behind), while dvijoke's upstream has been
quiet since 2026-07-07 (22 commits, 332K, our delta = 3 commits) and dxvk's
fork parent since 2026-03 (dev-only, 126MB history, never ships in the web
build). A full monorepo would put ~670MB / ~8,600 commits (97% other
people's) in every clone and kill the upstream-PR path + go-time fork
banners. **Chosen: Option B (4→2 in daily terms).**

- `dvijoke/` is now **vendored inline** in the workspace via
  `git subtree add` with full history — tree OID verified byte-identical to
  the former submodule pin (ba6791de). The engine's
  `wasm-deps.cmake` reference (`../dvijoke/d8web`) is path-unchanged.
- Licensing reviewed first: dvijoke is MIT (Meerzulee), same family as our
  workspace code; no third-party headers inside d8web; MIT notice retention
  satisfied by keeping `dvijoke/LICENSE` in place; GPL linkage unaffected
  (MIT→GPL-compatible; the combined wasm binary ships GPL, files stay MIT).
  No copyleft enters the workspace — that's why the engine stays separate.
- `warpowers-dvijoke` is **archived** (read-only) on GitHub; history is
  preserved both there and inline.
- Amends D012's go-time plan: **two** public forks (engine, dxvk) + the
  public workspace carrying dvijoke inline with credit + upstream SHA.

Revisit if: meerzulee's dvijoke resumes active development we want to track,
or we accumulate dvijoke patches worth upstreaming (extract from inline
history; at 3 commits this is trivial).

## D021 — Faction names finalized: Meridian Combine / Jackal Front (2026-08-31, user delegated)

The shipped strings said Combine/League while every doc said Command/Front
(the Combine/League pair entered with the in-engine shell and no doc
followed). User delegated the pick; chosen: **the Meridian Combine** vs
**the Jackal Front** — the stronger name from each pair.
- *Combine* over *Command*: carries the corporate-war-machine satire (D004),
  more distinctive than RTS-generic "Command", avoids "the Meridian Command
  command center", and the shipped VO copy already says it ("Fastest boots
  in the Combine").
- *Front* over *League*: the insurgent-front register matches the faction's
  guerrilla identity; "League" reads soft.
One string changed in game data (League → Front; deploy buttons compose
from it); docs synced; D014/D017 annotated. "Meridian Command Center"
(the building) is unaffected — command centers stay command centers.
