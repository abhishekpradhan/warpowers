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
- [ ] Convert remaining Quaternius tanks into distinct units
- [ ] Base defenses per faction
- [ ] Second unit class (infantry or light vehicle) per faction

## 4. Opponent
- [x] Scripted attack waves via map scripts
- [ ] Skirmish AI investigation (engine's real AI path)

## 5. UI/UX
- [ ] Radar/minimap (currently a black box)
- [ ] Styled command bar + unit portraits
- [ ] Main-menu shell instead of booting straight into a match

## 6. Web hardening
- [ ] Performance measurement (fps, load time) + budgets
- [ ] Audio in the wasm build
- [ ] Settings persistence

## 7. Publish readiness (prepare only — nothing goes public without approval)
- [x] Rebrand: window title + console banner clean (full audit pass still to run pre-publish)
- [ ] LICENSE files: GPL (code), CC BY-SA 4.0 (assets); ledger + credits complete
- [ ] Public README drafts for each repo
- [ ] Fresh-clone reproducibility (submodules, pipelines, build docs)
- [ ] D012 execution checklist: org, true forks (engine, dvijoke, dxvk), private→public flip order
- [ ] Hosting comparison doc (Vercel/Railway/Modal/other) — decision only, no deploy
