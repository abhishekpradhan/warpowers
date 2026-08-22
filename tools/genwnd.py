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

def drawdata(bg):
    rows = [f"IMAGE: NoImage, COLOR: {bg}, BORDERCOLOR: 255 255 255 255"]
    rows += ["IMAGE: NoImage, COLOR: 255 255 255 255, BORDERCOLOR: 255 255 255 255"] * 8
    return ",\n                    ".join(rows)

def window(name, rect, wtype="USER", status="ENABLED+IMAGE+NOFOCUS",
           syscb="[None]", bg="0 0 0 255", extra="", children=()):
    x0, y0, x1, y1 = rect
    body = f"""WINDOW
  WINDOWTYPE = {wtype};
  SCREENRECT = UPPERLEFT: {x0} {y0}, BOTTOMRIGHT: {x1} {y1}, CREATIONRESOLUTION: 800 600;
  NAME = "{CB}:{name}";
  STATUS = {status};
  STYLE = {wtype};
  SYSTEMCALLBACK = "{syscb}";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
{extra}  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 255 255 255 255,
              DISABLED: 128 128 128 255, DISABLEDBORDER: 128 128 128 255,
              HILITE: 255 255 128 255, HILITEBORDER: 255 255 255 255;
  ENABLEDDRAWDATA = {drawdata(bg)};
  DISABLEDDRAWDATA = {drawdata('40 40 40 255')};
  HILITEDRAWDATA = {drawdata('90 90 110 255')};
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
                          wtype="PUSHBUTTON", status="ENABLED",
                          syscb="PassSelectedButtonsToParentSystem", **kw))
    return out

children = []
# context panels (ControlBar shows/hides these per selection context)
children.append(window("UnderConstructionWindow", (10, 440, 200, 590)))
children.append(window("OCLTimerWindow", (10, 440, 200, 590)))
children.append(window("BeaconWindow", (10, 440, 200, 590)))
children.append(window("CommandWindow", (210, 440, 590, 590),
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonCommand", 18, 6, 212, 442, 58, 44, 63, 49,
                                     bg="60 60 70 255")))
children.append(window("ProductionQueueWindow", (210, 440, 590, 590),
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonQueue", 9, 5, 212, 442, 44, 44, 47, 47,
                                     bg="50 70 50 255")))
children.append(window("ObserverPlayerListWindow", (210, 440, 590, 590)))
children.append(window("ObserverPlayerInfoWindow", (210, 440, 590, 590)))
children.append(window("WinUnitSelected", (600, 440, 700, 480)))
children.append(window("CameoWindow", (700, 440, 790, 530)))
children.append(window("PopupCommunicator", (760, 400, 790, 430)))
children.append(window("BackgroundMarker", (0, 420, 10, 430)))
children.append(window("WinUAttack", (0, 400, 10, 410)))
children.append(window("RightHUD", (600, 480, 790, 590),
                       children=[window(f"UnitUpgrade{i}", (600 + 20 * (i - 1), 560,
                                                           618 + 20 * (i - 1), 578))
                                 for i in range(1, 6)]))
# money readout + power bar (InGameUI::update derefs both every frame)
children.append(window("MoneyDisplay", (600, 422, 750, 438), wtype="STATICTEXT",
                       status="ENABLED", bg="20 20 20 255",
                       extra="  STATICTEXTDATA = CENTERED: 1;\n"))
children.append(window("PowerWindow", (600, 402, 750, 418), bg="20 30 60 255"))

parent = window("ControlBarParent", (0, 420, 800, 600),
                status="ENABLED+IMAGE+NOFOCUS", syscb="ControlBarSystem",
                bg="0 0 0 255", children=children)

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
