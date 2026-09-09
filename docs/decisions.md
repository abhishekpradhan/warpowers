# Decision log

The project's compact why-trail: what was decided, why, and what would make
us revisit. Entry IDs are stable and never renumbered; new entries append at
the end, so numeric order is chronological. Superseded entries keep their ID
and a banner but are compressed to their gist — full original text lives in
git history (per D011).

---

## D001 — Greenfield, not a port (2026-08-21) → resolved: fork

From-scratch web-native game; EA's GPL source is read for understanding only, never copied.
**Why:** assets are excluded from EA's release (ports can never be link-to-play); the port lane has four teams in it already; GPL v3 + EA §7 terms attach to that lineage; a 2003 single-threaded C++ engine is a bad foundation for the modern half.
**Reviewed 2026-08-21** at the maintainer's challenge ("could be a very expensive decision") — full trade study written, later removed in the D011 doc cleanup (see git history). Key corrections to the original rationale: EA's license is clean GPL v3 that fully permits a standalone renamed total-conversion; faction-scale conversion needs INI + art only (no C++), so the fork path is more viable than v0.1 implied; and the dominant costs (assets, design, balance) are **path-independent and transfer between paths**, so this decision is smaller and more reversible than it looks. **Outcome:** direction shifted 2026-08-21 — the maintainer wants a much lighter project (weeks, not months), desktop-only, starting from the "ZH free in a browser, no files needed" experience and evolving from there. **Final (maintainer-accepted 2026-08-21): fork path confirmed** — engine base GeneralsX (tracking TheSuperHackers), zero-retail dataset built natively first, web layer composed at Stage 2 from donor parts (d8web MIT, GeneralsXWeb audio fix, Generals-Web HTTP-Range VFS design). The base evaluation and staged roadmap lived in fork-plan.md (executed in full; removed in the 2026-08-31 docs cleanup — git history). This supersedes D005 and revises D007.

## D002 — Single-player skirmish first (2026-08-21)

First playable target is 1v1 vs a computer opponent; multiplayer comes after.
**Why:** fastest route to a fun shareable build. The engine is lockstep-native, so MP later is plumbing, not surgery.

## D003 — Stylized low-poly 3D (2026-08-21)

**Why:** keeps the real Generals feel (3D camera, arcing projectiles, terrain) at hobby-achievable asset cost; silhouettes + faction palettes carry identity; ages better than dated realism.

## D004 — Thinly-veiled fictional faction tone (2026-08-21)

**Why:** keeps the modern-warfare satire energy without naming real nations; shippable publicly without the controversy the original courted.

## D005 — Tech stack (2026-08-21)

> **Superseded by D001's fork outcome the same week.** Chose a greenfield
> TypeScript/Three.js/Cloudflare stack (deterministic TS sim, Web Worker,
> lockstep plan). The project became a GPL engine fork instead; none of the
> stack survives. Full table in git history.

## D006 — Name: **War Powers** (2026-08-21)

Names the signature mechanic (your general powers) and the era's satire (the War Powers Resolution). Shortlist collision-checked 2026-08-21: War Powers (clean), Top Brass (clean in games; obscure 2024 board game), Thunder Run (clean); rejected: Arclight (well-known Mechabellum unit), Zero Sum (multiple Steam games), Warpath (Lilith mobile war-strategy game).
**Before public branding (M1):** formal trademark search + domain grab (warpowers.gg or similar).

## D007 — License: MIT code + CC BY-NC assets; private until M1 (2026-08-21)

> **Superseded in steps.** Original greenfield licensing: MIT code +
> CC BY-NC 4.0 assets, private until playable. The fork forced engine code
> to GPL v3 + EA §7 terms (D001 outcome); assets moved BY-NC → BY-SA (D009)
> → CC BY 4.0 with workspace code MIT (D019); "private until playable"
> hardened into "private until polished" (D013). The era's "never copy
> GPL-lineage code" guardrail was retired by D009. Full text in git history.

## D008 — Desktop-only (2026-08-21)

No mobile or touch scope. Maintainer decision; simplifies input, UI, and testing matrices across all paths.

## D009 — Uniform copyleft; greenfield-era code guardrail retired (2026-08-21)

> **Superseded on licensing** (assets CC BY-SA → CC BY 4.0 and code MIT via
> D019/D022; the uniform-copyleft story is historical — full text in git
> history). What remains live from this entry:
- **GPL ecosystem code may be copied/adapted with commit-level provenance**
  — the greenfield guardrail is retired because the project *is* a GPL fork
  (this unlocked lifting GeneralsXWeb's audio fix and d8web rather than
  reimplementing them).
- **The three load-bearing rules:** (1) no EA asset/data bytes ever ship —
  that's EA's redistribution right, not our license; (2) no EA trademarks in
  branding (§7 terms); (3) every asset gets a provenance ledger row.

## D010 — Repo topology: engine backed up + submoduled (2026-08-21)

> **Operationally superseded** by D012/D020 and WORKSPACE.md. Gist: the
> engine gained a private remote (laptop-only history was the finding) and
> became a workspace submodule — pinned SHAs keep data ↔ engine versions
> consistent while real git remotes keep upstream rebasing clean (the reason
> a vendored monorepo stays rejected). Private standalone repos rather than
> GitHub-button forks because public forks can't be private. Full text in
> git history.

## D011 — Living documents only; git history is the archive (2026-08-21)

Maintainer direction: keep the repo clean and ready for eventual open-sourcing. Policy: the repo carries only **living** documents. Superseded documents are **deleted, not banner-archived** — anyone needing them reads git history. Future doc rot gets the same treatment; docs polish is a standing item on the go-public checklist. (Applied 2026-08-21 to brainstorm.md and port-vs-greenfield.md; 2026-08-31 to fork-plan.md, hosting.md, and tools/patches/.)

## D012 — Publish-time repo plan: GitHub org + real forks; multi-repo stays (2026-08-22)

Maintainer review: "repos aren't proper forks and aren't well organized; consider an org at publish; consider whether we still need multiple repos at all."

**Do we still need multiple repos?** Yes: (1) the engine must rebase onto GeneralsX/TheSuperHackers via real git remotes — folding its full history into the workspace as a subtree would make upstream tracking painful and bloat every clone; (2) the repo edge is the cleanest license boundary (engine = GPL v3 + EA §7; workspace = *[since D019/D022: MIT + CC BY, entirely permissive — which makes the boundary even cleaner]*). The DXVK fork stays a separate repo, formalized as an engine submodule so `clone --recursive` reproduces the native build.

**Why the repos aren't GitHub forks today:** a GitHub fork of a public repo **cannot be private**, and private-until-polished (D013) wins until go-time. Our histories are full clones of upstream, so fork-ability is preserved — pushing into a real fork later is a plain `git push` (shared ancestry).

**At publish (go-public checklist):**
1. Create the GitHub **org** — name follows the D006 trademark check.
2. Fork `GeneralsX/GeneralsX` → `<org>/warpowers-engine` via the fork button (public, "forked from" banner, upstream PRs), push our branch into it.
3. Fork `fbraz3/dxvk` → `<org>/warpowers-dxvk`, push our branch (fbraz3 is the fork parent and first PR target).
4. Transfer the workspace repo to `<org>/warpowers`, make public; update the engine submodule URL to the org fork.
5. Retire the private standalones after verifying the org repos are complete.

**Addendum (2026-08-31, audited):** the planned layout is in place — remotes
normalized everywhere (`origin` = ours; upstreams fetch-only with push URLs
`DISABLED`, so "never push upstream" is enforced by git), GitHub Actions
disabled at repo level (inherited upstream CI had burned private-repo
minutes), every submodule pin verified reachable. dvijoke was subsequently
**vendored inline** and its fork repo archived (D020), so the go-time fork
list is **engine + dxvk**. Vercel deploys go through the CLI from the local
tree only — no GitHub↔Vercel integration, nothing deploys on push.
Operational detail lives in [WORKSPACE.md](WORKSPACE.md) and [RELEASING.md](../RELEASING.md).

## D013 — Product bar: polished modern experience; private until polished (2026-08-22)

Maintainer direction after the first browser match: the objective is a **polished, modern product** — every aspect judged by that bar: in-game UX, the web shell around the canvas, loading experience, performance, and hosting. Explicitly: **nothing is shared until it is polished** — the go-public gate is product quality, not feature completeness. Hosting accounts available: **Vercel, Railway, Modal** (open to alternatives). Working posture:
- **Vercel** is the presumptive game host: static bundle + global CDN + brotli, per-commit preview deployments, and **Deployment Protection** so private iteration can still happen against a real CDN before anything is shareable. Custom domain at launch (D006 trademark/domain task).
- **Railway** reserved for future server-side needs (multiplayer signaling/relay — the merged web branch already carries a WebRTC UDP transport expecting a lobby service).
- **Modal** not needed for hosting; candidate for future asset-pipeline compute.
- No deployment of any kind until the web shell is a designed product (branded loading, error states, no debug chrome) and the EA-trademark window title is gone from every surface.

*(hosting.md's comparison matrix was folded here in the 2026-08-31 docs
cleanup: Cloudflare Pages was the credible alternative — equally static +
CDN + access-gated — and Vercel won on the existing account; the deploy
mechanics now live in the root RELEASING.md.)*

## D014 — Creative round: the trio, names, VO direction (2026-08-22)

Maintainer-selected from proposals: factions **Meridian Command** (superpower), **Jackal Front** (guerrilla), **Iron Pact** (industrial horde — designed now, built third); build order Meridian + Jackal first for maximum per-match asymmetry.
*[Names finalized 2026-08-31: **Meridian Combine** / **Jackal Front** — D021.]* VO direction: **processed radio barks** (short recorded phrases through a fixed comms chain — any voice usable, personality lives in the writing). Full taste document: [creative.md](creative.md) — palettes with colorblind-aware trims, naming rules (no EA/C&C names, ever), slice rosters, art spec (300–800 tri units, shared palette-atlas texturing, HLod subobject hierarchy), audio identity. First general powers after the slice: Precision Strike vs Tunnel Ambush.

## D015 — Asset quality bar: ZH-comparable; all self-produced (2026-08-22)

Maintainer review of the beauty target: the procedural part-language models are "nowhere close to the quality of Command and Conquer Zero Hour" — and the nostalgia pillar demands that bar. Recalibration: **"finished" assets mean ZH-comparable quality** — modeled forms (wheel wells, muzzle brakes, greebles), painted-detail textures (panel lines, weathering, baked AO — texture carries most of the look), team-color regions, and eventually animation (turret traverse, treads, build-ups). The part-language (`genw3d.py`) is demoted to **placeholder tier**: gameplay stand-ins until each asset's real replacement lands.

Production path: **Blender pipeline, everything self-produced** (maintainer decision: no commissioned art). Model + UV + bake + texture in Blender via headless Python scripting; export W3D via the OpenSAGE Blender plugin (the unproven link — validated by spike before anything else). CC-licensed asset packs remain an opportunistic accelerator through the same pipeline, with ledger rows *[inbound license family narrowed by D022]*. Commissioned art: ruled out.

## D016 — Construction model: dozer-built (2026-08-22)

**Dozer-built, Generals-style.** The engine decides it: DozerAIUpdate, GUI_COMMAND_DOZER_CONSTRUCT buttons, the placement UI, and construction-percent rendering are native engine paths — while "build from Command Center" (C&C sidebar style) has no engine support and would need custom BuildAssistant/ControlBar changes that also pull away from the Generals nostalgia feel. Each faction gets a construction vehicle (Meridian: Surveyor; Jackal: Packrat — creative.md naming rules apply)
*[Names since revised: the shipped builders are Fabricator and Rigger.]*. Structures build where you place them; base layout stays a player skill.

## D017 — Publish faction scope: 2 playable, no tease (2026-08-22, maintainer decision)

Meridian Combine vs Jackal Front are the publish bar (names per D021); **Iron Pact stays fully internal** — no roster, no teaser presence, nothing on public surfaces until after launch. All roster work targets the two factions only.
*[Amended by D025: the design notes in [creative.md](creative.md) are public with the repository, and the roadmap may name the faction as not planned; nothing about it ships in the game.]*

## D018 — Direction: port-parity first; content is the bundled pack (2026-08-23, maintainer decision)

Drift review against the founding goal ("generals.wasm.ltd / wasm-generals,
without needing the game files") found the project had grown a new-game
ambition beyond the port objective. The maintainer chose **port-parity first**: the
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
  *[AI landed Phase 4, music Phase 3, once the port surface was there.]*
- vision.md is trimmed to reflect this framing; the nostalgia checklist
  survives as the asset-pack ambition backlog, not the near-term plan.

## D019 — License policy: legality is the bar; per-file licensing (2026-08-23, maintainer decision)

> **Narrowed by D022** (inbound pre-approval reduced to the
> permissive-attribution family). The planks below otherwise stand.

Third-party assets are excluded only when using them would be illegal or
functionally impossible, never for license-mixing tidiness. Our terms adjust
to fit: the pack is a collection of individually licensed files. Ours stay
CC BY 4.0; imports keep their upstream license, tracked per-file in
ASSETS.md and credited in CREDITS.md. ND stays out on functional grounds
(the style-coherence pipeline modifies everything, and ND bars derivatives).
EA-derived content stays out on legality (unlicensed derivative works).
(This entry also records the licensing moves it implies: our assets
CC BY-SA 4.0 → CC BY 4.0, and workspace code MIT — superseding D009's
uniform-copyleft story.)

## D020 — Repo consolidation: dvijoke vendored inline; engine + dxvk stay forks (2026-08-31, maintainer decision)

The maintainer asked whether four repos could be one. Mapped three endpoints (full
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

## D021 — Faction names finalized: Meridian Combine / Jackal Front (2026-08-31, maintainer delegated)

The shipped strings said Combine/League while every doc said Command/Front
(the Combine/League pair entered with the in-engine shell and no doc
followed). The maintainer delegated the pick; chosen: **the Meridian Combine** vs
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

## D022 — Licensing streamlined: permissive-only workspace (2026-08-31, maintainer decision)

Revises D019's inbound pre-approval. A licensing audit found the ledger's
actual licenses are exclusively permissive-with-attribution — CC BY 4.0
(ours + the MacLeod music), CC0 (Quaternius), OFL (font) — while the policy
pre-approved ShareAlike, GPL art, and NC-by-exception: machinery documented
for imports that never happened, complicating every licensing surface with
collection-vs-derivative caveats.

**Narrowed:** pre-approved inbound licenses are **CC0/public domain, CC BY,
and SIL OFL**. ShareAlike, GPL art, and NC now require a fresh decision
entry *before* import — nothing is newly forbidden, the bar just moves from
pre-approved to needs-a-decision, and zero existing files are affected. The
payoff is a one-sentence story: **everything in the workspace is free to
reuse with attribution; the only copyleft is the engine repo, and the
compiled game ships GPL.** D019's other planks stand unchanged (legality is
the exclusion bar; per-file licensing; ledger + credits).

Same cleanup: LICENSE-ASSETS.md renamed **LICENSING.md** (it maps all
licensing, not just assets); this log restructured (numeric order,
superseded entries compressed per D011); executed/stale docs deleted per
D011 — fork-plan.md (plan fully executed), hosting.md (folded into D013),
tools/patches/ (its one patch is committed in the vendored dvijoke).

On 2026-09-05 the overview was renamed again to **LICENSE.md** so GitHub
surfaces it in a License tab. The root **LICENSE** still contains the MIT
terms; the overview's content and the browser's `licenses/LICENSING.md`
download URL are unchanged.

## D023 — Open mission access; optional portable operation record (2026-09-05)

**Maintainer direction:** this browser game has no accounts, and losing browser data
must never prevent someone from playing content. A local completion record
cannot be a reliable access requirement when it may disappear with a browser
reset, storage eviction or a change of device.

**Implementation choice:** all seven authored missions—Field Orientation,
four operations and two commander trials—are available immediately. Story
order is recommended. Each authored mission keeps its assigned faction and
shows only that faction's deployment action, without a misleading locked
alternate. Skirmish continues to offer both factions. In-match technology
requirements, costs and cooldowns retain their gameplay roles.

We also chose an optional downloadable JSON backup of the operation record
so players can carry their completions and best times between browsers.
Restoring it performs an idempotent, non-destructive merge: existing
completions remain and valid better times are retained. The backup excludes
settings and battle checkpoints. It is a convenience for personal records;
neither possession of a backup nor completion history controls access.

The deployment presentation and backup format are our implementation choices
in response to the maintainer's concern, not a direct quotation or a requirement
to introduce accounts or cloud saves. Browser record/restore/replay checks
remain part of the release checklist.

## D024 — Readable orders and recoverable guidance (2026-09-05)

Player feedback found active and unavailable portraits too similar, and
training guidance difficult to follow or recover after dismissal.

The visual direction keeps the battlefield dominant and uses gold for an
available action, brighter colored portraits, and a dark grayscale face with
a padlock for unavailable orders. Existing hover, selection, queue and recharge
overlays retain their roles. Guidance stays a compact secondary panel: current
step, live requirements, one next action, then access to the full sequence.
Collapse/reopen, step updates and existing reduced-motion-aware entrance
behavior provide feedback without interrupting the battle.

Native mission stages remain authoritative. Completed living template counts
explain the current training gate; metadata is validated against the shipped
map's actual prerequisites. Training does not advance because a player closes
a tip or reviews a later step. The Guidance action stays available in the
mission HUD, and its step indicator updates while the panel is collapsed.
Settings controls automatic opening; manual opening remains available.
New battles, including same-map retries detected by frame reset, start a fresh
guidance session. Checkpoints recover their native saved objective stage.
If a required structure is missing and the builder count is confirmed zero,
training advises replacing the Fabricator without regressing completed steps.

The duplicated local server was a QA process left running beside the player
server. Standard development now uses `http://localhost:8322`; the redundant
8321 listener was stopped. Documentation and the server default agree, and
an occupied port reports a clear error instead of suggesting a second origin.
The hostname and port are part of browser storage identity, so developers
should reuse the standard URL and use separate browser profiles for QA.

## D025 — Open-source readiness pass (2026-09-07)

The repositories are being prepared for public release. Decisions recorded in
this pass:

- **`LICENSE.md` renamed back to `LICENSING.md`.** GitHub's license detection
  reads the root `LICENSE` file (the MIT text); a second license-named file
  only adds ambiguity to the License tab. The browser's `licenses/LICENSING.md`
  download name never changed. Amends the last paragraph of D022.
- **The diagnostic harness is compiled out of production builds.**
  `WP_AUTOTEST` (including the `mission` verdicts), `WP_CLICKTEST` and the
  `WP_REVIEW_SCENE` review and stress scenes exist only with the CMake option
  `WP_HARNESS=ON` (preset `wasm-harness`, build directory
  `engine/build/wasm-harness`); the `wasm` preset ignores their variables. The
  engine traces (`IG_TRACE`, `WP_AI_TRACE`, `WP_DOZER_TRACE`,
  `WP_SURFACE_TRACE`, `WP_SCENE_DUMP`, `WP_FRAME_DUMP`, `WP_PRESENT_SKIP`)
  stay in production builds behind runtime environment switches, so a bug
  report from a shipped build can still carry them. The shell forwards
  diagnostic URL parameters to the engine environment only with `?debug=1`.
  Shipping self-play code paths that inject state was a leftover from
  bring-up, not something a public build should carry.
- **Engine switches in `GameData.ini`.** Six fields parsed in
  `GlobalData.cpp`, each defaulting to the retail behaviour, so the fork stays
  usable with another dataset and the War Powers names and behaviours live in
  data: `RallyPointModel` (default `SCMNode`; War Powers `WPNODE01`),
  `RallyPointLineTexture` (`EXLaser.tga`; `wp_rallyline.tga`),
  `DozerResumesAbandonedConstruction` (`No`; `Yes`),
  `MapPlacedHarvestersAutoGather` (`No`; `Yes`),
  `CommandButtonAvailabilityCues` (`No`; `Yes`) and `MusicRotation` (empty;
  `Track_WP_01` to `Track_WP_06`).
- **Rocket projectile renamed `WPRKT01`**, and the generators now fail closed
  on name collisions; the projectile had shared `wprock01` with the boulder
  prop, which keeps that name.
- **`refs/` removed from the tree.** The Quaternius FBX packs (6 MB) were
  prototype references nothing uses; provenance stays in ASSETS.md and
  CREDITS.md and the files remain in git history.
- **D017 amended: the Iron Pact design notes are public.** "Stays fully
  internal" meant no roster, teaser or public game surface; the design notes
  in [creative.md](creative.md) are published with the repository, and the
  roadmap may name the faction as not planned. Nothing about it ships in the
  game.
- **Docs restructured with a `history/` folder.** Amends D011: living
  documents remain the rule and superseded plans are still deleted, but dated
  records that other documents cite — the verification notes, the polish
  assessment, the engine bring-up log — move to `docs/history/` under a banner
  instead of disappearing into git history. `docs/README.md` indexes
  everything; `publish-checklist.md` became the root `RELEASING.md`;
  `parity.md` folded into the roadmap; `verification.md` split into
  `testing.md` (procedure) and history (evidence).
- **CI workflows added, Actions still disabled.** `.github/workflows/ci.yml`
  runs the local gate list and `wasm-build.yml` builds the engine on demand
  and weekly. GitHub Actions stay disabled at the repository level — the
  inherited upstream workflows once drained the account's minutes — until the
  public release, when they are enabled per repository.
- **Standard community files:** Contributor Covenant 2.1 code of conduct, a
  security policy using GitHub private vulnerability reporting (no bounty), a
  Keep-a-Changelog changelog, issue and pull-request templates and an
  `.editorconfig`.

Revisit if GitHub changes how the License tab is populated, if community bug
reports need the harness in a shipped build (then behind a build flag the
release process checks), or if Actions minutes become a problem again after
enabling.

## D026 — Publish under the personal profile; Vercel subdomain first (2026-09-09)

The maintainer chose to publish the repositories under the existing
`github.com/abhishekpradhan` account rather than a new organization, and to
launch on `warpowers.vercel.app` with a purchased domain to follow later.

Naming is a two-form convention: **"War Powers"** stays the display name on
every player-facing and documentation surface (wordmark, window title, README,
credits, `WP:` string keys), and **`warpowers`** is the single identifier for
everything machine-readable (repository names, the Vercel project and
subdomain, the future domain). Availability checked on 2026-09-08: the GitHub
handle `warpowers` was free, `warpowers.gg/.app/.game/.io/.dev` unregistered,
`warpowers.com` parked. A web search found no shipped game titled "War Powers";
the formal trademark pass in D006 remains a launch step.

Consequences: every Git URL already points at the personal account, so the
"When the repositories move" list in RELEASING.md needs no action for the
first release; the launch sequence is tag, make the three repositories public,
publish the GitHub release that the credits page links to as corresponding
source, then deploy the release stage to production.
