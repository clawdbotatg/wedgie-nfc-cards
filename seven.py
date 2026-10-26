"""Dollar card #7 (Mix ETH), with a seat: every part has its own place.

    uv run --with manifold3d --with numpy --with fonttools python seven.py

  base       black. Floor + border. In the floor: a shallow seat shaped like the medallion's lip and two tabs,
             and under it a deeper pocket for the NFC sticker.
  medallion  black, the ETH logo traced in grey, green inside. Lip and two side tabs drop into the seat, flush with the floor. Body comes up
             through the lid's oval, flush with the lid.
  lid        white face, flat bottom. Sits on the floor and the tabs, inside the border.

Build: sticker in its pocket, medallion in its seat, a drop of PETG super glue on each tab, lid on top.
Writes seven.html (3D) and the print files.
"""
import json
import os

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

from dollar import BORDER, CHIP_D, corners, mix_eth, oval, pack
from make import FIT, HERE, INLAY, OUT, OUT3, H, R, W, circle, eth, face_down, rrect, save, save_3mf, slab, text

FLOOR = 1.2                 # base floor
SEAT = 0.4                  # seat depth = medallion lip + tab thickness
POCKET = 0.2                # NFC pocket, under the seat; leaves 0.6 (3 layers) under the sticker.
                            # 1 layer there tore coming off the bed.
# lid colors standing up above the face: layers, inset per layer. Empty = flat lid printed face down
# (Austin, 10-24: flat face-down lids look cleaner than raised ones)
RAISE = {}
PIT = 0.2                   # glue pits in the floor under the lid's green circles: one layer deep
NOTCH = 0.2                 # pry notch: the first layer left out at an edge, so a blade slips under
NOTCH_W, NOTCH_IN = 8.0, 3.0
# where each print sits on the 256 mm bed: away from the hot center
AT = {"base": (75, 190), "medallion": (60, 60), "lid": (185, 70)}
LID = 0.8                   # white lid, flush with the border
GAP = 0.1                   # lid to border, each side
FW, FH = W - 2 * BORDER - 2 * GAP, H - 2 * BORDER - 2 * GAP
FR = R - BORDER - GAP
LIP_W = 2.0                 # medallion lip reach past the oval
TAB_W, TAB_TO = 6.0, 23.0   # tabs: width, and how far out they reach from the center (each side)
GLUE_ROOM = 1.5             # extra room in the seat around each tab, for the glue to spread


def medallion_outline(bw, bh):
    lip = oval(bw + 2 * LIP_W, bh + 2 * LIP_W)
    tabs = rrect(2 * TAB_TO, TAB_W, TAB_W / 2)
    return lip + tabs


def base(bw, bh, pits=None):
    floor = slab(rrect(W, H, R), 0, FLOOR)
    tabs = rrect(2 * TAB_TO, TAB_W, TAB_W / 2).offset(FIT + GLUE_ROOM, JoinType.Round)
    seat = slab(medallion_outline(bw, bh).offset(FIT) + tabs, FLOOR - SEAT, FLOOR + 1)
    pocket = slab(circle(CHIP_D), FLOOR - SEAT - POCKET, FLOOR + 1)
    rim = slab(rrect(W, H, R) - rrect(W - 2 * BORDER, H - 2 * BORDER, R - BORDER), FLOOR, FLOOR + LID)
    notches = sum((slab(CrossSection.square([2 * NOTCH_IN, NOTCH_W], center=True).translate([sx * W / 2, 0]), -1, NOTCH)
                   for sx in (-1, 1)), Manifold())
    out = floor - seat - pocket + rim - notches
    if pits is not None:                                    # glue pits right under the lid's green corners
        out = out - slab(pits, FLOOR - PIT, FLOOR + 1)
    return {"black": out}


def medallion(bw, bh, art, rise=None, deep=None):
    rise, deep = rise or RISE, deep or DEEP
    top = FLOOR + LID
    body = slab(medallion_outline(bw, bh), FLOOR - SEAT, FLOOR) + slab(oval(bw, bh), FLOOR - SEAT, top)
    parts, taken = {}, Manifold()
    for c, cs in art.items():
        cs = cs ^ oval(bw - 1.0, bh - 1.0)
        d = deep.get(c, INLAY)
        parts[c] = slab(cs, top - d, top) if d else Manifold()
        if d:
            taken = taken + slab(cs, top - d, top + 1)
    edge = bh / 2 + LIP_W                                   # pry notches at the oval's top and bottom
    notches = sum((slab(CrossSection.square([NOTCH_W, 2 * NOTCH_IN], center=True).translate([0, sy * edge]),
                        FLOOR - SEAT - 1, FLOOR - SEAT + NOTCH) for sy in (-1, 1)), Manifold())
    parts["black"] = body - taken - notches
    for c, (start, steps, step_in) in rise.items():        # color standing up above the face, smaller each layer
        if c not in art:
            continue
        cs = art[c] ^ oval(bw - 1.0, bh - 1.0)
        for k in range(steps):
            if k:
                cs = cs.offset(-step_in, JoinType.Miter)
            if cs.is_empty() or cs.area() < 0.3:
                break
            z = top + start + 0.2 * k
            parts[c] = parts[c] + slab(cs, z, z + 0.2)
        print(f"{c} {start:.1f} to {parts[c].bounding_box()[5] - top:.1f} mm above the face")
    return parts


LINE = 0.6                  # grey line width of the traced ETH logo
# logo colors stacked on top of the black face, in 0.2 layers: (start above the face, layers, inset per layer).
# Each color sits fully above the one before, so a medallion prints all black, then each color once:
# ETH = 2 filament changes, USDC = 1 (Austin, 10-26: few changes, colors stick up).
# ETH: 2 layers of grey (the whole logo), then green inside it, shrinking to a point; the grey shows as the outline.
# Blue goes straight up: its strokes are only 1.9 mm wide, any real inset eats them in 2 layers.
RISE = {"grey": (0, 2, 0), "green": (0.4, 8, 0.8), "blue": (0, 6, 0.05)}
DEEP = {"grey": 0, "green": 0, "blue": 0}   # color depth into the face: 0 = sits on top. Others inlay INLAY deep.
# CLAWD stacked (test vs flat, 10-26): 4 layers of white (2 over black looks grey), 2 of red on top.
# The white under the red is pulled in TUCK so the red hangs over it and hides it.
TUCK = 0.4
STACKED = ({"white": (0, 4, 0), "red": (0.8, 2, 0)}, {"white": 0, "red": 0})


def eth_traced(h):
    logo = eth(h)
    inside = logo.offset(-LINE, JoinType.Miter)
    return {"grey": logo, "green": inside}         # grey under the green too, to hold it up


def usdc(d):
    """The USDC logo: two arcs and a dollar sign, d = the arcs' outer diameter."""
    ro = d / 2
    w, gap = d * 0.073, d * 0.125                         # arc width, half the gap top and bottom (from the logo)
    arcs = circle(d) - circle(d - 2 * w) - CrossSection.square([2 * gap, d + 2], center=True)
    arcs = arcs.offset(-w * 0.3, JoinType.Round).offset(w * 0.3, JoinType.Round)   # round the ends
    dollar = text("$", d * 0.39, d * 0.66)
    return {"blue": arcs + dollar}


def clawd(_ow, _oh):
    """The $CLAWD logo, traced by art/trace.py: red and white on the black medallion."""
    data = json.load(open(os.path.join(HERE, "art", "clawd.json")))
    return {c: CrossSection([np.array(p, dtype=float) for p in ps], FillRule.EvenOdd) for c, ps in data.items()}


def clawd_stacked(ow, oh):
    art = clawd(ow, oh)
    under = CrossSection()
    for piece in art["red"].decompose():                  # thin red bits keep full white under them, or they'd float
        tucked = piece.offset(-TUCK, JoinType.Round)
        under = under + (tucked if tucked.area() > 0.5 * piece.area() else piece)
    return {"white": art["white"] + under, "red": art["red"]}


MEDALLIONS = {"eth": lambda ow, oh: eth_traced(min(ow, oh) * 0.62), "usdc": lambda ow, oh: usdc(min(ow, oh) - 3.5), "clawd": clawd,
              "clawd-stacked": clawd_stacked}
STYLE = {"clawd-stacked": STACKED}          # (rise, deep) for medallions that don't use RISE / DEEP


def pit_glue():
    """A drop in each glue pit (render only)."""
    drop = Manifold.sphere(2.2, 32).scale([1, 1, 0.12])
    return sum((drop.translate([x, y, FLOOR - PIT]) for x, y in corners(7, 7)), Manifold())


def glue():
    """A drop on each tab's outer end (render only)."""
    x = TAB_TO - TAB_W / 2
    drop = Manifold.sphere(1.6, 32).scale([1, 1, 0.3])
    return {"glue": drop.translate([x, 0, FLOOR]) + drop.translate([-x, 0, FLOOR])}


def lid(ow, oh, inlays):
    z0, z1 = FLOOR, FLOOR + LID
    body = slab(rrect(FW, FH, FR) - oval(ow, oh), z0, z1)
    keep = rrect(FW - 1.2, FH - 1.2, max(FR - 0.6, 0.3)) - oval(ow + 1.2, oh + 1.2)
    order = ("grey", "red", "green")            # later colors win where they overlap
    cut = {c: inlays[c] ^ keep for c in order if c in inlays}
    parts, taken = {}, CrossSection()
    for i, c in enumerate(order):
        if c not in cut:
            continue
        cs = cut[c]
        for later in order[i + 1:]:
            if later in cut:
                cs = cs - cut[later]
        parts[c] = slab(cs, z1 - INLAY, z1)
        taken = taken + cs
    parts["white"] = body - slab(taken, z1 - INLAY, z1 + 1)
    for c, (layers, inset) in RAISE.items():               # raised colors: the last layers
        if c not in parts:
            continue
        cs = parts[c].slice(z1 - 0.1)
        for k in range(layers):
            if inset:
                cs = cs.offset(-inset, JoinType.Round)
            parts[c] = parts[c] + slab(cs, z1 + 0.2 * k, z1 + 0.2 * (k + 1))
    return parts


if __name__ == "__main__":
    ow, oh, inlays, _, name, note = mix_eth()
    bw, bh = ow - 2 * FIT, oh - 2 * FIT
    keep = rrect(FW - 1.2, FH - 1.2, max(FR - 0.6, 0.3))
    b, l = base(bw, bh, inlays["green"] ^ keep), lid(ow, oh, inlays)

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT3, exist_ok=True)
    save(b["black"], "seven-base-black.stl")                       # floor down
    save_3mf([("black", b["black"])], "seven-base", AT["base"])
    if RAISE:
        lp = {c: x.translate([0, 0, -FLOOR]) for c, x in l.items()}    # face up: raised colors print last
    else:
        lp = {c: face_down(x, FLOOR + LID) for c, x in l.items()}      # face down: flat, smooth face
    for c, x in lp.items():
        save(x, f"seven-lid-{c}.stl")
    save_3mf([(c, lp[c]) for c in ("white", "grey", "green", "red") if c in lp], "seven-lid", AT["lid"])

    designs = []
    for key, art in MEDALLIONS.items():
        m = medallion(bw, bh, art(ow, oh), *STYLE.get(key, ()))
        stem = "seven-medallion" if key == "eth" else f"seven-medallion-{key}"
        mp = {c: x.translate([0, 0, -(FLOOR - SEAT)]) for c, x in m.items()}   # lip down, face up
        for c, x in mp.items():
            save(x, f"{stem}-{c}.stl")
        save_3mf([("black", mp["black"])] + [(c, x) for c, x in mp.items() if c != "black"], stem, AT["medallion"])
        label = {"eth": ("ETH", "ETH logo on top of the black: grey, then green stepped up to a point."),
                 "usdc": ("USDC", "USDC logo in blue on black: two arcs and a dollar sign, sitting 1.2 mm up on the black (one color change)."),
                 "clawd": ("CLAWD", "The $CLAWD logo in red and white on black. Flat, no steps."),
                 "clawd-stacked": ("CLAWD up", "$CLAWD stacked on the black: white, then red on top. The white under the red is tucked in.")}[key]
        designs.append({"name": label[0], "note": label[1], "oval": [ow, oh],
                        "face": {c: pack(x) for c, x in l.items()},
                        "medallion": {c: pack(x) for c, x in dict(m, **glue()).items()}})

    data = {"dims": dict(W=W, H=H, FLOOR=FLOOR, FACE=LID, POCKET=POCKET + SEAT, BORDER=BORDER, CHIP_D=CHIP_D),
            "tray": {c: pack(x) for c, x in dict(b, glue=pit_glue()).items()}, "designs": designs}
    tpl = open(os.path.join(HERE, "seven.tpl.html")).read()
    html = tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    open(os.path.join(HERE, "seven.html"), "w").write(html)
    print(f"seven.html  {len(html) / 1e6:.1f} MB   card {FLOOR + LID:.1f} mm")
