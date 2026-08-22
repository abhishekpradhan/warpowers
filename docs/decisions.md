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

User-selected from proposals: factions **Meridian Command** (superpower), **Jackal Front** (guerrilla), **Iron Pact** (industrial horde — designed now, built third); build order Meridian + Jackal first for maximum per-match asymmetry. VO direction: **processed radio barks** (short recorded phrases through a fixed comms chain — any voice usable, personality lives in the writing). Full taste document: [creative.md](creative.md) — palettes with colorblind-aware trims, naming rules (no EA/C&C names, ever), slice rosters, art spec (300–800 tri units, shared palette-atlas texturing, HLod subobject hierarchy), audio identity. First general powers after the slice: Precision Strike vs Tunnel Ambush.
