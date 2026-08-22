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
height_payload = struct.pack("<iiii", W, H, BORDER, 1)      # width,height,border,numBoundaries
height_payload += struct.pack("<ii", PLAY, PLAY)            # boundary[0] -> world extent 640x640
height_payload += struct.pack("<i", N) + bytes([HEIGHT_BYTE]) * N

# ---------- BlendTileData v8 ----------
tile_ndx = bytearray()
for y in range(H):
    for x in range(W):
        # single texture class, firstTile 0: ndx = (tile<<2) + 2*(y&1) + (x&1)
        tile_ndx += struct.pack("<h", 2 * (y & 1) + (x & 1))
zeros16 = struct.pack("<h", 0) * N
blend_payload = struct.pack("<i", N)
blend_payload += bytes(tile_ndx)          # tileNdxes
blend_payload += zeros16                  # blendTileNdxes
blend_payload += zeros16                  # extraBlendTileNdxes
blend_payload += zeros16                  # cliffInfoNdxes
blend_payload += bytes(H * FSW)           # cellCliffState
blend_payload += struct.pack("<iiii", 1, 1, 1, 1)  # bitmapTiles, blendedTiles, cliffInfo, texClasses
blend_payload += struct.pack("<iiii", 0, 1, 1, 0) + ascii_s("WPGround")  # first,num,width,legacyGDF,name
blend_payload += struct.pack("<ii", 0, 0)  # numEdgeTiles, numEdgeTextureClasses

# ---------- WorldInfo v1 ----------
world_payload = dict_pairs([
    ("mapName", D_ASCII, "WPTest"),
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
    ("playerFaction", D_ASCII, "FactionWP"),
    ("playerAllies", D_ASCII, ""),
    ("playerEnemies", D_ASCII, "PlayerB"),
    ("playerColor", D_INT, 0x2882FF),
    ("playerNightColor", D_INT, 0x2882FF),
    ("playerStartMoney", D_INT, 5000),
    ("multiplayerStartIndex", D_INT, 0),
])
sides_payload += side([
    ("playerName", D_ASCII, "PlayerB"),
    ("playerIsHuman", D_BOOL, False),
    ("playerDisplayName", D_UNI, "Player B"),
    ("playerFaction", D_ASCII, "FactionWP"),
    ("playerAllies", D_ASCII, ""),
    ("playerEnemies", D_ASCII, "PlayerA"),
    ("playerColor", D_INT, 0xFF3C28),
    ("playerNightColor", D_INT, 0xFF3C28),
    ("playerStartMoney", D_INT, 5000),
    ("multiplayerStartIndex", D_INT, 1),
])
sides_payload += struct.pack("<i", 3)
sides_payload += dict_pairs([("teamName", D_ASCII, "team"),
                             ("teamOwner", D_ASCII, ""),
                             ("teamIsSingleton", D_BOOL, True)])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamPlayerA"),
                             ("teamOwner", D_ASCII, "PlayerA"),
                             ("teamIsSingleton", D_BOOL, True)])
sides_payload += dict_pairs([("teamName", D_ASCII, "teamPlayerB"),
                             ("teamOwner", D_ASCII, "PlayerB"),
                             ("teamIsSingleton", D_BOOL, True)])
# nested PlayerScriptsList appended below (win/lose scripts), after its
# helper definitions

# ---------- ObjectsList v3 with nested Object v3 chunks ----------
def obj(x, y, angle, name, pairs):
    payload = struct.pack("<ffff", x, y, 0.0, angle)
    payload += struct.pack("<i", 0)  # flags
    payload += ascii_s(name)
    payload += dict_pairs(pairs)
    return chunk("Object", 3, payload)

objects_payload = b"".join([
    obj(400.0, 400.0, 0.0, "WP_CommandCenter",
        [("originalOwner", D_ASCII, "teamPlayerA"),
         ("objectName", D_ASCII, "PlayerCC")]),
    obj(1200.0, 1200.0, 3.14159265, "WP_CommandCenter",
        [("originalOwner", D_ASCII, "teamPlayerB"),
         ("objectName", D_ASCII, "EnemyCC")]),
    obj(400.0, 450.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 1), ("waypointName", D_ASCII, "Player_1_Start")]),
    obj(1200.0, 1150.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 2), ("waypointName", D_ASCII, "Player_2_Start")]),
    obj(400.0, 400.0, 0.0, "*Waypoints/Waypoint",
        [("waypointID", D_INT, 3), ("waypointName", D_ASCII, "InitialCameraPosition")]),
])

# ---------- GlobalLighting v3 ----------
light = struct.pack("<9f", 0.3, 0.3, 0.3, 0.7, 0.7, 0.7, -0.5, 0.5, -0.75)
lighting_payload = struct.pack("<i", 2)  # AFTERNOON
lighting_payload += (light * 6) * 4      # per TOD: TL[0], TOL[0], TOL[1], TOL[2], TL[1], TL[2]

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

def script(name, conditions, actions):
    payload = ascii_s(name) + ascii_s("") * 3          # name + 3 comments
    payload += bytes([1, 1, 1, 1, 1, 0])               # active, oneShot, easy, normal, hard, subroutine
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
             [action("LOCALDEFEAT")])
)
scripts_payload = (
    chunk("ScriptList", 1, b"")            # index 0: neutral
    + chunk("ScriptList", 1, scripts_a)    # index 1: PlayerA (local)
    + chunk("ScriptList", 1, b"")          # index 2: PlayerB
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
    "~/GeneralsX/GeneralsZH/Maps/WPTest/WPTest.map")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "wb") as f:
    f.write(toc.emit() + chunks)
print(f"wrote {out_path} ({os.path.getsize(out_path)} bytes, {len(toc.names)} TOC entries)")
