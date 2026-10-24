"""The wedgie NFC card: STLs for the three prints.

    uv run --with manifold3d --with numpy --with fonttools python make.py

Every part comes out the way it prints, no supports. A part with more than one color is one STL
per color, all in the same place, plus a 3MF that already holds them as one object with a
filament per color (3mf/).
"""
import os
import struct
import zipfile

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, JoinType, Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")
OUT3 = os.path.join(HERE, "3mf")

# mm. US business card. 0.2 mm layers.
W, H, R = 88.9, 50.8, 5.0
BACK = 0.8                  # black plate (the chip pocket leaves 0.4 under the chip)
FRONT = 1.0                 # white plate
LIP = 0.4                   # the tile's lip, and the recess for it under the front
SINK = 0.2                  # tile face sits this far under the front face
INLAY = 0.4                 # color depth in a face (2 layers)
FIT = 0.15                  # gap on every side that slides into something
LIP_W = 2.5                 # how far the lip reaches under the front
CHIP_D, POCKET = 25.6, 0.4  # NTAG215 sticker is 25 mm; its pocket is in the back

# the real wedgie lid turned sideways and scaled 1.52x
SCREEN = dict(x=-0.2, y=-0.4, w=40.2, h=38.3, r=1.6)       # the hole in the front
STICK = dict(x=-30.6, y=0.0, ring=15.2, ring_w=1.0, cap=10.6)
BTN = dict(x=33.4, w=8.6, h=6.6, r=1.9, rows=[(13.0, "green"), (4.36, "grey"), (-4.13, "grey"), (-12.8, "red")])

SEG = 96


def rrect(w, h, r, x=0.0, y=0.0):
    return CrossSection.square([w - 2 * r, h - 2 * r], center=True).offset(r, JoinType.Round, 2.0, SEG).translate([x, y])


def circle(d, x=0.0, y=0.0):
    return CrossSection.circle(d / 2, SEG).translate([x, y])


def slab(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def face_down(m, top):
    """Turn a part built face up (face at z=top) onto its face."""
    return m.rotate([180, 0, 0]).translate([0, 0, top])


def save(m, name):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(b"wedgie card".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        for a, b, c in t:
            p, q, s = v[a], v[b], v[c]
            n = np.cross(q - p, s - p)
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *p, *q, *s, 0))
    lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
    print(f"{name:24s} {len(t):6d} tris  {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.2f} mm")


def save_3mf(parts, name, at=(128, 128)):
    """One object, one part per color, each part on its own filament (1, 2, ...), the order given.
    Bambu Studio's own layout, so the CLI slices it with no GUI."""
    objs, comps, cfg = [], [], []
    for i, (color, m) in enumerate(parts, 1):
        mesh = m.to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3]
        t = np.asarray(mesh.tri_verts)
        vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
        objs.append(f'<object id="{i}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
        comps.append(f'<component objectid="{i}"/>')
        cfg.append(f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{color}"/><metadata key="extruder" value="{i}"/></part>')
    top = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
             '<metadata name="Application">BambuStudio-02.07.01.62</metadata><metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<resources>{"".join(objs)}<object id="{top}" type="model"><components>{"".join(comps)}</components></object></resources>'
             f'<build><item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 {at[0]} {at[1]} 0" printable="1"/></build></model>')
    settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                f'<object id="{top}"><metadata key="name" value="{name}"/><metadata key="extruder" value="1"/>{"".join(cfg)}</object>'
                '</config>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    path = os.path.join(OUT3, f"{name}.3mf")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", settings)
    print(f"{name + '.3mf':24s} filaments: " + ", ".join(f"{i}={c}" for i, (c, _) in enumerate(parts, 1)))


# ---------- text and logos as 2D shapes

class Flat(BasePen):
    """Glyph outlines to polygons."""
    def __init__(self, gs):
        super().__init__(gs)
        self.polys, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 11):
            t = i / 10
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


def text(s, max_w, max_h, x=0.0, y=0.0):
    font = TTFont(os.path.join(HERE, "Nunito-Black.ttf"))
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    polys, pen_x = [], 0
    for ch in s:
        g = cmap[ord(ch)]
        pen = Flat(gs)
        gs[g].draw(pen)
        polys += [[(px + pen_x, py) for px, py in p] for p in pen.polys]
        pen_x += hmtx[g][0]
    cs = CrossSection([np.array(p, dtype=float) for p in polys], FillRule.NonZero)
    lo, hi = cs.bounds()[:2], cs.bounds()[2:]
    k = min(max_w / (hi[0] - lo[0]), max_h / (hi[1] - lo[1]))
    return cs.translate([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2]).scale([k, k]).translate([x, y])


def eth(h, x=0.0, y=0.0):
    """The Ethereum diamond: top and bottom, with the gap between them (official 256 x 417 drawing)."""
    top = [(128, 0), (0, 212.3), (128, 288), (256, 212.3)]
    bot = [(128, 312.2), (0, 236.6), (128, 416.9), (256, 236.6)]
    cs = CrossSection([np.array([(px - 128, 208.45 - py) for px, py in p], dtype=float) for p in (top, bot)], FillRule.NonZero)
    k = h / 416.9
    return cs.scale([k, k]).translate([x, y])


# ---------- the parts

def back():
    """Prints outside face down; the chip pocket opens up."""
    pocket = slab(circle(CHIP_D, SCREEN["x"], SCREEN["y"]), BACK - POCKET, BACK + 1)
    return {"black": slab(rrect(W, H, R), 0, BACK) - pocket}


def front():
    sx, sy = SCREEN["x"], SCREEN["y"]
    tw, th = SCREEN["w"] - 2 * FIT, SCREEN["h"] - 2 * FIT
    recess = rrect(tw + 2 * LIP_W + 2 * FIT, th + 2 * LIP_W + 2 * FIT, SCREEN["r"] + LIP_W + FIT, sx, sy)
    hole = rrect(SCREEN["w"], SCREEN["h"], SCREEN["r"], sx, sy)
    body = slab(rrect(W, H, R) - recess, 0, LIP) + slab(rrect(W, H, R) - hole, LIP, FRONT)

    colors = {"grey": None, "green": None, "red": None}
    def add(c, cs):
        colors[c] = cs if colors[c] is None else colors[c] + cs
    for y, c in BTN["rows"]:
        add(c, rrect(BTN["w"], BTN["h"], BTN["r"], BTN["x"], y))
    ring = circle(STICK["ring"], STICK["x"], STICK["y"]) - circle(STICK["ring"] - 2 * STICK["ring_w"], STICK["x"], STICK["y"])
    add("grey", ring + circle(STICK["cap"], STICK["x"], STICK["y"]))

    out = {}
    for c, cs in colors.items():
        out[c] = slab(cs, FRONT - INLAY, FRONT)
        body = body - out[c]
    out["white"] = body
    return {c: face_down(m, FRONT) for c, m in out.items()}


def tile(art):
    """The screen. Lip under the front, block up through the hole. Prints lip down, face up
    (face down, the lip would hang 2.5 mm in the air). Face = the last 2 layers: iron it."""
    tw, th = SCREEN["w"] - 2 * FIT, SCREEN["h"] - 2 * FIT
    top = FRONT - SINK
    body = slab(rrect(tw + 2 * LIP_W, th + 2 * LIP_W, SCREEN["r"] + LIP_W), 0, LIP) + slab(rrect(tw, th, SCREEN["r"] - FIT), LIP, top)
    color = slab(art, top - INLAY, top)
    return {"black": body - color, "color": color}


TILES = {
    "5": lambda: text("$5", 30, 22),
    "10": lambda: text("$10", 32, 20),
    "20": lambda: text("$20", 32, 20),
    "eth": lambda: eth(30),
}


TILE_COLOR = {"5": "white", "10": "white", "20": "white", "eth": "blue"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT3, exist_ok=True)
    for c, m in back().items():
        save(m, f"back-{c}.stl")
    f = front()
    for c, m in f.items():
        save(m, f"front-{c}.stl")
    save_3mf([(c, f[c]) for c in ("white", "grey", "green", "red")], "front")
    for name, art in TILES.items():
        t = tile(art())
        for c, m in t.items():
            save(m, f"tile-{name}-{c}.stl")
        save_3mf([("black", t["black"]), (TILE_COLOR[name], t["color"])], f"tile-{name}")
