"""Dollar-bill card mockups: five face designs, built as real parts, written into dollar.html.

    uv run --with manifold3d --with numpy --with fonttools python dollar.py

Three prints:
  tray     black. Floor + a raised border; the chip pocket is in the floor.
  face     white, sits inside the border, flush with it. Oval hole; a recess under it for the medallion's lip.
           Green / red / grey are 2-layer inlays in its top.
  medallion  the oval piece. Lip under the face, body up through the hole. Swappable, like the old tile.

1.4 mm total (was 1.8).
"""
import base64
import json
import math
import os

import numpy as np
from manifold3d import CrossSection, FillRule

from make import FIT, HERE, INLAY, LIP, R, SEG, SINK, H, W, circle, eth, rrect, slab, text

FLOOR = 0.6                 # tray floor
POCKET = 0.2                # chip pocket in the floor (sticker is ~0.15); leaves 0.4 under it
FACE = 0.8                  # white face, flush with the border
BORDER = 2.5                # black border width
LIP_W = 2.5                 # medallion lip reach under the face
CHIP_D = 25.6

FW, FH = W - 2 * BORDER - 2 * FIT, H - 2 * BORDER - 2 * FIT     # the white face
FR = R - BORDER - FIT


def oval(w, h, x=0.0, y=0.0):
    return CrossSection.circle(1, SEG).scale([w / 2, h / 2]).translate([x, y])


def ring(d, w, x=0.0, y=0.0):
    return circle(d, x, y) - circle(d - 2 * w, x, y)


def oval_ring(ow, oh, w):
    return oval(ow, oh) - oval(ow - 2 * w, oh - 2 * w)


def poly(pts):
    return CrossSection([np.array(pts, dtype=float)], FillRule.NonZero)


def stroke(pts, w):
    """A thin band along a polyline (small slopes only)."""
    top = [(x, y + w / 2) for x, y in pts]
    bot = [(x, y - w / 2) for x, y in reversed(pts)]
    return poly(top + bot)


def wave(x0, x1, y, amp, period, w, phase=0.0):
    n = int((x1 - x0) / 0.4) + 1
    return stroke([(x0 + i * (x1 - x0) / (n - 1), y + amp * math.sin(2 * math.pi * (x0 + i * (x1 - x0) / (n - 1)) / period + phase))
                   for i in range(n)], w)


def seal(d, teeth, depth, x=0.0, y=0.0):
    pts = []
    for i in range(teeth * 2):
        a = math.pi * i / teeth
        r = d / 2 - (depth if i % 2 else 0)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    return poly(pts)


def hline(x0, x1, y, w):
    return CrossSection.square([x1 - x0, w]).translate([x0, y - w / 2])


def corners(dx, dy):
    return [(sx * (FW / 2 - dx), sy * (FH / 2 - dy)) for sx in (-1, 1) for sy in (-1, 1)]


# ---------- the medallion's art

def face_art(ow, oh):
    """A bust: head + shoulders, clipped to the oval."""
    head = oval(ow * 0.42, oh * 0.38, 0, oh * 0.1)
    body = oval(ow * 0.9, oh * 0.55, 0, -oh * 0.42)
    return (head + body) ^ oval(ow - 2 * FIT - 1.6, oh - 2 * FIT - 1.6)


def pyramid_art(ow, oh):
    s = min(ow, oh) * 0.62
    tri = poly([(-s / 2, -s * 0.38), (s / 2, -s * 0.38), (0, s * 0.5)])
    cap = poly([(-s * 0.16, s * 0.23), (s * 0.16, s * 0.23), (0, s * 0.5)])
    rows = [hline(-s, s, -s * 0.38 + k * s * 0.13, 0.5) for k in range(1, 5)]
    body = tri - cap
    for r in rows:
        body = body - r
    eye = oval(s * 0.17, s * 0.09, 0, s * 0.355)
    return {"grey": body, "green": eye}


# ---------- five faces. Each returns (oval w, oval h, {color: inlay}, {color: medallion art}, name, note)

def classic():
    ow, oh = 30, 38
    green = sum((circle(8.5, x, y) for x, y in corners(7, 7)), CrossSection())
    red = circle(6.5, -26, 0) + circle(6.5, 26, 0)
    grey = CrossSection()
    for y in (FH / 2 - 3.0, FH / 2 - 4.8, -(FH / 2 - 3.0), -(FH / 2 - 4.8)):
        grey = grey + hline(-FW / 2 + 13, FW / 2 - 13, y, 0.6)
    return ow, oh, {"green": green, "red": red, "grey": grey}, {"grey": face_art(ow, oh)}, \
        "Classic", "Green corner dots, red dots left and right, grey rules top and bottom. A bust in the oval."


def rosette():
    ow, oh = 44, 30
    green = CrossSection()
    for x, y in corners(7, 7):
        green = green + ring(10, 0.8, x, y) + circle(5, x, y)
    red = circle(6, -33, 0) + circle(6, 33, 0)
    grey = oval_ring(ow + 2 * LIP_W + 3, oh + 2 * LIP_W + 3, 0.6) + oval_ring(ow + 2 * LIP_W + 6, oh + 2 * LIP_W + 6, 0.6)
    return ow, oh, {"green": green, "red": red, "grey": grey}, {"green": eth(22)}, \
        "Rosette", "Wide oval with two engraved grey rings, green rosettes in the corners. ETH in the oval."


def frame():
    ow, oh = 28, 36
    inner = rrect(FW - 4, FH - 4, max(FR - 2, 0.5)) - rrect(FW - 5.2, FH - 5.2, max(FR - 2.6, 0.3))
    green = sum((circle(9, x, y) for x, y in corners(6.5, 6.5)), CrossSection())
    red = circle(7, -24, 0) + circle(7, 24, 0)
    grey = inner
    for k, y in enumerate((-7, -3.5, 0, 3.5, 7)):
        grey = grey + wave(-FW / 2 + 3, -20, y, 0.9, 7, 0.5, k) + wave(20, FW / 2 - 3, y, 0.9, 7, 0.5, k)
    grey = grey - circle(9.6, -24, 0) - circle(9.6, 24, 0)
    return ow, oh, {"green": green, "red": red, "grey": grey}, {"white": text("$", 14, 22)}, \
        "Engraved", "Grey inner frame and wavy guilloche bands behind red dots. A dollar sign in the oval."


def seals():
    ow, oh = 30, 38
    green = sum((circle(7, x, y) for x, y in corners(6, 6)), CrossSection())
    red = seal(13, 24, 1.1, -26, 0) + seal(13, 24, 1.1, 26, 0)
    grey = ring(7.5, 0.6, -26, 0) + ring(7.5, 0.6, 26, 0)
    red = red - circle(8.7, -26, 0) - circle(8.7, 26, 0)
    for y in (FH / 2 - 2.6, -(FH / 2 - 2.6)):
        grey = grey + hline(-FW / 2 + 11, FW / 2 - 11, y, 0.6)
    return ow, oh, {"green": green, "red": red, "grey": grey}, pyramid_art(ow, oh), \
        "Seals", "Red toothed seals like a Treasury seal, small green corners. Pyramid and eye in the oval."


def modern():
    ow, oh = 32, 40
    green = CrossSection()
    for sx in (-1, 1):
        for sy in (-1, 1):
            green = green + circle(16, sx * FW / 2, sy * FH / 2)
    green = green ^ rrect(FW, FH, FR)
    green = green - sum((circle(10.4, sx * FW / 2, sy * FH / 2) for sx in (-1, 1) for sy in (-1, 1)), CrossSection())
    red = rrect(4, 10, 2, -27, 0) + rrect(4, 10, 2, 27, 0)
    grey = rrect(FW - 2.4, FH - 2.4, max(FR - 1.2, 0.5)) - rrect(FW - 3.6, FH - 3.6, max(FR - 1.8, 0.3))
    grey = grey - sum((circle(17.6, sx * FW / 2, sy * FH / 2) for sx in (-1, 1) for sy in (-1, 1)), CrossSection())
    return ow, oh, {"green": green, "red": red, "grey": grey}, {"white": text("1", 9, 20)}, \
        "Modern", "Green quarter-rings in the corners, red bars left and right, one thin grey frame. A big 1 in the oval."


DESIGNS = [classic, rosette, frame, seals, modern]


# ---------- the parts, assembled (z up, face up)

def tray():
    pocket = slab(circle(CHIP_D), FLOOR - POCKET, FLOOR + 1)
    floor = slab(rrect(W, H, R), 0, FLOOR) - pocket
    rim = slab(rrect(W, H, R) - rrect(W - 2 * BORDER, H - 2 * BORDER, R - BORDER), FLOOR, FLOOR + FACE)
    return {"black": floor + rim}


def face(ow, oh, inlays):
    outline = rrect(FW, FH, FR)
    recess = oval(ow + 2 * LIP_W + 2 * FIT, oh + 2 * LIP_W + 2 * FIT)
    hole = oval(ow, oh)
    z0 = FLOOR
    body = slab(outline - recess, z0, z0 + LIP) + slab(outline - hole, z0 + LIP, z0 + FACE)
    keep = rrect(FW - 1.2, FH - 1.2, max(FR - 0.6, 0.3)) - oval(ow + 1.2, oh + 1.2)
    out, taken = {}, CrossSection()
    for c in ("grey", "red", "green"):           # later colors win where they overlap
        cs = inlays.get(c)
        if cs is None or cs.is_empty():
            continue
        cs = cs ^ keep
        out[c] = cs
        taken = taken + cs
    parts = {}
    for i, c in enumerate(("grey", "red", "green")):
        if c not in out:
            continue
        cs = out[c]
        for later in ("grey", "red", "green")[i + 1:]:
            if later in out:
                cs = cs - out[later]
        parts[c] = slab(cs, z0 + FACE - INLAY, z0 + FACE)
    parts["white"] = body - slab(taken, z0 + FACE - INLAY, z0 + FACE + 1)
    return parts


def medallion(ow, oh, art):
    bw, bh = ow - 2 * FIT, oh - 2 * FIT
    top = FLOOR + FACE - SINK
    body = slab(oval(bw + 2 * LIP_W, bh + 2 * LIP_W), FLOOR, FLOOR + LIP) + slab(oval(bw, bh), FLOOR + LIP, top)
    parts, taken = {}, CrossSection()
    for c, cs in art.items():
        cs = cs ^ oval(bw - 1.0, bh - 1.0)
        parts[c] = slab(cs, top - INLAY, top)
        taken = taken + cs
    parts["black"] = body - slab(taken, top - INLAY, top + 1)
    return parts


def pack(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts).astype(np.uint32)
    return {"v": base64.b64encode(v.tobytes()).decode(), "i": base64.b64encode(t.tobytes()).decode()}


if __name__ == "__main__":
    data = {"dims": dict(W=W, H=H, FLOOR=FLOOR, FACE=FACE, POCKET=POCKET, BORDER=BORDER, CHIP_D=CHIP_D, LIP=LIP, SINK=SINK),
            "tray": {c: pack(m) for c, m in tray().items()}, "designs": []}
    for d in DESIGNS:
        ow, oh, inlays, art, name, note = d()
        f, med = face(ow, oh, inlays), medallion(ow, oh, art)
        tris = sum(len(m.to_mesh().tri_verts) for m in list(f.values()) + list(med.values()))
        print(f"{name:10s} oval {ow}x{oh}  {tris} tris  face colors: {', '.join(f)}  medallion: {', '.join(med)}")
        data["designs"].append({"name": name, "note": note, "oval": [ow, oh],
                                "face": {c: pack(m) for c, m in f.items()},
                                "medallion": {c: pack(m) for c, m in med.items()}})
    tpl = open(os.path.join(HERE, "dollar.tpl.html")).read()
    html = tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    open(os.path.join(HERE, "dollar.html"), "w").write(html)
    print(f"dollar.html  {len(html) / 1e6:.1f} MB")
