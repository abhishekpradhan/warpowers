#!/usr/bin/env python3
"""War Powers audio pack — synthesized SFX + processed-radio unit VO.

Everything is original: weapon/explosion sounds are pure DSP; voice barks are
eSpeak NG synthesis (output unencumbered) pushed through a radio chain
(bandpass, soft clip, noise floor, squelch clicks) per the D014 VO direction —
"processed radio barks: any voice usable, personality lives in the writing."

Outputs 22050 Hz 16-bit mono WAVs into data/Data/Audio/Sounds/ (repo) and the
runtime dir. Run: python3 tools/gensfx.py
"""
import math
import os
import random
import struct
import subprocess
import sys
import tempfile
import wave

SR = 22050
REPO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'data', 'Data', 'Audio', 'Sounds')
RUNTIME = os.path.expanduser('~/GeneralsX/GeneralsZH/Data/Audio/Sounds')
ESPEAK = '/opt/homebrew/bin/espeak-ng'

# ---------------- DSP helpers ----------------

def lowpass(x, cutoff, passes=1):
    a = 1.0 - math.exp(-2.0 * math.pi * cutoff / SR)
    for _ in range(passes):
        y = 0.0
        out = []
        for s in x:
            y += a * (s - y)
            out.append(y)
        x = out
    return x

def highpass(x, cutoff, passes=1):
    for _ in range(passes):
        lp = lowpass(x, cutoff)
        x = [s - l for s, l in zip(x, lp)]
    return x

def bandpass(x, lo, hi, passes=2):
    return highpass(lowpass(x, hi, passes), lo, passes)

def softclip(x, drive):
    return [math.tanh(s * drive) for s in x]

def normalize(x, peak=0.9):
    m = max(1e-9, max(abs(s) for s in x))
    g = peak / m
    return [s * g for s in x]

def write_wav(path, x):
    x = normalize(x)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(
            struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32000)) for s in x))
    print('wrote', path)

def out(name, x):
    for d in (REPO, RUNTIME):
        os.makedirs(d, exist_ok=True)
        write_wav(os.path.join(d, name + '.wav'), x)

# ---------------- SFX ----------------

def cannon(seed):
    rng = random.Random(seed)
    n = int(SR * 0.55)
    crack = [rng.uniform(-1, 1) * math.exp(-i / (SR * 0.014)) for i in range(n)]
    crack = bandpass(crack, 900, 6500, 1)
    thump, ph = [], 0.0
    for i in range(n):
        f = 82.0 - 30.0 * (i / n)
        ph += 2 * math.pi * f / SR
        thump.append(math.sin(ph) * math.exp(-i / (SR * 0.17)))
    body = lowpass([rng.uniform(-1, 1) for _ in range(n)], 750)
    body = [b * math.exp(-i / (SR * 0.2)) for i, b in enumerate(body)]
    mix = [1.1 * c + 1.5 * t + 0.9 * b for c, t, b in zip(crack, thump, body)]
    return softclip(mix, 1.7)

def boom(seed):
    rng = random.Random(seed)
    n = int(SR * 1.5)
    sub, ph = [], 0.0
    for i in range(n):
        f = 52.0 - 24.0 * (i / n)
        ph += 2 * math.pi * f / SR
        sub.append(math.sin(ph) * math.exp(-i / (SR * 0.5)))
    roar = lowpass([rng.uniform(-1, 1) for _ in range(n)], 480)
    roar = [r * math.exp(-i / (SR * 0.42)) for i, r in enumerate(roar)]
    mid = bandpass([rng.uniform(-1, 1) for _ in range(n)], 250, 1600, 1)
    mid = [m * math.exp(-i / (SR * 0.22)) for i, m in enumerate(mid)]
    crackle = [0.0] * n
    for _ in range(26):
        p = int(rng.uniform(0.04, 0.9) * n)
        amp = rng.uniform(0.2, 0.7) * math.exp(-p / (SR * 0.5))
        for j in range(p, min(n, p + 260)):
            crackle[j] += rng.uniform(-1, 1) * amp * math.exp(-(j - p) / (SR * 0.004))
    mix = [1.6 * s + 1.0 * r + 0.7 * m + 0.8 * c
           for s, r, m, c in zip(sub, roar, mid, crackle)]
    return softclip(mix, 2.1)

def impact(seed):
    rng = random.Random(seed)
    n = int(SR * 0.32)
    crack = [rng.uniform(-1, 1) * math.exp(-i / (SR * 0.008)) for i in range(n)]
    crack = bandpass(crack, 1200, 7000, 1)
    puff = lowpass([rng.uniform(-1, 1) for _ in range(n)], 650)
    puff = [p * math.exp(-i / (SR * 0.09)) for i, p in enumerate(puff)]
    thud, ph = [], 0.0
    for i in range(n):
        ph += 2 * math.pi * 110.0 / SR
        thud.append(math.sin(ph) * math.exp(-i / (SR * 0.05)))
    mix = [1.2 * c + 0.9 * p + 0.8 * t for c, p, t in zip(crack, puff, thud)]
    return softclip(mix, 1.5)

# ---------------- VO ----------------

def tts(text, voice, pitch, speed):
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp = f.name
    subprocess.run([ESPEAK, '-v', voice, '-p', str(pitch), '-s', str(speed),
                    '-a', '160', '-w', tmp, text], check=True)
    with wave.open(tmp, 'rb') as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    os.unlink(tmp)
    x = [struct.unpack_from('<h', raw, i * 2)[0] / 32768.0
         for i in range(len(raw) // 2)]
    if sr != SR:   # linear resample
        ratio = sr / SR
        x = [x[min(len(x) - 1, int(i * ratio))] for i in range(int(len(x) / ratio))]
    return x

def squelch(rng, closing=False):
    n = int(SR * 0.045)
    blip = []
    ph = 0.0
    f = 1250.0 if not closing else 950.0
    for i in range(n):
        ph += 2 * math.pi * f / SR
        env = math.exp(-i / (SR * 0.012))
        blip.append(0.5 * math.sin(ph) * env + 0.35 * rng.uniform(-1, 1) * env)
    return bandpass(blip, 500, 4000, 1)

def radio(text, voice, pitch, speed, seed, grit=1.0):
    rng = random.Random(seed)
    v = tts(text, voice, pitch, speed)
    v = bandpass(v, 380, 3100, 2)
    v = softclip(v, 2.2 * grit)
    v = normalize(v, 0.85)
    floor = 0.016 * grit
    v = [s + floor * rng.uniform(-1, 1) for s in v]
    pad = [0.0] * int(SR * 0.02)
    return squelch(rng) + pad + v + pad + squelch(rng, closing=True)

# ---------------- the pack ----------------

out('wp_cannon_01', cannon(11))
out('wp_cannon_02', cannon(23))
out('wp_boom_01', boom(31))
out('wp_boom_02', boom(47))
def rifle(seed):
    rng = random.Random(seed)
    n = int(SR * 0.22)
    crack = [rng.uniform(-1, 1) * math.exp(-i / (SR * 0.006)) for i in range(n)]
    crack = bandpass(crack, 1500, 7500, 1)
    snap, ph = [], 0.0
    for i in range(n):
        ph += 2 * math.pi * 240.0 / SR
        snap.append(math.sin(ph) * math.exp(-i / (SR * 0.02)))
    mix = [1.3 * c + 0.6 * t for c, t in zip(crack, snap)]
    return softclip(mix, 1.6)

def bodyfall(seed):
    rng = random.Random(seed)
    n = int(SR * 0.4)
    thud, ph = [], 0.0
    for i in range(n):
        ph += 2 * math.pi * 90.0 / SR
        thud.append(math.sin(ph) * math.exp(-i / (SR * 0.07)))
    dust = lowpass([rng.uniform(-1, 1) for _ in range(n)], 500)
    dust = [d * math.exp(-i / (SR * 0.12)) for i, d in enumerate(dust)]
    return softclip([1.2 * t + 0.7 * d for t, d in zip(thud, dust)], 1.4)

def rocket(seed):
    """launch whoosh: broadband ignition crack into a falling roar tail"""
    rng = random.Random(seed)
    n = int(SR * 0.85)
    x = [0.0] * n
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 5.5) * (1.0 if t > 0.015 else t / 0.015)
        x[i] = (rng.uniform(-1, 1)) * env
    x = bandpass(x, 300, 5200)
    # descending motor tone under the noise
    for i in range(n):
        t = i / SR
        f = 900 * math.exp(-t * 2.2) + 90
        x[i] += 0.4 * math.sin(2 * math.pi * f * t) * math.exp(-t * 4.0)
    return softclip(x, 1.6)

def uiclick(seed, freq=1900.0, dur=0.05):
    rng = random.Random(seed)
    n = int(SR * dur)
    x = [0.0] * n
    for i in range(n):
        t = i / SR
        env = math.exp(-t * 90.0)
        x[i] = (0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * rng.uniform(-1, 1)) * env
    return x

out('wp_ui_click', uiclick(11))
out('wp_ui_hover', uiclick(23, freq=1400.0, dur=0.035))

out('wp_impact_03', impact(151))
out('wp_impact_04', impact(163))

out('wp_rocket_01', rocket(311))
out('wp_rocket_02', rocket(347))

out('wp_rifle_01', rifle(71))
out('wp_rifle_02', rifle(83))
out('wp_bodyfall_01', bodyfall(91))
out('wp_impact_01', impact(53))
out('wp_impact_02', impact(61))

# One voice per unit — every unit gets its own synth voice, pitch, cadence and
# grit so nothing on the battlefield shares a throat. (Lesson learned: the
# Fabricator shipped saying "Vector ready" — tools/lint_voices.py now fails the
# web stage if two templates ever share a voice event again.)
UNIT_STYLES = {
    # Meridian: clean, professional radio discipline
    'wp_vec': dict(voice='en-us+m3', pitch=44, speed=156, grit=0.9),    # Vector MBT: steady
    'wp_out': dict(voice='en-us+m4', pitch=57, speed=186, grit=0.8),    # Outrider scout: young, eager
    'wp_zen': dict(voice='en-us+m2', pitch=30, speed=134, grit=1.0),    # Zenith artillery: slow gravel
    'wp_fab': dict(voice='en-us+m6', pitch=50, speed=166, grit=0.9),    # Fabricator: matter-of-fact site boss
    # Jackal: scrap-yard rowdies
    'wp_mon': dict(voice='en-us+m7', pitch=28, speed=180, grit=1.35),   # Mongrel tank: surly
    'wp_vul': dict(voice='en-us+m5', pitch=62, speed=202, grit=1.5),    # Vulture raider: manic
    'wp_rig': dict(voice='en-us+m1', pitch=24, speed=148, grit=1.3),    # Rigger: gruff foreman
    'wp_war': dict(voice='en-gb+m3', pitch=48, speed=168, grit=0.95),   # Warden rifleman: crisp drill
    'wp_scr': dict(voice='en-us+m7', pitch=40, speed=192, grit=1.45),   # Scrapper: jumpy scrapyard kid
    'wp_lan': dict(voice='en-gb+m1', pitch=38, speed=150, grit=1.0),    # Lancer: calm AT professional
    'wp_stg': dict(voice='en-us+m2', pitch=52, speed=176, grit=1.4),    # Sting: cackling rocketeer
    'wp_kes': dict(voice='en-gb+m4', pitch=54, speed=172, grit=0.75),   # Kestrel pilot: cool flier
    'wp_buz': dict(voice='en-us+m6', pitch=34, speed=170, grit=1.5),    # Buzzard pilot: airborne junker
}

def barks(prefix, lines, base_seed):
    style = UNIT_STYLES[prefix]
    for key, texts in lines.items():
        for i, text in enumerate(texts):
            out(f'{prefix}_{key}_{i + 1:02d}',
                radio(text, style['voice'], style['pitch'], style['speed'],
                      base_seed + i * 7 + hash(key) % 97, style['grit']))

barks('wp_vec', {
    'sel': ['Vector online.', 'Standing by.', 'Crew reports green.'],
    'mov': ['Moving out.', 'Course set.', 'Treads turning.'],
    'atk': ['Engaging.', 'Target locked.', 'Main gun hot.'],
    'rdy': ['Vector ready.'],
}, 100)

barks('wp_out', {
    'sel': ['Outrider, eyes open.', 'Scout on the line.'],
    'mov': ['On it.', 'Fast run.'],
    'atk': ['Tagging them!', 'Peppering!'],
    'rdy': ['Outrider ready.'],
}, 300)

barks('wp_zen', {
    'sel': ['Zenith standing by.', 'Big gun listening.'],
    'mov': ['Repositioning.', 'Hauling the piece.'],
    'atk': ['Firing solution set.', 'Rain incoming.'],
    'rdy': ['Zenith deployed.'],
}, 400)

barks('wp_fab', {
    'sel': ['Fabricator.', 'Site crew here.'],
    'mov': ['Rolling out.', 'On the clock.'],
    'rdy': ['Fabricator ready.'],
}, 500)

barks('wp_mon', {
    'sel': ['Mongrel here.', 'Talk to me.', 'Still running, barely.'],
    'mov': ['Rolling.', 'Yeah yeah, going.', 'Kicking gravel.'],
    'atk': ['Light them up!', 'Chew them down!', 'Bite time!'],
    'rdy': ['Mongrel loose.'],
}, 200)

barks('wp_vul', {
    'sel': ['Vulture!', 'Yeah, what?'],
    'mov': ['Gone!', 'Zip zip.'],
    'atk': ['Strip them down!', 'Get the shiny bits!'],
    'rdy': ['Vulture out of the cage.'],
}, 600)

barks('wp_war', {
    'sel': ['Warden reporting.', 'Rifle ready.', 'Standing to.'],
    'mov': ['Boots moving.', 'On the double.', 'Covering ground.'],
    'atk': ['Open fire!', 'Suppressing!', 'Targets marked!'],
    'rdy': ['Warden ready.'],
}, 750)

barks('wp_scr', {
    'sel': ['Scrapper!', 'Yeah boss?', 'What now?'],
    'mov': ['Leggin it.', 'Going going.', 'Dust up!'],
    'atk': ['Perforate them!', 'Eat pellets!', 'Scrap fight!'],
    'rdy': ['Scrapper on the yard.'],
}, 780)

barks('wp_lan', {
    'sel': ['Lancer set.', 'Launcher shouldered.'],
    'mov': ['Repositioning.', 'Finding an angle.'],
    'atk': ['Rocket out!', 'Backblast clear!'],
    'rdy': ['Lancer ready to hunt.'],
}, 810)

barks('wp_stg', {
    'sel': ['Sting here!', 'Rack is hot!'],
    'mov': ['Dragging the rack.', 'Yeah, moving!'],
    'atk': ['Send it screaming!', 'Big one away!'],
    'rdy': ['Sting is loaded!'],
}, 840)

barks('wp_kes', {
    'sel': ['Kestrel airborne.', 'Skies are mine.'],
    'mov': ['Vectoring.', 'On the wind.'],
    'atk': ['Talons out!', 'Diving in!'],
    'rdy': ['Kestrel off the pad.'],
}, 870)

barks('wp_buz', {
    'sel': ['Buzzard up!', 'Still flying, somehow!'],
    'mov': ['Rattling over.', 'Hold together, girl!'],
    'atk': ['Dump the rack!', 'Rain scrap on them!'],
    'rdy': ['Buzzard off the roost!'],
}, 890)

barks('wp_rig', {
    'sel': ['Rigger.', 'Wrench is ready.'],
    'mov': ['Hauling.', 'Moving the rig.'],
    'rdy': ['Rigger is up.'],
}, 700)

# EVA — the command-net announcer: one composed voice, cleaner processing than
# the unit radios (she is speaking from HQ, not a moving vehicle)
EVA = dict(voice='en-us+f3', pitch=46, speed=148, grit=0.7)

def eva(name, text, seed):
    out('wp_eva_' + name,
        radio(text, EVA['voice'], EVA['pitch'], EVA['speed'], seed, EVA['grit']))

eva('lowpower_01', 'Warning: power levels critical.', 810)
eva('funds_01', 'Insufficient funds.', 820)
eva('attack_01', 'Our base is under attack.', 830)
eva('attack_02', 'Base is under attack.', 831)
eva('bldglost_01', 'Structure lost.', 840)
eva('unitlost_01', 'Unit lost.', 850)
eva('upgrade_01', 'Upgrade complete.', 860)

print('audio pack complete')
