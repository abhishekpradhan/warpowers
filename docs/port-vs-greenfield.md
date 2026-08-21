# Fork vs Greenfield — D001 Trade Study

Triggered 2026-08-21 by a fair challenge: "no forking/copying EA code could be a very expensive decision." The v0.1 brainstorm dismissed the fork path too quickly. This is the honest re-examination, based on newly verified facts.

---

## 1. Verified facts (2026-08-21)

**The license is cleaner than assumed.** EA's release is genuine, unmodified **GPL v3**. The "additional terms" ([LICENSE.md](https://github.com/electronicarts/CnC_Generals_Zero_Hour/blob/main/LICENSE.md)) are only: no EA trademarks or claimed affiliation, preserve the notices, indemnify EA only if you voluntarily assume contractual liability, **mark modified versions as modified and don't call them the original**, warranty disclaimer. No non-commercial clause. No field-of-use restriction. **No requirement to use EA's assets.** A standalone, renamed, total-conversion game on this engine is unambiguously permitted — the origin-marking term practically *demands* the new name we want anyway.

**EA's assets are unusable either way.** The repo is code-only (no INI, no maps, no art). The [EA modding FAQ](https://www.ea.com/games/command-and-conquer/news/modding-faq) grants asset use only as a *revocable, non-commercial* license *inside mods of the owned game* — and music never. So **a full replacement asset set is mandatory in both paths**. (This is the pivotal fact — see §3.)

**Faction-scale conversion needs no C++.** Every classic total-conversion mod (Rise of the Reds, Shockwave, Contra) was built while the source was still *closed* — Rise of the Reds added two entire new factions through INI + art alone. The engine's data layer demonstrably supports building "a different game" without touching engine code. A maintained (beta) [Blender W3D import/export plugin](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin) exists for the model format.

**The fork has a living upstream, but a shaky web layer.** [TheSuperHackers](https://github.com/TheSuperHackers/GeneralsGameCode) is an active de-facto mainline (CMake, VS2022, Windows+Linux; macOS "future plans" — GeneralsX covers Mac today). But the browser ports we'd stand on are young: wasm-generals has **2 stars**, an unverified "MIT with proof-of-usage condition" on its web layer, and self-reported claims; GeneralsXWeb is one person's "experimental, expect glitches."

**Greenfield's scary precedent is real but disanalogous.** [OpenSAGE](https://github.com/OpenSAGE/OpenSAGE) (C# SAGE reimplementation) is 5–9 years in, multi-contributor, and still "a long way from anything playable." *But* it targets full compatibility with original assets/INI/maps — reimplementing all of SAGE's surface. Our greenfield builds a small bespoke game with zero compatibility burden. Different beast — though a real warning against scope creep.

**Nobody occupies the niche in either direction.** No free-asset replacement project exists (SuperHackers listed one as an aspirational someday-goal; zero replies). Whichever path we take, an assets-included browser Generals-like is first-of-its-kind.

## 2. What the fork path actually looks like (steelmanned)

Fork TheSuperHackers as engine base (native builds for dev iteration; GeneralsX for macOS), deliver to browser via the proven Emscripten lineage. Build the game as the mods did: **our own INI data (factions, units, balance), our own W3D assets, our own maps, new name and UI skin**. Ship standalone under GPL v3 + EA's terms (source public, marked as modified, no EA marks). Our assets can still be CC BY-NC — GPL binds the code, not the art. Modern web UX lives in a TS shell *around* the canvas (site, menus, lobby links); the in-game HUD stays engine-rendered (WND scripts — reskinnable, not modern). C++ only where INI's vocabulary runs out. The original's deterministic lockstep already exists; NewShoes proved WebRTC transport works.

**What this buys:** the *actual* 20-years-debugged Generals feel — pathfinding, projectile physics, AI, balance grammar — free and perfect on day one. A working game to mutate instead of a void to fill. Plug-in access to the existing modding community and its skills.

**What this costs:** GPL v3 forever (MIT off the table; one pasted file makes this true in the greenfield path too, hence the standing guardrail). Dev loop = CMake/vcpkg/Emscripten C++ toolchain on a Mac for a Windows-born engine, with our web layer forked from a 2-star project. The in-game experience is architecturally capped at "2003 with a nicer wrapper." And identity: mechanically it *is* Zero Hour, renamed and reskinned — which collides with the brief's "won't be the same game exactly."

## 3. The reframe that shrinks this decision

**The most expensive components are path-independent.** Both paths require, from zero: every model, texture, animation, sound, voice line, music track, UI art set, map, and the entire faction/unit/balance design. That content is plausibly the *majority* of total project cost — and it **transfers between paths** (Blender sources export to W3D or glTF; design docs are engine-agnostic). The paths only truly diverge on: engine code, license, dev experience, and identity.

Corollary: **choosing greenfield does not burn the fork option.** If greenfield's engine work stalls, we flip to the fork and keep all content and design. The reverse migration (fork → greenfield later) also preserves content, but abandons accumulated C++/INI/WND investment. Greenfield-first keeps more optionality; fork-first delivers playability sooner.

## 4. Honest side-by-side

| | **A — Greenfield (TS)** | **B — Fork total-conversion** |
|---|---|---|
| Time to *our own* rough playable skirmish in browser | ~3–6 months (engine M0/M1 + content) | ~1–3 months (content-dominated; engine works day one) |
| Feel authenticity | Execution risk — recreated by taste; the place greenfield RTS projects die | Perfect by construction |
| "Not the same game exactly" | Native — mechanics are ours | Capped — it *is* ZH mechanically; INI rebalance ≠ new game |
| Modern experience ceiling | None — HUD, onboarding, netcode, mobile all native | Web shell modern; in-game UI/UX architecturally 2003 |
| Dev loop | Vite hot-reload, TS end-to-end, agent-friendly | CMake/vcpkg/Emscripten C++ on macOS + INI/WND/W3D; native rebuilds fast, web builds slow |
| Netcode | Build lockstep ourselves (designed-in from day 1) | Original lockstep exists; WebRTC transport proven by NewShoes |
| License | MIT + CC BY-NC (as preferred) | GPL v3 + EA terms (code); assets still ours (CC BY-NC) |
| Foundation risk | Our own bugs | 1.7M-line legacy engine + a 2-star web-port layer we'd co-maintain |
| Differentiation | New game in the Generals idiom — empty lane | "ZH, free, in a browser, no files needed" — also an empty lane, but adjacent to 4 existing ports that could add free assets too |
| Failure mode | Engine hobbyism: years of tech, no game | Legacy quicksand: shipped fast, plateaus as a renamed ZH; every modern ambition fights the engine |

## 5. The real question

These aren't two implementations of one product — **they're two different products:**

- **B is "free Zero Hour, essentially"** — a preservation/content play. Fastest route to real players feeling real nostalgia. A genuinely great project… that is 90% *content creation* and 10% web-shell engineering, on someone else's engine, forever GPL.
- **A is "a new game that channels Zero Hour"** — the product the original brief describes: modern experience, modern stack, our mechanics, our identity. Slower to first playability, with engine-feel execution risk concentrated in M0/M1.

## 6. Recommendation

**Stay greenfield — but demote "never" to "bounded bet with a live fallback":**

1. **D001 stands** for the brief as written ("won't be the same game exactly", "modern experience", "modern stack"): three of the brief's four pillars point at A; only cost points at B — and §3 shows the cost gap is mostly the *engine schedule*, not the majority of the work.
2. **The fork becomes our reference harness, not a rejected path.** We run the original (SuperHackers/GeneralsX native + owned retail copy) side-by-side for feel calibration and mechanics study. Read the GPL source freely to *understand*; copy nothing (that discipline is what keeps MIT alive).
3. **Explicit kill-criteria on M0** (the feel spike): if after ~4 weeks of focused M0 work, unit movement/selection/combat doesn't feel convincingly good, or the sim can't hold ~400 units at budget on target hardware — **we flip to Path B** and carry every asset and design document with us. The fallback is real, priced, and stays open indefinitely.
4. AI-assisted development changes A's historical base rate: OpenSAGE-style multi-year estimates come from pre-AI, compatibility-burdened efforts. A bespoke 2-faction TS sim is a different, much smaller object.

**Flip to B instead if** the goal has genuinely shifted to "get the ZH experience to players ASAP and spend the project on content, not engineering." That's a legitimate, coherent project — it's just a different one than the brief. A middle option also exists: a **1-week validation spike on B's crux risks** (does Blender-exported W3D actually load in-engine? does the web build run sanely on our Mac with our own data?) before final commitment — buys certainty at the cost of a week.
