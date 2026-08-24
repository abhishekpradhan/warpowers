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
           fontsize=10, bold=0, hilitebg=None):
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
  HILITEDRAWDATA = {drawdata(hilitebg or '58 64 74 255', border)};
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
# Power meter: a decorative trough frame with the live meter as its child.
# The child carries DRAWCALLBACK W3DPowerDraw (engine draw: log-scale tick
# bar green/yellow/red by margin + consumption needle - images PowerPointG/
# Y/R + PowerBarSlider on the glyph sheet). A draw callback REPLACES the
# default bg/border paint, hence the split; neither window may carry
# WIN_STATUS_IMAGE (image-flagged windows without an image paint nothing
# and haunt the tooltip hit-test).
# One window, no decorative sibling: an overlapping sibling wins the input
# hit-test and eats the hover tooltip. W3DPowerDraw paints its own trough +
# border around the window rect, then ticks + needle.
children.append(window("PowerWindow", (613, 446, 787, 455), status="ENABLED+NOFOCUS",
                       drawcb="W3DPowerDraw"))
# radar draws into this window (engine hardcodes the name ControlBar.wnd:LeftHUD).
# Square, so the square map fills it edge to edge.
children.append(window("LeftHUD", (648, 456, 788, 596), bg="10 12 14 255",
                       border="120 104 60 255",
                       drawcb="W3DLeftHUDDraw", inputcb="LeftHUDInput"))

# WPHudSwallowInput: the opaque bar consumes every click that no child
# handled (disabled buttons, panel gaps) - without it those fall through
# to the world as rally/move orders behind the HUD.
parent = window("ControlBarParent", (0, 420, 800, 600),
                status="ENABLED+IMAGE+NOFOCUS", syscb="ControlBarSystem",
                inputcb="WPHudSwallowInput",
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
PBG = "16 20 27 250"
# Parent drops WIN_STATUS_IMAGE so its fill actually paints (the default draw
# only color-fills without the flag) - otherwise the text rows float as bare
# strips when the popup opens for money/power hovers.
POPUP = window("PopupParent", (210, 352, 500, 454), status="ENABLED+NOFOCUS",
               bg=PBG, border="58 66 80 255", children=[
    window("StaticTextName", (218, 358, 492, 376), wtype="STATICTEXT", status="ENABLED",
           bg="0 0 0 0", border="0 0 0 0", textcolor="215 180 90 255",
           fontsize=12, bold=1,
           extra="  STATICTEXTDATA = CENTERED: 0;\n"),
    window("StaticTextCost", (218, 380, 492, 396), wtype="STATICTEXT", status="ENABLED",
           bg="0 0 0 0", border="0 0 0 0", textcolor="215 180 90 255",
           extra="  STATICTEXTDATA = CENTERED: 0;\n"),
    window("StaticTextDescription", (218, 400, 492, 448), wtype="STATICTEXT", status="ENABLED",
           bg="0 0 0 0", border="0 0 0 0", textcolor="199 206 218 255",
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
    # Layout callbacks are UNQUOTED: parseInit/parseUpdate/parseShutdown
    # tokenize on whitespace only, so a quoted name never resolves in the
    # function lexicon (window-level callbacks parse differently and accept
    # quotes). Cost a full click-forensics session to find.
    content = ("FILE_VERSION = 2;\n"
               "STARTLAYOUTBLOCK\n"
               f"  LAYOUTINIT = {init};\n"
               f"  LAYOUTUPDATE = {update};\n"
               f"  LAYOUTSHUTDOWN = {shutdown};\n"
               "ENDLAYOUTBLOCK\n") + body.replace(CB + ":", f"{fname}.wnd:")
    for t in targets:
        d = os.path.join(os.path.dirname(t), "Menus")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, fname + ".wnd")
        with open(p, "w") as f:
            f.write(content)
        print("wrote", p)

# ---------- shell style system (matches the web page: web/index.html) ----------
# Page palette: bg #0a0c10, panel #10141b, line #232a35, text #c7ceda,
# dim #6b7686, accent #d7b45a, danger tint. WND color fills only draw when
# WIN_STATUS_IMAGE is ABSENT (W3DGameWinDefaultDraw takes the image branch
# and draws nothing for NoImage), so panels/backdrops use ENABLED+NOFOCUS.
SHELL_BG   = "10 12 16 255"      # page --bg
PANEL      = "16 20 27 250"      # page --panel
LINE       = "35 42 53 255"      # page --line
TEXT       = "199 206 218 255"   # page --text
DIM        = "107 118 134 255"   # page --text-dim
GOLD       = "215 180 90 255"    # page --accent
GOLD_DARK  = "13 15 18 255"      # text on gold
GOLD_HI    = "232 202 122 255"
GOLD_LINE  = "150 126 66 255"

def backdrop(alpha=255, name="ScreenBackdrop"):
    bg = f"10 12 16 {alpha}"
    return window(name, (0, 0, 800, 600), status="ENABLED+NOFOCUS",
                  bg=bg, border=bg)

def frame_border(name="ScreenFrame"):
    # Inset 1px outline matching the page's framed-stage look (the window
    # draw paints BORDERCOLOR as the outline; bg alpha 0 keeps the inside
    # untouched).
    return window(name, (14, 12, 786, 588), status="ENABLED+NOFOCUS",
                  bg="0 0 0 0", border=LINE)

def label(name, rect, text_label, size=11, color=None, centered=1, bold=0,
          bg=None):
    fill = bg or "0 0 0 0"
    # Empty TEXT is a native crash: parseText strtoks the value and calls
    # strlen(NULL) on the missing token (wasm survives only because address
    # 0 is readable there). Runtime-filled labels omit the field entirely.
    text_line = f'  TEXT = "{text_label}";\n' if text_label else ""
    return window(name, rect, wtype="STATICTEXT", status="ENABLED",
                  bg=fill, border=fill, textcolor=color or TEXT,
                  fontsize=size, bold=bold,
                  extra=text_line + f'  STATICTEXTDATA = CENTERED: {centered};\n')

def rule(name, rect, color=GOLD):
    return window(name, rect, status="ENABLED+NOFOCUS", bg=color, border=color)

def btn(name, rect, text_label, kind="ghost", size=12):
    # Button faces are color fills; the gadget draw honors HILITEDRAWDATA on
    # hover, so each kind carries its own hover shade.
    kinds = {
        "primary": dict(bg=GOLD, border=GOLD_LINE, textcolor=GOLD_DARK,
                        hilitebg=GOLD_HI, bold=1),
        "ghost":   dict(bg="26 30 38 255", border="58 66 80 255",
                        textcolor=TEXT, hilitebg="38 44 55 255", bold=0),
        "danger":  dict(bg="44 26 26 255", border="122 62 62 255",
                        textcolor="216 162 162 255", hilitebg="60 34 34 255",
                        bold=0),
        "meridian": dict(bg="34 44 58 255", border="96 128 168 255",
                         textcolor="208 220 236 255", hilitebg="44 57 75 255",
                         bold=1),
        "jackal":  dict(bg="50 39 26 255", border="168 128 78 255",
                        textcolor="235 219 197 255", hilitebg="64 50 33 255",
                        bold=1),
    }
    k = kinds[kind]
    return window(name, rect, wtype="PUSHBUTTON", status="ENABLED",
                  syscb="PassSelectedButtonsToParentSystem", bg=k["bg"],
                  border=k["border"], textcolor=k["textcolor"],
                  hilitebg=k["hilitebg"], fontsize=size, bold=k["bold"],
                  extra=f'  TEXT = "{text_label}";\n')

# ---------- QuitMenu.wnd (ESC pause menu; stock QuitMenuSystem callback) ----------
# Engine contract (QuitMenu.cpp): ButtonReturn/ButtonRestart/ButtonExit are
# dereferenced unguarded; ButtonSaveLoad/ButtonOptions lookups are guarded.
# Restart/Exit text is set at runtime (GUI:RestartMission / GUI:ExitMission).
quit_children = [
    backdrop(alpha=150, name="PauseDim"),
    window("PausePanel", (288, 186, 512, 400), status="ENABLED+NOFOCUS",
           bg=PANEL, border=LINE),
    rule("PauseRule", (352, 228, 448, 230)),
    label("PausedTitle", (300, 202, 500, 224), "WP:PausedTitle", size=15,
          color=GOLD, bold=1),
    btn("ButtonReturn",  (312, 250, 488, 284), "WP:ReturnToBattle", "primary"),
    btn("ButtonRestart", (312, 294, 488, 326), "GUI:RestartMission", "ghost"),
    btn("ButtonExit",    (312, 340, 488, 374), "GUI:ExitMission", "danger"),
]
QUIT = window("QuitMenuParent", (0, 0, 800, 600),
              status="ENABLED+NOFOCUS", syscb="QuitMenuSystem",
              bg="0 0 0 0", border="0 0 0 0", children=quit_children)
menu_layout("QuitMenu", QUIT)

# ---------- MessageBox.wnd / QuitMessageBox.wnd (yes/no/ok confirm dialogs) ----------
# Engine contract (gogoMessageBox): all four buttons must exist (ButtonOk's
# position is read unguarded even in yes/no boxes); engine unhides the
# flagged ones, so buttons are authored HIDDEN. StaticTextTitle/
# StaticTextMessage get runtime text.
def message_box(fname, syscb):
    kids = [
        window("BoxPanel", (250, 224, 550, 372), status="ENABLED+NOFOCUS",
               bg=PANEL, border=LINE),
        label("StaticTextTitle", (260, 238, 540, 262), "", size=13,
              color=GOLD, bold=1),
        label("StaticTextMessage", (264, 270, 536, 318), "", size=11,
              color=TEXT),
    ]
    bx = 270
    for bname, blabel in [("ButtonOk", "GUI:Ok"), ("ButtonYes", "GUI:Yes"),
                          ("ButtonNo", "GUI:No"), ("ButtonCancel", "GUI:Cancel")]:
        b = btn(bname, (bx, 328, bx + 60, 358), blabel, "ghost", size=11)
        b = b.replace("STATUS = ENABLED;", "STATUS = ENABLED+HIDDEN;")
        kids.append(b)
        bx += 68
    box = window("MessageBoxParent", (250, 224, 550, 372),
                 status="ENABLED+NOFOCUS", syscb=syscb,
                 bg="0 0 0 0", border="0 0 0 0", children=kids)
    menu_layout(fname, box)

message_box("MessageBox", "MessageBoxSystem")
message_box("QuitMessageBox", "QuitMessageBoxSystem")


# ---------- In-engine shell screens (WPShell.cpp callbacks) ----------
# The engine shell is the BETWEEN-MATCHES hub (post-match score, redeploy,
# stand down). At boot the web page is the menu: its DEPLOY boots straight
# into the picked faction's map via WP_BOOT_MAP. Styled to match the page.

main_children = [
    backdrop(),
    frame_border(),
    # Two-tone wordmark like the page (WAR warm-white, POWERS gold): two
    # left-justified labels on one baseline; box origins hand-tuned to the
    # rendered glyph widths (checked via native frame dump).
    label("TitleWar", (217, 158, 383, 210), "WP:TitleWar", size=36,
          color="232 226 214 255", bold=1, centered=0),
    label("TitlePowers", (363, 158, 720, 210), "WP:TitlePowers", size=36,
          color=GOLD, bold=1, centered=0),
    rule("TitleRule", (352, 218, 448, 221)),
    label("TitleTag", (100, 232, 700, 252), "WP:Tagline", size=10, color=DIM),
    btn("ButtonEngage",  (290, 312, 510, 352), "WP:Engage", "primary", size=13),
    btn("ButtonQuit",    (290, 366, 510, 400), "WP:QuitGame", "danger"),
    label("LabelVersion", (540, 576, 792, 594), "", size=9, color=DIM,
          centered=0),
]
MAINMENU = window("MainMenuParent", (0, 0, 800, 600),
                  status="ENABLED+NOFOCUS", syscb="WPMainMenuSystem",
                  bg=SHELL_BG, border=SHELL_BG, children=main_children)
menu_layout("MainMenu", MAINMENU, init="WPMainMenuInit",
            update="WPMainMenuUpdate", shutdown="WPShellShutdown")

# Deployment picker, two sections: battlefield selector (arrow buttons
# flanking the runtime-set name, description beneath), then the faction
# deploy buttons. MapName/MapDesc text is filled by WPSkirmishInit /
# the arrow handlers (winSetText / GadgetStaticTextSetText).
sk_children = [
    backdrop(),
    frame_border(),
    label("TitleDeploy", (100, 140, 700, 176), "WP:Deployment", size=22,
          color="232 226 214 255", bold=1),
    rule("DeployRule", (368, 184, 432, 186)),
    label("DeployHint", (100, 196, 700, 212), "WP:DeployHint", size=10,
          color=DIM),
    label("BattlefieldLabel", (100, 238, 700, 252), "WP:BattlefieldLabel",
          size=9, color=DIM),
    btn("ButtonMapPrev", (252, 258, 288, 292), "WP:ArrowLeft", "ghost", size=13),
    label("MapName", (296, 262, 504, 288), "", size=14, color=GOLD, bold=1,
          bg="20 24 31 255"),
    btn("ButtonMapNext", (512, 258, 548, 292), "WP:ArrowRight", "ghost", size=13),
    label("MapDesc", (100, 298, 700, 314), "", size=9, color=DIM),
    label("FrontLabel", (100, 340, 700, 354), "WP:ChooseFront",
          size=9, color=DIM),
    btn("ButtonDeployMeridian", (240, 360, 560, 404), "WP:DeployMeridian",
        "meridian", size=13),
    btn("ButtonDeployJackal",   (240, 414, 560, 458), "WP:DeployJackal",
        "jackal", size=13),
    btn("ButtonBack", (330, 480, 470, 512), "WP:Back", "ghost"),
]
SKIRMISH = window("SkirmishParent", (0, 0, 800, 600),
                  status="ENABLED+NOFOCUS", syscb="WPSkirmishSystem",
                  bg="0 0 0 0", border="0 0 0 0", children=sk_children)
menu_layout("WPSkirmish", SKIRMISH, init="WPSkirmishInit",
            shutdown="WPShellShutdown")

# (In-engine Options retired: the page overlay strip owns volume/fullscreen.)

# Post-match score screen (pushed over the main menu; WPScoreInit fills
# stats and recolors the banner on defeat).
score_children = [
    backdrop(),
    frame_border(),
    label("ResultBanner", (150, 150, 650, 200), "", size=32, color=GOLD,
          bold=1),
    rule("ScoreRule", (352, 212, 448, 214)),
]
sy = 240
for stat in ["StatUnits", "StatStructures", "StatMoney", "StatDuration"]:
    score_children.append(label(stat, (200, sy, 600, sy + 22), "", size=12,
                                color=TEXT))
    sy += 30
score_children.append(btn("ButtonContinue", (310, 386, 490, 422),
                          "WP:Continue", "primary", size=13))
SCORE = window("ScoreParent", (0, 0, 800, 600),
               status="ENABLED+NOFOCUS", syscb="WPScoreSystem",
               bg="0 0 0 0", border="0 0 0 0", children=score_children)
menu_layout("WPScore", SCORE, init="WPScoreInit", shutdown="WPShellShutdown")
