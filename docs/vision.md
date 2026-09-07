# Vision

> **Direction (D018, 2026-08-23): port-parity first.** The product is the
> browser port — wasm-generals' surface without the game-files requirement.
> Everything below the Pillars describes the *bundled asset pack* and its
> long-term ambitions, not the near-term plan; the working plan lives in
> [roadmap.md](roadmap.md).

**Open a link, and 90 seconds later you're plopping down a base, hearing radio chatter, and dreading a superweapon timer.** War Powers is a free, browser-playable RTS in the *Command & Conquer: Generals / Zero Hour* idiom — built on the GPL-released engine lineage with fully original, freely licensed assets, so players need no game files, no install, no launcher, no account.

**Positioning:** every other browser project in this space is a preservation port requiring players to import ~1.9GB of game files they already own. War Powers is the first assets-included, link-to-play entry — the lane nobody else occupies.

## Pillars

1. **90 seconds to fun.** The web's superpower is zero friction. Cold load to playable skirmish stays brutally fast; every milestone ships as a URL.
2. **The real feel, legally clean.** The authentic 20-years-refined engine underneath; 100% original data and art on top. No EA bytes ever ship — that rule is what makes "no files needed" possible.
3. **Readable chaos.** Big armies, big explosions, still legible: strong silhouettes, faction color trims, disciplined VFX. Low-poly stylized art; identity carried by silhouette and palette.
4. **Data-driven everything.** Units, weapons, powers, and balance live in INI data — the engine's native modding culture is our content pipeline and, eventually, the community's.
5. **Keep the fantasy, not the jank.** 2003's design sensations, not its input latency, UI clunk, or install friction.

## The nostalgia checklist

What specifically made Generals feel like Generals — our design backlog:

**Economy** — finite supply piles with a visible gatherer loop; raidable supply lines; no population cap (money is the cap); capturable derrick-style tech buildings; alternate passive income; sell-back.

**Base building** — builder units construct anywhere (no grid adjacency); scaffold build-up animations; a power grid with brownout penalties — and one faction that famously needs no power; base defenses that hold ground; garrisonable civilian buildings.

**Combat** — hard-ish counters with tooltips that say so; physical projectiles (dodgeable missiles, point-defense); aircraft that sortie from airfields and come home; veterancy chevrons; husks and salvage crates; area denial (toxin, fire, radiation).

**Meta layer** — promotion points buying general powers on cooldowns (paradrops, barrages, bombing runs); superweapons on globally visible timers — the shared dread clock; capturable neutral tech buildings.

**Presentation** — bottom command bar, radar minimap, unit portrait; classic RTS camera; unit acknowledgment VO with personality; a battle announcer; orchestral-industrial score; desert/urban theaters; particle-heavy explosions, decals, toggleable screen shake.

## The modern bar

- **Instant:** fast cold load; assets stream behind the menu; desktop browsers only (D008).
- **QoL:** control groups with on-screen UI, rally points and queued waypoints, attack-move and stances, smart-cast powers, camera bookmarks, full replays, observer mode, pings.
- **Onboarding:** guided first skirmish; counter tooltips; a build advisor.
- **Accessibility:** colorblind-safe palettes, remappable keys, UI scale, runs on integrated GPUs.
- **Social:** a lobby is a URL; replays share the same way.
- **Session shape:** 15–30 minute matches; later a "Boss Ladder" solo gauntlet (our Generals-Challenge homage — boss commanders with personalities, far cheaper than a campaign).

## Faction tone

Thinly-veiled fictional (D004): modern-warfare satire energy — superpower tech vs guerrilla vs industrial horde — without naming real nations. Faction identity lives in asymmetry axes: economy style, power dependency, cost curve, map presence.
