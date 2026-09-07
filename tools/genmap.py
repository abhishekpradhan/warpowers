#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""War Powers .map generator — emits the engine's CkMp chunk format.

Byte-level format extracted from the GPL engine source (wire-format notes
live in docs/engine-notes.md and this file's writer comments). Emits the skirmish map set: layout-driven terrain (120-200-cell
playable areas with dune/ridge/basin features) and two sides — PlayerA
(human) vs PlayerB, a full AIPlayer opponent driven by this file's build
lists, economy structures, and difficulty-gated attack-team scripts
(escalation tiers + defense patrol / punish / eco-raid behaviors).
Little-endian throughout.

python3 tools/genmap.py [--layout L --faction F | --mission ID] [--out DIR | OUTPUT.map]
python3 tools/genmap.py --all [--out DIR]     # every skirmish layout x faction plus every authored operation
"""
import argparse
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_NAMES = ("flats", "ridge", "scrap", "basin", "range")
FACTIONS = ("meridian", "jackal")


def load_missions(root=ROOT):
    return json.loads((root / "data/operations.json").read_text())["missions"]


def faction_table(faction):
    """Template names per side. --faction=jackal writes the mirrored WPTestJ
    map: the player starts as the Jackal Front and the AI opponent is the
    Meridian Combine."""
    if faction == 'jackal':
        F = dict(map_name=None, is_jackal=True,
                 player_cc='WPJ_CommandPost', player_faction='FactionWPJ',
                 enemy_cc='WP_CommandCenter', enemy_faction='FactionWP',
                 guard='WP_Tank',
                 wave_raider='WP_Tank', wave_pack_a='WP_Outrider', wave_pack_b='WP_Tank',
                 enemy_factory='WP_VehiclePlant', enemy_tower='WP_Bulwark',
                 enemy_power='WP_PowerArray', enemy_aa='WP_Skyspear',
                 enemy_income='WP_Exchange', enemy_pad='WP_LaunchPad',
                 player_income='WPJ_Racket', player_power='WPJ_Dynamo',
                 player_hauler='WPJ_Scavenger', player_tank='WPJ_Mongrel',
                 player_air='WPJ_Buzzard', player_strafer='WPJ_Gnat',
                 raid_a='WP_Outrider',
                 assault_a='WP_Tank', assault_b='WP_Zenith',
                 assault_c='WP_Lancer', wave_air='WP_Kestrel',
                 defender='WP_Tank', defender_scout='WP_Outrider')
    else:
        F = dict(map_name=None,
                 player_cc='WP_CommandCenter', player_faction='FactionWP',
                 enemy_cc='WPJ_CommandPost', enemy_faction='FactionWPJ',
                 guard='WPJ_Mongrel',
                 wave_raider='WPJ_Mongrel', wave_pack_a='WPJ_Vulture', wave_pack_b='WPJ_Mongrel',
                 enemy_factory='WPJ_ChopShop', enemy_tower='WPJ_Watchpost',
                 enemy_power='WPJ_Racket', enemy_aa='WPJ_Flakhut',
                 enemy_income='WPJ_Racket', enemy_pad='WPJ_Roost',
                 player_income='WP_Exchange', player_power='WP_PowerArray',
                 player_hauler='WP_Porter', player_tank='WP_Tank',
                 player_air='WP_Kestrel', player_strafer='WP_Shrike',
                 raid_a='WPJ_Vulture',
                 assault_a='WPJ_Mongrel', assault_b='WPJ_Vulture',
                 assault_c='WPJ_Sting', wave_air='WPJ_Buzzard',
                 defender='WPJ_Mongrel', defender_scout='WPJ_Vulture')
    return F


# ---------- layouts ----------
# --layout=NAME picks the battlefield shape; 'flats' is the original WPTest.
# Every coordinate below derives from these anchors, so a layout is just
# geometry: map size, base anchors, and an optional ridge wall with passes.
LAYOUTS = {
    # the original: diagonal bases, open ground
    "flats": dict(play=160, player=(400.0, 400.0), enemy=(1200.0, 1200.0),
                  ridge=None, name="WPTest", jname="WPTestJ"),
    # bigger field split by a NE/SW ridge wall with two passes - lane play
    "ridge": dict(play=180, player=(360.0, 360.0), enemy=(1440.0, 1440.0),
                  ridge=dict(gap1=0.30, gap2=0.74, halfw=52.0, h=34.0),
                  name="WPRidge", jname="WPRidgeJ"),
    # tight brawl: close bases, no cover - rush tempo
    "scrap": dict(play=120, player=(300.0, 600.0), enemy=(900.0, 600.0),
                  ridge=None, ground="WPGroundAsh",
                  name="WPScrap", jname="WPScrapJ"),
    # sunken center bowl ringed by a rim - whoever holds the basin sees all
    "basin": dict(play=170, player=(380.0, 850.0), enemy=(1320.0, 850.0),
                  ridge=None, basin=dict(r=330.0, rim=26.0, depth=6.0),
                  name="WPBasin", jname="WPBasinJ"),
    # long north-south field crossed by two offset ridge walls - trench lines
    "range": dict(play=200, player=(1000.0, 320.0), enemy=(1000.0, 1680.0),
                  ridge=dict(gap1=0.22, gap2=0.80, halfw=46.0, h=30.0),
                  ridge2=dict(gap1=0.55, gap2=0.90, halfw=46.0, h=30.0),
                  ground="WPGroundAsh",
                  name="WPRange", jname="WPRangeJ"),
}


# ---------- primitive encoders ----------
def ascii_s(s):
    b = s.encode("ascii")
    return struct.pack("<H", len(b)) + b

def uni_s(s):
    return struct.pack("<H", len(s)) + s.encode("utf-16-le")

class Toc:
    def __init__(self):
        self.names = {}
    def key(self, name):
        if name not in self.names:
            self.names[name] = len(self.names) + 1
        return self.names[name]
    def emit(self):
        out = [b"CkMp", struct.pack("<i", len(self.names))]
        for name, i in self.names.items():
            nb = name.encode("ascii")
            out.append(struct.pack("<B", len(nb)) + nb + struct.pack("<I", i))
        return b"".join(out)


def generate(layout, faction, mission=None, preview=False):
    """Build one map. Returns (map name, CkMp bytes)."""
    F = faction_table(faction)
    MISSION = mission
    MISSION_ID = mission["id"] if mission else None
    LAY = dict(LAYOUTS[layout])
    if MISSION:
        LAY["name"] = LAY["jname"] = MISSION["map"]
    PLAYER_BASE = LAY["player"]
    ENEMY_BASE = LAY["enemy"]

    # ---------- geometry ----------
    BORDER = 10
    PLAY = LAY["play"]
    W = H = PLAY + 2 * BORDER          # vertices per axis, border included (layout-dependent)
    N = W * H                          # total vertices
    FSW = (W + 7) // 8                 # cliff-state bitfield bytes per row
    HEIGHT_BYTE = 16                   # flat ground at z = 16 * 0.625 = 10.0

    toc = Toc()

    # Dict value types
    D_BOOL, D_INT, D_REAL, D_ASCII, D_UNI = 0, 1, 2, 3, 4

    def dict_pairs(pairs):
        out = [struct.pack("<H", len(pairs))]
        for key, dtype, val in pairs:
            out.append(struct.pack("<i", (toc.key(key) << 8) | dtype))
            if dtype == D_BOOL:
                out.append(struct.pack("<B", 1 if val else 0))
            elif dtype == D_INT:
                out.append(struct.pack("<i", val))
            elif dtype == D_REAL:
                out.append(struct.pack("<f", val))
            elif dtype == D_ASCII:
                out.append(ascii_s(val))
            elif dtype == D_UNI:
                out.append(uni_s(val))
        return b"".join(out)

    def chunk(label, version, payload):
        return struct.pack("<IHi", toc.key(label), version, len(payload)) + payload

    # ---------- HeightMapData v4 ----------
    # Gentle dunes from layered sines; base zones flattened with a smooth falloff
    # so structures sit level and pathing stays trivial there.

    BASES = [PLAYER_BASE, ENEMY_BASE]   # world coords
    FLAT_R, FLAT_FADE = 320.0, 160.0             # flat radius, blend band (wide enough to actually build a base)

    def _wall(wx, wy, r, frac):
        """one wall: a band at 'frac' of the way from player to enemy along the
        base axis, spanning the crosswise direction, broken by two gaps."""
        ext = PLAY * 10.0
        px, py = PLAYER_BASE
        ex, ey = ENEMY_BASE
        axx, axy = ex - px, ey - py
        L = (axx * axx + axy * axy) ** 0.5
        axx, axy = axx / L, axy / L
        # distance of this point from the wall line (perp to base axis at frac)
        cxw = px + (ex - px) * frac
        cyw = py + (ey - py) * frac
        d = abs((wx - cxw) * axx + (wy - cyw) * axy)
        if d > r["halfw"]:
            return 0.0
        # crosswise position 0..1 for the gaps
        t = ((wx - cxw) * (-axy) + (wy - cyw) * axx + ext / 2.0) / ext
        for g in (r["gap1"], r["gap2"]):
            if abs(t - g) < 0.055:
                return 0.0
        prof = 1.0 - (d / r["halfw"]) ** 2
        return r["h"] * prof

    def ridge_height(wx, wy):
        """layout terrain features: ridge walls (perpendicular to the base
        axis at 50% / 68% of the way) and the basin bowl."""
        h = 0.0
        r = LAY.get("ridge")
        if r:
            h += _wall(wx, wy, r, 0.5)
        r2 = LAY.get("ridge2")
        if r2:
            h += _wall(wx, wy, r2, 0.68)
        b = LAY.get("basin")
        if b:
            ext = PLAY * 10.0
            cx = cy = ext / 2.0
            dist = ((wx - cx) ** 2 + (wy - cy) ** 2) ** 0.5
            if dist < b["r"]:
                edge = (b["r"] - dist) / b["r"]
                h -= b["depth"] * min(1.0, edge * 3.0)          # sunken floor
            elif dist < b["r"] + 60.0:
                t = 1.0 - (dist - b["r"]) / 60.0
                h += b["rim"] * (t * t)                          # rim wall
        return h

    def dune_height(wx, wy):
        d = (math.sin(wx * 0.0071 + 1.3) + math.sin(wy * 0.0063 + 4.1)
             + 0.6 * math.sin((wx + wy) * 0.0047 + 2.2)
             + 0.5 * math.sin((wx * 0.9 - wy) * 0.0102 + 0.7))
        h = HEIGHT_BYTE + d * 1.2                # gentle dunes; steeper amp left too little legal build ground
        near = min(((wx - bx) ** 2 + (wy - by) ** 2) ** 0.5 for bx, by in BASES)
        if near < FLAT_R:
            return float(HEIGHT_BYTE)
        if near < FLAT_R + FLAT_FADE:
            t = (near - FLAT_R) / FLAT_FADE
            t = t * t * (3 - 2 * t)
            return HEIGHT_BYTE + (h - HEIGHT_BYTE) * t
        return h

    height_bytes = bytearray()
    for cy in range(H):
        for cx in range(W):
            wx, wy = (cx - BORDER) * 10.0, (cy - BORDER) * 10.0  # MAP_XY_FACTOR
            height_bytes.append(max(0, min(255, int(round(dune_height(wx, wy) + ridge_height(wx, wy))))))
    height_payload = struct.pack("<iiii", W, H, BORDER, 1)      # width,height,border,numBoundaries
    height_payload += struct.pack("<ii", PLAY, PLAY)            # boundary[0]
    height_payload += struct.pack("<i", N) + bytes(height_bytes)

    # ---------- BlendTileData v8 ----------
    # WPGround is a 4x4 grid of 64px tiles (16 variants); each 2x2 cell block
    # shows one full tile, chosen by a position hash to break repetition.
    NUM_TILES, TILE_GRID_W = 16, 4
    CONCRETE_FIRST, CONCRETE_NUM = 16, 16          # 4x4 sheet: 0-7 clean, 8-15 worn

    # base aprons: concrete pads under the start locations (ZH bases sat on
    # concrete, not bare dunes). Cell size is MAP_XY_FACTOR world units.
    APRONS = [(PLAYER_BASE[0], PLAYER_BASE[1], 150.0), (ENEMY_BASE[0], ENEMY_BASE[1], 150.0)]

    def apron_state(bx, by):
        """0 = sand, 1 = worn concrete (edge ring), 2 = clean concrete."""
        wx = (bx * 2 + 0.5 - BORDER) * 10.0                   # block center, world
        wy = (by * 2 + 0.5 - BORDER) * 10.0
        best = 0
        for ax, ay, ar in APRONS:
            d = ((wx - ax) ** 2 + (wy - ay) ** 2) ** 0.5
            if d < ar - 26.0:
                return 2
            if d < ar:
                best = max(best, 1)
        return best

    def tile_pick(bx, by):
        h = (bx * 73856093) ^ (by * 19349663)
        h = (h ^ (h >> 13)) * 0x5BD1E995 & 0xFFFFFFFF
        state = apron_state(bx, by)
        if state == 2:
            return CONCRETE_FIRST + (h >> 8) % 8           # clean rows
        if state == 1:
            return CONCRETE_FIRST + 8 + (h >> 8) % 8       # worn rows
        return (h >> 8) % NUM_TILES

    tile_ndx = bytearray()
    for y in range(H):
        for x in range(W):
            tile = tile_pick(x // 2, y // 2)
            tile_ndx += struct.pack("<h", (tile << 2) + 2 * (y & 1) + (x & 1))
    zeros16 = struct.pack("<h", 0) * N
    # Pathfinding reads this authored bitfield, not terrain slope. The visible
    # ridge footprints must therefore carry real cliffs; the wide low passes
    # remain clear. Keep basin rims walkable: they are elevation, not cliff walls.
    cliff_state = bytearray(H * FSW)
    for y in range(H - 1):
        for x in range(W - 1):
            wx, wy = (x - BORDER + 0.5) * 10, (y - BORDER + 0.5) * 10
            blocked = any(_wall(wx, wy, LAY[key], fraction) > 3.0
                          for key, fraction in (("ridge", 0.5), ("ridge2", 0.68)) if LAY.get(key))
            if blocked:
                cliff_state[y * FSW + (x >> 3)] |= 1 << (x & 7)
    blend_payload = struct.pack("<i", N)
    blend_payload += bytes(tile_ndx)          # tileNdxes
    blend_payload += zeros16                  # blendTileNdxes
    blend_payload += zeros16                  # extraBlendTileNdxes
    blend_payload += zeros16                  # cliffInfoNdxes
    blend_payload += cliff_state              # cellCliffState (real ridge barriers)
    blend_payload += struct.pack("<iiii", NUM_TILES + CONCRETE_NUM, 1, 1, 2)  # bitmapTiles, blendedTiles, cliffInfo, texClasses
    blend_payload += struct.pack("<iiii", 0, NUM_TILES, TILE_GRID_W, 0) + ascii_s(LAY.get("ground", "WPGround"))
    blend_payload += struct.pack("<iiii", CONCRETE_FIRST, CONCRETE_NUM, 4, 0) + ascii_s("WPConcrete")
    blend_payload += struct.pack("<ii", 0, 0)  # numEdgeTiles, numEdgeTextureClasses

    def clear_ridge_point(x, y):
        """Keep playable fixtures off cliffs after a layout places its ridge wall."""
        def clear(cx, cy):
            for dx, dy in ((dx, dy) for dx in (-35, 0, 35) for dy in (-35, 0, 35)):
                ix, iy = int((cx + dx) / 10) + BORDER, int((cy + dy) / 10) + BORDER
                if not (BORDER <= ix < W - BORDER and BORDER <= iy < H - BORDER):
                    return False
                if cliff_state[iy * FSW + (ix >> 3)] & (1 << (ix & 7)):
                    return False
            return True
        if clear(x, y):
            return x, y
        toward_home = math.atan2(PLAYER_BASE[1] - y, PLAYER_BASE[0] - x)
        for radius in range(20, 201, 10):
            for index in range(16):
                angle = toward_home + index * math.pi / 8
                candidate = x + math.cos(angle) * radius, y + math.sin(angle) * radius
                if clear(*candidate):
                    return candidate
        raise ValueError(f"no accessible fixture site near {x}, {y}")

    # ---------- WorldInfo v1 ----------
    world_payload = dict_pairs([
        ("mapName", D_ASCII, (LAY["jname"] if F.get("is_jackal") else LAY["name"])),
        ("weather", D_INT, 0),
    ])

    PX, PY = PLAYER_BASE
    EX, EY = ENEMY_BASE
    # enemy-base cluster offsets, expressed from the enemy anchor and mirrored
    # toward the player so every layout keeps the towers on the approach side.
    _toP = math.atan2(PY - EY, PX - EX)
    def _off(dx, dy):
        """offset in the flats frame (enemy at 1200,1200, player toward SW),
        rotated so 'toward player' tracks the actual layout geometry."""
        base = math.atan2(400.0 - 1200.0, 400.0 - 1200.0)
        rot = _toP - base
        c, sn = math.cos(rot), math.sin(rot)
        return (EX + dx * c - dy * sn, EY + dx * sn + dy * c)

    _fac = _off(-80.0, 50.0)
    _pow = _off(70.0, 40.0)
    _tw1 = _off(-95.0, -95.0)
    _tw2 = _off(80.0, -80.0)
    _df1 = _off(-50.0, -50.0)
    _df2 = _off(40.0, -40.0)
    _df3 = _off(-5.0, -80.0)
    _aa = _off(-30.0, 60.0)
    _inc = _off(130.0, 20.0)          # enemy income structure (pre-placed)
    _pad = _off(30.0, 120.0)          # enemy air pad (pre-placed; unlocks air teams)
    _bl_pow2 = _off(150.0, 85.0)      # AI expansion: second power
    _bl_inc2 = _off(185.0, -35.0)     # AI expansion: second income
    _bl_twf = (EX + 0.30 * (PX - EX), EY + 0.30 * (PY - EY))  # forward tower on the lane
    _rly = _off(-20.0, -130.0)        # attack-team gather point at the base front

    # ---------- SidesList v3 ----------
    # Build-list entry wire format (SidesList::ParseSidesDataChunk, v3):
    # buildingName, templateName, x, y, z(forced 0), angle, byte initiallyBuilt,
    # int numRebuilds, script, int health, byte whiner/unsellable/repairable.
    # AIPlayer::processBaseBuilding walks these and dozer-constructs anything
    # missing (queueing a dozer from a build-list factory if none exists), so a
    # not-initially-built entry = the AI visibly expands to that spot in-match.
    def build_entry(template, x, y, angle=0.0, built=False, rebuilds=99):
        x, y = clear_ridge_point(x, y)
        return (ascii_s("") + ascii_s(template)
                + struct.pack("<fff", x, y, 0.0) + struct.pack("<f", angle)
                + bytes([1 if built else 0]) + struct.pack("<i", rebuilds)
                + ascii_s("") + struct.pack("<i", 100) + bytes([0, 0, 1]))

    def side(pairs, build_list=()):
        payload = dict_pairs(pairs) + struct.pack("<i", len(build_list))
        return payload + b"".join(build_list)

    sides_payload = struct.pack("<i", 3)
    sides_payload += side([
        ("playerName", D_ASCII, ""),
        ("playerIsHuman", D_BOOL, False),
        ("playerDisplayName", D_UNI, "Neutral"),
        ("playerFaction", D_ASCII, ""),
        ("playerAllies", D_ASCII, ""),
        ("playerEnemies", D_ASCII, ""),
    ])
    sides_payload += side([
        ("playerName", D_ASCII, "PlayerA"),
        ("playerIsHuman", D_BOOL, True),
        ("playerDisplayName", D_UNI, "Player A"),
        ("playerFaction", D_ASCII, F["player_faction"]),
        ("playerAllies", D_ASCII, ""),
        ("playerEnemies", D_ASCII, "PlayerB"),
        ("playerColor", D_INT, 0x2882FF),
        ("playerNightColor", D_INT, 0x2882FF),
        ("playerStartMoney", D_INT, 7000 if MISSION_ID in ("op03", "challenge-meridian") else 6000),
        ("multiplayerStartIndex", D_INT, 0),
    ])
    sides_payload += side([
        ("playerName", D_ASCII, "PlayerB"),
        ("playerIsHuman", D_BOOL, False),
        ("playerDisplayName", D_UNI, "Player B"),
        ("playerFaction", D_ASCII, F["enemy_faction"]),
        ("playerAllies", D_ASCII, ""),
        ("playerEnemies", D_ASCII, "PlayerA"),
        ("playerColor", D_INT, 0xFF3C28),
        ("playerNightColor", D_INT, 0xFF3C28),
        ("playerStartMoney", D_INT, 4500 if MISSION_ID == "training" else 6000),
        ("multiplayerStartIndex", D_INT, 1),
    ], build_list=[
        # The AI expands to these during the match (dozer-built, rebuilt if razed).
        build_entry(F["enemy_power"], _bl_pow2[0], _bl_pow2[1], 3.4),
        build_entry(F["enemy_income"], _bl_inc2[0], _bl_inc2[1], 3.0),
     ] + ([] if MISSION_ID == "training" else [
        build_entry(F["enemy_tower"], _bl_twf[0], _bl_twf[1], _toP),
     ]))
    # team dicts are collected first so the COUNT is derived, never hand-kept
    # (a stale hardcoded count silently desyncs every chunk after the team
    # list - the zero-objects-in-world failure).
    _team_dicts = []
    def team(pairs):
        _team_dicts.append(dict_pairs(pairs))
    team([("teamName", D_ASCII, "team"),
                                 ("teamOwner", D_ASCII, ""),
                                 ("teamIsSingleton", D_BOOL, True)])
    team([("teamName", D_ASCII, "teamPlayerA"),
                                 ("teamOwner", D_ASCII, "PlayerA"),
                                 ("teamIsSingleton", D_BOOL, True)])
    team([("teamName", D_ASCII, "teamPlayerB"),
                                 ("teamOwner", D_ASCII, "PlayerB"),
                                 ("teamIsSingleton", D_BOOL, True)])
    # Pre-placed base garrison: its own team, priority ABOVE every attack team
    # and explicitly non-recruitable — Team::tryToRecruit treats the DEFAULT
    # team as always poachable and steals from any lower-priority team within
    # recruit radius — an unprotected garrison gets drafted into the first
    # attack team.
    team([("teamName", D_ASCII, "teamBaseGuards"),
                                 ("teamOwner", D_ASCII, "PlayerB"),
                                 ("teamIsSingleton", D_BOOL, True),
                                 ("teamProductionPriority", D_INT, 100),
                                 ("teamIsAIRecruitable", D_BOOL, False)])
    # Phase 4: the enemy TRAINS its attack teams (AIPlayer team production) —
    # no more free spawns. Each team carries a production-condition script
    # (evaluated by name; escalation tiers unlock on timers armed at match
    # start), a priority (higher wins when affordable + factory idle), an
    # instance cap, and a gather point at the base front. Units cost the AI
    # real money: killing its Exchange/Racket starves the waves.
    def attack_team(name, cond, pri, maxinst, units, on_create="WP_WaveAttack"):
        pairs = [("teamName", D_ASCII, name),
                 ("teamOwner", D_ASCII, "PlayerB"),
                 ("teamIsSingleton", D_BOOL, False),
                 ("teamHome", D_ASCII, "EnemyRally"),
                 ("teamProductionCondition", D_ASCII, cond),
                 ("teamProductionPriority", D_INT, pri),
                 ("teamMaxInstances", D_INT, maxinst),
                 ("teamExecutesActionsOnCreate", D_BOOL, True),
                 ("teamOnCreateScript", D_ASCII, on_create)]
        for i, (tmpl, n) in enumerate(units, start=1):
            pairs += [("teamUnitType%d" % i, D_ASCII, tmpl),
                      ("teamUnitMinCount%d" % i, D_INT, n),
                      ("teamUnitMaxCount%d" % i, D_INT, n)]
        team(pairs)

    attack_team("teamWaveRaiders", "WP_ProdRaiders", 10, 2,
                [(F["wave_raider"], 2)])
    attack_team("teamWavePack", "WP_ProdPack", 20, 2,
                [(F["wave_pack_a"], 2), (F["wave_pack_b"], 1)])
    attack_team("teamWaveAssault", "WP_ProdAssault", 30, 1,
                [(F["assault_a"], 3), (F["assault_b"], 2), (F["assault_c"], 2)],
                on_create="WP_WaveHunt")
    attack_team("teamWaveAir", "WP_ProdAir", 25, 1,
                [(F["wave_air"], 2)])
    # Eco-raid: fast movers that hunt with an attack-priority set favoring the
    # player's income/power — they slip past the front and gut the economy.
    attack_team("teamEcoRaid", "WP_ProdRaid", 28, 1,
                [(F["raid_a"], 3)], on_create="WP_EcoRaid")
    # Punish: unlocked the moment the player destroys an enemy structure —
    # aggression gets answered (normal/brutal only via the condition script).
    attack_team("teamPunish", "WP_ProdPunish", 40, 1,
                [(F["assault_a"], 3), (F["assault_b"], 2)],
                on_create="WP_PunishHunt")
    # Defense patrol: trained garrison replacement — guards the base front and
    # is rebuilt whenever it dies. Outranks every attack tier so the AI heals
    # its defense before it schedules offense.
    attack_team("teamDefensePatrol", "WP_ProdDefense", 45, 1,
                [(F["defender"], 2)], on_create="WP_HoldBase")
    # A bounded response to committed armor/air: native production pays for the
    # rocket squad, and a surviving squad prevents another instance being trained.
    attack_team("teamCounterSquad", "WP_ProdCounter", 35, 1,
                [(F["assault_c"], 3)], on_create="WP_HoldBase")
    sides_payload += struct.pack("<i", len(_team_dicts))
    sides_payload += b"".join(_team_dicts)
    # nested PlayerScriptsList appended below (win/lose scripts), after its
    # helper definitions

    # ---------- ObjectsList v3 with nested Object v3 chunks ----------
    def obj(x, y, angle, name, pairs):
        if MISSION_ID == "training" and name in (F["enemy_tower"], F["enemy_aa"]):
            return b""  # Orientation teaches mobile combat before fortified bases.
        if not name.startswith(("WP_Prop", "*Waypoints/")):
            x, y = clear_ridge_point(x, y)
        payload = struct.pack("<ffff", x, y, 0.0, angle)
        payload += struct.pack("<i", 0)  # flags
        payload += ascii_s(name)
        payload += dict_pairs(pairs)
        return chunk("Object", 3, payload)

    # --preview: art-review mode — park enemy structures in view of the start
    # camera so new assets can be judged without driving across the map.
    preview_objects = []
    if preview:
        row = [("WPJ_CommandPost", 510.0, 320.0, 0.3), ("WPJ_ChopShop", 640.0, 360.0, 0.2),
               ("WPJ_Watchpost", 700.0, 300.0, 0.0), ("WPJ_Rigger", 560.0, 260.0, 0.8),
               ("WPJ_Vulture", 620.0, 260.0, 0.8),
               ("WP_Bulwark", 300.0, 300.0, 0.0), ("WP_Outrider", 250.0, 350.0, 0.6),
               ("WP_Zenith", 250.0, 430.0, 0.6)]
        for tmpl, px, py, ang in row:
            preview_objects.append(obj(px, py, ang, tmpl,
                               [("originalOwner", D_ASCII,
                                 "teamPlayerB" if tmpl.startswith("WPJ") else "teamPlayerA")]))

    objects_payload = b"".join(preview_objects + [
        obj(PX, PY, 0.0, F["player_cc"],
            [("originalOwner", D_ASCII, "teamPlayerA"),
             ("objectName", D_ASCII, "PlayerCC")]),
        obj((PX + EX) / 2.0, (PY + EY) / 2.0, 2.4, F["guard"],
            [("originalOwner", D_ASCII, "teamBaseGuards")]),
        obj(EX, EY, 3.14159265, F["enemy_cc"],
            [("originalOwner", D_ASCII, "teamPlayerB"),
             ("objectName", D_ASCII, "EnemyCC")]),
        obj(_fac[0], _fac[1], 2.6, F["enemy_factory"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_pow[0], _pow[1], 3.4, F["enemy_power"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_tw1[0], _tw1[1], 2.4, F["enemy_tower"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_tw2[0], _tw2[1], 3.6, F["enemy_tower"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_df1[0], _df1[1], 2.4, F["defender"],
            [("originalOwner", D_ASCII, "teamBaseGuards")]),
        obj(_df2[0], _df2[1], 3.2, F["defender"],
            [("originalOwner", D_ASCII, "teamBaseGuards")]),
        obj(_df3[0], _df3[1], 2.8, F["defender_scout"],
            [("originalOwner", D_ASCII, "teamBaseGuards")]),
        obj(_aa[0], _aa[1], 3.0, F["enemy_aa"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_inc[0], _inc[1], 3.2, F["enemy_income"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(_pad[0], _pad[1], 3.0, F["enemy_pad"],
            [("originalOwner", D_ASCII, "teamPlayerB")]),
        obj(PX, PY + 50.0, 0.0, "*Waypoints/Waypoint",
            [("waypointID", D_INT, 1), ("waypointName", D_ASCII, "Player_1_Start")]),
        obj(EX, EY - 50.0, 0.0, "*Waypoints/Waypoint",
            [("waypointID", D_INT, 2), ("waypointName", D_ASCII, "Player_2_Start")]),
        obj(PX, PY, 0.0, "*Waypoints/Waypoint",
            [("waypointID", D_INT, 3), ("waypointName", D_ASCII, "InitialCameraPosition")]),
        obj(_rly[0], _rly[1], 0.0, "*Waypoints/Waypoint",
            [("waypointID", D_INT, 5), ("waypointName", D_ASCII, "EnemyRally")]),
    ])

    # Environmental silhouettes frame clear movement corridors. The deterministic
    # placements stay outside base build zones; all scenery has small, honest
    # collision bounds instead of disguising invisible walls as open terrain.
    def lane(fraction, lateral=0.0):
        dx, dy = EX - PX, EY - PY
        length = (dx * dx + dy * dy) ** 0.5
        return (PX + dx * fraction - dy / length * lateral,
                PY + dy * fraction + dx / length * lateral)

    def placed(template, position, owner="team", name=None, angle=0.0):
        pairs = [("originalOwner", D_ASCII, owner)]
        if name:
            pairs.append(("objectName", D_ASCII, name))
        return obj(*position, angle, template, pairs)

    for i in range(18):
        fraction = 0.16 + (i // 2) * 0.085
        lateral = (255 + (i % 3) * 33) * (-1 if i % 2 else 1)
        pos = lane(fraction, lateral)
        if all(65 < v < PLAY * 10 - 65 for v in pos) and min(
                ((pos[0] - b[0]) ** 2 + (pos[1] - b[1]) ** 2) ** 0.5 for b in BASES) > 240:
            template = "WP_PropScrap" if layout in ("scrap", "range") and i % 3 else "WP_PropRock"
            objects_payload += placed(template, pos, angle=i * 0.73)
    for fraction, offset in ((0.31, -165), (0.69, 175)):
        objects_payload += placed("WP_PropRelay", lane(fraction, offset), angle=_toP)
        objects_payload += placed("WP_PropBarrier", lane(fraction, offset + 36), angle=_toP)

    # Finite supplies give expansions and raids a physical purpose. Home caches
    # are visible from the opening base; the two lateral caches reward map control.
    for name, pos in (("HomeSupplyA", lane(0.08, -155)), ("HomeSupplyB", lane(0.92, 155)),
                      ("FieldSupplyA", lane(0.36, 215)), ("FieldSupplyB", lane(0.66, -215))):
        objects_payload += placed("WP_SupplyCache", pos, name=name)
    if MISSION_ID != "training":
        objects_payload += placed("WPJ_Scavenger" if F.get("is_jackal") else "WP_Porter",
                                  (PX - 65, PY + 55), "teamPlayerA")
    objects_payload += placed("WP_Porter" if F.get("is_jackal") else "WPJ_Scavenger",
                              (_inc[0] + 20, _inc[1] + 45), "teamPlayerB")

    # Authored operations use named physical targets. Destruction conditions count
    # actual battlefield objects; objective completion never depends on a label or
    # a wall-clock timeout in the browser.
    if MISSION_ID == "op01":
        objects_payload += placed("WP_MissionRelay", lane(0.65, -120), "teamPlayerB", "ObjectiveRelay")
        objects_payload += placed("WPJ_Sting", lane(0.64, -80), "teamBaseGuards")
    elif MISSION_ID == "op02":
        for name, template, pos in (
                ("SupplyOfficeA", "WP_Exchange", lane(0.47, -230)),
                ("SupplyOfficeB", "WP_Exchange", lane(0.60, 235)),
                ("GridSubstation", "WP_PowerArray", lane(0.75, -125))):
            objects_payload += placed(template, pos, "teamPlayerB", name)
            objects_payload += placed("WP_Warden", (pos[0] + 30, pos[1] + 30), "teamBaseGuards")
        for i in range(3):
            objects_payload += placed("WPJ_Vulture", (PX - 55 + i * 26, PY + 95), "teamPlayerA")
    elif MISSION_ID in ("op03", "challenge-meridian"):
        objects_payload += placed("WP_MissionRelay", lane(0.25), "teamPlayerA", "AlliedRelay")
        for template, dx, dy in (("WP_Fabricator", -70, 65), ("WP_VehiclePlant", 105, 10),
                                  ("WP_Exchange", -85, -50), ("WP_PowerArray", 15, -100)):
            objects_payload += placed(template, (PX + dx, PY + dy), "teamPlayerA")
        for i, template in enumerate(("WP_Warden", "WP_Warden", "WP_Lancer", "WP_Tank")):
            objects_payload += placed(template, lane(0.25, -60 + i * 32), "teamPlayerA")
        if MISSION_ID == "challenge-meridian":
            for i, side in enumerate((-105, 105), 1):
                objects_payload += placed("WPJ_Lobber", lane(0.42, side), "teamPlayerB", f"SiegePit{i}")
                objects_payload += placed("WPJ_Sting", lane(0.46, side), "teamBaseGuards")
    elif MISSION_ID == "op04":
        for i, side in enumerate((-150, 150), 1):
            objects_payload += placed("WP_Skyspear", lane(0.62, side), "teamPlayerB", f"AirDefense{i}")
            objects_payload += placed("WP_Rampart", lane(0.67, side), "teamPlayerB")
    elif MISSION_ID == "challenge-jackal":
        for i, template in enumerate(("WPJ_Vulture", "WPJ_Vulture", "WPJ_Mongrel", "WPJ_Sting", "WPJ_Sting")):
            objects_payload += placed(template, (PX - 60 + i * 26, PY + 100), "teamPlayerA")
        objects_payload += placed("WPJ_ChopShop", (PX + 100, PY), "teamPlayerA")
        objects_payload += placed("WPJ_Racket", (PX - 85, PY - 50), "teamPlayerA")

    # ---------- GlobalLighting v3 ----------
    # Warm desert key + faint cool fill. Slot order per TOD:
    # TL[0], TOL[0], TOL[1], TOL[2], TL[1], TL[2] (terrain / object lights).
    def L(amb, dif, d):
        return struct.pack("<9f", *amb, *dif, *d)

    SUN = (-0.55, 0.40, -0.73)
    FILL = (0.65, -0.35, -0.67)
    ZERO = L((0, 0, 0), (0, 0, 0), (0, 0, -1))
    tod_lights = (
        L((0.36, 0.35, 0.36), (0.92, 0.84, 0.68), SUN)      # terrain key
        + L((0.40, 0.39, 0.41), (1.00, 0.93, 0.78), SUN)    # object key
        + L((0.00, 0.00, 0.00), (0.14, 0.16, 0.20), FILL)   # object cool fill
        + ZERO                                               # object light 3
        + L((0.00, 0.00, 0.00), (0.10, 0.12, 0.16), FILL)   # terrain fill
        + ZERO                                               # terrain light 3
    )
    lighting_payload = struct.pack("<i", 2)  # AFTERNOON
    lighting_payload += tod_lights * 4

    # ---------- PlayerScriptsList (win/lose via named CCs) ----------
    # Engine readers: ScriptList::ParseScriptsDataChunk et al. (Scripts.cpp).
    # The map reader only accepts this chunk NESTED inside SidesList (registered
    # with the SidesList label scope in SidesList::ParseSidesDataChunk); the
    # ScriptList sub-chunk order maps 1:1 to side order.
    # Condition/action chunks are v4/v2 so the engine rematches the type by its
    # internal-name key (we write ordinal 0); parameter type ordinals are fixed
    # by enum Parameter::ParameterType (UNIT = 14).
    P_INT, P_REAL, P_TEAM, P_COUNTER, P_COMPARE, P_WAYPOINT = 0, 1, 3, 4, 6, 7
    P_TEXT, P_SIDE, P_UNIT, P_OBJTYPE, P_APS = 10, 11, 14, 15, 28

    def namekey(name):
        return struct.pack("<i", (toc.key(name) << 8) | D_ASCII)

    def parameter(ptype, i=0, r=0.0, s=""):
        return struct.pack("<iif", ptype, i, r) + ascii_s(s)

    def condition(internal_name, params):
        payload = struct.pack("<i", 0) + namekey(internal_name)
        payload += struct.pack("<i", len(params)) + b"".join(params)
        return chunk("Condition", 4, payload)

    def action(internal_name, params=()):
        payload = struct.pack("<i", 0) + namekey(internal_name)
        payload += struct.pack("<i", len(params)) + b"".join(params)
        return chunk("ScriptAction", 2, payload)

    def script(name, conditions, actions, one_shot=True, subroutine=False,
               easy=True, normal=True, hard=True, alternatives=()):
        payload = ascii_s(name) + ascii_s("") * 3          # name + 3 comments
        payload += bytes([1, 1 if one_shot else 0,
                          1 if easy else 0, 1 if normal else 0, 1 if hard else 0,
                          1 if subroutine else 0])         # active, oneShot, easy, normal, hard, subroutine
        payload += struct.pack("<i", 0)                    # delayEvaluationSeconds
        payload += chunk("OrCondition", 1, b"".join(conditions))
        for group in alternatives:
            payload += chunk("OrCondition", 1, b"".join(group))
        payload += b"".join(actions)
        return chunk("Script", 2, payload)

    def destroyed(name):
        return condition("NAMED_DESTROYED", [parameter(P_UNIT, s=name)])

    def alive(name):
        return condition("NAMED_NOT_DESTROYED", [parameter(P_UNIT, s=name)])

    def counter(name, value, compare=2):
        return condition("COUNTER", [parameter(P_COUNTER, s=name), parameter(P_COMPARE, i=compare), parameter(P_INT, i=value)])

    def set_counter(name, value):
        return action("SET_COUNTER", [parameter(P_COUNTER, s=name), parameter(P_INT, i=value)])

    def has(template, count=1):
        return condition("PLAYER_HAS_OBJECT_COMPARISON", [parameter(P_SIDE, s="PlayerA"),
                         parameter(P_COMPARE, i=3), parameter(P_INT, i=count), parameter(P_OBJTYPE, s=template)])

    def objective(stage, target=0):
        key = f"WP:Objective_{MISSION_ID}_{stage}" if MISSION else "WP:HQObjective"
        return [set_counter("WP_ObjectiveStage", stage),
                set_counter("WP_ObjectiveProgress", 0), set_counter("WP_ObjectiveTarget", target),
                action("DISPLAY_TEXT", [parameter(P_TEXT, s=key)])]

    def timer(name, seconds):
        return action("SET_MILLISECOND_TIMER", [parameter(P_COUNTER, s=name), parameter(P_REAL, r=float(seconds))])

    def expired(name):
        return condition("TIMER_EXPIRED", [parameter(P_COUNTER, s=name)])

    target_count = 3 if MISSION_ID == "op02" else 2 if MISSION_ID == "op04" else 0
    initial_actions = objective(0, target_count)
    hold_seconds = 480 if MISSION_ID == "op03" else 600 if MISSION_ID == "challenge-meridian" else 0
    if hold_seconds:
        initial_actions += [timer("WP_ObjectiveTimer", hold_seconds)]
    if MISSION_ID == "challenge-jackal":
        initial_actions += [timer("WP_ObjectiveTimer", 540)]
    scripts_a = script("WP_MissionStart", [condition("CONDITION_TRUE", [])], initial_actions)
    scripts_a += script("WP_Lose", [destroyed("PlayerCC")], [action("DEFEAT")])

    win_conditions = [destroyed("EnemyCC"), alive("PlayerCC")]
    if MISSION_ID == "training":
        for step, requirements in enumerate((
                [has("WP_Fabricator")], [has("WP_Exchange"), has("WP_PowerArray"), has("WP_Porter")],
                [has("WP_VehiclePlant"), has("WP_Tank", 2)], [has("WP_Vigil")])):
            scripts_a += script(f"WP_TrainingStep{step}", [counter("WP_ObjectiveStage", step)] + requirements,
                                objective(step + 1))
        win_conditions += [counter("WP_ObjectiveStage", 4)]
    elif MISSION_ID == "op01":
        scripts_a += script("WP_FootholdReady", [counter("WP_ObjectiveStage", 0), has("WP_Exchange"), has("WP_VehiclePlant")], objective(1))
        win_conditions = [destroyed("ObjectiveRelay"), counter("WP_ObjectiveStage", 1), alive("PlayerCC")]
    elif MISSION_ID == "op02":
        targets = ("SupplyOfficeA", "SupplyOfficeB", "GridSubstation")
        for name in targets:
            scripts_a += script(f"WP_Sabotage_{name}", [destroyed(name)],
                                [action("INCREMENT_COUNTER", [parameter(P_INT, i=1), parameter(P_COUNTER, s="WP_ObjectiveProgress")])])
        win_conditions = [destroyed(name) for name in targets] + [alive("PlayerCC")]
    elif MISSION_ID in ("op03", "challenge-meridian"):
        scripts_a += script("WP_RelayLost", [destroyed("AlliedRelay")], [action("DEFEAT")])
        if MISSION_ID == "op03":
            scripts_a += script("WP_RelayHeld", [expired("WP_ObjectiveTimer"), alive("AlliedRelay")], objective(1))
            win_conditions += [counter("WP_ObjectiveStage", 1), alive("AlliedRelay")]
        else:
            win_conditions = [expired("WP_ObjectiveTimer"), alive("AlliedRelay"), alive("PlayerCC")]
    elif MISSION_ID == "op04":
        for name in ("AirDefense1", "AirDefense2"):
            scripts_a += script(f"WP_AADown_{name}", [destroyed(name)],
                                [action("INCREMENT_COUNTER", [parameter(P_INT, i=1), parameter(P_COUNTER, s="WP_ObjectiveProgress")])])
        scripts_a += script("WP_ScreenDown", [destroyed("AirDefense1"), destroyed("AirDefense2")], objective(1))
        win_conditions += [destroyed("AirDefense1"), destroyed("AirDefense2")]
    elif MISSION_ID == "challenge-jackal":
        scripts_a += script("WP_DeadlineMissed", [expired("WP_ObjectiveTimer"), alive("EnemyCC")], [action("DEFEAT")])
        # HQ destruction on the expiry frame wins the tie. Keeping a separate
        # positive-timer check would leave neither result eligible on that frame.
    scripts_a += script("WP_Win", win_conditions, [action("VICTORY")])

    # Fog-of-war start: force classic black shroud. No scripted home reveal —
    # own structures light the base themselves (CC ShroudClearingRange 300); a
    # permanent reveal circle would swallow the starting viewport and any
    # enemies inside it.
    scripts_a += (
        script("WP_FogStart",
               [condition("CONDITION_TRUE", [])],
               [action("MAP_SHROUD_ALL", [parameter(P_SIDE, s="")])])   # all human players
    )

    # Phase 4 scripts: the arm scripts start escalation timers once; the
    # WP_Prod* scripts are TEAM PRODUCTION CONDITIONS (evaluated by name from
    # the team dicts — never "fired", so their actions stay empty). Raiders are
    # always in the pool; pack/assault/air join when their timer expires (a
    # TIMER_EXPIRED counter stays expired — nothing resets it — so each tier
    # unlocks permanently). The AI's own team timer paces actual builds.
    def arm(name, counter, seconds, **flags):
        """one-shot timer-arm script; difficulty flags carry the per-difficulty
        escalation (a script disabled for the current difficulty never runs, so
        its counter never starts and TIMER_EXPIRED stays false = tier locked)"""
        if MISSION_ID == "training":
            if counter != "RaiderTimer":
                return b""
            seconds = 240
        elif MISSION_ID == "op01" and counter == "AirWaveTimer":
            return b""
        else:
            seconds *= {"op03": 0.85, "op04": 0.8, "challenge-meridian": 0.65,
                        "challenge-jackal": 0.8}.get(MISSION_ID, 1.0)
        return script(name,
                      [condition("CONDITION_TRUE", [])],
                      [action("SET_MILLISECOND_TIMER",
                              [parameter(P_COUNTER, s=counter), parameter(P_REAL, r=float(seconds))])],
                      **flags)

    scripts_b = (
        # The plain AIPlayer constructor turns unit production OFF (campaign
        # convention: map scripts must switch the computer player on — the
        # stock skirmish AI's ctor re-enables it, the campaign one doesn't).
        # Without this the AI builds its base but never trains a single team;
        # only queueDozer's temporary force-enable ever slips a unit through.
        script("WP_AIProductionOn",
               [condition("CONDITION_TRUE", [])],
               [action("PLAYER_ENABLE_UNIT_CONSTRUCTION",
                       [parameter(P_SIDE, s="PlayerB")]), timer("WP_PunishCooldown", 0)])
        # Escalation timers, per difficulty (deployment-screen OPPOSITION row →
        # MSG_NEW_GAME difficulty → script easy/normal/hard flags). Easy never
        # arms assault/air at all.
        + arm("WP_RaiderStartE", "RaiderTimer", 240, easy=True, normal=False, hard=False)
        + arm("WP_RaiderStartN", "RaiderTimer", 120, easy=False, normal=True, hard=False)
        + arm("WP_RaiderStartH", "RaiderTimer", 60, easy=False, normal=False, hard=True)
        + arm("WP_PackStartE", "PackTimer", 480, easy=True, normal=False, hard=False)
        + arm("WP_PackStartN", "PackTimer", 240, easy=False, normal=True, hard=False)
        + arm("WP_PackStartH", "PackTimer", 150, easy=False, normal=False, hard=True)
        + arm("WP_AssaultStartN", "AssaultTimer", 480, easy=False, normal=True, hard=False)
        + arm("WP_AssaultStartH", "AssaultTimer", 300, easy=False, normal=False, hard=True)
        + arm("WP_AirWaveArmN", "AirWaveTimer", 600, easy=False, normal=True, hard=False)
        + arm("WP_AirWaveArmH", "AirWaveTimer", 420, easy=False, normal=False, hard=True)
        + script("WP_ProdRaiders",
                 [expired("RaiderTimer")] + ([counter("WP_ObjectiveStage", 4, compare=3)] if MISSION_ID == "training" else []), [],
                 one_shot=False, subroutine=True)
        + script("WP_ProdPack",
                 [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="PackTimer")])], [],
                 one_shot=False, subroutine=True)
        + script("WP_ProdAssault",
                 [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="AssaultTimer")])], [],
                 one_shot=False, subroutine=True)
        + script("WP_ProdAir",
                 [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="AirWaveTimer")])], [],
                 one_shot=False, subroutine=True)
        + script("WP_WaveAttack",
                 [condition("CONDITION_TRUE", [])],
                  [action("TEAM_ATTACK_NAMED",
                         [parameter(P_TEAM, s="<This Team>"), parameter(P_UNIT, s="AlliedRelay" if hold_seconds else "PlayerCC")])],
                 one_shot=False, subroutine=True)
        + script("WP_WaveHunt",
                 [condition("CONDITION_TRUE", [])],
                 [action("TEAM_HUNT",
                         [parameter(P_TEAM, s="<This Team>")])],
                 one_shot=False, subroutine=True)
        + script("WP_PunishHunt",
                 [condition("CONDITION_TRUE", [])],
                 [action("TEAM_HUNT", [parameter(P_TEAM, s="<This Team>")]), timer("WP_PunishCooldown", 100)],
                 one_shot=False, subroutine=True)
        # Eco-raid machinery: a one-shot script defines the attack-priority set
        # (default 1, the player's income/power heavily favored); the raid
        # team's on-create applies it and hunts — the hunt then prefers the
        # economy over whatever is closest.
        + script("WP_RaidPrioritySetup",
                 [condition("CONDITION_TRUE", [])],
                 [action("SET_DEFAULT_ATTACK_PRIORITY",
                         [parameter(P_APS, s="WPRaidTargets"), parameter(P_INT, i=1)]),
                  action("SET_ATTACK_PRIORITY_THING",
                         [parameter(P_APS, s="WPRaidTargets"),
                          parameter(P_OBJTYPE, s=F["player_hauler"]), parameter(P_INT, i=75)]),
                  action("SET_ATTACK_PRIORITY_THING",
                         [parameter(P_APS, s="WPRaidTargets"),
                          parameter(P_OBJTYPE, s=F["player_income"]), parameter(P_INT, i=60)]),
                  action("SET_ATTACK_PRIORITY_THING",
                         [parameter(P_APS, s="WPRaidTargets"),
                          parameter(P_OBJTYPE, s=F["player_power"]), parameter(P_INT, i=40)])])
        + script("WP_EcoRaid",
                 [condition("CONDITION_TRUE", [])],
                 [action("TEAM_APPLY_ATTACK_PRIORITY_SET",
                         [parameter(P_TEAM, s="<This Team>"), parameter(P_APS, s="WPRaidTargets")]),
                  action("TEAM_HUNT",
                         [parameter(P_TEAM, s="<This Team>")])],
                 one_shot=False, subroutine=True)
        + script("WP_HoldBase",
                 [condition("CONDITION_TRUE", [])],
                 [action("TEAM_GUARD",
                         [parameter(P_TEAM, s="<This Team>")])],
                 one_shot=False, subroutine=True)
        # Behavior production conditions: the eco-raid unlocks on its own timer
        # (never on easy); the punish team unlocks permanently the first time
        # the player kills an enemy structure (ScoreKeeper-backed condition —
        # normal/brutal only); the defense patrol is always eligible.
        + arm("WP_RaidStartN", "RaidTimer", 420, easy=False, normal=True, hard=False)
        + arm("WP_RaidStartH", "RaidTimer", 240, easy=False, normal=False, hard=True)
        + script("WP_ProdRaid",
                 [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="RaidTimer")])], [],
                 one_shot=False, subroutine=True, easy=False)
        + script("WP_ProdPunish",
                 [condition("PLAYER_DESTROYED_N_BUILDINGS_PLAYER",
                            [parameter(P_SIDE, s="PlayerA"), parameter(P_INT, i=1),
                             parameter(P_SIDE, s="PlayerB")]), expired("WP_PunishCooldown")]
                 + ([counter("WP_ObjectiveStage", 99)] if MISSION_ID == "training" else []), [],
                 one_shot=False, subroutine=True, easy=False)
        + script("WP_ProdDefense",
                 [condition("CONDITION_TRUE", [])], [],
                 one_shot=False, subroutine=True)
        + script("WP_ProdCounter", [has(F["player_air"], 2)], [],
                 alternatives=([has(F["player_strafer"], 2)], [has(F["player_tank"], 4)]),
                 one_shot=False, subroutine=True, easy=False,
                 normal=MISSION_ID != "training", hard=MISSION_ID != "training")
    )
    scripts_payload = (
        chunk("ScriptList", 1, b"")            # index 0: neutral
        + chunk("ScriptList", 1, scripts_a)    # index 1: PlayerA (local)
        + chunk("ScriptList", 1, scripts_b)    # index 2: PlayerB
    )
    sides_payload += chunk("PlayerScriptsList", 5, scripts_payload)

    # ---------- WaypointsList v1 ----------
    waylinks_payload = struct.pack("<i", 0)

    # ---------- assemble ----------
    chunks = (
        chunk("HeightMapData", 4, height_payload)
        + chunk("BlendTileData", 8, blend_payload)
        + chunk("WorldInfo", 1, world_payload)
        + chunk("SidesList", 3, sides_payload)
        + chunk("ObjectsList", 3, objects_payload)
        + chunk("GlobalLighting", 3, lighting_payload)
        + chunk("WaypointsList", 1, waylinks_payload)
    )

    map_name = LAY["jname"] if F.get("is_jackal") else LAY["name"]
    return map_name, toc.emit() + chunks


def resolve_mission(missions, mission_id):
    return next(m for m in missions if m["id"] == mission_id)


def main(argv=None):
    missions = load_missions()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", nargs="?", type=Path,
                        help="explicit destination .map for a single map (default: <out>/<Name>/<Name>.map)")
    parser.add_argument("--out", type=Path, default=ROOT / "data/Maps",
                        help="map dataset root (default: the repository data/Maps)")
    parser.add_argument("--layout", choices=LAYOUT_NAMES, help="skirmish battlefield shape (default: flats)")
    parser.add_argument("--faction", choices=FACTIONS, help="the human player's faction (default: meridian)")
    parser.add_argument("--mission", choices=[m["id"] for m in missions],
                        help="authored operation; its layout and faction come from data/operations.json")
    parser.add_argument("--all", action="store_true", help="Rebuild all skirmishes and authored operations")
    parser.add_argument("--preview", action="store_true",
                        help="art-review map: park enemy structures in view of the start camera")
    args = parser.parse_args(argv)
    if args.mission and (args.layout or args.faction):
        parser.error("--mission fixes the layout and faction; it cannot be combined with --layout/--faction")
    if args.all and (args.output or args.mission or args.layout or args.faction):
        parser.error("--all rebuilds every map; it takes only --out and --preview")

    def write(map_name, data, explicit=None):
        target = explicit or args.out / map_name / f"{map_name}.map"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"wrote {target} ({len(data)} bytes)")

    if args.all:
        for layout in LAYOUT_NAMES:
            for faction in FACTIONS:
                write(*generate(layout, faction, preview=args.preview))
        for mission in missions:
            write(*generate(mission["layout"], mission["faction"], mission, preview=args.preview))
        return
    if args.mission:
        mission = resolve_mission(missions, args.mission)
        layout, faction = mission["layout"], mission["faction"]
    else:
        mission = None
        layout, faction = args.layout or "flats", args.faction or "meridian"
    write(*generate(layout, faction, mission, preview=args.preview), args.output)


if __name__ == "__main__":
    main()
