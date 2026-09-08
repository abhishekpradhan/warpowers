#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate shipped map bytes, mission outcomes, balance contracts and INI links.

This independently decodes the generated CkMp files. It deliberately does not
import genmap: a writer bug must not validate itself. Script scenarios check
objective logic, not combat/pathfinding; those still require a browser match.

Every rule raises ``Failure``; ``main`` collects them per map, mission and
object template and reports them all (exit 1), like tools/check_content.py.
Native script signatures are read from the engine submodule's ScriptEngine.cpp.

python3 tools/validate_gameplay.py [--data DIR] [--engine DIR]
"""
import argparse
from collections import Counter, deque
from copy import deepcopy
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
# Skirmish layouts ship one map per faction: WP<Name> (Meridian) and WP<Name>J.
SKIRMISH_LAYOUTS = {"flats": "WPTest", "ridge": "WPRidge", "scrap": "WPScrap", "basin": "WPBasin", "range": "WPRange"}
RIDGE_LAYOUTS = ("ridge", "range")   # the only layouts that author cliff collision
AMBIENT_EMITTER = "WP_AmbientWind"   # the one carrier of the Limit 1 looping weather bed
SCRIPT_ENGINE = "GeneralsMD/Code/GameEngine/Source/GameLogic/ScriptEngine/ScriptEngine.cpp"


class Failure(Exception):
    """A violated gameplay contract (never an AssertionError: -O must not silence gates)."""


def check(condition, message):
    if not condition:
        raise Failure(message)


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        check(0 <= count <= len(self.data) - self.pos,
              f"truncated map chunk: {count} bytes requested at offset {self.pos} of {len(self.data)}")
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
                check(kind in (3, 4), f"unknown dictionary kind {kind}")
                value = self.string(kind == 4)
            result[toc[key >> 8]] = value
        return result


def call(reader, toc):
    _, namekey, count = reader.unpack("iii")
    params = []
    for _ in range(count):
        kind, integer, real = reader.unpack("iif")
        params.append((kind, integer, real, reader.string()))
    check(reader.pos == len(reader.data), "parameter/chunk length mismatch")
    return toc[namekey >> 8], params


def read_map(path):
    r = Reader(path.read_bytes())
    check(r.take(4) == b"CkMp", "not a CkMp map file")
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
            check(count == width * height, "height map size disagrees with its dimensions")
            result["terrain"] = dict(width=width, height=height, border=border,
                                     playable=boundaries[0], heights=payload.take(count))
        elif label == "BlendTileData":
            count, = payload.unpack("i")
            payload.take(count * 8)  # four arrays of signed 16-bit indices
            terrain = result["terrain"]
            terrain["cliffs"] = payload.take(terrain["height"] * ((terrain["width"] + 7) // 8))
        elif label == "ObjectsList":
            for object_label, _, obj in payload.chunks(toc):
                check(object_label == "Object", f"unexpected {object_label} chunk in ObjectsList")
                x, y, z, angle, flags = obj.unpack("ffffi")
                template = obj.string()
                props = obj.dictionary(toc)
                result["objects"].append(dict(template=template, x=x, y=y, props=props))
                check(obj.pos == len(obj.data), f"{template}: object chunk has trailing bytes")
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
                check(script_label == "PlayerScriptsList", f"unexpected {script_label} chunk in SidesList")
                for side_index, (list_label, _, script_list) in enumerate(script_payload.chunks(toc)):
                    check(list_label == "ScriptList", f"unexpected {list_label} chunk in PlayerScriptsList")
                    for entry_label, _, entry in script_list.chunks(toc):
                        check(entry_label == "Script", f"unexpected {entry_label} chunk in ScriptList")
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
                                check(kind == "ScriptAction", f"{name}: unexpected {kind} chunk in Script")
                                script["actions"].append(call(body, toc))
                        result["scripts"].append(script)
    return result


def blocks(path, word):
    text = path.read_text()
    return {m[1]: m[0] for m in re.finditer(r"(?ms)^" + word + r" (\w+)\n.*?(?=^" + word + r" |\Z)", text)}


def scalar(block, key):
    value = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*([^;\n]+)", block)
    check(value, f"missing {key}")
    return float(value[1].strip())


def combat_commands(buttons, command_sets):
    contracts = (("Command_WPAttackMove", "ATTACK_MOVE", True),
                 ("Command_WPGuard", "GUARD", True),
                 ("Command_WPStop", "STOP", False))
    available = set(re.findall(r"(?m)^\s*\d+\s*=\s*(\w+)", command_sets["WP_CombatUnitCommandSet"]))
    for name, command, needs_position in contracts:
        check(name in available, f"{name}: missing from the shared combat command set")
        button = buttons[name]
        actual_command = re.search(r"(?m)^\s*Command\s*=\s*(\w+)", button)
        check(actual_command and actual_command[1] == command, f"{name}: wrong native order")
        options_match = re.search(r"(?m)^\s*Options\s*=\s*([^;\n]+)", button)
        options = set(options_match[1].split()) if options_match else set()
        check("OK_FOR_MULTI_SELECT" in options, f"{name}: must work for a selected army")
        # NEED_TARGET_POS keeps the destination click in GUICommandTranslator.
        # Without it, ATTACK_MOVE toggles legacy mode and the normal selection
        # translator consumes the left-click instead in right-click order mode.
        if needs_position:
            check("NEED_TARGET_POS" in options, f"{name}: needs position targeting to consume the destination click")
        else:
            check(not any(option.startswith("NEED_TARGET_") for option in options), f"{name}: Stop must execute immediately without targeting")


def training_requirements(mission, game_map, objects):
    objectives = mission["objectives"]
    check(len(objectives) >= 2 and all(not objective["optional"] for objective in objectives), "training guidance stages must match required objectives")
    check(objectives[-1].get("requirements", []) == [], "training finish must not invent a construction gate")
    gates = {}
    for script in game_map["scripts"]:
        if not script["name"].startswith("WP_TrainingStep"):
            continue
        match = re.fullmatch(r"WP_TrainingStep(\d+)", script["name"])
        check(match, f"invalid training gate name: {script['name']}")
        stage = int(match[1])
        check(stage not in gates, f"duplicate training gate {stage}")
        gates[stage] = script
    check(set(gates) == set(range(len(objectives) - 1)), "training metadata stages differ from shipped native gates")
    for stage, script in gates.items():
        requirements = objectives[stage].get("requirements")
        check(isinstance(requirements, list) and requirements, f"training stage {stage}: missing requirements")
        described = set()
        for requirement in requirements:
            check(isinstance(requirement, dict), f"training stage {stage}: invalid requirement")
            template, count = requirement.get("template"), requirement.get("count")
            check(isinstance(template, str) and template in objects, f"training stage {stage}: unknown requirement template")
            check(type(count) is int and count > 0, f"training stage {stage}: requirement count must be a positive integer")
            check(type(requirement.get("requiresBuilder", False)) is bool, f"training stage {stage}: requiresBuilder must be boolean")
            if requirement.get("requiresBuilder"):
                check(re.search(r"(?m)^\s*KindOf\s*=.*\bSTRUCTURE\b", objects[template]), f"training stage {stage}: builder recovery requires a structure")
            for field in ("label", "hint"):
                check(isinstance(requirement.get(field), str) and requirement[field].strip(), f"training stage {stage}: requirement needs {field}")
            check(template not in {item[0] for item in described}, f"training stage {stage}: duplicate requirement template")
            described.add((template, count))
        check(script["side"] == 1 and script["active"] and script["once"] and not script["subroutine"] and all(script["enabled"]), f"training stage {stage}: gate must run once for the player on every difficulty")
        check(len(script["conditions"]) == 1, f"training stage {stage}: guidance cannot describe alternative native gates")
        actual, counters = set(), []
        for name, params in script["conditions"][0]:
            if name == "COUNTER":
                counters.append((params[0][3], params[1][1], params[2][1]))
            else:
                check(name == "PLAYER_HAS_OBJECT_COMPARISON", f"training stage {stage}: unrepresented native prerequisite {name}")
                check(params[0][3] == "PlayerA" and params[1][1] == 3, f"training stage {stage}: requirements must test player-owned minimum counts")
                pair = (params[3][3], params[2][1])
                check(pair not in actual, f"training stage {stage}: duplicate native prerequisite")
                actual.add(pair)
        check(counters == [("WP_ObjectiveStage", 2, stage)], f"training stage {stage}: native gate listens to the wrong objective stage")
        check(described == actual, f"training stage {stage}: metadata requirements {sorted(described)} differ from native gate {sorted(actual)}")
        advances = [(params[0][3], params[1][1]) for name, params in script["actions"]
                    if name == "SET_COUNTER" and params[0][3] == "WP_ObjectiveStage"]
        check(advances == [("WP_ObjectiveStage", stage + 1)], f"training stage {stage}: gate must advance to the next guidance stage")


def ambient_emitter_placement(game_map):
    """Each map carries exactly one weather-bed emitter, neutral and unnamed, at the playable
    centre: the bed is a looping Limit 1 event, so a second carrier is re-requested and
    rejected by the sound system every frame for the whole match."""
    emitters = [o for o in game_map["objects"] if o["template"] == AMBIENT_EMITTER]
    check(len(emitters) == 1, f"a Limit 1 looping ambient tolerates exactly one {AMBIENT_EMITTER} carrier, found {len(emitters)}")
    check(emitters[0]["props"] == {"originalOwner": "team"}, f"{AMBIENT_EMITTER} must be neutral, unnamed scenery")
    width, height = game_map["terrain"]["playable"]
    check((emitters[0]["x"], emitters[0]["y"]) == (width * 5.0, height * 5.0), f"{AMBIENT_EMITTER} must sit at the playable centre")


def validate_links(game_map, objects, strings, templates):
    named = {o["props"]["objectName"] for o in game_map["objects"] if "objectName" in o["props"]}
    for o in game_map["objects"]:
        check(o["template"] in objects or o["template"].startswith("*Waypoints/"), o["template"])
    for side in game_map["sides"]:
        for template in side["builds"]:
            check(template in objects, f"unknown build-list template {template}")
    for script in game_map["scripts"]:
        calls = [("action", c) for c in script["actions"]]
        calls += [("condition", c) for group in script["conditions"] for c in group]
        for kind, (name, params) in calls:
            check((kind, name) in templates, f"unknown native script {kind} {name}")
            check(len(params) == templates[kind, name], f"{name} {len(params)} {templates[kind, name]}")
            for param_type, _, _, value in params:
                if param_type == 14 and value and not value.startswith("<"):
                    check(value in named, f"missing named target: {value}")
                if param_type == 15:
                    check(value in objects, f"missing object type: {value}")
                if name == "DISPLAY_TEXT":
                    check(value in strings, f"missing objective string: {value}")
    caches = [o for o in game_map["objects"] if o["template"] == "WP_SupplyCache"]
    check(len(caches) == 4, "each map needs home and contested supply sites")
    ambient_emitter_placement(game_map)
    scripts_by_name = {s["name"]: s for s in game_map["scripts"]}
    for team in game_map["teams"]:
        for key in ("teamProductionCondition", "teamOnCreateScript"):
            if key in team:
                check(team[key] in scripts_by_name, f"missing team script: {team[key]}")
        for key, value in team.items():
            if key.startswith("teamUnitType"):
                check(value in objects, f"unknown team unit: {value}")


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
        raise Failure(f"scenario evaluator missing {name}")

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
                elif name not in ("DISPLAY_TEXT", "MAP_SHROUD_ALL"): raise Failure(f"scenario evaluator missing action {name}")
        check(len(self.results) <= 1, f"conflicting/repeated outcomes: {self.results}")

    def destroy(self, *names):
        self.dead.update(names)
        self.tick()


def mission_scenarios(mission_id, game_map):
    baseline = MissionState(game_map)
    check(not baseline.results, f"{mission_id}: mission completes at boot")
    loss = deepcopy(baseline)
    loss.destroy("PlayerCC")
    check(loss.results == ["DEFEAT"], f"{mission_id}: losing the HQ must be a defeat")
    s = deepcopy(baseline)
    if mission_id == "training":
        s.destroy("EnemyCC")
        check(not s.results, f"{mission_id}: destroying the enemy HQ alone must not finish the training")
        for stage, additions in enumerate(({"WP_Fabricator": 1}, {"WP_Exchange": 1, "WP_PowerArray": 1, "WP_Porter": 1},
                                           {"WP_VehiclePlant": 1, "WP_Tank": 2}, {"WP_Vigil": 1}), 1):
            s.units.update(additions); s.tick()
            check(s.counters["WP_ObjectiveStage"] == stage, f"{mission_id}: training stage {stage} did not advance")
    elif mission_id == "op01":
        s.destroy("EnemyCC")
        check(not s.results, f"{mission_id}: destroying the enemy HQ alone must not win")
        s.units.update({"WP_Exchange": 1, "WP_VehiclePlant": 1}); s.tick()
        check(s.counters["WP_ObjectiveStage"] == 1, f"{mission_id}: foothold objective did not advance")
        s.destroy("ObjectiveRelay")
    elif mission_id == "op02":
        s.destroy("EnemyCC", "SupplyOfficeA", "SupplyOfficeB")
        check(not s.results and s.counters["WP_ObjectiveProgress"] == 2, f"{mission_id}: two sabotage targets must count as two")
        s.destroy("GridSubstation")
    elif mission_id in ("op03", "challenge-meridian"):
        relay_loss = deepcopy(s); relay_loss.destroy("AlliedRelay")
        check(relay_loss.results == ["DEFEAT"], f"{mission_id}: losing the allied relay must be a defeat")
        s.counters["WP_ObjectiveTimer"] = 0; s.tick()
        if mission_id == "op03":
            check(not s.results and s.counters["WP_ObjectiveStage"] == 1, f"{mission_id}: holding the relay must advance the objective, not win")
            s.destroy("EnemyCC")
    elif mission_id == "op04":
        s.destroy("EnemyCC", "AirDefense1")
        check(not s.results and s.counters["WP_ObjectiveProgress"] == 1, f"{mission_id}: one air defense down must count as one")
        s.destroy("AirDefense2")
    elif mission_id == "challenge-jackal":
        deadline_loss = deepcopy(s); deadline_loss.counters["WP_ObjectiveTimer"] = 0; deadline_loss.tick()
        check(deadline_loss.results == ["DEFEAT"], f"{mission_id}: missing the deadline must be a defeat")
        tie = deepcopy(s); tie.counters["WP_ObjectiveTimer"] = 0; tie.destroy("EnemyCC")
        check(tie.results == ["VICTORY"], "expiry-frame destruction must resolve")
        s.destroy("EnemyCC")
    check(s.results == ["VICTORY"], f"{mission_id} {s.results} {s.counters}")
    # All required targets destroyed concurrently with HQ loss must lose, not
    # enqueue contradictory victory and defeat transitions.
    simultaneous = deepcopy(baseline)
    simultaneous.dead.update(s.dead | {"PlayerCC"})
    simultaneous.units = deepcopy(s.units)
    simultaneous.counters.update(s.counters)
    simultaneous.tick()
    check(simultaneous.results == ["DEFEAT"], f"{mission_id} {simultaneous.results}")


def ai_scenarios(map_name, game_map):
    """Check the map's actual paid team recipes and reactive eligibility gates."""
    scripts = {s["name"]: s for s in game_map["scripts"] if s["side"] == 2}
    teams = {t["teamName"]: t for t in game_map["teams"]}
    response = teams["teamCounterSquad"]
    check(response["teamMaxInstances"] == 1, "counter squads must not accumulate")
    check(response["teamUnitMinCount1"] == response["teamUnitMaxCount1"] == 3, "counter squads are exactly three rocket infantry")
    check(teams["teamDefensePatrol"]["teamProductionPriority"] > response["teamProductionPriority"], "the defense patrol outranks the counter squad")
    condition_script = scripts[response["teamProductionCondition"]]
    if map_name == "WPTraining":
        check(not any(condition_script["enabled"]), "orientation must not trigger advanced counters")
        check(len(game_map["sides"][2]["builds"]) == 2, "no training forward-tower rush")
        check(not any(name.startswith(("WP_AssaultStart", "WP_AirWaveArm", "WP_RaidStart")) for name in scripts), "training must not arm assault, air or raid tiers")
    else:
        check(condition_script["enabled"] == (0, 1, 1), "reactive counters belong to normal/hard")
    eligible = lambda state: any(all(state.condition(c) for c in group) for group in condition_script["conditions"])
    state = MissionState(game_map)
    state.units.clear()
    check(not eligible(state), "the counter squad must not be eligible against an empty army")
    groups = condition_script["conditions"]
    check(len(groups) == 3, "the counter squad listens for air, strafer and armor commitments")
    for group in groups:
        check(len(group) == 1 and group[0][0] == "PLAYER_HAS_OBJECT_COMPARISON", "each counter trigger is one owned-object comparison")
        params = group[0][1]
        template, threshold = params[3][3], params[2][1]
        check(threshold == (4 if template in ("WP_Tank", "WPJ_Mongrel") else 2), f"{template}: unexpected commitment threshold {threshold}")
        state.units.clear(); state.units[template] = threshold - 1
        check(not eligible(state), "AI counter triggers before the commitment threshold")
        state.units[template] += 1
        check(eligible(state), "AI ignores a committed armor/air force")
    priorities = {p[1][3]: p[2][1] for name, p in scripts["WP_RaidPrioritySetup"]["actions"]
                  if name == "SET_ATTACK_PRIORITY_THING"}
    truck = "WPJ_Scavenger" if "WPJ_Scavenger" in priorities else "WP_Porter"
    hub = "WPJ_Racket" if truck == "WPJ_Scavenger" else "WP_Exchange"
    check(priorities[truck] > priorities[hub] > 1, "supply raiders must value the real supply route")
    cooldowns = [p[1][2] for name, p in scripts["WP_PunishHunt"]["actions"] if name == "SET_MILLISECOND_TIMER"]
    check(cooldowns == [100.0], "retaliation must be paced, not infinitely retrained")


def terrain_routes(map_name, game_map, ridge_map):
    terrain = game_map["terrain"]
    width, height = terrain["playable"]
    border, stride = terrain["border"], (terrain["width"] + 7) // 8
    blocked = set()
    for y in range(height):
        for x in range(width):
            xx, yy = x + border, y + border
            if terrain["cliffs"][yy * stride + (xx >> 3)] & (1 << (xx & 7)):
                blocked.add((x, y))
    check(bool(blocked) == ridge_map, f"{map_name}: missing/stray authored ridge collision")
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
        check(point in reachable, f"{map_name}: terrain seals off {name}")
    for obj in game_map["objects"]:
        if obj["props"].get("originalOwner") in ("teamPlayerA", "teamPlayerB", "teamBaseGuards"):
            point = int(obj["x"] / 10), int(obj["y"] / 10)
            check(point in reachable, f"{map_name}: terrain strands {obj['template']}")



def native_script_templates(engine):
    """(kind, internal name) -> parameter count, read from the engine's ScriptEngine.cpp."""
    source = engine / SCRIPT_ENGINE
    if not source.is_file():
        raise SystemExit(f"Engine sources not found: {source}\n"
                         "The engine is a git submodule; run `git submodule update --init --recursive` "
                         "or point --engine at a GeneralsX checkout.")
    templates = {}
    for match in re.finditer(r"curTemplate = &m_(action|condition)Templates\[[^\]]+\];(.*?)(?=curTemplate =|\Z)",
                             source.read_text(), re.S):
        name = re.search(r'm_internalName = "(\w+)"', match[2])
        count = re.search(r"m_numParameters = (\d+)", match[2])
        if name and count:
            templates[match[1], name[1]] = int(count[1])
    check(templates, f"{source}: no script templates found")
    return templates


def locomotor_contract(name, locomotor):
    if re.search(r"(?m)^\s*Appearance\s*=\s*FOUR_WHEELS\b", locomotor):
        # Native steering divides forward speed by MinTurnSpeed. The
        # omitted default is BIGNUM, which made all new wheel vehicles
        # drive almost straight and prevented either hauler from docking.
        check(re.search(r"(?m)^\s*MinTurnSpeed\s*=", locomotor), f"{name}: FOUR_WHEELS requires explicit MinTurnSpeed to steer")
        check(0 < scalar(locomotor, "MinTurnSpeed") <= scalar(locomotor, "Speed"), f"{name}: turn speed must be attainable")
        check(re.search(r"(?m)^\s*CanMoveBackwards\s*=\s*Yes\b", locomotor), f"{name}: wheel vehicles must be able to reverse out of close approaches")


def mission_contract(mission, ids, strings, objects, maps):
    check("unlock" not in mission, "Operation access must not depend on a browser record")
    check(mission["nextMission"] is None or mission["nextMission"] in ids, f"{mission['id']}: unknown nextMission {mission['nextMission']}")
    check(mission["briefing"] and mission["debriefWin"] and mission["debriefLoss"], f"{mission['id']}: briefing and both debriefs are required")
    required = [o for o in mission["objectives"] if not o["optional"]]
    for stage in range(len(required)):
        check(f'WP:Objective_{mission["id"]}_{stage}' in strings, f"{mission['id']}: missing objective string for stage {stage}")
    check(mission["map"] in maps, f"{mission['id']}: map {mission['map']} is not shipped")
    if mission["id"] == "training":
        training_requirements(mission, maps[mission["map"]], objects)
    mission_scenarios(mission["id"], maps[mission["map"]])


def object_contract(name, obj, locomotors, creation_lists):
    if "Draw =" in obj:
        check("Body =" in obj, f"{name}: native drawable startup requires a body module")
    if re.search(r"(?m)^\s*Behavior\s*=\s*OCLSpecialPower\b", obj) and re.search(r"(?m)^\s*KindOf\s*=.*\bSTRUCTURE\b", obj):
        # A newly built power structure must start its recharge when
        # construction completes; the special-power constructor only
        # starts a countdown for objects that are already built.
        check(re.search(r"(?m)^\s*Behavior\s*=\s*SpecialPowerCreate\b", obj), f"{name}: special-power construction must initialize recharge via SpecialPowerCreate")
    if "Draw = W3DTruckDraw" in obj:
        locomotor = re.search(r"Locomotor\s*=\s*SET_NORMAL\s+(\w+)", obj)
        check(locomotor and "Appearance = FOUR_WHEELS" in locomotors.get(locomotor[1], ""), f"{name}: wheel draw needs native wheel physics information")
        for bone in ("WHL_F", "WHR_F", "WHL_R", "WHR_R"):
            check(bone in obj, f"{name}: incomplete left/right wheel pair")
    for reference in re.findall(r"(?m)^\s*(?:CreationList|OCL)\s*=\s*(\w+)", obj):
        check(reference in creation_lists, f"{name}: missing creation list {reference}")
    if re.search(r"KindOf\s*=.*\bINFANTRY\b.*\bSELECTABLE\b", obj):
        check("ConditionState = DYING" in obj and "SlowDeathBehavior" in obj, f"{name}: selectable infantry need a dying state and slow death")
        check("Behavior = DestroyDie" not in obj, f"{name}: instant deletion hides its death animation")
        check(scalar(obj, "DestructionDelay") >= 1200, f"{name}: infantry need 1.2s to play their death")
    if "ModuleTag_Remains" in obj:
        check("ExemptStatus = UNDER_CONSTRUCTION" in obj, f"{name}: canceled foundations must not leave completed wrecks")
    if name.startswith("WPJ_"):
        check(not re.search(r"EnergyProduction\s*=\s*-", obj), f"Jackal power dependency: {name}")
        check(not re.search(r"KindOf\s*=.*\bPOWERED\b", obj), f"Jackal powered structure: {name}")


def ambient_contract(objects, audio):
    """A looping Limit 1 ambient tolerates one carrier template, and that carrier is inert
    scenery: Drawable::updateDrawable re-requests a non-playing looping ambient every frame,
    so every extra carrier is rejected ~30x/s for the whole match (the wind bed once rode on
    both command centers)."""
    carriers = {}
    for name, obj in objects.items():
        for event in re.findall(r"(?m)^\s*SoundAmbient\s*=\s*(\w+)", obj):
            carriers.setdefault(event, set()).add(name)
    for event, templates in sorted(carriers.items()):
        check(event in audio, f"{event}: missing ambient audio event")
        if re.search(r"(?mi)^\s*Control\s*=.*\bloop\b", audio[event]) and re.search(r"(?m)^\s*Limit\s*=\s*1\s*(?:;|$)", audio[event]):
            check(templates == {AMBIENT_EMITTER}, f"{event}: a looping Limit 1 ambient must ride only on {AMBIENT_EMITTER}, not {sorted(templates)}")
    check(AMBIENT_EMITTER in objects and any(AMBIENT_EMITTER in templates for templates in carriers.values()),
          f"{AMBIENT_EMITTER}: the weather-bed emitter must exist and carry an ambient")
    emitter = objects[AMBIENT_EMITTER]
    kinds = re.search(r"(?m)^\s*KindOf\s*=\s*([^;\n]+)", emitter)
    kinds = set(kinds[1].split()) if kinds else set()
    check({"IMMOBILE", "INERT", "UNATTACKABLE", "NO_COLLIDE"} <= kinds and not kinds & {"SELECTABLE", "STRUCTURE", "SCORE", "MP_COUNT_FOR_VICTORY"},
          f"{AMBIENT_EMITTER}: the emitter must be inert, unattackable, passable, unselectable scenery")
    check(re.search(r"(?m)^\s*Model\s*=\s*NONE\s*$", emitter) and "Body =" in emitter,
          f"{AMBIENT_EMITTER}: the emitter is invisible but ambient startup needs a body")


def balance_contracts(objects, weapons, maps):
    for structure in ("WP_Bulwark", "WP_Skyspear", "WP_Rampart", "WP_Longbow", "WP_Directorate"):
        check(re.search(r"KindOf\s*=.*\bPOWERED\b", objects[structure]), f"{structure}: power-grid counterplay must disable defenses/strike recharge")
    check(scalar(objects["WP_Tank"], "BuildCost") > scalar(objects["WPJ_Mongrel"], "BuildCost"), "the Vector costs more than the Mongrel")
    check(scalar(objects["WP_Tank"], "MaxHealth") > scalar(objects["WPJ_Mongrel"], "MaxHealth"), "the Vector is tougher than the Mongrel")
    tank_hit = scalar(weapons["WP_TankGun"], "PrimaryDamage") * 0.35
    check(scalar(objects["WP_Lancer"], "MaxHealth") > tank_hit, "a Lancer survives one tank shell")
    check(scalar(objects["WPJ_Sting"], "MaxHealth") > tank_hit, "a Sting survives one tank shell")
    for hub in ("WP_Exchange", "WPJ_Racket"):
        check("SupplyCenterDockUpdate" in objects[hub] and "SupplyCenterCreate" in objects[hub], f"{hub}: supply hubs need dock and create modules")
    for truck in ("WP_Porter", "WPJ_Scavenger"):
        check("SupplyTruckAIUpdate" in objects[truck] and scalar(objects[truck], "MaxBoxes") > 0, f"{truck}: haulers need truck AI and cargo capacity")
    check("DeathWeapon = WP_PrecisionImpact" in objects["WP_StrikeBeacon"], "the strike beacon must detonate the precision impact")
    for remains in ("WP_MeridianWreck", "WP_JackalWreck", "WP_LargeRuin", "WP_SmallRuin"):
        check("NO_COLLIDE" in objects[remains] and "SELECTABLE" not in objects[remains], f"{remains}: remains must be passable and unselectable")
        check(scalar(objects[remains], "MaxLifetime") <= 60000, "wrecks must not accumulate indefinitely")
    opening = sum(scalar(objects[name], "BuildCost") * count for name, count in
                  (("WP_Fabricator", 1), ("WP_Exchange", 1), ("WP_PowerArray", 1),
                   ("WP_Porter", 1), ("WP_VehiclePlant", 1), ("WP_Tank", 2), ("WP_Vigil", 1)))
    check("WPTraining" in maps, "the training map is not shipped")
    check(opening <= maps["WPTraining"]["sides"][1]["playerStartMoney"], "training opening must be affordable")


def validate(data, engine):
    """Run every gate; returns (failures, map count, mission count)."""
    failures = []

    def attempt(label, fn, *args):
        try:
            fn(*args)
        except Failure as error:
            failures.append(f"{label}: {error}")

    ini = data / "Data/INI"
    objects = blocks(ini / "Default/Object.ini", "Object")
    weapons = blocks(ini / "Weapon.ini", "Weapon")
    locomotors = blocks(ini / "Locomotor.ini", "Locomotor")
    creation_lists = blocks(ini / "ObjectCreationList.ini", "ObjectCreationList")
    audio = blocks(ini / "SoundEffects.ini", "AudioEvent")
    attempt("CommandButton.ini", combat_commands, blocks(ini / "Default/CommandButton.ini", "CommandButton"),
            blocks(ini / "CommandSet.ini", "CommandSet"))
    for name, locomotor in locomotors.items():
        attempt("Locomotor.ini", locomotor_contract, name, locomotor)
    for name, ocl in creation_lists.items():
        for reference in re.findall(r"(?m)^\s*ObjectNames\s*=\s*(\w+)", ocl):
            attempt("ObjectCreationList.ini", check, reference in objects, f"{name}: missing created template {reference}")
    strings = set(re.findall(r"(?m)^([A-Za-z][\w:-]+)\s*$", (data / "Data/Generals.str").read_text()))
    templates = native_script_templates(engine)
    metadata = json.loads((data / "operations.json").read_text())
    attempt("operations.json", check, metadata.get("schemaVersion") == 1, "unsupported schemaVersion")
    missions = metadata["missions"]
    ids = {m["id"] for m in missions}
    attempt("operations.json", check, len(ids) == len(missions), "duplicate mission ids")
    # The shipped map set is derived, never hand-counted: every skirmish layout
    # for both factions plus one map per authored operation.
    expected = {name for layout in SKIRMISH_LAYOUTS.values() for name in (layout, layout + "J")} | {m["map"] for m in missions}
    ridge_maps = {SKIRMISH_LAYOUTS[layout] + suffix for layout in RIDGE_LAYOUTS for suffix in ("", "J")}
    ridge_maps |= {m["map"] for m in missions if m["layout"] in RIDGE_LAYOUTS}
    maps = {}
    for path in sorted((data / "Maps").glob("*/*.map")):
        try:
            game_map = read_map(path)
        except Failure as error:
            failures.append(f"{path.stem}: {error}")
            continue
        maps[path.stem] = game_map
        attempt(path.stem, validate_links, game_map, objects, strings, templates)
        attempt(path.stem, ai_scenarios, path.stem, game_map)
        attempt(path.stem, terrain_routes, path.stem, game_map, path.stem in ridge_maps)
    attempt("Maps", check, set(maps) == expected,
            f"shipped maps differ from the skirmish layouts x factions plus operations.json: {sorted(set(maps) ^ expected)}")
    for mission in missions:
        attempt(mission["id"], mission_contract, mission, ids, strings, objects, maps)
    for name, obj in objects.items():
        attempt("Object.ini", object_contract, name, obj, locomotors, creation_lists)
    attempt("ambient", ambient_contract, objects, audio)
    attempt("balance", balance_contracts, objects, weapons, maps)
    return failures, len(maps), len(missions)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=ROOT / "data", help="dataset root (default: the repository data/)")
    parser.add_argument("--engine", type=Path, default=ROOT / "engine",
                        help="GeneralsX engine checkout for native script signatures (default: the engine submodule)")
    args = parser.parse_args(argv)
    failures, map_count, mission_count = validate(args.data.resolve(), args.engine.resolve())
    for failure in sorted(set(failures)):
        print(f"ERROR: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"PASS: {map_count} binary maps; {mission_count} mission success/failure/edge cases; native script signatures; "
          "combat orders, cliff/pass routes, paid AI responses, supply, weather-bed carrier, faction and opening-budget contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
