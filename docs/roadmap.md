# War Powers — road to publish readiness

Working roadmap; tick items as they land. Decisions referenced live in
decisions.md. **Direction (D018): port-parity first** — publish bar: the
wasm-generals surface with zero player-supplied files, current content as
the bundled pack (Meridian vs Jackal; Iron Pact internal — D017).
Nothing ships or deploys until the user says go.

## Next up (ordered, 2026-08-24 — port surface is done)
1. **Playability pass on the one match we have**: user playthrough drives a
   balance/feel round (fix the WPTest $10000 vs WPTestJ $5000 start-money
   mismatch in genmap first); victory path witnessed live (defeat is).
2. **Close the QoL tail**: attack-move/guard/stop as command-bar buttons
   (needs icon-sheet expansion — first non-portrait icons), rally-point live
   check; retune WP_AUTOTEST=full so the regression gate is all-green.
3. **Polish debt quickies** (§6b): W3DFS_MISS spam (Locater01 + empty-name
   per-frame hunt), voice-limit tuning.
4. **Content to the parity bar** (docs/parity.md): infantry via KayKit CC0
   rigs (unlocks skeletal animation — the #1 asset gap), aircraft class,
   structures to 10/faction, genmap biome/layout variety toward 8-10 maps,
   SFX bulk via CC0 packs; music unpark = cheap CC-BY import when wanted.
5. **The real opponent**: AISkirmishPlayer path (base build lists in genmap
   + auto-reinforce teams + minimal .scb) — replaces timer waves with an AI
   that builds and reacts; biggest "feels like a game" jump after content.
6. **Hardening + publish prep** (gated on explicit go): fps budget pass,
   Safari/Firefox, real-network boot numbers, docs/publish-checklist.md;
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
- [ ] Victory screen live-confirm (same path as defeat; not yet witnessed)
- [ ] Full-autotest retune (2-tank fleet now loses to the defended enemy base)
- [x] Restart Battle + redeploy black screen FIXED (dangling mid-transition window: destroyed quit-menu windows unlink but the transition styles' update() deref'd the nulled m_win — native SIGSEGV, wasm silent low-memory writes corrupting the next match; 45 null-guards in GameWindowTransitionsStyles)
- [ ] Balance pass after a real playthrough (incl. start-money discrepancy between maps)

## 7. Publish readiness (prepare only — nothing goes public without approval)
- [x] Rebrand: window title + console banner clean (full audit pass still to run pre-publish)
- [x] LICENSE-ASSETS.md (MIT code / CC BY 4.0 content / per-file imports, D019) + ledger + credits current
- [x] README.draft.md for the workspace repo (engine/dvijoke fork READMEs at D012 time)
- [x] Fresh-clone reproducibility verified (clone --recursive + genmap/genwnd/Blender-from-clone; blender scripts de-absolutized; gentex single-arg mode quirk noted)
- [x] D012 execution runbook written (docs/publish-checklist.md)
- [ ] Upstream PR candidates (with user approval): wasm audio fixes (decode config, group routing), INI unknown-block diagnostics, icon null-guards
- [x] Hosting comparison doc (docs/hosting.md): Vercel static now, Railway reserved for lobby
