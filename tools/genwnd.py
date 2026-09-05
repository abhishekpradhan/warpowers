#!/usr/bin/env python3
"""War Powers ControlBar.wnd generator.

Replaces the hand-authored ControlBar.wnd with a declarative table. Adds the
windows the in-game UI dereferences at runtime (ButtonQueue01..09 are hard
requirements — ControlBarCommand.cpp derefs them unguarded) and wires the
gadget message chain: button GBM_SELECTED -> PassSelectedButtonsToParentSystem
-> container -> ControlBarParent's ControlBarSystem -> ControlBar command
processing. HUD coordinates use a 1280x720 reference; shell rectangles authored
on the legacy canvas are uniformly scaled and centered within that reference.
"""
import os
import sys

CB = "ControlBar.wnd"
# Native HUD coordinates; legacy shell rectangles are centered without stretching.
WIDE_COORDS = True

def drawdata(bg, border=None, image=None):
    if border is None:
        border = "70 76 84 255"          # subtle steel; pass bg to hide entirely
    img = image or "NoImage"
    rows = [f"IMAGE: {img}, COLOR: {bg}, BORDERCOLOR: {border}"]
    rows += [f"IMAGE: {img}, COLOR: {bg}, BORDERCOLOR: {border}"] * 8
    return ",\n                    ".join(rows)

def window(name, rect, wtype="USER", status="ENABLED+IMAGE+NOFOCUS",
           syscb="[None]", bg="0 0 0 255", extra="", children=(),
           drawcb="[None]", inputcb="[None]", border=None, textcolor=None,
           fontsize=10, bold=0, hilitebg=None, image=None):
    x0, y0, x1, y1 = rect
    if not WIDE_COORDS:
        if rect == (0, 0, 800, 600):
            x0, y0, x1, y1 = 0, 0, 1280, 720
        else:
            x0, x1 = round(x0 * 1.2 + 160), round(x1 * 1.2 + 160)
            y0, y1 = round(y0 * 1.2), round(y1 * 1.2)
        fontsize = max(12, round(fontsize * 1.2))
    if textcolor is None:
        textcolor = "255 255 255 255"
    body = f"""WINDOW
  WINDOWTYPE = {wtype};
  SCREENRECT = UPPERLEFT: {x0} {y0}, BOTTOMRIGHT: {x1} {y1}, CREATIONRESOLUTION: 1280 720;
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
  ENABLEDDRAWDATA = {drawdata(bg, border, image)};
  DISABLEDDRAWDATA = {drawdata('26 28 32 255', border, image)};
  HILITEDRAWDATA = {drawdata(hilitebg or '58 64 74 255', border, image)};
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

# Visual thesis: a restrained field console, with the battlefield dominant.
# Content hierarchy: selected identity / orders and queue / economy and radar.
# Interactions: existing command hover, queue progress, and context panels.
DARK = "14 18 24 255"
children = []
def hud_label(name, rect, text=None, size=12, color="188 199 211 255"):
    extra = '  STATICTEXTDATA = CENTERED: 0;\n'
    if text: extra += f'  TEXT = "{text}";\n'
    return window(name, rect, wtype="STATICTEXT", status="ENABLED+NOFOCUS",
                  bg="0 0 0 0", border="0 0 0 0", textcolor=color, fontsize=size, extra=extra)

# All required context windows remain, with mutually exclusive selection UI.
children.append(window("UnderConstructionWindow", (20, 594, 368, 674), bg=DARK, border=DARK,
    children=[hud_label("UnderConstructionDesc", (130, 606, 354, 630)),
              window("ButtonCancelConstruction", (228, 637, 354, 669), wtype="PUSHBUTTON",
                     status="ENABLED", syscb="PassSelectedButtonsToParentSystem",
                     bg="61 30 30 255", border="124 62 62 255", extra='  TEXT = "WP:Cancel";\n')]))
for name in ["OCLTimerWindow", "BeaconWindow"]:
    children.append(window(name, (20, 594, 368, 674), bg=DARK, border=DARK))
# Every command slot has a real, non-overlapping hit rectangle. Two rows of
# nine include expansion slots without colliding with the nine-item queue.
children.append(window("CommandWindow", (386, 582, 932, 678), bg=DARK, border=DARK,
    syscb="PassSelectedButtonsToParentSystem",
    children=grid("ButtonCommand", 18, 9, 390, 586, 44, 44, 60, 47,
                  bg="30 39 48 255", border="57 69 82 255")))
children.append(window("ProductionQueueWindow", (386, 681, 932, 716), bg=DARK, border=DARK,
    syscb="PassSelectedButtonsToParentSystem",
    children=grid("ButtonQueue", 9, 9, 390, 683, 30, 30, 39, 34,
                  bg="29 45 41 255", border="65 88 79 255")))
for name in ["ObserverPlayerListWindow", "ObserverPlayerInfoWindow"]:
    children.append(window(name, (390, 586, 928, 714), bg=DARK, border=DARK))
children.append(window("WinUnitSelected", (20, 566, 368, 592), bg=DARK, border=DARK))
children.append(window("CameoWindow", (20, 605, 92, 677), bg="0 0 0 0", border="0 0 0 0"))
children.append(window("PopupCommunicator", (1242, 543, 1266, 559), bg=DARK, border=DARK))
children.append(window("BackgroundMarker", (0, 560, 8, 568), bg=DARK, border=DARK))
children.append(window("WinUAttack", (0, 544, 8, 552), bg=DARK, border=DARK))
children.append(window("RightHUD", (944, 684, 986, 712), bg=DARK, border=DARK,
    children=[window(f"UnitUpgrade{i}", (946+8*(i-1),686,952+8*(i-1),692),bg=DARK,border=DARK) for i in range(1,6)]))
children.append(window("MoneyDisplay", (944, 566, 1118, 588), wtype="STATICTEXT", status="ENABLED",
    bg=DARK, border=DARK, textcolor="229 195 108 255", fontsize=16,
    extra="  STATICTEXTDATA = CENTERED: 0;\n"))
children.append(window("PowerWindow", (946, 599, 1117, 613), status="ENABLED+NOFOCUS", drawcb="W3DPowerDraw"))
children.append(window("ButtonIdleWorker", (20, 684, 56, 716), wtype="PUSHBUTTON", status="ENABLED+IMAGE",
    syscb="PassSelectedButtonsToParentSystem", bg="28 37 46 255", border="62 77 90 255", image="WPGlyIdleWorker"))
children.append(window("LeftHUD", (1130, 570, 1270, 710), bg="9 13 17 255", border="109 101 71 255",
    drawcb="W3DLeftHUDDraw", inputcb="LeftHUDInput"))
# Persistent identity never disappears when the engine swaps cameo for queue.
children.extend([
    hud_label("SelectionTitle", (20, 570, 374, 595), "WP:SelectionHint", 15, "230 234 238 255"),
    hud_label("SelectionDetail", (130, 608, 374, 629)),
    hud_label("ArmySummary", (130, 642, 374, 663)),
    hud_label("PowerSummary", (944, 622, 1118, 643), None, 12, "164 180 193 255"),
    hud_label("OrdersTitle", (390, 565, 926, 581), "WP:OrdersLabel", 11, "131 146 160 255"),
    hud_label("ControlsHint", (67, 691, 370, 711), None, 11, "133 147 161 255"),
])
parent = window("ControlBarParent", (0, 560, 1280, 720), status="ENABLED+NOFOCUS",
    syscb="ControlBarSystem", inputcb="WPHudSwallowInput", bg=DARK, border=DARK, children=children)

content = """FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = "[None]";
  LAYOUTUPDATE = "[None]";
  LAYOUTSHUTDOWN = "[None]";
ENDLAYOUTBLOCK
""" + parent

targets = sys.argv[1:] or [
    os.path.join(os.path.dirname(__file__), "..", "data", "Window", "ControlBar.wnd"),
]
for t in targets:
    with open(t, "w") as f:
        f.write(content)
    print(f"wrote {t} ({len(content)} bytes)")

# ---------- ControlBarPopupDescription.wnd (build-button hover tooltip) ----------
# One seamless panel docked just above the command grid (grid top = 586).
# Engine contract (ControlBarPopupDescription.cpp): parent min height 102; the
# description row is measured with word-wrap and BOTH desc + parent grow by the
# overflow while the parent slides UP by the same amount — so the panel is
# bottom-anchored: author the fixed look, long descriptions extend upward.
PBG = "17 23 30 252"
POPUP = window("PopupParent", (386, 438, 766, 550), status="ENABLED+NOFOCUS",
    bg=PBG, border="67 80 91 255", children=[
        window("StaticTextName", (399, 447, 753, 469), wtype="STATICTEXT", status="ENABLED",
               bg="0 0 0 0", border="0 0 0 0", textcolor="225 191 107 255", fontsize=15, bold=1,
               extra="  STATICTEXTDATA = CENTERED: 0;\n"),
        window("StaticTextCost", (399, 473, 753, 492), wtype="STATICTEXT", status="ENABLED",
               bg="0 0 0 0", border="0 0 0 0", textcolor="225 191 107 255", fontsize=12,
               extra="  STATICTEXTDATA = CENTERED: 0;\n"),
        window("StaticTextDescription", (399, 498, 753, 540), wtype="STATICTEXT", status="ENABLED",
               bg="0 0 0 0", border="0 0 0 0", textcolor="201 211 221 255", fontsize=12,
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


WIDE_COORDS = False

# ---------- match-result screens (ScriptActions loads these on VICTORY/DEFEAT) ----------
def result_screen(fname, key, color):
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
               "ENDLAYOUTBLOCK\n") + parent.replace(CB + ":", fname + ".wnd:")
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
    # quotes).
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

def menu_art():
    # Original game-scene artwork; the mapped image crops its power-of-two
    # texture to 16:9 so the full-screen native panel preserves composition.
    return window("MenuArtwork", (0, 0, 800, 600),
                  status="ENABLED+IMAGE+NOFOCUS", image="WPMenuBackdrop",
                  bg="255 255 255 255", border="0 0 0 0")

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
# The engine shell is the only match-launch hub. Web utilities provide
# settings, briefing and progression around these native controls.

main_children = [
    menu_art(),
    backdrop(alpha=95),
    # The artwork leaves open terrain on the left; this translucent field
    # keeps the live wordmark and controls readable at any output resolution.
    window("MenuTextField", (55, 127, 625, 453), status="ENABLED+NOFOCUS",
           bg="10 12 16 165", border="10 12 16 165"),
    frame_border(),
    # Two-tone wordmark (WAR warm-white, POWERS gold): two
    # left-justified labels on one baseline; box origins hand-tuned to the
    # rendered glyph widths (checked via native frame dump).
    label("TitleWar", (90, 158, 256, 210), "WP:TitleWar", size=36,
          color="232 226 214 255", bold=1, centered=0),
    label("TitlePowers", (236, 158, 593, 210), "WP:TitlePowers", size=36,
          color=GOLD, bold=1, centered=0),
    rule("TitleRule", (90, 218, 186, 221)),
    label("TitleTag", (90, 239, 593, 279), "WP:Tagline", size=11,
          color="172 183 199 255", centered=0),
    btn("ButtonEngage",  (90, 312, 310, 352), "WP:Engage", "primary", size=13),
    btn("ButtonQuit",    (90, 366, 310, 400), "WP:QuitGame", "ghost"),
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
    menu_art(), backdrop(alpha=235), frame_border(),
    label("TitleDeploy", (70, 62, 730, 99), "WP:Deployment", size=25,
          color="232 226 214 255", centered=0),
    rule("DeployRule", (70, 112, 730, 114)),
]
for idx, kind in enumerate(["Training", "Skirmish", "Operation", "Challenge"]):
    x = 70 + idx * 166
    sk_children.append(btn("ButtonMode" + kind, (x, 129, x+158, 161),
                           "WP:MissionType" + kind, "ghost", size=11))
sk_children.extend([
    window("MapPreview", (70, 193, 326, 385), status="ENABLED+IMAGE+NOFOCUS",
           image="WPMapPreviewFlats", bg="20 25 30 255", border=LINE),
    btn("ButtonMapPrev", (345, 192, 375, 226), "WP:ArrowLeft", "ghost", size=13),
    label("MapName", (388, 194, 687, 222), "", size=19, color=GOLD, bold=1, centered=0),
    btn("ButtonMapNext", (700, 192, 730, 226), "WP:ArrowRight", "ghost", size=13),
    label("MapDesc", (345, 239, 730, 301), "", size=12, centered=0),
    label("DifficultyLabel", (345, 309, 730, 330), "WP:DifficultyLabel", size=10, color=DIM, centered=0),
    btn("ButtonDiffPrev", (345, 338, 375, 370), "WP:ArrowLeft", "ghost", size=13),
    label("DiffName", (388, 338, 687, 370), "", size=14, color=GOLD, bold=1, centered=0),
    btn("ButtonDiffNext", (700, 338, 730, 370), "WP:ArrowRight", "ghost", size=13),
    label("DiffDesc", (345, 378, 730, 410), "", size=11, color=DIM, centered=0),
    label("ObjectiveHint", (70, 398, 326, 444), "WP:HQObjective", size=11, color=DIM, centered=0),
    btn("ButtonDeployMeridian", (70, 462, 386, 502), "WP:DeployMeridian", "meridian", size=13),
    btn("ButtonDeployJackal", (410, 462, 730, 502), "WP:DeployJackal", "jackal", size=13),
    label("MeridianBrief", (70, 510, 386, 544), "WP:MeridianBrief", size=10, color=DIM, centered=0),
    label("JackalBrief", (410, 510, 730, 544), "WP:JackalBrief", size=10, color=DIM, centered=0),
    btn("ButtonBack", (70, 554, 175, 579), "WP:Back", "ghost", size=10),
])
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
score_children.append(btn("ButtonRetry", (200, 386, 395, 426), "WP:ScoreRetry", "primary", size=13))
score_children.append(btn("ButtonChoose", (410, 386, 605, 426), "WP:ScoreChoose", "ghost", size=11))
score_children.append(btn("ButtonContinue", (310, 447, 490, 479), "WP:Continue", "ghost", size=11))
SCORE = window("ScoreParent", (0, 0, 800, 600),
               status="ENABLED+NOFOCUS", syscb="WPScoreSystem",
               bg="0 0 0 0", border="0 0 0 0", children=score_children)
menu_layout("WPScore", SCORE, init="WPScoreInit", shutdown="WPShellShutdown")
