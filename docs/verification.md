# Current polish verification

Local evidence recorded 2026-09-05 in the Chromium in-app browser on the
development Mac. The current local playtest candidate is `1df03a19fdd9`. Earlier
candidate results are identified below; they are retained evidence, not a
claim that every diagnostic was rerun after each subsequent change.

## Menu and disabled-state follow-up

Player screenshots exposed a redundant main-menu frame and content panel,
plus command availability that relied too heavily on grayscale portraits.
The follow-up removes both menu boxes, retains a full-screen contrast wash,
and adds an outlined padlock to unavailable commands and faction deployment
buttons. Web buttons use the same shape cue, readable neutral text and dashed
borders; disabled buttons no longer receive active hover colors.

Candidate `15907462d540` was observed in an ordinary Field Orientation game:

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

Candidate `1df03a19fdd9` adds the faction deployment badge. The final menu has
neither extra box; Field Training remains selected without a lock, the
unavailable Jackal deployment has a lock and ignores clicks, and Meridian
deploys normally. Its headquarters command locks were also checked visually.
In ordinary training, a player-built Directorate displayed its lock and
RECHARGING 2:04, then a readable sweep at 0:34 and 0:05. After natural recharge
the heading changed to POWER READY and the lock disappeared. Choosing the
power and targeting revealed ground started RECHARGING 2:30 and restored the
lock. No browser error-level logs were reported during this final run.
Settings confirms build `1df03a19fdd9` and clearly distinguishes the enabled
Save checkpoint from locked Resume checkpoint in the same row. The follow-up
engine revision is `4d68b9ef6ae95322229520c79469f5fe12c622f8`, pinned by the
parent `codex/product-polish` branch.
The final WASM build, six web-state tests, six packaging tests and all voice,
content and map gates pass. Stage size is 66,730,332 bytes, below 64 MiB.
The unchanged keyboard implementation retains the earlier 16-case evidence
below; those cases were not repeated for this presentation-only follow-up.

## Automated local gates

Candidate `2a5fb93551f9` passes the full WASM build, six web-state tests, six
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

Run commands are in [CONTRIBUTING.md](../CONTRIBUTING.md). These checks do
not establish final balance, presentation or the full release matrix.

## Native missions and faction mechanics

Candidate `6375e6bfb189` passed all seven native mission success cases,
all seven mission failure cases and the three additional HQ-loss failures.
Each asserted the actual native result callback; no `MISSION_CHECK FAIL`
was reported. The same candidate's power fixtures passed: Precision Strike
inflicted 550 damage and Tunnel Ambush spawned five infantry. These fixtures
explicitly satisfy prerequisites or advance timers; they do not prove the
normal player targeting flow or a human mission playthrough.

Both supply fixtures failed on `6375e6bfb189`. A steering defect was corrected
in the later candidate whose ID begins `6b10`. On that build, native production,
gathering and delivery passed for both factions:

| Faction | Observation at 60 seconds | Income detail |
|---|---|---|
| Meridian | 39 crates removed; maximum observed cargo 4 | Cash delta $2,100, including $300 passive income |
| Jackal | 22 crates removed; maximum observed cargo 2 | Cash delta $1,240, including $240 passive income |

Totals include the opening hauler as well as the produced truck. They must
not be presented as the throughput of one newly trained unit. Full depletion,
reassignment, supply raids and balance remain separate checks.

## Observed player flows

On `6375e6bfb189`, a normal menu deployment into Field Orientation proceeded
through HQ selection, production of two Fabricators, Power Array construction
and starting an Exchange. Saving, fully reloading the page and choosing Resume
checkpoint restored the correct Field Orientation identity and stage 1, a
3:20 battle time, existing structures and the Exchange foundation, $3,500 and
the native HUD. The earlier save-map identity/control-bar defects are therefore
covered by an observed round trip. The resumed Exchange construction
subsequently completed successfully.

On the `6b10` candidate:

- Deploying diagnostic Field Orientation through the normal menu reached the
  native debrief, then the Victory report; Retry opened a fresh training match.
  This verifies the same-faction retry path.
- Fullscreen and returning through Settings/Escape worked.
- Pressing P to pause, opening Settings and closing it with Escape preserved
  the paused 10:47 clock; pressing P again resumed the match.

On `db2a99b4c142`, Control+1 assigned nine selected units to group 1 with
visible group labels. After deselecting, bare 1 recalled all nine. A right-click
move order moved the whole selected army. The Jackal Chop Shop produced two
Mongrels through its normal UI. With four units queued, two finished, one active
entry was cancelled with a refund and one remained pending.

The attack-move button initially failed to enter targeting mode on this build.
The missing `NEED_TARGET_POS` declaration was corrected, covered by the validator
and restaged as `a89d614eaa5c`. On that candidate, Q selected seven Jackal units;
clicking Attack Move and then revealed ground moved the army with its selection
retained. The I shortcut selected and centered the original Rigger and displayed
eight construction portraits. The earlier targeting failure is resolved.
Settings also remapped the idle-worker action from I to J; after Restart,
the native hint displayed J and pressing J selected/centered the Fabricator.

On `a89d614eaa5c`, an ordinary builder placement constructed a Jackal Watchpost.
Progress was observed at 63%, then the original tower finished and the centered
“Construction complete.” toast appeared, including in the accessibility tree.

The same candidate passed a player-input Tunnel Ambush check after 120 seconds
elapsed naturally: select Den, click the power button, then left-click open
explored ground. Five infantry spawned (unit count 8 → 13), with selection
retained. This adds targeting and natural recharge evidence to the native fixture.

On `9294283038c0`, Precision Strike passed the player-input flow after its
150-second recharge elapsed naturally. At current frame 4505, its ready frame
was 4500 and the button was enabled. Clicking the power button set the pending
command to `Command_WPPrecisionStrike`; clicking empty explored ground accepted
the target. At frame 6719 the next-ready frame advanced to 11216, the button
became disabled and the pending command cleared. A new impact scorch appeared
on the ground, while the Directorate selection remained intact. The initial
unsuccessful attempt was not reproduced. The transient three-second warning was
not captured, so its readability remains unverified.

The final `2a5fb93551f9` candidate visibly displayed RECHARGING 1:51 at 0:39,
RECHARGING 0:01 at 2:29 and POWER READY at 2:44. The ready heading fit its
existing bounds. Clicking the power and empty explored ground fired another
strike, produced a new scorch and displayed RECHARGING 2:22 at 3:28. This
verifies the native ready/cooldown presentation. Q selecting the army resets
the heading to ORDERS. The POWER REQUIRED condition
and transient warning readability remain separate checks.

A normal Field Orientation checkpoint round trip also passed on `9294283038c0`.
The HQ trained a Fabricator, which built a Power Array. Saving through Settings
updated the persistent checkpoint timestamp. A full page reload enabled Resume;
the correct Field Orientation briefing opened, and Return restored stage 1's
Exchange/power/Porter objective, 2:46 time, $4,850, one Fabricator, two structures,
16 power and the native HUD. The remapped J hint remained intact. This run
restored a completed Power Array; the earlier `6375e6bfb189` run separately
covered a foundation that resumed and completed construction.

Both commander-trial result destinations passed through ordinary menu controls
with diagnostic mission outcomes. On `9294283038c0`, Engage → Commander Trials
→ Hostile Takeover → Deploy Jackal reached the native win at three seconds,
the correct web debrief/story/stats, the native Victory report and Continue →
main menu. On `2a5fb93551f9`, Meridian's Glass Rampart followed the corresponding
menu → deployment → native win → debrief → Victory report flow; Change
Battlefield returned to the correct deployment screen. Final trial preview
titles and summaries fit, with the full briefings preserved. These are navigation
checks, not human mission completions. The diagnostic operation record remained
0/4 because fixture outcomes do not write progression.
The primary final stage also opened the ordinary main menu without
diagnostics and with a fresh 0/4 operation record. The independent checkout
provides build/staging evidence; its compiled candidate was not browser-tested.

The Jackal native art review on `db2a99b4c142` contained 22 fixtures with zero
missing models. Original structures, infantry, vehicles and both Jackal airframes
were visible, with distinct rust tones and silhouettes. Meridian was reviewed
on the `db2a99b4c142` and `9294283038c0` scenes: 23 fixtures, zero missing models,
all building/unit rows visible, including white/gold architecture, infantry,
armor/support units and both airframes. Q selected nine combat units; vehicles
steered and aircraft flew.

The crowded `6b10` scene also showed firing, explosions, smoke, ground scorches
and dark wrecks; those wrecks later expired. These observations cover real
motion and several combat states, not every lifecycle condition. Rendered model
and portrait contacts were also reviewed.

Both final browser tabs reported an empty console-error list. See
[perf.md](perf.md) for the separate isolated crowded-battle measurement.

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
`6375e6bfb189`, including the additional cases indicated here:

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
all recursive pins resolved. Its candidate `a50ecbb361a0` is 66,734,559 bytes,
159 bytes larger than primary candidate `2a5fb93551f9` and below 64 MiB.
That independent artifact was not browser-tested. The current playtest build
and the later visual follow-up are identified at the top of this document.

A fresh recursive GitHub clone at root `5ad409c`, engine `d04deed8` and
DXVK `538cb703` passed all 12 tests and content/gameplay/voice gates. The
documented Emscripten configuration, full 1,279-step clean engine build and
staging also passed. Its candidate was `8b0a011a5989`, 66,729,527 staged
bytes. Different compiled bytes from the primary checkout demonstrate a
working clean build, not byte-identical compilation. The final checkout reused
that independently built tree for its incremental build after fetching the
subsequent fixes; it was not a second full clean build.

All 471 final manifest entries, engine files and the font were checked against
their declared hashes and lengths. Local HTTP HEAD checks returned 200:
HTML/build metadata use no-cache; WASM uses application/wasm and JavaScript
uses text/javascript with immutable one-year caching. Bundled notices also
passed the packaging checks. The current stage is identified by
`webstage/build.json`; [perf.md](perf.md) records its exact size.

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
and real-network loading. Keep the independent gates
in [publish-checklist.md](publish-checklist.md) open until their complete
requirements have evidence.
