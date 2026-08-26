# War Powers — road to publish readiness

Working roadmap; tick items as they land. Decisions referenced live in
decisions.md. **Direction (D018): port-parity first** — publish bar: the
wasm-generals surface with zero player-supplied files, current content as
the bundled pack (Meridian vs Jackal; Iron Pact internal — D017).
Nothing ships or deploys until the user says go.

## Phases (2026-08-24 — the port surface is done; user-defined structure)

**Phase 2 — Playability (DONE 2026-08-24):** make the one match we have feel right.
- [x] User playthrough passed with no balance notes ("looks good") — no
      dedicated balance round needed; tuning rides along with Phase 3
      content as new units land
- [x] Start-money mismatch fixed (both maps deploy with $10000)
- [x] Victory path witnessed live (WP_AUTOTEST=win + full both end in the
      score screen)
- [x] QoL tail: attack-move/guard/stop command-bar buttons (gencmdicons
      glyph sheet) live in wasm; rally points end-to-end (locomotor probe +
      WPNODE01/WPRALLY01 + line texture, set-message + flag verified)
- [x] WP_AUTOTEST=full retune → real 4-tank fleet; gate all-green
      (base/cycle/win/defeat/full)
- [x] Polish debt: W3DFS_MISS spam killed (move-hint root cause + WPMOVE01),
      voice pools 12/32, invisible-hoverable sweep (power meter paints,
      popup panels opaque)

**Phase 3 — Content to the parity bar (CURRENT)** (its own phase; the plan and
per-class sourcing live in docs/parity.md):
- [x] Skeletal animation unlocked — procedural W3D rigs (shared skeleton,
      walk/idle/fire); KayKit import remains an optional fidelity upgrade
- [x] Infantry to 4/faction: rifle, rocket (AA), scout (Vigil/Prowler),
      heavy gunner (Bastion/Bruiser, tech-gated) — BAR MET
- [x] Aircraft to 2/faction: Kestrel/Buzzard + Shrike/Gnat strafers
      (tech-gated) — BAR MET (Buzzard/Gnat share the verified hover recipe
      but haven't been individually flown)
- [x] Structures to 9/faction: +AA (Skyspear/Flakhut), +tech
      (Directorate/Den), +pillbox (Rampart/Nest), +Jackal power (Dynamo);
      one shy of the 10 bar
- [x] Maps: 5 layouts × 2 factions (flats/ridge/scrap/basin/range) with
      the picker; biome tinting still pending
- [x] Enemy waves upgraded: rocket infantry in assaults + a 10-minute air
      wave; enemy bases carry AA and real power
- [x] SFX toward ~40 (now ~26: +chaingun, +flak, +deny/click UI, +arty boom)
- [x] VO depth (19 voice sets; newest 6 deepened to 3-deep sel/mov/atk = ~10 lines each)
- [x] Music: 6-track CC-BY rotation (Kevin MacLeod, ~15MB re-encoded; engine rotation in GameEngine::update; native-verified, browser audibility = user ears)
- [x] Biome tinting (ash on Scrapyard/Range) and 10th structure (Longbow/Lobber artillery, firing untested)
- [x] Ambient sound beds (wind bed on CCs via SoundAmbient, power hum, factory loop — seamless generated loops)

**Phase 4 — The real opponent** (v1 LANDED 2026-08-26): the enemy is a live
AIPlayer — trains its own dozer, expands via a map build list (2nd power,
2nd income, forward tower; rebuilds), and produces escalating attack teams
with real money (raider/pack/assault/air tiers on 2/4/8/10-minute unlocks;
economy counterplay: killing its income starves the waves). Timer-spawned
waves are gone. v2a (2026-08-26): OPPOSITION
difficulty row on the deployment screen — SKIRMISH/STANDARD/BRUTAL, persisted,
pure data via difficulty-flagged timer-arm scripts (easy never fields
assault/air; brutal escalates at 1/2.5/5/7 minutes). v2b (2026-08-26): reactive
behaviors — trained defense patrol (regarrisons when killed), punish squad
(unlocked the moment the player destroys an enemy structure; the stock
script condition was a stub, now implemented via ScoreKeeper), and an
eco-raid tier that hunts the player's income/power via attack-priority
sets. AISkirmishPlayer/.scb RETIRED as unnecessary — **Phase 4 closed.**

**Phase 5 — Hardening + publish prep** (gated on explicit go): fps budget
pass, Safari/Firefox, real-network boot numbers, docs/publish-checklist.md;
LAN/relay multiplayer after (wasm-generals parity).

## 0. Port parity (the working plan — D018)
- [x] Overlay control strip (2026-08-24): hover pill over the canvas (mute + volume slider + fullscreen), page-styled, drives the engine live via the exported wpSetMasterVolume and persists to the WP_VOLUME boot key; the in-engine Options screen (its only content was the volume slider, which behaved poorly) is retired — pause menu is Return/Restart/Abandon
- [x] Shell (final architecture 2026-08-24, rev 2): THE ENGINE SHELL is the only menu — the page is a pure auto-booting loader (wordmark + progress, no buttons; audio unlocks on first in-menu click). Boot lands on the in-engine main menu (two-tone wordmark, page-matched styling) → deployment picker → match; every exit returns in-engine (score screen on W/L, quit-to-menu on abandon). ESC pause unchanged. ?map= keeps the -file harness path
- [x] Boot ≤20s: 8.7s local total; performance.mark marks + [BOOT] report permanent (re-measure on real hosting)
- [x] QoL verified in browser: control groups (Ctrl+#/#/Shift/Alt), select-all, view-CC, stop/scatter, camera keys, pause key, force-attack/-move mod-holds (CommandMap.ini authored — was a 1-line stub, nothing was ever bound)
  - [ ] Attack-move + guard as command-bar buttons (ATTACK_MOVE/GUARD CommandButtons in unit command sets); rally-point live check
- [x] Pause menu / quit-to-menu flow: ESC pause (Return/Restart/Options/Abandon+confirm) → in-engine menu; match end → score → menu
- [x] Fog-of-war start: classic black shroud (the "anomaly" was our own 450wu scripted home reveal; CC vision lights the base)
- [ ] Later: LAN/relay multiplayer (wasm-generals parity)
- Content track runs alongside (bar + per-class sourcing: docs/parity.md —
  generate / import CC0+CC-BY / community post-publish; music is solved by
  CC-BY import when unparked)
- Parked until parity (game depth): economy loop, general powers, superweapons, real skirmish AI, music

## 1. Combat juice — fights feel like Generals
- [x] Real projectile on WP_TankGun (visible, dodgeable shells; ProjectileDetonationFX fires)
- [x] Death FX: explosions, smoke, scorch decals (husks: later)
- [x] Audio pipeline: cannon/explosion SFX + processed-radio unit barks wired (EVA announcer: later; audibility = user morning test)
- [x] LocalDefeat path exercised (enemy razed an undefended CC mid-test); input-disable still needs an interactive check

## 2. Base-building loop
- [x] Ground context: aprons/pads so structures sit in bases, not on bare dunes
- [x] Construction model decision (D016) implemented
- [x] Economy structures: Meridian power + production (Jackal mirror pending)
- [x] Money/power economy live (HUD already displays both)

## 3. Roster breadth
- [x] Convert remaining Quaternius tanks into distinct units (Outrider, Vulture, Zenith)
- [x] Base defenses per faction (Bulwark, Watchpost)
- [x] Second unit class per faction (recon/gun-truck/artillery)
- [x] Infantry class per faction (Warden/Scrapper: models, portraits, own VO, SMALL_ARMS damage model)

## 4. Opponent
- [x] Scripted attack waves via map scripts
- [x] Skirmish AI investigation — findings + implementation plan in engine-notes (build lists + AISkirmishPlayer + .scb; deferred)
- [x] Scripted skirmish opponent: defended enemy base (factory/power/towers/defenders) + escalating assault tier; victory = raze it
- [ ] True skirmish AI (builds, reacts, expands) — the AISkirmishPlayer path

## 5. UI/UX
- [x] Radar/minimap live (terrain, shroud, view frustum; layout polish pending)
- [x] Command bar complete: portraits, tooltips w/ descriptions, multi-queue with cancel, construction context
- [x] Faction select on the menu (Meridian/Jackal, persisted); mirrored WPTestJ map
- [x] Construction scaffolds (sites read as scaffolding, not ghost buildings)
- [x] Main menu: the web page is the menu (DEPLOY gates boot + doubles as the WebAudio unlock gesture)

## 6. Web hardening
- [x] Boot time measured + instrumented (8.7s local; §0); fps budget pass still open
- [x] Wasm logic-clock crawl under tab throttling fixed (catch-up: up to 10 updates/tick)
- [x] Audio in the wasm build (two engine bugs found+fixed: zero-channel decode buffers, dead group routing; user-confirmed audible)
- [x] Settings persistence (volume slider + faction choice, localStorage -> WP_VOLUME env)

## 6b. Polish debt (from playtesting/debugging)
- [ ] Voice-limit tuning: GameSounds occasionally rejects select-barks
- [ ] Silence W3DFS_MISS spam: 'Locater01.w3d' (userdata hunt) + per-frame empty-name '.w3d' hunt (shell+game; suspect cursor model resolution)
- [ ] Audio mix pass once more content exists (levels: SFX 80% / voice 85% are first guesses)
- [x] EVA announcer live (Eva.ini + command-net voice: base under attack, structure/unit lost, low power, funds)
- [x] Interactive checks: placement flow (incl. the preview-leak root cause), DEFEAT screen verified on-screen
- [x] Victory screen live-confirm (VICTORY banner witnessed via WP_FRAME_DUMP on the win gate; the shell score screen verified twice with real defeat stats)
- [x] Full-autotest retune (4-tank fleet; full/base/wedge gates green on the dozer-fix build)
- [x] Restart Battle + redeploy black screen FIXED (dangling mid-transition window: destroyed quit-menu windows unlink but the transition styles' update() deref'd the nulled m_win — native SIGSEGV, wasm silent low-memory writes corrupting the next match; 45 null-guards in GameWindowTransitionsStyles)
- [x] Balance pass riding along with playtests (start-money fixed; three real matches played this sweep — home defense matters, waves punish all-in pushes: by design)
- [ ] Known balance edge: artillery min-range dead zone means a lone battery can't defend itself or the CC — pillbox pairing is mandatory (documented, acceptable)

## 7. Publish readiness (prepare only — nothing goes public without approval)
- [x] Rebrand: window title + console banner clean (full audit pass still to run pre-publish)
- [x] LICENSE-ASSETS.md (MIT code / CC BY 4.0 content / per-file imports, D019) + ledger + credits current
- [x] README.draft.md for the workspace repo (engine/dvijoke fork READMEs at D012 time)
- [x] Fresh-clone reproducibility verified (clone --recursive + genmap/genwnd/Blender-from-clone; blender scripts de-absolutized; gentex single-arg mode quirk noted)
- [x] D012 execution runbook written (docs/publish-checklist.md)
- [ ] Upstream PR candidates (with user approval): wasm audio fixes (decode config, group routing), INI unknown-block diagnostics, icon null-guards
- [x] Hosting comparison doc (docs/hosting.md): Vercel static now, Railway reserved for lobby
