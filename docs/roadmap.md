# War Powers — road to publish readiness

Working roadmap; tick items as they land. Decisions referenced live in
decisions.md. Publish bar: polished modern experience, ZH-level nostalgia,
2 playable factions (Meridian vs Jackal; Iron Pact internal — D017).
Nothing ships or deploys until the user says go.

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
- [x] Second unit class per faction (recon/gun-truck/artillery; infantry still open)

## 4. Opponent
- [x] Scripted attack waves via map scripts
- [x] Skirmish AI investigation — findings + implementation plan in engine-notes (build lists + AISkirmishPlayer + .scb; deferred)

## 5. UI/UX
- [x] Radar/minimap live (terrain, shroud, view frustum; layout polish pending)
- [~] Command bar: programmatic icon sheet wired via ButtonImage (browser verify + portraits/tooltips pending)
- [x] Main menu: the web page is the menu (DEPLOY gates boot + doubles as the WebAudio unlock gesture)

## 6. Web hardening
- [ ] Performance measurement (fps, load time) + budgets — includes the wasm logic-clock crawl under tab throttling (FramePacer vs throttled clocks)
- [x] Audio in the wasm build (two engine bugs found+fixed: zero-channel decode buffers, dead group routing; user-confirmed audible)
- [ ] Settings persistence

## 6b. Polish debt (from playtesting/debugging)
- [ ] Voice-limit tuning: GameSounds occasionally rejects select-barks
- [ ] Silence W3DFS_MISS 'Locater01.w3d' spam (engine hunts a locater model in userdata)
- [ ] Audio mix pass once more content exists (levels: SFX 80% / voice 85% are first guesses)
- [ ] EVA-style announcer (Eva.ini system) — "unit ready", "base under attack"
- [ ] Interactive checks: dozer placement-cursor UI flow; LocalDefeat input-disable

## 7. Publish readiness (prepare only — nothing goes public without approval)
- [x] Rebrand: window title + console banner clean (full audit pass still to run pre-publish)
- [x] LICENSE-ASSETS.md (CC BY-SA 4.0) + ledger + credits current (engine GPL file present upstream)
- [x] README.draft.md for the workspace repo (engine/dvijoke fork READMEs at D012 time)
- [x] Fresh-clone reproducibility verified (clone --recursive + genmap/genwnd/Blender-from-clone; blender scripts de-absolutized; gentex single-arg mode quirk noted)
- [x] D012 execution runbook written (docs/publish-checklist.md)
- [ ] Upstream PR candidates (with user approval): wasm audio fixes (decode config, group routing), INI unknown-block diagnostics, icon null-guards
- [x] Hosting comparison doc (docs/hosting.md): Vercel static now, Railway reserved for lobby
