# SPDX-License-Identifier: MIT
"""Original base-kit architecture and builders for build_polish.py.

The seven established base models — both command structures, the Meridian
Power Array and Vehicle Plant, the Jackal Chop Shop and the two builders —
keep the geometry, palette and painted treatment of the August 2026 kit
scripts they were first authored in (build_mercc.py, build_jakcp.py,
build_meridian_base.py and build_jackal_base.py, retired on 2026-09-08 when
the models joined the catalog). +X is forward. Everything is authored from
primitives; no imported geometry or images.

Each builder returns the catalog contract build_polish.py needs: the
HOUSECOLOR0 ownership panel (the frustum legacy_contracts.py used to append
after export), the UV island margin and the complete composite recipe the kit
used, so the catalog reproduces the established look rather than restyling it.
"""

# Linear RGBA. Upper-case names keep the kit palette distinct from
# build_polish.PAL inside one Kit; both are available to every builder.
PALETTE = {
    'STEEL': (0.722, 0.761, 0.800, 1.0),
    'WHITE': (0.910, 0.925, 0.941, 1.0),
    'GOLD': (0.843, 0.706, 0.353, 1.0),
    'GUN': (0.353, 0.376, 0.408, 1.0),
    'DARK': (0.290, 0.306, 0.333, 1.0),
    'TREAD': (0.200, 0.212, 0.231, 1.0),
    'GLASS': (0.18, 0.24, 0.30, 1.0),
    'SAND': (0.788, 0.690, 0.541, 1.0),
    'RUST': (0.541, 0.353, 0.235, 1.0),
    'OXIDE': (0.435, 0.561, 0.353, 1.0),
    'GRAPHITE': (0.290, 0.306, 0.333, 1.0),
    'CHARCOAL': (0.180, 0.192, 0.220, 1.0),
}

# HOUSECOLOR0 ownership panels: (cx, cy, z, sx, sy, sz) frustums the engine
# recolors for the owning player. Positions are the engine-facing contract
# established on 2026-09-05; they sit on each model's most visible roof.
PANELS = {
    'mercc01': (-2, -5, 28.46, 4.2, 4.2, .10),
    'jakcp01': (-3, 0, 12.27, 4.5, 4.5, .10),
    'merpp01': (-2, 0, 14.12, 4.5, 5, .10),
    'merwf01': (21, -6, 10.36, 4.5, 5, .10),
    'jakcs01': (0, 0, 16.67, 7, 2, .10),
    'mersuv01': (-1.8, 0, 8.36, 2.1, 2.7, .10),
    'jakrig01': (5, 0, 6.76, 2.4, 2.8, .10),
}

# The kit scripts' smart-UV island margin and painted-composite settings.
# build_polish.py's house defaults differ (.009 margin, lighter edge wear,
# finer grain); these values are what the shipped textures were made with.
UV_MARGIN = 0.006
BUILDING = dict(shade_lo=0.52, shade_hi=0.48, grain=0.018, edge_strength=0.45, edge_radius=2, lowfreq=0.035)
JACKAL_BUILDING = dict(shade_lo=0.50, shade_hi=0.50, grain=0.028, edge_strength=0.5, edge_radius=2, lowfreq=0.05)
FABRICATOR = dict(shade_lo=0.52, shade_hi=0.48, grain=0.02, edge_strength=0.5, edge_radius=1, lowfreq=0.045)
RIGGER = dict(shade_lo=0.50, shade_hi=0.50, grain=0.03, edge_strength=0.5, edge_radius=1, lowfreq=0.045)


def contract(model, role, seed, recipe):
    return dict(asset_role=role, house=[PANELS[model]], uv_margin=UV_MARGIN, composite=dict(seed=seed, **recipe))


# ---------- Meridian Command Center (hero building, D015 bar) ----------
def command_center(k):
    # Terraced white monolith, gold cornice ring, corner tower with a
    # gold-tipped mast: chamfered plinth, entry portal, comms dish, vents,
    # landing pad.
    # plinth + podium
    k.box('PLINTH', 'DARK', 0, 0, 1.25, 46, 46, 2.5, bevel=0.8)
    k.box('PODIUM', 'STEEL', 0, 0, 5.5, 40, 40, 6, bevel=0.5)

    # entry portal on the front (-y): frame, recessed door, flanking lights
    k.box('PORTFRAME', 'STEEL', 0, -20.4, 5.4, 11, 2.0, 7.2, bevel=0.3)
    k.box('PORTDOOR', 'GLASS', 0, -21.1, 4.8, 7.4, 1.2, 5.6)
    k.box('LIGHTL', 'GOLD', -6.6, -20.9, 7.6, 1.0, 0.6, 1.0)
    k.box('LIGHTR', 'GOLD', 6.6, -20.9, 7.6, 1.0, 0.6, 1.0)

    # vents + landing pad on the podium roof
    k.box('VENTL', 'GUN', -14, 13, 9.6, 6.5, 4.5, 2.2, bevel=0.3)
    k.box('VENTR', 'GUN', -14, 5, 9.6, 6.5, 4.5, 2.2, bevel=0.3)
    k.box('PAD', 'DARK', 12, 12, 9.0, 13, 14, 1.0)
    k.box('PADTRIM', 'GOLD', 12, 12, 9.55, 9.5, 10.5, 0.35)

    # main block with cornice ring
    k.box('BLOCK', 'WHITE', 0, -3, 14.5, 30, 30, 12, bevel=0.6)
    for nm, x, y, sx, sy in (('CORN_N', 0, 11.6, 27.5, 1.2), ('CORN_S', 0, -17.6, 27.5, 1.2),
                             ('CORN_E', 14.6, -3, 1.2, 25.0), ('CORN_W', -14.6, -3, 1.2, 25.0)):
        k.box(nm, 'GOLD', x, y, 19.9, sx, sy, 1.4)

    # glass band near the block top (command deck windows)
    k.box('DECKGLASS', 'GLASS', 0, -18.7, 17.5, 22, 0.6, 2.2)

    # clerestory + crown
    k.box('CLERE', 'STEEL', 0, -3, 22.0, 23, 23, 3.0, bevel=0.4)
    k.box('CROWN', 'WHITE', -2, -5, 25.5, 15, 15, 4.0, bevel=0.5)
    k.box('BEACON', 'GOLD', -2, -5, 27.9, 5.5, 5.5, 1.0, bevel=0.2)
    k.cyl('ANT1', 'DARK', -6.5, -9.5, 30.0, 0.16, 5.0, verts=6)
    k.cyl('ANT2', 'DARK', 2.0, -1.0, 29.4, 0.16, 3.6, verts=6)

    # corner comms tower
    k.box('TOWER', 'STEEL', 10, 8, 26.0, 10, 10, 9.0, bevel=0.4)
    k.box('TOWERTRIM', 'GOLD', 10, 8, 30.7, 8.2, 8.2, 0.8)
    k.cyl('MAST', 'GUN', 10, 8, 34.5, 0.7, 7.0, verts=8)
    k.box('TIP', 'GOLD', 10, 8, 38.4, 1.9, 1.9, 1.2)
    # dish: tilted disc + bracket on the tower's outboard corner
    k.box('BRACKET', 'GUN', 14.2, 12.2, 29.5, 1.4, 1.4, 3.4)
    k.cyl('DISH', 'STEEL', 15.6, 13.6, 31.6, 3.4, 0.8, axis='Z', verts=12,
          rot=(0.9, 0.0, -0.78))
    k.cyl('FEED', 'GUN', 15.6, 13.6, 32.6, 0.22, 2.6, verts=6, rot=(0.9, 0.0, -0.78))

    # walkway from clerestory to tower
    k.box('WALK', 'STEEL', 5, 2, 21.2, 6.0, 2.6, 0.7)
    return contract('mercc01', 'structure', 11, BUILDING)


# ---------- Jackal Command Post (hero building, D015 bar) ----------
def command_post(k):
    # Scavenger compound: bermed perimeter, roofed blockhouse with rust
    # reinforcement, crate stacks under an oxide tarp, water tank, lattice
    # watchtower with a crow's nest, salvaged dish.
    k.rough = 0.95  # portrait roughness only; the bakes are roughness-independent
    # ground slab + berm walls (entry gap on -y)
    k.box('SLAB', 'GRAPHITE', 0, 0, 1.1, 40, 36, 2.2, bevel=0.6)
    wall = [(-19, 2.2), (19, 2.2), (16.5, 5.6), (-16.5, 5.6)]
    k.prism('BERM_N', 'SAND', wall, 15.4, 18.0)
    k.prism('BERM_S1', 'SAND', [(-19, 2.2), (-6, 2.2), (-5, 5.4), (-16.5, 5.4)], -18.0, -15.4)
    k.prism('BERM_S2', 'SAND', [(7, 2.2), (19, 2.2), (16.5, 5.4), (8, 5.4)], -18.0, -15.4)
    k.box('BERM_E', 'SAND', 18.2, 0, 3.8, 2.8, 31, 3.2, bevel=0.5)
    k.box('BERM_W', 'SAND', -18.2, 0, 3.8, 2.8, 31, 3.2, bevel=0.5)

    # sandbags at the entry gap
    for i, (bx, by) in enumerate(((-2.5, -16.6), (0.5, -16.9), (3.5, -16.5))):
        k.box(f'BAG{i}', 'SAND', bx, by, 2.9, 2.6, 1.6, 1.3, bevel=0.35)

    # blockhouse with roof overhang + rust reinforcement
    k.box('HOUSE', 'SAND', -4, 3, 6.7, 22, 16, 9, bevel=0.4)
    k.box('ROOF', 'GRAPHITE', -3.2, 3, 11.6, 25, 19, 1.2, rot=(0, 0, 0.04))
    k.box('RIB1', 'RUST', -14.7, 3, 6.7, 0.9, 15.5, 8.5)
    k.box('RIB2', 'RUST', -4, 10.7, 6.7, 21.5, 0.9, 8.5)
    k.box('DOOR', 'CHARCOAL', -4, -5.2, 4.9, 5.5, 0.8, 5.5)
    k.box('WINDOW', 'CHARCOAL', 3.5, -5.1, 8.0, 4.0, 0.6, 2.0)
    # rooftop clutter: cooler + pipe
    k.box('COOLER', 'GUN', -9, 6, 12.8, 4.0, 3.2, 1.6, bevel=0.25)
    k.cyl('STACK', 'CHARCOAL', 2, 8.5, 13.8, 0.9, 5.0, verts=8)
    k.cyl('STACKBAND', 'RUST', 2, 8.5, 15.2, 1.05, 0.8, verts=8)

    # crates + oxide tarp
    k.box('CRATE1', 'CHARCOAL', -12, -9, 3.6, 4.6, 3.8, 2.8)
    k.box('CRATE2', 'RUST', -8.5, -10, 3.3, 3.4, 3.0, 2.2, rot=(0, 0, 0.25))
    k.box('CRATE3', 'CHARCOAL', -11, -6.5, 5.6, 3.2, 2.8, 1.6, rot=(0, 0, -0.15))
    k.box('TARP', 'OXIDE', -10.5, -8, 6.9, 9.5, 8.0, 0.9, bevel=0.4, rot=(0.06, -0.08, 0.12))

    # water tank on legs
    k.cyl('TANK', 'RUST', 12, 10, 6.8, 3.6, 6.0, verts=12)
    k.cyl('TANKCAP', 'CHARCOAL', 12, 10, 10.0, 3.7, 0.5, verts=12)
    for i, (lx, ly) in enumerate(((9.5, 7.6), (14.5, 7.6), (9.5, 12.4), (14.5, 12.4))):
        k.box(f'LEG{i}', 'CHARCOAL', lx, ly, 2.9, 0.8, 0.8, 1.6)

    # watchtower: legs, platform, nest, roof, mast
    TX, TY = 13, -8
    for i, (lx, ly) in enumerate(((TX - 2.6, TY - 2.6), (TX + 2.6, TY - 2.6),
                                  (TX - 2.6, TY + 2.6), (TX + 2.6, TY + 2.6))):
        k.box(f'TLEG{i}', 'GRAPHITE', lx, ly, 7.7, 1.0, 1.0, 13)
    k.box('TBRACE1', 'GRAPHITE', TX, TY - 2.7, 7.5, 5.6, 0.5, 0.7)
    k.box('TBRACE2', 'GRAPHITE', TX - 2.7, TY, 10.5, 0.5, 5.6, 0.7)
    k.box('TDECK', 'SAND', TX, TY, 14.6, 8.8, 8.8, 1.0)
    for nm, dx, dy, sx, sy in (('NW_N', 0, 4.1, 8.8, 0.6), ('NW_S', 0, -4.1, 8.8, 0.6),
                               ('NW_E', 4.1, 0, 0.6, 7.6), ('NW_W', -4.1, 0, 0.6, 7.6)):
        k.box(f'NEST{nm}', 'SAND', TX + dx, TY + dy, 16.2, sx, sy, 2.2)
    k.box('TROOF', 'RUST', TX + 0.4, TY, 19.3, 10, 10, 0.8, rot=(0, 0.05, 0))
    k.cyl('TPOLE', 'GRAPHITE', TX - 3.5, TY - 3.5, 17.8, 0.35, 4.5, verts=6)
    k.cyl('TMAST', 'GRAPHITE', TX + 3.8, TY + 3.8, 21.8, 0.35, 6.0, verts=6)
    k.box('PENNANT', 'OXIDE', TX + 3.8, TY + 4.9, 24.2, 0.25, 2.0, 1.1)

    # salvaged dish, propped on the roof
    k.box('DBRACK', 'GUN', 4, 9.5, 12.8, 1.2, 1.2, 1.8)
    k.cyl('DISH', 'GUN', 4.6, 10.1, 14.0, 3.0, 0.7, axis='Z', verts=10,
          rot=(1.05, 0.0, 0.6))
    return contract('jakcp01', 'structure', 17, JACKAL_BUILDING)


# ---------- Fabricator: tracked construction vehicle with dozer blade ----------
def fabricator(k):
    k.box('CHASSIS', 'STEEL', 0, 0, 3.4, 12.0, 8.0, 3.2, bevel=0.4)
    for side, yc in (('L', -4.6), ('R', 4.6)):
        k.box(f'TRACK{side}', 'TREAD', 0, yc, 1.8, 13.5, 2.2, 2.8)
    # angled dozer blade up front
    k.prism('BLADE', 'GOLD', [(7.0, 0.6), (8.6, 0.6), (8.2, 4.6), (6.6, 4.2)], -5.2, 5.2)
    k.box('BLADEARM_L', 'GUN', 5.2, -3.4, 2.8, 3.4, 0.7, 0.7)
    k.box('BLADEARM_R', 'GUN', 5.2, 3.4, 2.8, 3.4, 0.7, 0.7)
    # cab with glass strip
    k.box('CAB', 'WHITE', -1.8, 0, 6.6, 6.0, 6.4, 3.4, bevel=0.4)
    k.box('GLASS', 'GLASS', 0.6, 0, 7.0, 1.4, 5.2, 1.8)
    k.box('STRIPE', 'GOLD', -4.6, 0, 6.4, 0.5, 6.0, 0.9)
    # rear equipment: crane arm stub + light
    k.box('RIG', 'GUN', -5.4, 1.8, 6.2, 2.6, 2.0, 1.6, bevel=0.25)
    k.cyl('MAST', 'DARK', -5.0, -2.4, 8.4, 0.14, 3.2, verts=6)
    k.box('LIGHT', 'GOLD', -5.0, -2.4, 10.1, 0.7, 0.7, 0.5)
    return contract('mersuv01', 'vehicle', 21, FABRICATOR)


# ---------- Power Array: hall + twin gold-ringed stacks + yard ----------
def power_array(k):
    k.box('PLINTH', 'DARK', 0, 0, 1.0, 40, 34, 2.0, bevel=0.6)
    k.box('HALL', 'WHITE', -4, 0, 8.0, 24, 24, 12, bevel=0.5)
    k.box('HALLTRIM', 'GOLD', -4, 0, 13.6, 21, 21, 0.9)
    k.box('CTRL', 'STEEL', -4, -13.6, 4.6, 12, 3.6, 7.0, bevel=0.4)
    k.box('CTRLGLASS', 'GLASS', -4, -15.3, 6.2, 9.0, 0.5, 2.0)
    for i, sx in enumerate((10.5, 15.5)):
        k.cyl(f'STACK{i}', 'STEEL', sx, 5.5, 13.0, 2.6, 18.0, verts=12)
        k.cyl(f'RING{i}', 'GOLD', sx, 5.5, 19.0, 2.85, 1.1, verts=12)
        k.cyl(f'CAP{i}', 'DARK', sx, 5.5, 22.2, 2.2, 0.8, verts=12)
    # transformer yard
    for i, (bx, by) in enumerate(((12, -8), (16, -8), (12, -12.5))):
        k.box(f'XFMR{i}', 'GUN', bx, by, 3.2, 3.0, 3.0, 2.4, bevel=0.3)
        k.cyl(f'COIL{i}', 'DARK', bx, by, 5.3, 0.8, 1.8, verts=8)
    k.box('VENT1', 'GUN', -10, 8, 14.6, 5.0, 4.0, 1.4, bevel=0.3)
    k.box('VENT2', 'GUN', -10, 1, 14.6, 5.0, 4.0, 1.4, bevel=0.3)
    return contract('merpp01', 'structure', 22, BUILDING)


# ---------- Vehicle Plant: assembly hall, gate, gantry crane ----------
def vehicle_plant(k):
    k.box('PLINTH', 'DARK', 0, 0, 1.0, 48, 40, 2.0, bevel=0.6)
    k.box('HALL', 'WHITE', 0, 3, 9.5, 34, 28, 15, bevel=0.6)
    k.box('CORNICE', 'GOLD', 0, 3, 16.6, 31, 25, 1.0)
    # gate: recessed dark opening with gold hazard frame, facing -y
    k.box('GATEFRAME', 'GOLD', 0, -11.6, 6.2, 15, 1.4, 10.4)
    k.box('GATE', 'TREAD', 0, -12.0, 5.6, 12.5, 1.2, 9.2)
    # roof: gantry crane rails + trolley + skylight band
    k.box('RAIL_L', 'GUN', -12, 3, 17.8, 1.0, 26, 1.4)
    k.box('RAIL_R', 'GUN', 12, 3, 17.8, 1.0, 26, 1.4)
    k.box('BRIDGE', 'STEEL', 0, 8, 18.4, 25, 2.4, 1.2)
    k.box('TROLLEY', 'GOLD', 4, 8, 19.3, 3.0, 2.8, 0.9)
    k.box('SKYLIGHT', 'GLASS', 0, -1, 17.2, 20, 6, 0.5)
    # side office
    k.box('OFFICE', 'STEEL', 21, -6, 5.4, 8.0, 12.0, 8.8, bevel=0.4)
    k.box('OFFGLASS', 'GLASS', 24.8, -6, 6.4, 0.5, 9.0, 2.0)
    k.box('OFFTRIM', 'GOLD', 21, -6, 10.0, 7.0, 11.0, 0.6)
    # stacks + vents
    k.cyl('STACK', 'GUN', -14, 12, 18.5, 1.3, 6.0, verts=10)
    k.box('VENT', 'GUN', 8, 13, 17.6, 6.0, 3.0, 1.2, bevel=0.3)
    return contract('merwf01', 'structure', 23, BUILDING)


# ---------- Rigger: welded half-truck with crane (canon: docs/creative.md) ----------
def rigger(k):
    k.rough = 0.92  # portrait roughness only; the bakes are roughness-independent
    k.box('BED', 'RUST', -2.0, 0, 3.4, 9.0, 7.0, 1.6)
    k.box('CAB', 'SAND', 5.0, 0, 4.6, 5.0, 6.2, 4.2, bevel=0.4)
    k.box('GLASS', 'GLASS', 7.2, 0, 5.4, 0.8, 4.8, 1.6)
    k.box('GRILLE', 'CHARCOAL', 7.8, 0, 3.2, 0.6, 4.6, 1.4)
    for side, yc in (('L', -3.2), ('R', 3.2)):
        k.box(f'TRACK{side}', 'TREAD', -2.2, yc, 1.6, 9.4, 1.8, 2.4)
        k.cyl(f'WHEELF{side}', 'CHARCOAL', 5.4, yc, 1.7, 1.7, 1.8, axis='Y', verts=10)
    # crane arm + welding rig on the bed
    k.box('CRANEBASE', 'GRAPHITE', -4.5, 1.6, 4.8, 2.2, 2.2, 1.6)
    k.box('CRANEARM', 'GUN', -2.0, 1.6, 6.6, 7.0, 0.9, 0.9, rot=(0, -0.18, 0))
    k.box('HOOK', 'GOLD', 1.4, 1.6, 5.6, 0.6, 0.6, 1.2)
    k.box('TANKS', 'OXIDE', -4.6, -2.0, 4.6, 2.4, 2.2, 1.8, bevel=0.3)
    k.cyl('STACK', 'CHARCOAL', 2.6, -2.8, 6.2, 0.5, 2.6, verts=8)
    return contract('jakrig01', 'vehicle', 51, RIGGER)


# ---------- Chop Shop: open-sided garage with hoist ----------
def chop_shop(k):
    k.rough = 0.92  # portrait roughness only; the bakes are roughness-independent
    k.box('SLAB', 'GRAPHITE', 0, 0, 1.0, 44, 36, 2.0, bevel=0.6)
    # four corner posts + big roof
    for i, (px, py) in enumerate(((-16, -12), (16, -12), (-16, 12), (16, 12))):
        k.box(f'POST{i}', 'RUST', px, py, 8.0, 2.2, 2.2, 12)
    k.box('ROOF', 'SAND', 0, 0, 15.0, 40, 30, 1.6, rot=(0, 0.03, 0))
    k.box('ROOFRIDGE', 'RUST', 0, 0, 16.2, 40, 3.0, 0.8)
    # back wall + side wall (open front and one side)
    k.box('BACK', 'SAND', 0, 14.2, 8.0, 38, 1.6, 11)
    k.box('SIDE', 'SAND', -18.4, 0, 8.0, 1.6, 28, 11)
    k.box('SIDERIB', 'RUST', -18.5, 0, 8.0, 0.8, 26, 9)
    # hoist gantry inside
    k.box('GANTRY', 'GUN', 0, 2, 12.6, 26, 1.6, 1.2)
    k.box('TROLLEY', 'GOLD', -4, 2, 11.4, 2.6, 2.2, 1.2)
    k.cyl('CHAIN', 'CHARCOAL', -4, 2, 9.9, 0.18, 2.2, verts=6)
    # clutter: engine block, tire stack, barrels
    k.box('BLOCK', 'CHARCOAL', 8, -6, 3.6, 4.5, 3.5, 3.2, bevel=0.3)
    for i in range(3):
        k.cyl(f'TIRE{i}', 'TREAD', -10, -8, 2.6 + i * 1.1, 2.2, 1.0, verts=12)
    k.cyl('BARREL1', 'OXIDE', 13, 8, 3.7, 1.3, 3.4, verts=10)
    k.cyl('BARREL2', 'RUST', 15.5, 6.5, 3.7, 1.3, 3.4, verts=10)
    k.box('SIGN', 'OXIDE', 0, -14.5, 13.0, 10, 0.5, 3.0, rot=(0, 0, 0.04))
    return contract('jakcs01', 'structure', 52, JACKAL_BUILDING)


# (portrait label, texture stem, authoring function, BAKE size): the five
# buildings bake at 512 and ship area-halved (optimize_art.HALVED); the two
# builders bake and ship at 256.
ASSETS = {
    'mercc01': ('command-center', 'wp_mercc', command_center, 512),
    'jakcp01': ('command-post', 'wp_jakcp', command_post, 512),
    'merpp01': ('power-array', 'wp_merpp', power_array, 512),
    'merwf01': ('vehicle-plant', 'wp_merwf', vehicle_plant, 512),
    'jakcs01': ('chop-shop', 'wp_jakcs', chop_shop, 512),
    'mersuv01': ('fabricator', 'wp_surveyor', fabricator, 256),
    'jakrig01': ('rigger', 'wp_rigger', rigger, 256),
}
