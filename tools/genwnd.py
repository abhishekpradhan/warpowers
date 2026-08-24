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
           drawcb="[None]", inputcb="[None]", border=None, textcolor=None,
           fontsize=10, bold=0):
    x0, y0, x1, y1 = rect
    if textcolor is None:
        textcolor = "255 255 255 255"
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
  FONT = NAME: "Arial", SIZE: {fontsize}, BOLD: {bold};
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
{extra}  TEXTCOLOR = ENABLED: {textcolor}, ENABLEDBORDER: {textcolor},
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
children.append(window("UnderConstructionWindow", (10, 440, 200, 590), bg=DARK, border=DARK,
                       children=[window("UnderConstructionDesc", (16, 448, 194, 478),
                                        wtype="STATICTEXT", status="ENABLED",
                                        bg="16 18 21 255", border="70 76 84 255",
                                        extra="  STATICTEXTDATA = CENTERED: 1;\n"),
                                 window("ButtonCancelConstruction", (100, 486, 190, 514),
                                        wtype="PUSHBUTTON", status="ENABLED",
                                        syscb="PassSelectedButtonsToParentSystem",
                                        bg="128 36 36 255", border="220 96 96 255",
                                        extra='  TEXT = "WP:Cancel";\n')]))
children.append(window("OCLTimerWindow", (10, 440, 200, 590), bg=DARK, border=DARK))
children.append(window("BeaconWindow", (10, 440, 200, 590), bg=DARK, border=DARK))
# command grid and production queue get DISJOINT rects: overlapped, the
# invisible queue buttons swallow command clicks while producing (a click on
# queue slot 1 cancels production — reads as "my clicks do nothing").
# command grid (2 rows) on top, queue strip below — disjoint rects, and both
# clear of the 3D viewport overdraw (scene renders down to ~UI y465).
children.append(window("CommandWindow", (210, 468, 590, 562), bg=DARK, border=DARK,
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonCommand", 18, 6, 212, 470, 58, 44, 63, 47,
                                     bg="34 38 44 255")))
children.append(window("ProductionQueueWindow", (210, 566, 590, 598), bg=DARK, border=DARK,
                       syscb="PassSelectedButtonsToParentSystem",
                       children=grid("ButtonQueue", 9, 9, 212, 567, 30, 30, 34, 34,
                                     bg="30 40 34 255")))
children.append(window("ObserverPlayerListWindow", (210, 440, 590, 590), bg=DARK, border=DARK))
children.append(window("ObserverPlayerInfoWindow", (210, 440, 590, 590), bg=DARK, border=DARK))
children.append(window("WinUnitSelected", (10, 440, 200, 470), bg=DARK, border=DARK))
# portrait cameo: transparent when no image is set (during production the
# engine intentionally nulls the portrait and shows the queue instead — an
# opaque bg here reads as a broken black box)
children.append(window("CameoWindow", (10, 475, 90, 565), bg="0 0 0 0", border="0 0 0 0"))
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

# ---------- ControlBarPopupDescription.wnd (build-button hover tooltip) ----------
# One seamless panel docked just above the command grid (grid top = 468).
# Engine contract (ControlBarPopupDescription.cpp): parent min height 102; the
# description row is measured with word-wrap and BOTH desc + parent grow by the
# overflow while the parent slides UP by the same amount — so the panel is
# bottom-anchored: author the fixed look, long descriptions extend upward.
PBG = "15 17 21 255"
POPUP = window("PopupParent", (210, 352, 500, 454), status="ENABLED+IMAGE+NOFOCUS",
               bg=PBG, border="120 104 60 255", children=[
    window("StaticTextName", (218, 358, 492, 376), wtype="STATICTEXT", status="ENABLED",
           bg=PBG, border=PBG, fontsize=12, bold=1,
           extra="  STATICTEXTDATA = CENTERED: 0;\n"),
    window("StaticTextCost", (218, 380, 492, 396), wtype="STATICTEXT", status="ENABLED",
           bg=PBG, border=PBG, textcolor="215 180 90 255",
           extra="  STATICTEXTDATA = CENTERED: 0;\n"),
    window("StaticTextDescription", (218, 400, 492, 448), wtype="STATICTEXT", status="ENABLED",
           bg=PBG, border=PBG, textcolor="196 202 210 255",
           extra="  STATICTEXTDATA = CENTERED: 0;\n"),
])
popup_content = ("FILE_VERSION = 2;\n"
                 "STARTLAYOUTBLOCK\n"
                 "  LAYOUTINIT = \"[None]\";\n"
                 "  LAYOUTUPDATE = \"[None]\";\n"
                 "  LAYOUTSHUTDOWN = \"[None]\";\n"
                 "ENDLAYOUTBLOCK\n") + POPUP.replace(CB + ":", "ControlBarPopupDescription.wnd:")
for t in targets:
    pt = os.path.join(os.path.dirname(t), "ControlBarPopupDescription.wnd")
    with open(pt, "w") as f:
        f.write(popup_content)
    print("wrote", pt)


# ---------- match-result screens (ScriptActions loads these on VICTORY/DEFEAT) ----------
def result_screen(fname, key, color):
    NAME = fname
    body = window("ResultBanner", (200, 240, 600, 320), wtype="STATICTEXT",
                  status="ENABLED", bg="12 14 17 235", border=color,
                  textcolor=color, fontsize=32, bold=1,
                  extra=f'  TEXT = "{key}";\n  STATICTEXTDATA = CENTERED: 1;\n')
    parent = window("ResultParent", (180, 220, 620, 340),
                    status="ENABLED+IMAGE+NOFOCUS",
                    bg="9 10 12 220", border=color, children=[body])
    content = ("FILE_VERSION = 2;\n"
               "STARTLAYOUTBLOCK\n"
               "  LAYOUTINIT = \"[None]\";\n"
               "  LAYOUTUPDATE = \"[None]\";\n"
               "  LAYOUTSHUTDOWN = \"[None]\";\n"
               "ENDLAYOUTBLOCK\n") + parent.replace(CB + ":", NAME + ".wnd:")
    for t in targets:
        d = os.path.join(os.path.dirname(t), "Menus")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname + ".wnd"), "w") as f:
            f.write(content)
        print("wrote", os.path.join(d, fname + ".wnd"))

result_screen("Victorious", "WP:Victory", "215 180 90 255")
result_screen("Defeat", "WP:Defeat", "200 70 70 255")
result_screen("LocalDefeat", "WP:Defeat", "200 70 70 255")


# ---------- generic Menus/ layout writer ----------
def menu_layout(fname, body, init="[None]", update="[None]", shutdown="[None]"):
    content = ("FILE_VERSION = 2;\n"
               "STARTLAYOUTBLOCK\n"
               f"  LAYOUTINIT = \"{init}\";\n"
               f"  LAYOUTUPDATE = \"{update}\";\n"
               f"  LAYOUTSHUTDOWN = \"{shutdown}\";\n"
               "ENDLAYOUTBLOCK\n") + body.replace(CB + ":", f"{fname}.wnd:")
    for t in targets:
        d = os.path.join(os.path.dirname(t), "Menus")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, fname + ".wnd")
        with open(p, "w") as f:
            f.write(content)
        print("wrote", p)

GOLD = "120 104 60 255"
PANEL = "15 17 21 250"

def menu_button(name, rect, text, accent="34 38 44 255"):
    return window(name, rect, wtype="PUSHBUTTON", status="ENABLED",
                  syscb="PassSelectedButtonsToParentSystem", bg=accent,
                  border=GOLD, fontsize=12,
                  extra=f'  TEXT = "{text}";\n')

# ---------- QuitMenu.wnd (ESC pause menu; stock QuitMenuSystem callback) ----------
# Engine contract (QuitMenu.cpp): ButtonReturn/ButtonRestart/ButtonExit are
# dereferenced unguarded; ButtonSaveLoad/ButtonOptions lookups are guarded
# (Options added with the in-engine shell round). Restart/Exit text is set at
# runtime (GUI:RestartMission / GUI:ExitMission).
quit_children = [
    window("PausedTitle", (300, 200, 500, 228), wtype="STATICTEXT", status="ENABLED",
           bg=PANEL, border=PANEL, textcolor="215 180 90 255", fontsize=16, bold=1,
           extra='  TEXT = "WP:PausedTitle";\n  STATICTEXTDATA = CENTERED: 1;\n'),
    menu_button("ButtonReturn",  (300, 244, 500, 276), "WP:ReturnToBattle"),
    menu_button("ButtonRestart", (300, 284, 500, 316), "GUI:RestartMission"),
    menu_button("ButtonExit",    (300, 324, 500, 356), "GUI:ExitMission",
                accent="60 34 34 255"),
]
QUIT = window("QuitMenuParent", (280, 180, 520, 380),
              status="ENABLED+IMAGE+NOFOCUS", syscb="QuitMenuSystem",
              bg=PANEL, border=GOLD, children=quit_children)
menu_layout("QuitMenu", QUIT)

# ---------- MessageBox.wnd / QuitMessageBox.wnd (yes/no/ok confirm dialogs) ----------
# Engine contract (gogoMessageBox): all four buttons must exist (ButtonOk's
# position is read unguarded even in yes/no boxes); engine unhides the flagged
# ones, so buttons are authored HIDDEN. StaticTextTitle/StaticTextMessage get
# runtime text.
def message_box(fname, syscb):
    kids = [
        window("StaticTextTitle", (260, 236, 540, 260), wtype="STATICTEXT",
               status="ENABLED", bg=PANEL, border=PANEL,
               textcolor="215 180 90 255", fontsize=13, bold=1,
               extra="  STATICTEXTDATA = CENTERED: 1;\n"),
        window("StaticTextMessage", (264, 268, 536, 316), wtype="STATICTEXT",
               status="ENABLED", bg=PANEL, border=PANEL,
               extra="  STATICTEXTDATA = CENTERED: 1;\n"),
    ]
    bx = 270
    for bname, blabel in [("ButtonOk", "GUI:Ok"), ("ButtonYes", "GUI:Yes"),
                          ("ButtonNo", "GUI:No"), ("ButtonCancel", "GUI:Cancel")]:
        kids.append(window(bname, (bx, 326, bx + 60, 354), wtype="PUSHBUTTON",
                           status="ENABLED+HIDDEN",
                           syscb="PassSelectedButtonsToParentSystem",
                           bg="34 38 44 255", border=GOLD, fontsize=11,
                           extra=f'  TEXT = "{blabel}";\n'))
        bx += 68
    box = window("MessageBoxParent", (250, 224, 550, 366),
                 status="ENABLED+IMAGE+NOFOCUS", syscb=syscb,
                 bg=PANEL, border=GOLD, children=kids)
    menu_layout(fname, box)

message_box("MessageBox", "MessageBoxSystem")
message_box("QuitMessageBox", "QuitMessageBoxSystem")
