# Fork Plan — Base Choice & Staged Roadmap

> **Historical planning document.** Licensing has since been revised:
> code MIT / content CC BY 4.0 / per-file imports — see LICENSE-ASSETS.md
> (decisions D018/D019 set the current direction and license policy).


Written 2026-08-21 after the user redirected: **desktop-only, much lighter than 3–6 months, start from "ZH free in a browser, no files needed" and evolve from there.** The game this builds toward is defined in [vision.md](vision.md); earlier greenfield-era documents were removed in the D011 cleanup (git history keeps them).

---

## 1. Base evaluation (all four web ports + native lineage, researched 2026-08-21)

| Candidate | Verdict | Why |
|---|---|---|
| **[Generals-Web](https://github.com/TheodoryLabs/Generals-Web)** (TheodoryLabs) | 🧩 Top donor — superseded, see §1a | The only port whose architecture already matches our end state: the engine **streams `.big` archives over HTTP Range requests** from whatever origin serves them — "our assets on a CDN" is a URL + CORS change, not a rewrite. Based on a TheSuperHackers snapshot (the community mainline with the biggest fix corpus). Clean GPL-3.0 + EA terms. Modern toolchain (Emscripten 6.0.2, CMake presets, CI, honest docs). Campaign + skirmish boot and play; saves work (IndexedDB). |
| [NewShoes](https://github.com/Agusx1211/NewShoes) | 🥈 Fallback + idea mine | Healthiest *project* (issues, releases, tests, mods, likely audio) — but its asset path is deliberately local-only OPFS ("no bytes uploaded"), the exact opposite of no-files-needed; pinned 2022-era Emscripten 3.1.6; EA-direct engine base missing the SuperHackers fix corpus; needs a case-sensitive volume on macOS. Steal its OPFS caching, launcher validation, and Cloudflare deployment ideas. |
| [GeneralsXWeb](https://github.com/meerzulee/GeneralsXWeb) | 🧩 Donor: closest bloodline — see §1a | The import/frontend lives in a *separate* repo (igroteka); no audio; broken saves; thin docs. **But**: its July 2026 commits contain real UDP-over-WebRTC multiplayer transport work — the reference when we want MP later. |
| [wasm-generals](https://github.com/origami-ltd/wasm-generals) | ❌ Do not touch the web layer | Its `web/` is under a non-standard "MIT with Proof-of-Usage Condition" license imposing registration + perpetual credit obligations on derived products — legally unclean. Also WebGPU-only (no Firefox/Safari) and its feature claims are unverifiable. Engine-side patches are plain GPL if ever needed. |

**Upstream strategy:** track **[TheSuperHackers/GeneralsGameCode](https://github.com/TheSuperHackers/GeneralsGameCode)** (weekly releases, all game-logic gravity) as the fix source. Generals-Web is a squashed snapshot with only ~34 web-port commits on top — rebasing that patch set onto fresh upstream periodically is the maintenance model. [GeneralsX](https://github.com/fbraz3/GeneralsX) (active macOS builds, Apple Silicon, Beta 17) is the native macOS reference build for fast iteration and feel-comparison outside the browser.

## 1a. Second look (2026-08-21, later) — nobody's worth marrying; split the decision

Exact repo ages from the GitHub API reframe the whole question. **Every web port is a summer-2026 solo code-drop; the only living projects are native:**

| Repo | Created | Last push | Stars/forks | Read |
|---|---|---|---|---|
| TheSuperHackers/GeneralsGameCode | 2025-02-28 | **2026-08-21 (today)** | 1,321 / 245 | The real community; weekly releases |
| fbraz3/GeneralsX | 2025-05-19 | **2026-08-21 (today)** | 294 / 50 | Living macOS/Linux carrier, tracks upstream |
| Agusx1211/NewShoes | 2026-06-28 | 2026-07-27 | 20 / 0 | Best-run port; quiet ~4 weeks |
| meerzulee/GeneralsXWeb | 2026-07-06 | 2026-07-09 | 16 / 2 | 3-day drop alongside its blog post |
| TheodoryLabs/Generals-Web | 2026-07-07 | **2026-07-07** | 3 / 0 | Created and last pushed the same day — a snapshot dump |
| origami-ltd/wasm-generals | 2026-08-05 | 2026-08-15 | 2 / 1 | Two weeks old; recent commits are license tooling only |

**Consequence:** no web port is an upstream — they are donor patch-sets over one engine family. The durable choice splits in two:

1. **Engine base (decide now): GeneralsX**, with TheSuperHackers as grand-upstream. Living (pushed today), native Apple Silicon builds, explicitly merges upstream, and it's the parent lineage of two of the three GeneralsX-derived web ports — so zero-retail dataset work debugged natively transfers cleanly to whatever web layer we pick. This also supersedes Stage 0's "fork Generals-Web" opening: **Stages 0–1 run on GeneralsX native; the web layer is chosen at Stage 2 with evidence.**
2. **Web layer (decide at Stage 2): compose from donors.** Likely shape: GeneralsX engine + **d8web** (D3D8→WebGL2, MIT) + **GeneralsXWeb's audio fix** (verified working from the port write-up: MiniAudio→WebAudio via a threadless resource manager + in-memory MP3/WAV decoding — the exact problem Generals-Web never finished) + an **HTTP/CDN VFS modeled on Generals-Web's Range-streaming design** (GPL, auditable). GeneralsXWeb's WebRTC UDP transport is the future multiplayer reference. wasm-generals: engine-side (GPL) ideas only if we ever want its D3D8→WebGPU layer; its `web/` stays untouched (encumbered MIT-PoU license).

Single-threaded web (GeneralsXWeb-style) is the default posture: static hosting, no COOP/COEP headers, Safari support, proven 30fps-logic on Apple Silicon — simplicity that matches the "light project" mandate.

## 2. Why "no files needed" is more tractable than it looked

Verified from TheSuperHackers' wiki: the engine ships launch flags that bypass most of the hard-to-replace data — **`-noshellmap -novideo -nomusic -noaudio -quickstart`**, and crucially **`-map <name>`**, which boots *straight into a match with no menu*. Loose `Data\INI\` files override `.big` contents by design. So the minimal zero-retail dataset for a first bootable match is roughly: our own INI tree + a map + a handful of placeholder W3D models/textures — **not** the shell UI, videos, music, or voice tree (all deferrable).

Difficulty tiers for replacement data:
- **Easy:** INI (plain text, 20 years of modding documentation, field names greppable in the GPL source), maps, AI scripts.
- **Medium:** models (Blender → W3D via the maintained [OpenSAGE Blender plugin](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin) — export support confirmed, in-original-engine loading strongly indicated but unproven → test first), textures, SFX.
- **Hard (deferred):** full shell/menu WND UI, fonts, localization CSF, EVA voice tree — all bypassed initially via `-map`/`-quickstart`, replaced incrementally later.

Nobody has ever demonstrated a zero-retail boot ([SuperHackers discussion #266](https://github.com/TheSuperHackers/GeneralsGameCode/discussions/266) lists open assets as an unstarted "very long-term goal") — we'd be first, and the engine source being public means the true hard-require list is a grep, not archaeology.

**Important boundary:** EA's INI text is EA content — we author our own from the documented format, never copy theirs. Same for [GeneralsGamePatch](https://github.com/TheSuperHackers/GeneralsGamePatch) content (extra restrictions) — structural reference only.

## 3. The staged plan (light-first, always playable)

**Stage 0 — "Runs on my Mac" (days).** Fork Generals-Web. Build with Emscripten 6.0.2 per its docs. Run ZH skirmish in Chrome locally using our own retail files (dev only, never shipped). Also stand up the GeneralsX native macOS build as the fast-iteration reference. Side quest: export one cube-with-a-texture from Blender to W3D and confirm the original engine loads it — this validates the entire future asset pipeline for ~an hour of work.
*Success gate: ZH skirmish plays in the browser on this machine.*

> **Revision 2026-08-21 — no retail copy available (user decision: work around it).** Stage 0's run-with-known-good-data validation is off; Stages 0–1 merge into one bring-up: build the engine (native GeneralsX build first for fast iteration and readable asserts, then the web build), and iterate the minimal zero-retail dataset directly against it — stubbing each missing file the boot path demands until a match loads. Cost of the workaround: two unknowns at once (port bugs vs. our data gaps, with no baseline to separate them), no reference copy for feel/nostalgia calibration, and Blender→W3D validation happens against our own boot rather than retail ZH. Estimate shifts from days + 1–2 weeks to ~2–3 weeks with wider error bars. A retail copy remains the cheap de-risk if we get stuck.

**Stage 1 — Zero-retail boot (1–2 weeks).** The first-of-its-kind experiment: grep the engine's boot path for fatal asset loads, then assemble a minimal fully-original dataset — tiny INI tree, one authored map, placeholder W3D units — and boot with `-quickstart -noshellmap -novideo -nomusic -map ourmap`.
*Success gate: a match starts in the browser with zero EA bytes. "No files needed" is now real.*

**Stage 2 — Playable & public (weeks, content-paced).** Grow the dataset to actually fun: one or two small factions (INI-designed, our balance), a few placeholder-art units each, 1–2 maps, basic SFX. Wire audio (Generals-Web's bridge is written but unfinished — this is the main engineering debt we inherit). Host archives on Cloudflare (COOP/COEP headers required for SharedArrayBuffer). Public URL, rough but legal and ours.

**Stage 3+ — Evolve.** Rebrand fully (name TBD — War Powers still fits), reskin the in-game UI (WND + control-bar art), better assets, more content, periodic upstream rebases, and — when wanted — multiplayer via WebRTC (GeneralsXWeb's transport work as the reference).

## 3a. Progress log

**2026-08-21 — Stages 0–1 substantially complete in one session.** Engine built natively (GeneralsX `warpowers` branch, Apple Silicon, DXVK→MoltenVK), and the **zero-retail boot was achieved**: the engine runs its main loop indefinitely on 100% original data — ~70 authored INI/WND files, 3 generated placeholder assets, zero EA bytes ([engine-notes.md](engine-notes.md) has the distilled requirements; `data/` holds the dataset; ASSETS.md tracks provenance). Engine patches so far (all small, marked, some upstreamable): `-file`/`-buildmapcache` exposed in release, transition-handler null-guard, temporary UI null-bail + debug traces. Corrections to §2: `-map`/`-noaudio`/`-nomusic`/`-novideo` are debug-only in release builds (we patched `-file` in instead), and one real music file is mandatory (engine quits silently without it). Next: author a minimal map + object roster and enter it via `-file`.

**2026-08-21 (later) — THE FIRST MATCH RUNS.** Boot Slice roster authored (WP faction, command center with production, tank with AI/weapon/armor — every INI field verified against engine parse tables, zero parse errors). `.map` binary format spec extracted from the GPL reader source; `tools/genmap.py` generates our first map (84×84 flat, 2 players + neutral, command center each, waypoints). Entered via patched `-file`: sides validate, both command centers instantiate as live objects, camera places, game loop runs indefinitely. Fixes en route: `ShellGameLoadScreen.wnd`, `PartitionCellSize` (0-default div-by-zero → shroud), `MultiplayerColor` entries (observer-side null deref), shroud surface fallback patch. **Known gap: viewport renders black** (shroud/terrain-render investigation next), and units/buildings are invisible pending W3D models. Next: reveal the scene (shroud/lighting/terrain debug), verify input (select/command), tank production, then win condition.

## 4. Risk register

| Risk | Note / mitigation |
|---|---|
| Zero-retail boot unknowns (hardcoded filenames, CSF/font/shell deps) | Nobody's done it; that's why it's Stage 1 and cheap — the source is greppable, and flags bypass the worst |
| Audio not wired on the chosen base | Inherited engineering debt; NewShoes (Web Audio) and the upstream Miles-stub seam are references |
| Blender→W3D export unproven in original engine | Stage 0 side quest — one hour to validate before anything depends on it |
| Map authoring: Worldbuilder is Windows-only | SuperHackers weekly releases include it; run via CrossOver/VM, or author maps on a Windows box once |
| Base is a solo, six-weeks-quiet, AI-assisted repo | We fork to own it; small patch set keeps upstream rebases feasible |
| Retail copy needed for Stage 0 dev/reference | ~$5–20 (ZH / Ultimate Collection on Steam or EA App) — dev-machine only, never shipped |
| License becomes GPL v3 + EA §7 terms | Confirmed and embraced (D009): uniform copyleft — GPL code, CC BY-SA assets |
| Chrome 149–150 V8 GC crash documented by the base | Likely fixed in current Chrome; verify in Stage 0 |

## 5. Effect on earlier decisions (if this plan is confirmed)

- **D001** flips: fork-based, with greenfield demoted to the someday-option (content transfers if ever needed).
- **D005** (TS/Three.js stack) is superseded for the game itself; survives for the *site shell* (React/TS around the canvas) and Cloudflare hosting.
- **D002** (SP skirmish first) — unchanged, and now nearly free.
- **D003** (low-poly art) — unchanged; applies to our replacement W3D assets.
- **D004** (fictional tone), **D006** (name) — unchanged.
- **D007** — code side becomes GPL v3 + EA terms (forced); assets: CC BY-SA 4.0 as of **D009** (uniform copyleft; D009 also retired the "no GPL code copying" guardrail — ecosystem GPL code may be lifted with provenance). Private-until-presentable still fine (GPL obligates source *when we distribute* — repos go public when the first public build ships in Stage 2).
- **New — D008: desktop-only.** No mobile/touch scope.
