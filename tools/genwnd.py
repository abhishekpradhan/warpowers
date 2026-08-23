#!/usr/bin/env python3
"""War Powers ControlBar.wnd generator.

Replaces the hand-authored ControlBar.wnd with a declarative table. Adds the
windows the in-game UI dereferences at runtime (ButtonQueue01..09 are hard
requirements — ControlBarCommand.cpp derefs them unguarded) and wires the
gadget message chain: button GBM_SELECTED -> PassSelectedButtonsToParentSystem
-> container -> ControlBarParent's ControlBarSystem -> ControlBar command
processing. Coordinates are absolute in the 800x600 creation resolution; the
engine rescales to the real display.
"""
import os
import sys

CB = "ControlBar.wnd"

def drawdata(bg, border=None):
    if border is None:
        border = "70 76 84 255"          # subtle steel; pass bg to hide entirely
    rows = [f"IMAGE: NoImage, COLOR: {bg}, BORDERCOLOR: {border}"]
    rows += [f"IMAGE: NoImage, COLOR: {bg}, BORDERCOLOR: {border}"] * 8
    return ",\n                    ".join(rows)

def window(name, rect, wtype="USER", status="ENABLED+IMAGE+NOFOCUS",
           syscb="[None]", bg="0 0 0 255", extra="", children=(),
           drawcb="[None]", inputcb="[None]", border=None):
    x0, y0, x1, y1 = rect
    body = f"""WINDOW
  WINDOWTYPE = {wtype};
  SCREENRECT = UPPERLEFT: {x0} {y0}, BOTTOMRIGHT: {x1} {y1}, CREATIONRESOLUTION: 800 600;
  NAME = "{CB}:{name}";
  STATUS = {status};
  STYLE = {wtype};
  SYSTEMCALLBACK = "{syscb}";
  INPUTCALLBACK = "{inputcb}";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "{drawcb}";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
{extra}  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 255 255 255 255,
              DISABLED: 128 128 128 255, DISABLEDBORDER: 128 128 128 255,
              HILITE: 255 255 128 255, HILITEBORDER: 255 255 255 255;
  ENABLEDDRAWDATA = {drawdata(bg, border)};
  DISABLEDDRAWDATA = {drawdata('26 28 32 255', border)};
  HILITEDRAWDATA = {drawdata('58 64 74 255', border)};
"""
    if children:
        body += "  CHILD\n"
        for c in children:
            body += c
        body += "  ENDALLCHILDREN\n"
    body += "END\n"
    return body

def grid(prefix, count, cols, x0, y0, w, h, px, py, **kw):
    out = []
    for i in range(count):
        x = x0 + (i % cols) * px
        y = y0 + (i // cols) * py
        out.append(window(f"{prefix}{i+1:02d}", (x, y, x + w, y + h),
                          wtype="PUSHBUTTON", status="ENABLED+IMAGE",
                          syscb="PassSelectedButtonsToParentSystem", **kw))
    return out

DARK = "13 15 18 255"
children = []
# context panels (ControlBar shows/hides these per selection context) — all
# borderless so idle contexts leave no chrome behind
children.append(window("UnderConstructionWindow", (10, 440, 200, 590), bg=DARK, border=DARK))
children.append(window("OCLTimerWindow", (10, 440, 200, 590), bg=DARK, border=DARK))
children.append(window("BeaconWindow", (10, 440, 200, 590), bg=DARK, border=DARK))
children.append(window("CommandWindow", (210, 440, 590, 590), bg=DARK, border=DARK,
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonCommand", 18, 6, 212, 442, 58, 44, 63, 49,
                                     bg="34 38 44 255")))
children.append(window("ProductionQueueWindow", (210, 440, 590, 590), bg=DARK, border=DARK,
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonQueue", 9, 5, 212, 442, 44, 44, 47, 47,
                                     bg="30 40 34 255")))
children.append(window("ObserverPlayerListWindow", (210, 440, 590, 590), bg=DARK, border=DARK))
children.append(window("ObserverPlayerInfoWindow", (210, 440, 590, 590), bg=DARK, border=DARK))
children.append(window("WinUnitSelected", (10, 440, 200, 470), bg=DARK, border=DARK))
children.append(window("CameoWindow", (10, 475, 90, 565), bg=DARK, border=DARK))
children.append(window("PopupCommunicator", (762, 402, 790, 418), bg=DARK, border=DARK))
children.append(window("BackgroundMarker", (0, 420, 8, 428), bg=DARK, border=DARK))
children.append(window("WinUAttack", (0, 400, 8, 408), bg=DARK, border=DARK))
children.append(window("RightHUD", (600, 560, 636, 596), bg=DARK, border=DARK,
                       children=[window(f"UnitUpgrade{i}", (602 + 6 * (i - 1), 562,
                                                           606 + 6 * (i - 1), 566),
                                        bg=DARK, border=DARK)
                                 for i in range(1, 6)]))
# money readout + power sliver (InGameUI::update derefs both every frame)
children.append(window("MoneyDisplay", (612, 426, 788, 442), wtype="STATICTEXT",
                       status="ENABLED", bg="16 18 21 255", border="120 104 60 255",
                       extra="  STATICTEXTDATA = CENTERED: 1;\n"))
children.append(window("PowerWindow", (612, 446, 788, 452), bg="22 30 46 255",
                       border="22 30 46 255"))
# radar draws into this window (engine hardcodes the name ControlBar.wnd:LeftHUD).
# Square, so the square map fills it edge to edge.
children.append(window("LeftHUD", (648, 456, 788, 596), bg="10 12 14 255",
                       border="120 104 60 255",
                       drawcb="W3DLeftHUDDraw", inputcb="LeftHUDInput"))

parent = window("ControlBarParent", (0, 420, 800, 600),
                status="ENABLED+IMAGE+NOFOCUS", syscb="ControlBarSystem",
                bg="10 11 13 255", border="10 11 13 255", children=children)

content = """FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = "[None]";
  LAYOUTUPDATE = "[None]";
  LAYOUTSHUTDOWN = "[None]";
ENDLAYOUTBLOCK
""" + parent

targets = sys.argv[1:] or [
    os.path.expanduser("~/GeneralsX/GeneralsZH/Window/ControlBar.wnd"),
    os.path.join(os.path.dirname(__file__), "..", "data", "Window", "ControlBar.wnd"),
]
for t in targets:
    with open(t, "w") as f:
        f.write(content)
    print(f"wrote {t} ({len(content)} bytes)")
