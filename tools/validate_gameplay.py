#!/usr/bin/env python3
"""Validate shipped map bytes, mission outcomes, balance contracts and INI links.

This independently decodes the generated CkMp files. It deliberately does not
import genmap: a writer bug must not validate itself. Script scenarios check
objective logic, not combat/pathfinding; those still require a browser match.
"""
from collections import Counter, deque
from copy import deepcopy
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        assert 0 <= count <= len(self.data) - self.pos, "truncated map chunk"
        out = self.data[self.pos:self.pos + count]
        self.pos += count
        return out

    def unpack(self, fmt):
        return struct.unpack("<" + fmt, self.take(struct.calcsize("<" + fmt)))

    def string(self, wide=False):
        size, = self.unpack("H")
        return self.take(size * (2 if wide else 1)).decode("utf-16-le" if wide else "ascii")

    def chunks(self, toc):
        while self.pos < len(self.data):
            key, version, size = self.unpack("IHi")
            yield toc[key], version, Reader(self.take(size))

    def dictionary(self, toc):
        count, = self.unpack("H")
        result = {}
        for _ in range(count):
            key, = self.unpack("i")
            kind = key & 255
            if kind == 0:
                value = bool(self.unpack("B")[0])
            elif kind == 1:
                value = self.unpack("i")[0]
            elif kind == 2:
                value = self.unpack("f")[0]
            else:
                assert kind in (3, 4), f"unknown dictionary kind {kind}"
                value = self.string(kind == 4)
            result[toc[key >> 8]] = value
        return result


def call(reader, toc):
    _, namekey, count = reader.unpack("iii")
    params = []
    for _ in range(count):
        kind, integer, real = reader.unpack("iif")
        params.append((kind, integer, real, reader.string()))
    assert reader.pos == len(reader.data), "parameter/chunk length mismatch"
    return toc[namekey >> 8], params


def read_map(path):
    r = Reader(path.read_bytes())
    assert r.take(4) == b"CkMp"
    count, = r.unpack("i")
    toc = {}
    for _ in range(count):
        size, = r.unpack("B")
        label = r.take(size).decode("ascii")
        key, = r.unpack("I")
        toc[key] = label
    result = dict(objects=[], sides=[], teams=[], scripts=[])
    for label, _, payload in r.chunks(toc):
        if label == "HeightMapData":
            width, height, border, boundary_count = payload.unpack("4i")
            boundaries = [payload.unpack("2i") for _ in range(boundary_count)]
            count, = payload.unpack("i")
            assert count == width * height
            result["terrain"] = dict(width=width, height=height, border=border,
                                     playable=boundaries[0], heights=payload.take(count))
        elif label == "BlendTileData":
            count, = payload.unpack("i")
            payload.take(count * 8)  # four arrays of signed 16-bit indices
            terrain = result["terrain"]
            terrain["cliffs"] = payload.take(terrain["height"] * ((terrain["width"] + 7) // 8))
        elif label == "ObjectsList":
            for object_label, _, obj in payload.chunks(toc):
                assert object_label == "Object"
                x, y, z, angle, flags = obj.unpack("ffffi")
                template = obj.string()
                props = obj.dictionary(toc)
                result["objects"].append(dict(template=template, x=x, y=y, props=props))
                assert obj.pos == len(obj.data)
        elif label == "SidesList":
            side_count, = payload.unpack("i")
            for _ in range(side_count):
                side = payload.dictionary(toc)
                build_count, = payload.unpack("i")
                side["builds"] = []
                for _ in range(build_count):
                    name, template = payload.string(), payload.string()
                    payload.take(21)  # position + angle + initial flag + rebuild count
                    payload.string()
                    payload.take(7)  # health + three behavior flags
                    side["builds"].append(template)
                result["sides"].append(side)
            team_count, = payload.unpack("i")
            result["teams"] = [payload.dictionary(toc) for _ in range(team_count)]
            for script_label, _, script_payload in payload.chunks(toc):
                assert script_label == "PlayerScriptsList"
                for side_index, (list_label, _, script_list) in enumerate(script_payload.chunks(toc)):
                    assert list_label == "ScriptList"
                    for entry_label, _, entry in script_list.chunks(toc):
                        assert entry_label == "Script"
                        name = entry.string()
                        for _ in range(3):
                            entry.string()
                        active, once, easy, normal, hard, subroutine = entry.unpack("6B")
                        entry.unpack("i")
                        script = dict(name=name, side=side_index, active=active, once=once, subroutine=subroutine,
                                      enabled=(easy, normal, hard), conditions=[], actions=[])
                        for kind, _, body in entry.chunks(toc):
                            if kind == "OrCondition":
                                script["conditions"].append([call(c, toc) for _, _, c in body.chunks(toc)])
                            else:
                                assert kind == "ScriptAction"
                                script["actions"].append(call(body, toc))
                        result["scripts"].append(script)
    return result


def blocks(path, word):
    text = path.read_text()
    return {m[1]: m[0] for m in re.finditer(r"(?ms)^" + word + r" (\w+)\n.*?(?=^" + word + r" |\Z)", text)}


def scalar(block, key):
    value = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*([^;\n]+)", block)
    assert value, f"missing {key}"
    return float(value[1].strip())


def combat_commands(buttons, command_sets):
    contracts = (("Command_WPAttackMove", "ATTACK_MOVE", True),
                 ("Command_WPGuard", "GUARD", True),
                 ("Command_WPStop", "STOP", False))
    available = set(re.findall(r"(?m)^\s*\d+\s*=\s*(\w+)", command_sets["WP_CombatUnitCommandSet"]))
    for name, command, needs_position in contracts:
        assert name in available, f"{name}: missing from the shared combat command set"
        button = buttons[name]
        actual_command = re.search(r"(?m)^\s*Command\s*=\s*(\w+)", button)
        assert actual_command and actual_command[1] == command, f"{name}: wrong native order"
        options_match = re.search(r"(?m)^\s*Options\s*=\s*([^;\n]+)", button)
        options = set(options_match[1].split()) if options_match else set()
        assert "OK_FOR_MULTI_SELECT" in options, f"{name}: must work for a selected army"
        # NEED_TARGET_POS keeps the destination click in GUICommandTranslator.
        # Without it, ATTACK_MOVE toggles legacy mode and the normal selection
        # translator consumes the left-click instead in right-click order mode.
        if needs_position:
            assert "NEED_TARGET_POS" in options, f"{name}: needs position targeting to consume the destination click"
        else:
            assert not any(option.startswith("NEED_TARGET_") for option in options), f"{name}: Stop must execute immediately without targeting"


def training_requirements(mission, game_map, objects):
    objectives = mission["objectives"]
    assert len(objectives) >= 2 and all(not objective["optional"] for objective in objectives), "training guidance stages must match required objectives"
    assert objectives[-1].get("requirements", []) == [], "training finish must not invent a construction gate"
    gates = {}
    for script in game_map["scripts"]:
        if not script["name"].startswith("WP_TrainingStep"):
            continue
        match = re.fullmatch(r"WP_TrainingStep(\d+)", script["name"])
        assert match, f"invalid training gate name: {script['name']}"
        stage = int(match[1])
        assert stage not in gates, f"duplicate training gate {stage}"
        gates[stage] = script
    assert set(gates) == set(range(len(objectives) - 1)), "training metadata stages differ from shipped native gates"
    for stage, script in gates.items():
        requirements = objectives[stage].get("requirements")
        assert isinstance(requirements, list) and requirements, f"training stage {stage}: missing requirements"
        described = set()
        for requirement in requirements:
            assert isinstance(requirement, dict), f"training stage {stage}: invalid requirement"
            template, count = requirement.get("template"), requirement.get("count")
            assert isinstance(template, str) and template in objects, f"training stage {stage}: unknown requirement template"
            assert type(count) is int and count > 0, f"training stage {stage}: requirement count must be a positive integer"
            assert type(requirement.get("requiresBuilder", False)) is bool, f"training stage {stage}: requiresBuilder must be boolean"
            if requirement.get("requiresBuilder"):
                assert re.search(r"(?m)^\s*KindOf\s*=.*\bSTRUCTURE\b", objects[template]), f"training stage {stage}: builder recovery requires a structure"
            for field in ("label", "hint"):
                assert isinstance(requirement.get(field), str) and requirement[field].strip(), f"training stage {stage}: requirement needs {field}"
            assert template not in {item[0] for item in described}, f"training stage {stage}: duplicate requirement template"
            described.add((template, count))
        assert script["side"] == 1 and script["active"] and script["once"] and not script["subroutine"] and all(script["enabled"]), f"training stage {stage}: gate must run once for the player on every difficulty"
        assert len(script["conditions"]) == 1, f"training stage {stage}: guidance cannot describe alternative native gates"
        actual, counters = set(), []
        for name, params in script["conditions"][0]:
            if name == "COUNTER":
                counters.append((params[0][3], params[1][1], params[2][1]))
            else:
                assert name == "PLAYER_HAS_OBJECT_COMPARISON", f"training stage {stage}: unrepresented native prerequisite {name}"
                assert params[0][3] == "PlayerA" and params[1][1] == 3, f"training stage {stage}: requirements must test player-owned minimum counts"
                pair = (params[3][3], params[2][1])
                assert pair not in actual, f"training stage {stage}: duplicate native prerequisite"
                actual.add(pair)
        assert counters == [("WP_ObjectiveStage", 2, stage)], f"training stage {stage}: native gate listens to the wrong objective stage"
        assert described == actual, f"training stage {stage}: metadata requirements {sorted(described)} differ from native gate {sorted(actual)}"
        advances = [(params[0][3], params[1][1]) for name, params in script["actions"]
                    if name == "SET_COUNTER" and params[0][3] == "WP_ObjectiveStage"]
        assert advances == [("WP_ObjectiveStage", stage + 1)], f"training stage {stage}: gate must advance to the next guidance stage"


def validate_links(game_map, objects, strings, templates):
    named = {o["props"]["objectName"] for o in game_map["objects"] if "objectName" in o["props"]}
    for o in game_map["objects"]:
        assert o["template"] in objects or o["template"].startswith("*Waypoints/"), o["template"]
    for side in game_map["sides"]:
        assert all(t in objects for t in side["builds"])
    for script in game_map["scripts"]:
        calls = [("action", c) for c in script["actions"]]
        calls += [("condition", c) for group in script["conditions"] for c in group]
        for kind, (name, params) in calls:
            assert (kind, name) in templates, f"unknown native script {kind} {name}"
            assert len(params) == templates[kind, name], (name, len(params), templates[kind, name])
            for param_type, _, _, value in params:
                if param_type == 14 and value and not value.startswith("<"):
                    assert value in named, f"missing named target: {value}"
                if param_type == 15:
                    assert value in objects, f"missing object type: {value}"
                if name == "DISPLAY_TEXT":
                    assert value in strings, f"missing objective string: {value}"
    caches = [o for o in game_map["objects"] if o["template"] == "WP_SupplyCache"]
    assert len(caches) == 4, "each map needs home and contested supply sites"
    scripts_by_name = {s["name"]: s for s in game_map["scripts"]}
    for team in game_map["teams"]:
        for key in ("teamProductionCondition", "teamOnCreateScript"):
            if key in team:
                assert team[key] in scripts_by_name, f"missing team script: {team[key]}"
        for key, value in team.items():
            if key.startswith("teamUnitType"):
                assert value in objects, f"unknown team unit: {value}"


class MissionState:
    """Small event evaluator for native predicates used by the authored missions."""
    def __init__(self, game_map):
        self.scripts = [s for s in game_map["scripts"] if s["side"] == 1 and not s["subroutine"]]
        self.dead, self.done, self.counters, self.results = set(), set(), {}, []
        self.units = Counter(o["template"] for o in game_map["objects"] if o["props"].get("originalOwner") == "teamPlayerA")
        self.tick()

    @staticmethod
    def compare(left, operator, right):
        return (left < right, left <= right, left == right, left >= right, left > right, left != right)[operator]

    def condition(self, entry):
        name, p = entry
        if name == "CONDITION_TRUE": return True
        if name == "NAMED_DESTROYED": return p[0][3] in self.dead
        if name == "NAMED_NOT_DESTROYED": return p[0][3] not in self.dead
        if name == "COUNTER": return self.compare(self.counters.get(p[0][3], 0), p[1][1], p[2][1])
        if name == "TIMER_EXPIRED": return p[0][3] in self.counters and self.counters[p[0][3]] <= 0
        if name == "PLAYER_HAS_OBJECT_COMPARISON": return self.compare(self.units[p[3][3]], p[1][1], p[2][1])
        raise AssertionError(f"scenario evaluator missing {name}")

    def tick(self):
        for script in self.scripts:
            if script["name"] in self.done: continue
            if not any(all(self.condition(c) for c in group) for group in script["conditions"]): continue
            if script["once"]: self.done.add(script["name"])
            for name, p in script["actions"]:
                if name == "SET_COUNTER": self.counters[p[0][3]] = p[1][1]
                elif name == "SET_MILLISECOND_TIMER": self.counters[p[0][3]] = p[1][2]
                elif name == "INCREMENT_COUNTER": self.counters[p[1][3]] = self.counters.get(p[1][3], 0) + p[0][1]
                elif name in ("VICTORY", "DEFEAT"): self.results.append(name)
                elif name not in ("DISPLAY_TEXT", "MAP_SHROUD_ALL"): raise AssertionError(name)
        assert len(self.results) <= 1, f"conflicting/repeated outcomes: {self.results}"

    def destroy(self, *names):
        self.dead.update(names)
        self.tick()


def mission_scenarios(mission_id, game_map):
    baseline = MissionState(game_map)
    assert not baseline.results, f"{mission_id}: mission completes at boot"
    loss = deepcopy(baseline)
    loss.destroy("PlayerCC")
    assert loss.results == ["DEFEAT"]
    s = deepcopy(baseline)
    if mission_id == "training":
        s.destroy("EnemyCC")
        assert not s.results
        for stage, additions in enumerate(({"WP_Fabricator": 1}, {"WP_Exchange": 1, "WP_PowerArray": 1, "WP_Porter": 1},
                                           {"WP_VehiclePlant": 1, "WP_Tank": 2}, {"WP_Vigil": 1}), 1):
            s.units.update(additions); s.tick()
            assert s.counters["WP_ObjectiveStage"] == stage
    elif mission_id == "op01":
        s.destroy("EnemyCC")
        assert not s.results
        s.units.update({"WP_Exchange": 1, "WP_VehiclePlant": 1}); s.tick()
        assert s.counters["WP_ObjectiveStage"] == 1
        s.destroy("ObjectiveRelay")
    elif mission_id == "op02":
        s.destroy("EnemyCC", "SupplyOfficeA", "SupplyOfficeB")
        assert not s.results and s.counters["WP_ObjectiveProgress"] == 2
        s.destroy("GridSubstation")
    elif mission_id in ("op03", "challenge-meridian"):
        relay_loss = deepcopy(s); relay_loss.destroy("AlliedRelay")
        assert relay_loss.results == ["DEFEAT"]
        s.counters["WP_ObjectiveTimer"] = 0; s.tick()
        if mission_id == "op03":
            assert not s.results and s.counters["WP_ObjectiveStage"] == 1
            s.destroy("EnemyCC")
    elif mission_id == "op04":
        s.destroy("EnemyCC", "AirDefense1")
        assert not s.results and s.counters["WP_ObjectiveProgress"] == 1
        s.destroy("AirDefense2")
    elif mission_id == "challenge-jackal":
        deadline_loss = deepcopy(s); deadline_loss.counters["WP_ObjectiveTimer"] = 0; deadline_loss.tick()
        assert deadline_loss.results == ["DEFEAT"]
        tie = deepcopy(s); tie.counters["WP_ObjectiveTimer"] = 0; tie.destroy("EnemyCC")
        assert tie.results == ["VICTORY"], "expiry-frame destruction must resolve"
        s.destroy("EnemyCC")
    assert s.results == ["VICTORY"], (mission_id, s.results, s.counters)
    # All required targets destroyed concurrently with HQ loss must lose, not
    # enqueue contradictory victory and defeat transitions.
    simultaneous = deepcopy(baseline)
    simultaneous.dead.update(s.dead | {"PlayerCC"})
    simultaneous.units = deepcopy(s.units)
    simultaneous.counters.update(s.counters)
    simultaneous.tick()
    assert simultaneous.results == ["DEFEAT"], (mission_id, simultaneous.results)


def ai_scenarios(map_name, game_map):
    """Check the map's actual paid team recipes and reactive eligibility gates."""
    scripts = {s["name"]: s for s in game_map["scripts"] if s["side"] == 2}
    teams = {t["teamName"]: t for t in game_map["teams"]}
    response = teams["teamCounterSquad"]
    assert response["teamMaxInstances"] == 1, "counter squads must not accumulate"
    assert response["teamUnitMinCount1"] == response["teamUnitMaxCount1"] == 3
    assert teams["teamDefensePatrol"]["teamProductionPriority"] > response["teamProductionPriority"]
    condition_script = scripts[response["teamProductionCondition"]]
    if map_name == "WPTraining":
        assert not any(condition_script["enabled"]), "orientation must not trigger advanced counters"
        assert len(game_map["sides"][2]["builds"]) == 2, "no training forward-tower rush"
        assert not any(name.startswith(("WP_AssaultStart", "WP_AirWaveArm", "WP_RaidStart")) for name in scripts)
    else:
        assert condition_script["enabled"] == (0, 1, 1), "reactive counters belong to normal/hard"
    eligible = lambda state: any(all(state.condition(c) for c in group) for group in condition_script["conditions"])
    state = MissionState(game_map)
    state.units.clear()
    assert not eligible(state)
    groups = condition_script["conditions"]
    assert len(groups) == 3
    for group in groups:
        assert len(group) == 1 and group[0][0] == "PLAYER_HAS_OBJECT_COMPARISON"
        params = group[0][1]
        template, threshold = params[3][3], params[2][1]
        assert threshold == (4 if template in ("WP_Tank", "WPJ_Mongrel") else 2)
        state.units.clear(); state.units[template] = threshold - 1
        assert not eligible(state), "AI counter triggers before the commitment threshold"
        state.units[template] += 1
        assert eligible(state), "AI ignores a committed armor/air force"
    priorities = {p[1][3]: p[2][1] for name, p in scripts["WP_RaidPrioritySetup"]["actions"]
                  if name == "SET_ATTACK_PRIORITY_THING"}
    truck = "WPJ_Scavenger" if "WPJ_Scavenger" in priorities else "WP_Porter"
    hub = "WPJ_Racket" if truck == "WPJ_Scavenger" else "WP_Exchange"
    assert priorities[truck] > priorities[hub] > 1, "supply raiders must value the real supply route"
    cooldowns = [p[1][2] for name, p in scripts["WP_PunishHunt"]["actions"] if name == "SET_MILLISECOND_TIMER"]
    assert cooldowns == [100.0], "retaliation must be paced, not infinitely retrained"


def terrain_routes(map_name, game_map):
    terrain = game_map["terrain"]
    width, height = terrain["playable"]
    border, stride = terrain["border"], (terrain["width"] + 7) // 8
    blocked = set()
    for y in range(height):
        for x in range(width):
            xx, yy = x + border, y + border
            if terrain["cliffs"][yy * stride + (xx >> 3)] & (1 << (xx & 7)):
                blocked.add((x, y))
    ridge_map = map_name.startswith(("WPRidge", "WPRange")) or map_name in ("WPOp01", "WPOp03", "WPChallengeM", "WPChallengeJ")
    assert bool(blocked) == ridge_map, f"{map_name}: missing/stray authored ridge collision"
    # Native pathfinding adds a small pinched margin around cliffs. Expand by
    # two cells before flood-fill so this cannot pass a vehicle-width slit.
    padded = {(x + dx, y + dy) for x, y in blocked for dx in range(-2, 3) for dy in range(-2, 3)}
    named = {o["props"]["objectName"]: (int(o["x"] / 10), int(o["y"] / 10))
             for o in game_map["objects"] if "objectName" in o["props"]}
    start = named["PlayerCC"]
    reachable, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= point[0] < width and 0 <= point[1] < height and point not in padded and point not in reachable:
                reachable.add(point); queue.append(point)
    for name, point in named.items():
        assert point in reachable, f"{map_name}: terrain seals off {name}"
    for obj in game_map["objects"]:
        if obj["props"].get("originalOwner") in ("teamPlayerA", "teamPlayerB", "teamBaseGuards"):
            point = int(obj["x"] / 10), int(obj["y"] / 10)
            assert point in reachable, f"{map_name}: terrain strands {obj['template']}"


def main():
    ini = ROOT / "data/Data/INI"
    objects = blocks(ini / "Default/Object.ini", "Object")
    weapons = blocks(ini / "Weapon.ini", "Weapon")
    combat_commands(blocks(ini / "Default/CommandButton.ini", "CommandButton"),
                    blocks(ini / "CommandSet.ini", "CommandSet"))
    locomotors = blocks(ini / "Locomotor.ini", "Locomotor")
    for name, locomotor in locomotors.items():
        if re.search(r"(?m)^\s*Appearance\s*=\s*FOUR_WHEELS\b", locomotor):
            # Native steering divides forward speed by MinTurnSpeed. The
            # omitted default is BIGNUM, which made all new wheel vehicles
            # drive almost straight and prevented either hauler from docking.
            assert re.search(r"(?m)^\s*MinTurnSpeed\s*=", locomotor), f"{name}: FOUR_WHEELS requires explicit MinTurnSpeed to steer"
            assert 0 < scalar(locomotor, "MinTurnSpeed") <= scalar(locomotor, "Speed"), f"{name}: turn speed must be attainable"
            assert re.search(r"(?m)^\s*CanMoveBackwards\s*=\s*Yes\b", locomotor), f"{name}: wheel vehicles must be able to reverse out of close approaches"
    creation_lists = blocks(ini / "ObjectCreationList.ini", "ObjectCreationList")
    for name, ocl in creation_lists.items():
        for reference in re.findall(r"(?m)^\s*ObjectNames\s*=\s*(\w+)", ocl):
            assert reference in objects, f"{name}: missing created template {reference}"
    strings = set(re.findall(r"(?m)^([A-Za-z][\w:-]+)\s*$", (ROOT / "data/Data/Generals.str").read_text()))
    script_source = (ROOT / "engine/GeneralsMD/Code/GameEngine/Source/GameLogic/ScriptEngine/ScriptEngine.cpp").read_text()
    templates = {}
    for match in re.finditer(r"curTemplate = &m_(action|condition)Templates\[[^\]]+\];(.*?)(?=curTemplate =|\Z)", script_source, re.S):
        name = re.search(r'm_internalName = "(\w+)"', match[2])
        count = re.search(r"m_numParameters = (\d+)", match[2])
        if name and count: templates[match[1], name[1]] = int(count[1])
    metadata = json.loads((ROOT / "data/operations.json").read_text())
    assert metadata["schemaVersion"] == 1
    ids = {m["id"] for m in metadata["missions"]}
    assert len(ids) == 7
    maps = {}
    for path in sorted((ROOT / "data/Maps").glob("*/*.map")):
        game_map = read_map(path)
        validate_links(game_map, objects, strings, templates)
        ai_scenarios(path.stem, game_map)
        terrain_routes(path.stem, game_map)
        maps[path.stem] = game_map
    assert len(maps) == 17
    for mission in metadata["missions"]:
        assert "unlock" not in mission, "Operation access must not depend on a browser record"
        assert mission["nextMission"] is None or mission["nextMission"] in ids
        assert mission["briefing"] and mission["debriefWin"] and mission["debriefLoss"]
        required = [o for o in mission["objectives"] if not o["optional"]]
        for stage in range(len(required)):
            assert f'WP:Objective_{mission["id"]}_{stage}' in strings
        if mission["id"] == "training":
            training_requirements(mission, maps[mission["map"]], objects)
        mission_scenarios(mission["id"], maps[mission["map"]])
    for name, obj in objects.items():
        if "Draw =" in obj:
            assert "Body =" in obj, f"{name}: native drawable startup requires a body module"
        if re.search(r"(?m)^\s*Behavior\s*=\s*OCLSpecialPower\b", obj) and re.search(r"(?m)^\s*KindOf\s*=.*\bSTRUCTURE\b", obj):
            # A newly built power structure must start its recharge when
            # construction completes; the special-power constructor only
            # starts a countdown for objects that are already built.
            assert re.search(r"(?m)^\s*Behavior\s*=\s*SpecialPowerCreate\b", obj), f"{name}: special-power construction must initialize recharge via SpecialPowerCreate"
        if "Draw = W3DTruckDraw" in obj:
            locomotor = re.search(r"Locomotor\s*=\s*SET_NORMAL\s+(\w+)", obj)
            assert locomotor and "Appearance = FOUR_WHEELS" in locomotors[locomotor[1]], f"{name}: wheel draw needs native wheel physics information"
            for bone in ("WHL_F", "WHR_F", "WHL_R", "WHR_R"):
                assert bone in obj, f"{name}: incomplete left/right wheel pair"
        for reference in re.findall(r"(?m)^\s*(?:CreationList|OCL)\s*=\s*(\w+)", obj):
            assert reference in creation_lists, f"{name}: missing creation list {reference}"
        if re.search(r"KindOf\s*=.*\bINFANTRY\b.*\bSELECTABLE\b", obj):
            assert "ConditionState = DYING" in obj and "SlowDeathBehavior" in obj
            assert "Behavior = DestroyDie" not in obj, f"{name}: instant deletion hides its death animation"
            assert scalar(obj, "DestructionDelay") >= 1200
        if "ModuleTag_Remains" in obj:
            assert "ExemptStatus = UNDER_CONSTRUCTION" in obj, f"{name}: canceled foundations must not leave completed wrecks"
        if name.startswith("WPJ_"):
            assert not re.search(r"EnergyProduction\s*=\s*-", obj), f"Jackal power dependency: {name}"
            assert not re.search(r"KindOf\s*=.*\bPOWERED\b", obj), f"Jackal powered structure: {name}"
    for structure in ("WP_Bulwark", "WP_Skyspear", "WP_Rampart", "WP_Longbow", "WP_Directorate"):
        assert re.search(r"KindOf\s*=.*\bPOWERED\b", objects[structure]), f"{structure}: power-grid counterplay must disable defenses/strike recharge"
    assert scalar(objects["WP_Tank"], "BuildCost") > scalar(objects["WPJ_Mongrel"], "BuildCost")
    assert scalar(objects["WP_Tank"], "MaxHealth") > scalar(objects["WPJ_Mongrel"], "MaxHealth")
    tank_hit = scalar(weapons["WP_TankGun"], "PrimaryDamage") * 0.35
    assert scalar(objects["WP_Lancer"], "MaxHealth") > tank_hit
    assert scalar(objects["WPJ_Sting"], "MaxHealth") > tank_hit
    for hub in ("WP_Exchange", "WPJ_Racket"):
        assert "SupplyCenterDockUpdate" in objects[hub] and "SupplyCenterCreate" in objects[hub]
    for truck in ("WP_Porter", "WPJ_Scavenger"):
        assert "SupplyTruckAIUpdate" in objects[truck] and scalar(objects[truck], "MaxBoxes") > 0
    assert "DeathWeapon = WP_PrecisionImpact" in objects["WP_StrikeBeacon"]
    for remains in ("WP_MeridianWreck", "WP_JackalWreck", "WP_LargeRuin", "WP_SmallRuin"):
        assert "NO_COLLIDE" in objects[remains] and "SELECTABLE" not in objects[remains]
        assert scalar(objects[remains], "MaxLifetime") <= 60000, "wrecks must not accumulate indefinitely"
    opening = sum(scalar(objects[name], "BuildCost") * count for name, count in
                  (("WP_Fabricator", 1), ("WP_Exchange", 1), ("WP_PowerArray", 1),
                   ("WP_Porter", 1), ("WP_VehiclePlant", 1), ("WP_Tank", 2), ("WP_Vigil", 1)))
    assert opening <= maps["WPTraining"]["sides"][1]["playerStartMoney"], "training opening must be affordable"
    print(f"PASS: {len(maps)} binary maps; 7 mission success/failure/edge cases; native script signatures; combat orders, cliff/pass routes, paid AI responses, supply, faction and opening-budget contracts.")


if __name__ == "__main__":
    main()
