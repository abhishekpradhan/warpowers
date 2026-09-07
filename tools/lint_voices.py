#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Voice-wiring lint — fails the web stage on shared or dangling unit voices.

Born from the Fabricator shipping with "Vector ready": placeholder voice
cross-wiring is silent in-game until someone notices. Rules:
  1. No two object templates may share a Voice* audio event.
  2. Every referenced Voice* event must exist in SoundEffects.ini.
  3. Every sound listed by those events must exist as a WAV on disk.
Exit code 1 on any violation (genwebstage runs this as a gate).

python3 tools/lint_voices.py [--data DIR]
"""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def lint(data: Path):
    """Return (errors, uses) for the dataset under ``data``."""
    objects = (data / 'Data/INI/Default/Object.ini').read_text()
    sfx_path = data / 'Data/INI/SoundEffects.ini'
    sounds = data / 'Data/Audio/Sounds'
    errors = []
    uses = {}          # event -> [(template, field)]
    for m in re.finditer(r'Object (\S+)\n(.*?)\nEnd\n', objects, re.S):
        tmpl, body = m.group(1), m.group(2)
        for field, event in re.findall(r'(Voice\w+) = (\S+)', body):
            uses.setdefault(event, []).append((tmpl, field))

    for event, users in sorted(uses.items()):
        templates = sorted({t for t, _ in users})
        if len(templates) > 1:
            errors.append(f"voice event {event} shared by {', '.join(templates)}"
                          f" - every unit gets its own voice")

    events = {}        # event -> [sound names]
    for m in re.finditer(r'AudioEvent (\S+)\n(.*?)\nEnd', sfx_path.read_text(), re.S):
        snd = re.search(r'Sounds = (.+)', m.group(2))
        events[m.group(1)] = snd.group(1).split() if snd else []

    for event, users in sorted(uses.items()):
        if event not in events:
            errors.append(f"voice event {event} (used by "
                          f"{users[0][0]}.{users[0][1]}) missing from SoundEffects.ini")
            continue
        for snd in events[event]:
            if not (sounds / f'{snd}.wav').exists():
                errors.append(f"{event}: sound file {snd}.wav missing from {sounds}")
    return errors, uses


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', type=Path, default=ROOT / 'data', help='dataset root (default: the repository data/)')
    args = parser.parse_args(argv)
    errors, uses = lint(args.data)
    if errors:
        for e in errors:
            print('VOICE LINT:', e, file=sys.stderr)
        return 1
    print(f"voice lint OK: {len(uses)} events across "
          f"{len({t for us in uses.values() for t, _ in us})} templates, no sharing")
    return 0


if __name__ == '__main__':
    sys.exit(main())
