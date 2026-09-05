#!/usr/bin/env python3
"""Compatibility entry point for the original rendered portrait pipeline.

python3 tools/genicons2.py /tmp/warpowers-portraits --data data
The retired vector placeholders cannot overwrite approved model portraits.
Both sheets are packed together to keep their camera, framing and palette aligned.
"""
from genportraitsheet import main

if __name__ == '__main__':
    main()
