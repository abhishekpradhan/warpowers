> **Historical record.** Verification notes for the September 2026 polish
> candidates, moved from `docs/verification.md` on 2026-09-07 and no longer
> updated; current test procedures are in [testing.md](../testing.md).
> Staged build identifiers were replaced by candidate numbers in order of
> first mention when this record was archived; commits are in git history.

# Polish verification (September 2026)

## September 5 — licensing and release packaging

Local candidate #1 contains 470 data files and is 66,918,344 bytes.
It reuses the previously built engine; no engine source changed. The unused
root `ExtrasMenu.wnd` was removed, its historical GPL provenance corrected,
and 17 browser dependency notice files added with a versioned inventory.

All 28 web tests, 15 packaging tests and the voice/gameplay/content staging
checks pass. Packaging tests cover missing notices preserving the previous
stage, notice-path containment, public-release source requirements, malformed
source URL rejection (including invalid ports), and notice or source-link
changes updating build identity without invalidating saves.
The native keyboard, sentence, mip-filter, surface-copy and browser renderer
resource harnesses also pass all 186 checks.
All 470 staged asset hashes and the final notice contents match their inputs;
the removed menu is absent. The source record identifies development status.

The in-app Chromium browser on `http://localhost:8322` passed boot, settings,
Field Orientation deployment, pause/resume and abandonment back to the main
menu on candidate #2. The final candidate changes only notice
inventory metadata from that smoke-tested package; its credits were reloaded
and the final build identifier verified. No browser console errors were
recorded. All 27 local credits links returned HTTP 200 and exact staged bytes
on the smoke-tested candidate. This is a bounded menu/credits smoke check,
not a full match or cross-browser release certification.

The project had not been released at the time of writing. Corresponding-source
preparation, clean rebuild verification, signed-out public access and the
maintainer's manual deployment remained open release gates (now [RELEASING.md](../../RELEASING.md)).

## September 5 — completed text and texture repairs

The unfinished crash investigation contained reproducible defects in shared text
layout, D3DX mip generation and the browser renderer. The repaired source now
keeps a mip surface referenced through its last copy, propagates failures, and
retains texture storage while callers still hold level surfaces. Copies validate
all rectangles before writing, honor separate row pitches and block rows, and
reject overlapping frontend self-copies. Linux mip staging reads only level
zero. Rectangular mip chains continue through their one-pixel tails. Text layout
handles trailing ampersands and independently optional hotkey coordinates;
centered hotkeys use their actual rendered line after wrapping. These are
confirmed fixes, rather than additional surface-release logging.

Release candidate #3 and the separate local ASan candidate
candidate #4 both compile and link. The final normal package is 66,773,830
bytes (63.681 MiB), with all 471 data hashes plus engine/font hashes verified;
the disposable sanitizer package is larger and is not a release package. The
native macOS Zero Hour target also builds successfully (320-step incremental
build, inherited warnings); a native gameplay run was not performed. The
following production-code regressions pass:

- 32 sentence-layout/glyph cases under ASan/UBSan; the previous revision
  reproduces both trailing-ampersand overreads and both nullable-output errors.
- 71 mip-filter ownership/error checks, with the previous revision failing the
  same ownership assertions.
- 40 surface-copy cases on the manual path and 40 with the real cached GLI
  headers, including row padding, block-compressed regions and narrow mip tails.
  The previous revision fails the row-copy negative control. Existing GLI
  sampling/quantization behavior is retained; these tests are not a claim of
  pixel-identical filtering across backends.
- 27 browser-renderer copy/lifetime cases under ASan/UBSan, including retained
  surfaces after texture release and invalid later rectangles leaving output
  untouched; 16 existing keyboard cases also pass.
- 28 web tests, nine packaging tests and all voice/content/17-map gates pass.

In the Chromium in-app browser, the ASan build passes
`/?autotest=retry&retryruns=1&retryframes=5400`: paid construction/production, a
real Porter supply delivery, eight observed UI selections, stage 4, an
explicitly injected headquarters loss at 3:00, the native defeat screen, Retry
and a new stage-0 battlefield with a selected headquarters. The result is `RETRY
PASS completed=1/1`; no sanitizer report or error-level browser log was
observed. The final release retains the existing inter-word spacing adjustment;
all 32 sanitizer text cases also pass on that final source. On the final
release, `/?autotest=retry&retryruns=2&retryframes=14400` passes two consecutive
eight-minute matches in one runtime, with ASan and surface tracing disabled.
Both runs reach real supply, completed army and Directorate, training stage 4
and the full `uiSelectionMask=0xff`. Each then injects headquarters loss at
frame 14,400, reports defeat at 480 seconds, waits on the native score screen
and invokes its Retry callback. The first restarted battlefield completes the
entire opening again; the second Retry returns a fresh stage-0 map with selected
headquarters and visible HUD: `RETRY PASS completed=2/2 phase=3 frame=90`. The
final screenshot shows training step 1, $6,000 and an intact headquarters. No
error-level browser logs or crash recovery screen appeared. These are controlled
losses, with normal combat and hauling beforehand, not two human-played defeats.

The normal web-debrief path also passes on candidate #3. With
`/?autotest=defeat`, pointer/DOM input opens Operations → Field Orientation →
Review deployment → Deploy Meridian Combine. The diagnostic injects a loss at
0:10 and the ordinary OPERATION FAILED web debrief appears. Clicking Continue to
battle report opens the native DEFEAT report; clicking its Retry button returns
training step 1. The restarted clock advances to 0:19, and no error-level
browser logs appear. Thus the Retry diagnostic's modal bypass does not hide a
broken player-facing debrief flow. The final page is restored to the ordinary
main menu, without diagnostic URL parameters. CPU checks and this bounded ASan
run do not establish a complete human or cross-browser playtest.

## Review before merging to main

The September 5 merge review covers the complete game, engine and native
renderer polish branches against their private forks' `main` branches.
It found and corrected two additional failures:

- Browser recovery previously called the native pause export while handling
  an engine failure. If that export also threw, the recovery UI never appeared.
  Failure handling now stays in the browser, disables subsequent native entry
  points and ignores late lifecycle callbacks so Reload and diagnostics remain
  available. This is an error-recovery fix, not a fix for the intermittent
  native Retry crash documented below.
- The stager's legacy `GeneralsXZH.wasm` marker could mistake the compiler
  output directory for a replaceable web stage. It now rejects compiler/source
  trees and repository roots before checking stage markers. Isolated fixtures
  verify that those directories survive rejection and safe custom legacy
  stages remain replaceable.

The engine quick-start also now uses the standard `http://localhost:8322`
URL and describes the MIME/cache headers the server actually sends. Engine
lifecycle/rendering/input review found no additional confirmed blocker;
the previously disclosed intermittent native Retry crash was still open at that review; the later repairs and verification above supersede that status.

Reviewed candidate #5 stages at 66,761,316 bytes (63.669 MiB),
with engine `5f4f3417` and renderer `538cb703`. The native WebAssembly build,
27 web tests, nine packaging tests, 16 production keyboard cases and all
voice/content/17-map gates pass. The final Chromium browser smoke check
boots the main menu, deploys Field Orientation, opens/closes the briefing,
reopens guidance and returns from its all-steps overview without browser
errors. A normally completed Fabricator advances guidance to step 2.
The new recovery and staging regressions also fail against the pre-fix
`8eba37e` source in isolated temporary fixtures, confirming both detect their
reported bugs. This bounded merge check supplements the earlier playtest evidence;
it does not claim another full campaign walkthrough or native crash fix.

## Earlier feedback verification

Local evidence recorded 2026-09-05 in the Chromium in-app browser on the
development machine. The previous feedback candidate was candidate #6. Earlier
candidate results are identified below; they are retained evidence, not a
claim that every diagnostic was rerun after each subsequent change.

## Command contrast, guidance and local server follow-up

Candidate #7 addresses the next player-feedback pass. Available
command portraits have brighter color artwork and a gold rim. Unavailable
portraits receive a separate dark veil because native grayscale rendering
ignored the previous vertex tint. Their padlocks remain; recharge keeps its
color and sweep, with a lighter veil. The opt-in image mode is implemented
in both base and Zero Hour display paths, with batch transitions restoring
normal modulation. The base native runtime was not exercised in this pass.

In ordinary Field Orientation play at 1280×720:

- Headquarters, builder, Exchange and Vehicle Plant orders visibly distinguish
  available actions from locked technology and busy-builder commands.
- A normally trained Fabricator advances guidance to step 2. An Exchange
  foundation stays at 0/1; completing it shows 1/1 and changes the advice to
  the Power Array. Completing that changes the advice to the missing Porter.
- Training a Porter advances to step 3 while guidance is collapsed; the
  persistent Guidance button updates to 3/5. The Vehicle Plant counts only
  after completion. Two trained Vectors advance to step 4, and a trained
  Vigil advances to the assault guidance at step 5. No test injections or
  forced mission counters were used for this sequence.
- Collapse/reopen, All steps, returning to current guidance and the automatic
  opening setting behave consistently. Manual opening works with automatic
  opening off; re-enabling it brings guidance back. The overview distinguishes
  completed/current/upcoming steps and does not advance gameplay.
- At 125% overlay text the full compound-economy checklist and its action are
  readable. Guidance has a vertical scroll bound above the native command bar
  for shorter viewports; smaller viewport dimensions were not exercised.
- A normally built Directorate displays its recharge countdown, sweep and
  padlock together at 1:11 remaining. The unattended assault subsequently
  lost its headquarters; this pass does not claim a full training victory or
  a newly verified transition to power readiness. No missing assets or browser
  errors were observed during those checks. A subsequent Retry exposed the
  intermittent native surface-destruction crash described below.
- An isolated QA-origin checkpoint saved during step 2 survives a full reload
  and restores the correct step and unmet economy requirements. The existing
  checkpoint on the original test origin was left untouched.

The 213-step incremental WASM build, 23 web tests, six packaging tests and
voice/content/17-map gates pass. New tests cover partial and two-unit training
requirements, native-stage authority after losses/restore, frame-reset battle
identity, current controls and persistent battle tips. The map validator also
checks guidance requirements against decoded native training gates. The stage
is 66,748,532 bytes (63.656 MiB), below 64 MiB.

After the normal training loss at 7:27, debrief → battle report → Retry failed
with `SurfaceClass::~SurfaceClass` → `Render2DSentenceClass::Reset` → window
destruction and a WASM `null function` exception. The same signature was
recorded in August; the stack alone does not establish an over-release.
Diagnostic candidate #8 adds opt-in outer-surface generation/vtable checks
before virtual dispatch, without suppressing releases. Its short normal-menu
training defeat → report → Retry sequence passes with tracing enabled. That
short pass does not resolve the intermittent longer-run failure. A subsequent
normal 7:56 training battle in the same traced runtime completed all five
guidance stages, built a Directorate and lost its headquarters to the enemy.
Debrief → report → Retry again reached a live battlefield with guidance reset
to step 1 and no trace violations or browser errors. Tracing changes allocation
layout; no corrective lifetime change had been identified at that point.
The later confirmed repairs and current verification are recorded above.

Candidate #6 retains that native build and adds a training recovery
hint when a required structure is missing and the native builder count is zero.
It advises training a replacement or waiting for an already queued Fabricator,
without changing the mission stage. All 25 web tests, six packaging tests and
voice/content/map gates pass; the stage is 66,760,647 bytes (63.668 MiB).
Its ordinary menu/training view confirms the command contrast, collapse/reopen,
all-steps overview and manual opening with automatic opening disabled. No
browser errors occurred in that focused final-build check.
The parent pins engine `b3c6f36ab554cd4f13e240633c0759e5028a8000`;
the command/telemetry and diagnostic changes are separate engine commits.

The two listeners were separate `tools/serve.py` processes serving the same
stage: the earlier QA server on 8321 and the player server on 8322. The former
was stopped; only 8322 remains. Server defaults, startup text and contributor
instructions now use `http://localhost:8322`. A duplicate invocation exits with
a readable occupied-port error. Browser storage belongs to an origin, so QA
uses isolated origins/profiles without adding a second server.

## Open access and portable records

Candidate #9 removes completion-based access requirements in the
browser journal, metadata and native deployment callbacks. All seven authored
missions are available immediately; story order is a recommendation (D023).
Assigned-side missions show their actual faction and deployment action;
skirmish retains both choices. In-match prerequisites, funds and cooldowns
are unchanged. The earlier faction-lock presentation below is superseded.

Observed through ordinary browser controls on the isolated QA origin:

- With 0/4 campaign completions, all seven journal deployment actions were
  enabled. Selecting operation 4 opened Jackal deployment, then its briefing
  and actual battlefield with the correct air-defense objective. The QA
  record already had a training result; no campaign prerequisite was satisfied.
- Operation 1 showed only Meridian's button and brief. Advancing to operation
  2 showed only Jackal's. Choosing Skirmish restored both buttons and briefs.
- Importing a record fixture marked operation 2 complete at 10:20. Merging a
  second fixture retained the existing training result, improved operation 2
  to 9:50 and added operation 4 at 12:00. A malformed JSON file displayed an
  error and left those results unchanged.
- Download record produced a real 648-byte JSON file, validated against the
  backup schema. Restoring that exact file preserved the three entries and
  best times. Full reload retained the 2/4 campaign count and results. These
  fixture results are QA data, not claims of completed human playthroughs.

Candidate #10 retains the same native build and adds record
preservation across game tabs and legacy map identifiers. On two isolated
QA tabs, importing a legacy `WPOp01` win alongside a newer `op01` loss showed
the preserved 11:00 completion in both journals. Importing operation 3 at
11:40 in the second tab updated the first without a reload. Restoring the
older three-entry download retained all five newer entries, and downloading
again produced a validated 996-byte file with canonical IDs and one win per
mission. A full reload retained the results. Both tabs reported no browser
error-level logs. These imported completions remain QA fixtures.

The WASM build, 17 web-state/record tests, six packaging tests and all content,
voice and map gates pass. Record tests cover non-destructive/idempotent merge,
round trips, invalid versions and fields, unsafe/inherited IDs, bounded stats
and dates, 64 KiB files, the 128-mission union limit, legacy aliases and
tolerant recovery from malformed local records. Final stage size is
66,740,374 bytes (63.649 MiB), below 64 MiB. The parent branch pins engine
revision `a12dc3d2c3afb7abbe51a1431b0c5fdfd133e2b8`. Record backups exclude
settings and battle checkpoints; they do not provide account sync or recover
files never backed up.

## Menu and disabled-state follow-up

Player screenshots exposed a redundant main-menu frame and content panel,
plus command availability that relied too heavily on grayscale portraits.
The follow-up removes both menu boxes, retains a full-screen contrast wash,
and adds an outlined padlock to unavailable commands and faction deployment
buttons. Web buttons use the same shape cue, readable neutral text and dashed
borders; disabled buttons no longer receive active hover colors.

Candidate #11 was observed in an ordinary Field Orientation game:

- Vector and Bastion portraits have locks for missing prerequisites. Clicking
  the locked Vector does not queue it or spend money; its Vehicle Plant
  prerequisite tooltip remains readable.
- Available Fabricators queue without locks. Cancelling an active entry
  refunds $450; another queued Fabricator completes. Empty queue slots stay blank.
- Spending down to $150 locks unaffordable units while the affordable Vigil
  remains unmarked. A cancellation returns funds to $600 and clears the
  corresponding locks; prerequisite locks remain. The builder's construction
  grid also distinguishes affordable orders from locked ones.
- Disabled Save/Resume checkpoint buttons display the padlock and dashed
  border at full text opacity, retain native HTML disabled semantics, and do
  not show an enabled gold fill.

Candidate #12 adds the faction deployment badge. The final menu has
neither extra box; Field Training remains selected without a lock, the
unavailable Jackal deployment has a lock and ignores clicks, and Meridian
deploys normally. Its headquarters command locks were also checked visually.
In ordinary training, a player-built Directorate displayed its lock and
RECHARGING 2:04, then a readable sweep at 0:34 and 0:05. After natural recharge
the heading changed to POWER READY and the lock disappeared. Choosing the
power and targeting revealed ground started RECHARGING 2:30 and restored the
lock. No browser error-level logs were reported during this final run.
Settings confirms build candidate #12 and clearly distinguishes the enabled
Save checkpoint from locked Resume checkpoint in the same row. The follow-up
engine revision is `4d68b9ef6ae95322229520c79469f5fe12c622f8`, pinned by the
parent polish branch.
The final WASM build, six web-state tests, six packaging tests and all voice,
content and map gates pass. Stage size is 66,730,332 bytes, below 64 MiB.
The unchanged keyboard implementation retains the earlier 16-case evidence
below; those cases were not repeated for this presentation-only follow-up.

## Automated local gates

Candidate #13 passes the full WASM build, six web-state tests, six
packaging tests, 16 native keyboard cases, voice lint, content-reference checks and
the independent map validator.

- Web-state tests cover malformed/blocked storage, settings bounds, command
  remapping, explicit-win progression, safe identifiers and time/map normalization.
- Packaging tests cover repeatable hashes, content references and notices,
  UI/save compatibility, engine-glue release identity, protected output paths
  and rejection of oversized candidates without replacing a working stage.
- Keyboard cases exercise production event-state methods for left/right
  Ctrl/Shift/Alt, chord ordering, release and repeat handling. They do not
  substitute for the observed browser input flows below.
- Voice lint checks 80 distinct events across 21 templates and shared-pool rules.
- Content checks cover native model/texture/icon/window references and operations.
- Map validation independently decodes all 17 binaries, checks seven mission
  success/failure/tie cases, native condition/action signatures, paid AI responses,
  supply/counter/budget contracts and traversable routes with cliff clearance.

Run commands are in [CONTRIBUTING.md](../../CONTRIBUTING.md). These checks do
not establish final balance, presentation or the full release matrix.

## Native missions and faction mechanics

Candidate #14 passed all seven native mission success cases,
all seven mission failure cases and the three additional HQ-loss failures.
Each asserted the actual native result callback; no `MISSION_CHECK FAIL`
was reported. The same candidate's power fixtures passed: Precision Strike
inflicted 550 damage and Tunnel Ambush spawned five infantry. These fixtures
explicitly satisfy prerequisites or advance timers; they do not prove the
normal player targeting flow or a human mission playthrough.

Both supply fixtures failed on candidate #14. A steering defect was corrected
in the later candidate #20. On that build, native production,
gathering and delivery passed for both factions:

| Faction | Observation at 60 seconds | Income detail |
|---|---|---|
| Meridian | 39 crates removed; maximum observed cargo 4 | Cash delta $2,100, including $300 passive income |
| Jackal | 22 crates removed; maximum observed cargo 2 | Cash delta $1,240, including $240 passive income |

Totals include the opening hauler as well as the produced truck. They must
not be presented as the throughput of one newly trained unit. Full depletion,
reassignment, supply raids and balance remain separate checks.

## Observed player flows

On candidate #14, a normal menu deployment into Field Orientation proceeded
through HQ selection, production of two Fabricators, Power Array construction
and starting an Exchange. Saving, fully reloading the page and choosing Resume
checkpoint restored the correct Field Orientation identity and stage 1, a
3:20 battle time, existing structures and the Exchange foundation, $3,500 and
the native HUD. The earlier save-map identity/control-bar defects are therefore
covered by an observed round trip. The resumed Exchange construction
subsequently completed successfully.

On candidate #20:

- Deploying diagnostic Field Orientation through the normal menu reached the
  native debrief, then the Victory report; Retry opened a fresh training match.
  This verifies the same-faction retry path.
- Fullscreen and returning through Settings/Escape worked.
- Pressing P to pause, opening Settings and closing it with Escape preserved
  the paused 10:47 clock; pressing P again resumed the match.

On candidate #15, Control+1 assigned nine selected units to group 1 with
visible group labels. After deselecting, bare 1 recalled all nine. A right-click
move order moved the whole selected army. The Jackal Chop Shop produced two
Mongrels through its normal UI. With four units queued, two finished, one active
entry was cancelled with a refund and one remained pending.

The attack-move button initially failed to enter targeting mode on this build.
The missing `NEED_TARGET_POS` declaration was corrected, covered by the validator
and restaged as candidate #16. On that candidate, Q selected seven Jackal units;
clicking Attack Move and then revealed ground moved the army with its selection
retained. The I shortcut selected and centered the original Rigger and displayed
eight construction portraits. The earlier targeting failure is resolved.
Settings also remapped the idle-worker action from I to J; after Restart,
the native hint displayed J and pressing J selected/centered the Fabricator.

On candidate #16, an ordinary builder placement constructed a Jackal Watchpost.
Progress was observed at 63%, then the original tower finished and the centered
“Construction complete.” toast appeared, including in the accessibility tree.

The same candidate passed a player-input Tunnel Ambush check after 120 seconds
elapsed naturally: select Den, click the power button, then left-click open
explored ground. Five infantry spawned (unit count 8 → 13), with selection
retained. This adds targeting and natural recharge evidence to the native fixture.

On candidate #17, Precision Strike passed the player-input flow after its
150-second recharge elapsed naturally. At current frame 4505, its ready frame
was 4500 and the button was enabled. Clicking the power button set the pending
command to `Command_WPPrecisionStrike`; clicking empty explored ground accepted
the target. At frame 6719 the next-ready frame advanced to 11216, the button
became disabled and the pending command cleared. A new impact scorch appeared
on the ground, while the Directorate selection remained intact. The initial
unsuccessful attempt was not reproduced. The transient three-second warning was
not captured, so its readability remains unverified.

The final candidate #13 candidate visibly displayed RECHARGING 1:51 at 0:39,
RECHARGING 0:01 at 2:29 and POWER READY at 2:44. The ready heading fit its
existing bounds. Clicking the power and empty explored ground fired another
strike, produced a new scorch and displayed RECHARGING 2:22 at 3:28. This
verifies the native ready/cooldown presentation. Q selecting the army resets
the heading to ORDERS. The POWER REQUIRED condition
and transient warning readability remain separate checks.

A normal Field Orientation checkpoint round trip also passed on candidate #17.
The HQ trained a Fabricator, which built a Power Array. Saving through Settings
updated the persistent checkpoint timestamp. A full page reload enabled Resume;
the correct Field Orientation briefing opened, and Return restored stage 1's
Exchange/power/Porter objective, 2:46 time, $4,850, one Fabricator, two structures,
16 power and the native HUD. The remapped J hint remained intact. This run
restored a completed Power Array; the earlier candidate #14 run separately
covered a foundation that resumed and completed construction.

Both commander-trial result destinations passed through ordinary menu controls
with diagnostic mission outcomes. On candidate #17, Engage → Commander Trials
→ Hostile Takeover → Deploy Jackal reached the native win at three seconds,
the correct web debrief/story/stats, the native Victory report and Continue →
main menu. On candidate #13, Meridian's Glass Rampart followed the corresponding
menu → deployment → native win → debrief → Victory report flow; Change
Battlefield returned to the correct deployment screen. Final trial preview
titles and summaries fit, with the full briefings preserved. These are navigation
checks, not human mission completions. The diagnostic operation record remained
0/4 because fixture outcomes do not write progression.
The primary final stage also opened the ordinary main menu without
diagnostics and with a fresh 0/4 operation record. The independent checkout
provides build/staging evidence; its compiled candidate was not browser-tested.

The Jackal native art review on candidate #15 contained 22 fixtures with zero
missing models. Original structures, infantry, vehicles and both Jackal airframes
were visible, with distinct rust tones and silhouettes. Meridian was reviewed
on the candidate #15 and candidate #17 scenes: 23 fixtures, zero missing models,
all building/unit rows visible, including white/gold architecture, infantry,
armor/support units and both airframes. Q selected nine combat units; vehicles
steered and aircraft flew.

The crowded candidate #20 scene also showed firing, explosions, smoke, ground scorches
and dark wrecks; those wrecks later expired. These observations cover real
motion and several combat states, not every lifecycle condition. Rendered model
and portrait contacts were also reviewed.

Both final browser tabs reported an empty console-error list. See
[perf.md](../perf.md) for the separate isolated crowded-battle measurement.

## Reproduce focused diagnostics

After staging and starting `tools/serve.py`:

- `/?map=Maps/WPTest.map&autotest=economy` — Meridian hauling.
- `/?map=Maps/WPTestJ.map&autotest=economy` — Jackal hauling.
- `/?map=Maps/WPTest.map&autotest=powers` — Precision Strike.
- `/?map=Maps/WPTestJ.map&autotest=powers` — Tunnel Ambush.

The page retains a visible diagnostic report; ordinary play does not show it.
Diagnostic outcomes do not write the player's persistent operation record.
Avoid `debug=1` unless tracing a specific engine problem: its logs are verbose.

Use `/?map=Maps/<map>.map&autotest=mission` for success and
`autotest=mission-defeat` for failure. All rows passed both branches on
candidate #14, including the additional cases indicated here:

| Map | Mission | Additional passing failure case |
|---|---|---|
| `WPTraining` | Field Orientation | — |
| `WPOp01` | First Light | — |
| `WPOp02` | Cut Wire | — |
| `WPOp03` | Long Watch | `mission-defeat-hq` |
| `WPOp04` | War Powers | — |
| `WPChallengeM` | Glass Rampart | `mission-defeat-hq` |
| `WPChallengeJ` | Hostile Takeover | `mission-defeat-hq` |

The fixtures create prerequisites, destroy named targets and advance timers
while asserting intermediate counters and the actual result callback. Require
`MISSION_RESULT PASS` and no `MISSION_CHECK FAIL`. Direct-map sessions exit
after a result. For menu/debrief/report testing, open `/?autotest=mission`
and deploy Field Orientation through the menu.

For a roster scene, use `/?map=Maps/WPTest.map&review=1` or the Jackal
`WPTestJ` map. `review=stress` creates a bounded 120-unit attack-move encounter
and reports render/logic timing and WASM heap capacity. Run it separately
from other active game tabs when measuring performance.

## Build reproduction and remaining release checks

The initial completed polish source snapshot is root `0ab5819`, engine
`05c81c9908d95f6428b14a96935694539b6c1b9d` and DXVK `538cb703`.
An independent checkout fetched these pins, passed all six web tests, six
packaging tests, 16 native keyboard cases and content/gameplay/voice gates,
then completed an incremental WASM build and staging. The tree was clean and
all recursive pins resolved. Its candidate #18 is 66,734,559 bytes,
159 bytes larger than primary candidate #13 and below 64 MiB.
That independent artifact was not browser-tested. The current playtest build
and the later visual follow-up are identified at the top of this document.

A fresh recursive GitHub clone at root `5ad409c`, engine `d04deed8` and
DXVK `538cb703` passed all 12 tests and content/gameplay/voice gates. The
documented Emscripten configuration, full 1,279-step clean engine build and
staging also passed. Its candidate was candidate #19, 66,729,527 staged
bytes. Different compiled bytes from the primary checkout demonstrate a
working clean build, not byte-identical compilation. The final checkout reused
that independently built tree for its incremental build after fetching the
subsequent fixes; it was not a second full clean build.

All 471 final manifest entries, engine files and the font were checked against
their declared hashes and lengths. Local HTTP HEAD checks returned 200:
HTML/build metadata use no-cache; WASM uses application/wasm and JavaScript
uses text/javascript with immutable one-year caching. Bundled notices also
passed the packaging checks. The current stage is identified by
`webstage/build.json`; [perf.md](../perf.md) records its exact size.

A final bounded hygiene review covered the root/engine changes at the pushed
snapshot: 16 changed text files, 638,130 bytes including keyboard fixtures.
It found no high-confidence credential patterns, absolute developer paths,
build/save/env artifacts, missing local links or removed attribution. The
root engine gitlink matched the pushed engine commit. This supplements the
earlier tracked-text scan; it is not a historical security certification.

The candidate is ready for local playtesting. Remaining release work includes
the rest of the input and lifecycle matrix, transient power-warning and
POWER REQUIRED presentation, full human training, campaign and balance
playthroughs, audio listening, other browsers/hardware, a controlled long soak
and real-network loading. The independent release gates (now [RELEASING.md](../../RELEASING.md)) stayed
open until their complete requirements had evidence.

## Performance measurements (September 2026)

Moved from `docs/perf.md` on 2026-09-07. Budgets and the measurement procedure
now live in [perf.md](../perf.md); the numbers below describe the candidates
of the time and do not certify other browsers, hardware or networks.

- The final September 5 release candidate staged at **66,773,830 bytes
  (63.681 MiB)** including engine, data, UI and notices. This is the local
  directory size, not compressed network transfer size.
- An earlier repaired bridge reached the main loop in **542 ms** on one local,
  cached development-browser run (64 ms download/compile, 343 ms data, 136 ms
  initialization). Cached local evidence, not a cold-network boot.
- A fresh recursive checkout configured, completed a 1,279-step clean engine
  build and staged **66,729,527 bytes (63.638 MiB)**; an incremental rebuild of
  that checkout at the later polish pins staged 66,734,559 bytes. Both show
  build/size reproducibility, not byte-identical compilation.

### Isolated crowded-battle sample

Candidate #20 (steering fix) ran the 120-unit attack-move fixture
(`?review=stress&map=Maps/WPTest.map`) in isolation on an Apple Silicon
development laptop with 64 GB of memory, Chromium in-app browser, Balanced
1600×900. The fixture reported 143 objects including its setup; no other game
tab was active.

| Fixture observation | Render frames/s | Logic updates/s |
|---|---:|---:|
| 9.9 seconds | 59.9 | 30.5 |
| 19.9 seconds | 59.9 | 30.3 |
| 29.9 seconds | 59.9 | 30.2 |
| 40 seconds | 59.9 | 30.1 |
| 50 seconds | 59.9 | 30.1 |
| 60 seconds | 59.9 | 30.1 |

Reported WASM heap **capacity** stayed at 512 MiB. That is the allocated
WebAssembly memory buffer, not operating-system process RSS or live allocation.
A battle was also observed around the 11-minute mark, but that was not a
controlled soak test. The one-minute sample met the intended render/logic
cadence under these conditions; it does not establish long-run memory
behaviour, worst-case late-game performance or performance on a lower-end
computer.
