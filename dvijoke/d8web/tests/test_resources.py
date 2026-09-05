#!/usr/bin/env python3
"""Build the actual d8web frontend with sanitizers and a CPU-only backend.

Requires Python 3 and a C++20 compiler with Address/UndefinedBehaviorSanitizer
(CXX, or c++).
No game build, browser, GL context or downloaded dependencies are required.
"""
from pathlib import Path
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CASES = ('copy-valid', 'copy-full', 'copy-default-point', 'copy-multiple',
         'copy-self', 'copy-source-outside', 'copy-source-outside-y', 'copy-source-crosses-edge',
         'copy-destination-outside', 'copy-destination-outside-y',
         'copy-destination-crosses-edge', 'copy-reversed', 'copy-reversed-height',
         'copy-negative', 'copy-negative-point', 'copy-empty', 'copy-empty-height',
         'copy-extreme', 'copy-invalid-second', 'lifetime-one-level',
         'lifetime-two-levels', 'lifetime-extra-ref', 'lifetime-repeated-query',
         'lifetime-surfaces-first', 'lifetime-reacquire', 'lifetime-texture-extra-ref',
         'lifetime-no-surface')


def main():
    compiler = shlex.split(os.environ.get('CXX', 'c++'))
    with tempfile.TemporaryDirectory(prefix='d8web-resource-contract-') as directory:
        binary = Path(directory) / 'resources'
        subprocess.run([*compiler, '-std=c++20', '-g', '-O1', '-fsanitize=address,undefined',
                        '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-I', str(ROOT / 'include'),
                        '-I', str(ROOT / 'src'), str(ROOT / 'src/frontend/device.cpp'),
                        str(ROOT / 'tests/resource_contract.cpp'), '-o', str(binary)], check=True)
        failed = 0
        for case in CASES:
            result = subprocess.run([str(binary), case], capture_output=True, text=True)
            print(result.stdout, end='')
            if result.returncode:
                failed += 1
                print(f'FAIL {case} (exit {result.returncode})', file=sys.stderr)
                print(result.stderr, end='', file=sys.stderr)
        print(f'{len(CASES) - failed}/{len(CASES)} resource contracts passed')
        return int(failed != 0)


if __name__ == '__main__':
    sys.exit(main())
