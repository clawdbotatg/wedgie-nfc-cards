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

from manifold3d import CrossSection, JoinType, Manifold

from dollar import BORDER, CHIP_D, mix_eth, oval, pack
from make import FIT, HERE, INLAY, OUT, OUT3, H, R, W, circle, eth, face_down, rrect, save, save_3mf, slab

FLOOR = 0.8                 # base floor
SEAT = 0.4                  # seat depth = medallion lip + tab thickness
POCKET = 0.2                # NFC pocket, under the seat; leaves 0.2 under the sticker
LID = 0.8                   # white lid, flush with the border
GAP = 0.1                   # lid to border, each side
FW, FH = W - 2 * BORDER - 2 * GAP, H - 2 * BORDER - 2 * GAP
FR = R - BORDER - GAP
LIP_W = 2.0                 # medallion lip reach past the oval
TAB_W, TAB_TO = 6.0, 23.0   # tabs: width, and how far out they reach from the center (each side)


def medallion_outline(bw, bh):
    lip = oval(bw + 2 * LIP_W, bh + 2 * LIP_W)
    tabs = rrect(2 * TAB_TO, TAB_W, TAB_W / 2)
    return lip + tabs


def base(bw, bh):
    floor = slab(rrect(W, H, R), 0, FLOOR)
    seat = slab(medallion_outline(bw, bh).offset(FIT), FLOOR - SEAT, FLOOR + 1)
    pocket = slab(circle(CHIP_D), FLOOR - SEAT - POCKET, FLOOR + 1)
    rim = slab(rrect(W, H, R) - rrect(W - 2 * BORDER, H - 2 * BORDER, R - BORDER), FLOOR, FLOOR + LID)
    return {"black": floor - seat - pocket + rim}


def medallion(bw, bh, art):
    top = FLOOR + LID
    body = slab(medallion_outline(bw, bh), FLOOR - SEAT, FLOOR) + slab(oval(bw, bh), FLOOR - SEAT, top)
    parts, taken = {}, CrossSection()
    for c, cs in art.items():
        cs = cs ^ oval(bw - 1.0, bh - 1.0)
        parts[c] = slab(cs, top - INLAY, top)
        taken = taken + cs
    parts["black"] = body - slab(taken, top - INLAY, top + 1)
    return parts


LINE = 0.6                  # grey line width of the traced ETH logo


def eth_traced(h):
    logo = eth(h)
    inside = logo.offset(-LINE, JoinType.Miter)
    return {"grey": logo - inside, "green": inside}


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
    return parts


if __name__ == "__main__":
    ow, oh, inlays, _, name, note = mix_eth()
    art = eth_traced(min(ow, oh) * 0.62)
    note = note.replace("ETH diamond", "ETH logo, grey outline, green inside")
    bw, bh = ow - 2 * FIT, oh - 2 * FIT
    b, m, l = base(bw, bh), medallion(bw, bh, art), lid(ow, oh, inlays)

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT3, exist_ok=True)
    save(b["black"], "seven-base-black.stl")                       # floor down
    mp = {c: x.translate([0, 0, -(FLOOR - SEAT)]) for c, x in m.items()}   # lip down, face up
    for c, x in mp.items():
        save(x, f"seven-medallion-{c}.stl")
    save_3mf([("black", mp["black"])] + [(c, x) for c, x in mp.items() if c != "black"], "seven-medallion")
    lp = {c: face_down(x, FLOOR + LID) for c, x in l.items()}      # face down
    for c, x in lp.items():
        save(x, f"seven-lid-{c}.stl")
    save_3mf([(c, lp[c]) for c in ("white", "grey", "green", "red") if c in lp], "seven-lid")

    m_render = dict(m, **glue())
    data = {"dims": dict(W=W, H=H, FLOOR=FLOOR, FACE=LID, POCKET=POCKET + SEAT, BORDER=BORDER, CHIP_D=CHIP_D),
            "tray": {c: pack(x) for c, x in b.items()},
            "designs": [{"name": "#7 Mix ETH", "note": note, "oval": [ow, oh],
                         "face": {c: pack(x) for c, x in l.items()},
                         "medallion": {c: pack(x) for c, x in m_render.items()}}]}
    tpl = open(os.path.join(HERE, "seven.tpl.html")).read()
    html = tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    open(os.path.join(HERE, "seven.html"), "w").write(html)
    print(f"seven.html  {len(html) / 1e6:.1f} MB   card {FLOOR + LID:.1f} mm")
