#!/usr/bin/env python3
"""War Powers .map generator — emits the engine's CkMp chunk format.

Byte-level format extracted from the GPL engine source (see docs/map-format
notes). Generates the Boot Slice map: flat 64x64-cell playable area, two
players (PlayerA human, PlayerB inert AI), one WP_CommandCenter each,
start + camera waypoints. Little-endian throughout.
"""
import os
import struct
import sys

# --faction=jackal writes the mirrored WPTestJ map: the player starts as the
# Jackal League and the scripted opponent is the Meridian Combine.
if '--faction=jackal' in sys.argv:
    sys.argv = [a for a in sys.argv if a != '--faction=jackal']
    F = dict(map_name='WPTestJ',
             player_cc='WPJ_CommandPost', player_faction='FactionWPJ',
             enemy_cc='WP_CommandCenter', enemy_faction='FactionWP',
             guard='WP_Tank',
             wave_raider='WP_Tank', wave_pack_a='WP_Outrider', wave_pack_b='WP_Tank',
             enemy_factory='WP_VehiclePlant', enemy_tower='WP_Bulwark',
             enemy_power='WP_PowerArray',
             assault_a='WP_Tank', assault_b='WP_Zenith',
             defender='WP_Tank', defender_scout='WP_Outrider')
else:
    F = dict(map_name='WPTest',
             player_cc='WP_CommandCenter', player_faction='FactionWP',
             enemy_cc='WPJ_CommandPost', enemy_faction='FactionWPJ',
             guard='WPJ_Mongrel',
             wave_raider='WPJ_Mongrel', wave_pack_a='WPJ_Vulture', wave_pack_b='WPJ_Mongrel',
             enemy_factory='WPJ_ChopShop', enemy_tower='WPJ_Watchpost',
             enemy_power='WP_PowerArray',
             assault_a='WPJ_Mongrel', assault_b='WPJ_Vulture',
             defender='WPJ_Mongrel', defender_scout='WPJ_Vulture')

# ---------- geometry ----------
BORDER = 10
PLAY = 160
W = H = PLAY + 2 * BORDER          # 84 vertices per axis, border included
N = W * H                          # 7056
FSW = (W + 7) // 8                 # cliff-state bitfield bytes per row
HEIGHT_BYTE = 16                   # flat ground at z = 16 * 0.625 = 10.0

# ---------- primitive encoders ----------
def ascii_s(s):
    b = s.encode("ascii")
    return struct.pack("<H", len(b)) + b

def uni_s(s):
    return struct.pack("<H", len(s)) + s.encode("utf-16-le")

class Toc:
    def __init__(self):
        self.names = {}
    def id(self, name):
        if name not in self.names:
            self.names[name] = len(self.names) + 1
        return self.names[name]
    def emit(self):
        out = [b"CkMp", struct.pack("<i", len(self.names))]
        for name, i in self.names.items():
            nb = name.encode("ascii")
            out.append(struct.pack("<B", len(nb)) + nb + struct.pack("<I", i))
        return b"".join(out)

toc = Toc()

# Dict value types
D_BOOL, D_INT, D_REAL, D_ASCII, D_UNI = 0, 1, 2, 3, 4

def dict_pairs(pairs):
    out = [struct.pack("<H", len(pairs))]
    for key, dtype, val in pairs:
        out.append(struct.pack("<i", (toc.id(key) << 8) | dtype))
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
    return struct.pack("<IHi", toc.id(label), version, len(payload)) + payload

# ---------- HeightMapData v4 ----------
# Gentle dunes from layered sines; base zones flattened with a smooth falloff
# so structures sit level and pathing stays trivial there.
import math

BASES = [(400.0, 400.0), (1200.0, 1200.0)]   # world coords
FLAT_R, FLAT_FADE = 320.0, 160.0             # flat radius, blend band (wide enough to actually build a base)

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
        height_bytes.append(max(0, min(255, int(round(dune_height(wx, wy))))))
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
APRONS = [(400.0, 400.0, 150.0), (1200.0, 1200.0, 150.0)]

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
blend_payload = struct.pack("<i", N)
blend_payload += bytes(tile_ndx)          # tileNdxes
blend_payload += zeros16                  # blendTileNdxes
blend_payload += zeros16                  # extraBlendTileNdxes
blend_payload += zeros16                  # cliffInfoNdxes
blend_payload += bytes(H * FSW)           # cellCliffState
blend_payload += struct.pack("<iiii", NUM_TILES + CONCRETE_NUM, 1, 1, 2)  # bitmapTiles, blendedTiles, cliffInfo, texClasses
blend_payload += struct.pack("<iiii", 0, NUM_TILES, TILE_GRID_W, 0) + ascii_s("WPGround")
blend_payload += struct.pack("<iiii", CONCRETE_FIRST, CONCRETE_NUM, 4, 0) + ascii_s("WPConcrete")
blend_payload += struct.pack("<ii", 0, 0)  # numEdgeTiles, numEdgeTextureClasses

# ---------- WorldInfo v1 ----------
world_payload = dict_pairs([
    ("mapName", D_ASCII, F["map_name"]),
    ("weather", D_INT, 0),
])

# ---------- SidesList v3 ----------
def side(pairs):
    return dict_pairs(pairs) + struct.pack("<i", 0)  # empty build list

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
    ("playerStartMoney", D_INT, 10000),
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
    ("playerStartMoney", D_INT, 10000),
    ("multiplayerStartIndex", D_INT, 1),
])
sides_payload += struct.pack("<i", 6)
sides_payload += dict_pairs([("teamName", D_ASCII, "team"),
                             ("teamOwner", D_ASCII, ""),
                             ("teamIsSingleton", D_BOOL, True)])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamPlayerA"),
                             ("teamOwner", D_ASCII, "PlayerA"),
                             ("teamIsSingleton", D_BOOL, True)])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamPlayerB"),
                             ("teamOwner", D_ASCII, "PlayerB"),
                             ("teamIsSingleton", D_BOOL, True)])
# attack-wave team: 2 Mongrels, spawned by script, attacks on creation
sides_payload += dict_pairs([("teamName", D_ASCII, "teamWaveRaiders"),
                             ("teamOwner", D_ASCII, "PlayerB"),
                             ("teamIsSingleton", D_BOOL, False),
                             ("teamHome", D_ASCII, "WaveSpawn"),
                             ("teamUnitType1", D_ASCII, F["wave_raider"]),
                             ("teamUnitMinCount1", D_INT, 2),
                             ("teamUnitMaxCount1", D_INT, 2),
                             ("teamOnCreateScript", D_ASCII, "WP_WaveAttack")])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamWavePack"),
                             ("teamOwner", D_ASCII, "PlayerB"),
                             ("teamIsSingleton", D_BOOL, False),
                             ("teamHome", D_ASCII, "WaveSpawn"),
                             ("teamUnitType1", D_ASCII, F["wave_pack_a"]),
                             ("teamUnitMinCount1", D_INT, 2),
                             ("teamUnitMaxCount1", D_INT, 2),
                             ("teamUnitType2", D_ASCII, F["wave_pack_b"]),
                             ("teamUnitMinCount2", D_INT, 1),
                             ("teamUnitMaxCount2", D_INT, 1),
                             ("teamOnCreateScript", D_ASCII, "WP_WaveAttack")])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamWaveAssault"),
                             ("teamOwner", D_ASCII, "PlayerB"),
                             ("teamIsSingleton", D_BOOL, False),
                             ("teamHome", D_ASCII, "WaveSpawn"),
                             ("teamUnitType1", D_ASCII, F["assault_a"]),
                             ("teamUnitMinCount1", D_INT, 3),
                             ("teamUnitMaxCount1", D_INT, 3),
                             ("teamUnitType2", D_ASCII, F["assault_b"]),
                             ("teamUnitMinCount2", D_INT, 2),
                             ("teamUnitMaxCount2", D_INT, 2),
                             ("teamOnCreateScript", D_ASCII, "WP_WaveAttack")])
# nested PlayerScriptsList appended below (win/lose scripts), after its
# helper definitions

# ---------- ObjectsList v3 with nested Object v3 chunks ----------
def obj(x, y, angle, name, pairs):
    payload = struct.pack("<ffff", x, y, 0.0, angle)
    payload += struct.pack("<i", 0)  # flags
    payload += ascii_s(name)
    payload += dict_pairs(pairs)
    return chunk("Object", 3, payload)

# WP_PREVIEW=1: art-review mode — park enemy structures in view of the start
# camera so new assets can be judged without driving across the map.
preview = []
if os.environ.get("WP_PREVIEW"):
    row = [("WPJ_CommandPost", 510.0, 320.0, 0.3), ("WPJ_ChopShop", 640.0, 360.0, 0.2),
           ("WPJ_Watchpost", 700.0, 300.0, 0.0), ("WPJ_Rigger", 560.0, 260.0, 0.8),
           ("WPJ_Vulture", 620.0, 260.0, 0.8),
           ("WP_Bulwark", 300.0, 300.0, 0.0), ("WP_Outrider", 250.0, 350.0, 0.6),
           ("WP_Zenith", 250.0, 430.0, 0.6)]
    for tmpl, px, py, ang in row:
        preview.append(obj(px, py, ang, tmpl,
                           [("originalOwner", D_ASCII,
                             "teamPlayerB" if tmpl.startswith("WPJ") else "teamPlayerA")]))

objects_payload = b"".join(preview + [
    obj(400.0, 400.0, 0.0, F["player_cc"],
        [("originalOwner", D_ASCII, "teamPlayerA"),
         ("objectName", D_ASCII, "PlayerCC")]),
    obj(720.0, 560.0, 2.4, F["guard"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1200.0, 1200.0, 3.14159265, F["enemy_cc"],
        [("originalOwner", D_ASCII, "teamPlayerB"),
         ("objectName", D_ASCII, "EnemyCC")]),
    obj(1120.0, 1250.0, 2.6, F["enemy_factory"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1270.0, 1240.0, 3.4, F["enemy_power"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1105.0, 1105.0, 2.4, F["enemy_tower"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1280.0, 1120.0, 3.6, F["enemy_tower"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1150.0, 1150.0, 2.4, F["defender"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1240.0, 1160.0, 3.2, F["defender"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(1195.0, 1120.0, 2.8, F["defender_scout"],
        [("originalOwner", D_ASCII, "teamPlayerB")]),
    obj(400.0, 450.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 1), ("waypointName", D_ASCII, "Player_1_Start")]),
    obj(1200.0, 1150.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 2), ("waypointName", D_ASCII, "Player_2_Start")]),
    obj(400.0, 400.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 3), ("waypointName", D_ASCII, "InitialCameraPosition")]),
    obj(1150.0, 1100.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 4), ("waypointName", D_ASCII, "WaveSpawn")]),
])

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
P_UNIT = 14

def namekey(name):
    return struct.pack("<i", (toc.id(name) << 8) | D_ASCII)

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

def script(name, conditions, actions, one_shot=True, subroutine=False):
    payload = ascii_s(name) + ascii_s("") * 3          # name + 3 comments
    payload += bytes([1, 1 if one_shot else 0, 1, 1, 1,
                      1 if subroutine else 0])         # active, oneShot, easy, normal, hard, subroutine
    payload += struct.pack("<i", 0)                    # delayEvaluationSeconds
    payload += chunk("OrCondition", 1, b"".join(conditions))
    payload += b"".join(actions)
    return chunk("Script", 2, payload)

scripts_a = (
    script("WP_Win",
           [condition("NAMED_DESTROYED", [parameter(P_UNIT, s="EnemyCC")])],
           [action("VICTORY")])
    + script("WP_Lose",
             [condition("NAMED_DESTROYED", [parameter(P_UNIT, s="PlayerCC")])],
             [action("DEFEAT")])
)
P_REAL, P_TEAM, P_COUNTER, P_WAYPOINT = 1, 3, 4, 7
P_TEXT, P_SIDE = 10, 11
P_INT = 0

# Fog-of-war start: force classic C&C black shroud. No scripted home reveal —
# own structures light the base themselves (CC ShroudClearingRange 300), and
# the old 450wu permanent reveal was the "initial-reveal anomaly": it swallowed
# the whole starting viewport plus the enemy guard at (720,560), reading as
# "map starts bright / never-seen enemies visible" (MAP_SHROUD_ALL worked all
# along — the far corners it left black were the tell).
scripts_a += (
    script("WP_FogStart",
           [condition("CONDITION_TRUE", [])],
           [action("MAP_SHROUD_ALL", [parameter(P_SIDE, s="")])])   # all human players
)

# Attack waves: after a 90s grace, 2 Mongrels spawn at WaveSpawn every 75s
# and attack the player CC (team on-create script drives the attack so
# "<This Team>" binds to the fresh instance).
scripts_b = (
    script("WP_WaveStart",
           [condition("CONDITION_TRUE", [])],
           [action("SET_MILLISECOND_TIMER",
                   [parameter(P_COUNTER, s="WaveTimer"), parameter(P_REAL, r=150.0)])])
    + script("WP_WaveSpawn",
             [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="WaveTimer")])],
             [action("CREATE_REINFORCEMENT_TEAM",
                     [parameter(P_TEAM, s="teamWaveRaiders"), parameter(P_WAYPOINT, s="WaveSpawn")]),
              action("SET_MILLISECOND_TIMER",
                     [parameter(P_COUNTER, s="WaveTimer"), parameter(P_REAL, r=90.0)])],
             one_shot=False)
    + script("WP_PackStart",
           [condition("CONDITION_TRUE", [])],
           [action("SET_MILLISECOND_TIMER",
                   [parameter(P_COUNTER, s="PackTimer"), parameter(P_REAL, r=300.0)])])
    + script("WP_PackSpawn",
             [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="PackTimer")])],
             [action("CREATE_REINFORCEMENT_TEAM",
                     [parameter(P_TEAM, s="teamWavePack"), parameter(P_WAYPOINT, s="WaveSpawn")]),
              action("SET_MILLISECOND_TIMER",
                     [parameter(P_COUNTER, s="PackTimer"), parameter(P_REAL, r=150.0)])],
             one_shot=False)
    + script("WP_AssaultStart",
           [condition("CONDITION_TRUE", [])],
           [action("SET_MILLISECOND_TIMER",
                   [parameter(P_COUNTER, s="AssaultTimer"), parameter(P_REAL, r=480.0)])])
    + script("WP_AssaultSpawn",
             [condition("TIMER_EXPIRED", [parameter(P_COUNTER, s="AssaultTimer")])],
             [action("CREATE_REINFORCEMENT_TEAM",
                     [parameter(P_TEAM, s="teamWaveAssault"), parameter(P_WAYPOINT, s="WaveSpawn")]),
              action("SET_MILLISECOND_TIMER",
                     [parameter(P_COUNTER, s="AssaultTimer"), parameter(P_REAL, r=240.0)])],
             one_shot=False)
    + script("WP_WaveAttack",
             [condition("CONDITION_TRUE", [])],
             [action("TEAM_ATTACK_NAMED",
                     [parameter(P_TEAM, s="<This Team>"), parameter(P_UNIT, s="PlayerCC")])],
             one_shot=False, subroutine=True)
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

out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/GeneralsX/GeneralsZH/Maps/%s/%s.map" % (F["map_name"], F["map_name"]))
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "wb") as f:
    f.write(toc.emit() + chunks)
print(f"wrote {out_path} ({os.path.getsize(out_path)} bytes, {len(toc.names)} TOC entries)")
