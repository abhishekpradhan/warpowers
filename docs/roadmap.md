# War Powers — road to publish readiness

Working roadmap; tick items as they land. Decisions referenced live in
decisions.md. **Direction (D018): port-parity first** — publish bar: the
wasm-generals surface with zero player-supplied files, current content as
the bundled pack (Meridian vs Jackal; Iron Pact internal — D017).
Nothing ships or deploys until the user says go.

## 0. Port parity (the working plan — D018)
- [ ] In-engine shell: main menu (in engine, replacing page-as-menu or behind it), skirmish setup (map/faction/color), options screen, score screen, load screens
- [ ] Boot ≤20s: chunked/streamed init behind the menu; performance.mark instrumentation
- [ ] Verify native engine QoL in the browser: control groups, rally points, attack-move, stances, hotkeys (engine features — likely work, never tested)
- [ ] Pause menu / quit-to-menu flow (game-exit currently just returns to the page)
- [ ] Fog-of-war start (initial-reveal anomaly — engine dig)
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
- [ ] Performance measurement (fps, load time) + budgets; boot 25-40s vs the ≤20s bar
- [x] Wasm logic-clock crawl under tab throttling fixed (catch-up: up to 10 updates/tick)
- [x] Audio in the wasm build (two engine bugs found+fixed: zero-channel decode buffers, dead group routing; user-confirmed audible)
- [x] Settings persistence (volume slider + faction choice, localStorage -> WP_VOLUME env)

## 6b. Polish debt (from playtesting/debugging)
- [ ] Voice-limit tuning: GameSounds occasionally rejects select-barks
- [ ] Silence W3DFS_MISS 'Locater01.w3d' spam (engine hunts a locater model in userdata)
- [ ] Audio mix pass once more content exists (levels: SFX 80% / voice 85% are first guesses)
- [x] EVA announcer live (Eva.ini + command-net voice: base under attack, structure/unit lost, low power, funds)
- [x] Interactive checks: placement flow (incl. the preview-leak root cause), DEFEAT screen verified on-screen
- [ ] Victory screen live-confirm (same path as defeat; not yet witnessed)
- [ ] Fog-of-war start: initial-reveal anomaly blocks MAP_SHROUD_ALL (engine dig)
- [ ] Full-autotest retune (2-tank fleet now loses to the defended enemy base)
- [ ] Balance pass after a real playthrough (incl. start-money discrepancy between maps)

## 7. Publish readiness (prepare only — nothing goes public without approval)
- [x] Rebrand: window title + console banner clean (full audit pass still to run pre-publish)
- [x] LICENSE-ASSETS.md (CC BY-SA 4.0) + ledger + credits current (engine GPL file present upstream)
- [x] README.draft.md for the workspace repo (engine/dvijoke fork READMEs at D012 time)
- [x] Fresh-clone reproducibility verified (clone --recursive + genmap/genwnd/Blender-from-clone; blender scripts de-absolutized; gentex single-arg mode quirk noted)
- [x] D012 execution runbook written (docs/publish-checklist.md)
- [ ] Upstream PR candidates (with user approval): wasm audio fixes (decode config, group routing), INI unknown-block diagnostics, icon null-guards
- [x] Hosting comparison doc (docs/hosting.md): Vercel static now, Railway reserved for lobby
