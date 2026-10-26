"""Trace a logo into printable color shapes (mm) for a medallion.

    uv run --with opencv-python-headless --with numpy python art/trace.py

art/clawd.jpg -> art/clawd.json: {color: [polygon, ...]}, polygons in mm, centered, y up. Fill rule: even-odd.
Black in the logo = the medallion itself, so only red and white are traced. Black = dark pixels plus thin lines
darker than what's around them (the smile, the lids: dark red, not black). Lines are thickened and specks dropped
so everything is at least ~0.5 mm, what a 0.4 nozzle can draw.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MM_PER_PX = 0.076           # 400 px logo -> 30 mm: fills the oval, tip and claw just inside
DARK = 100                  # HSV value below this is black
LINE = 60                   # a pixel this much darker than its neighborhood is a line (black-hat)
LINE_GROW = 2               # px added to each side of every black line (3 px lines -> ~0.5 mm). 3 lost the smile
MIN_W = 3                   # px half-width: red/white slivers thinner than ~0.5 mm are dropped
MIN_AREA = 250              # px (~1.2 mm2); smaller specks are dropped
HOLE = 400                  # px (~2 mm2); black specks inside a color smaller than this get filled
SMOOTH = 1.5                # px blur on each shape's edge, so outlines print smooth, not jagged


def disk(n):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * n + 1,) * 2)


def masks(path):
    hsv = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2HSV)
    h, s, v = (hsv[..., i].astype(int) for i in range(3))
    lines = cv2.morphologyEx(hsv[..., 2], cv2.MORPH_BLACKHAT, disk(5)) > LINE
    black = cv2.dilate(((v < DARK) | lines).astype(np.uint8), disk(LINE_GROW)) > 0
    red = ((h < 12) | (h > 165)) & (s > 80) & ~black                        # both reds (lit and shaded)
    white = (((s < 70) & (v > 150)) | ((h >= 12) & (h < 35) & (v > 150))) & ~black   # white, and the tea
    return {c: tidy(m) for c, m in (("red", red), ("white", white))}


def tidy(m):
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, disk(MIN_W))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
    for i in range(1, n):                                   # fill small black specks inside the color
        x, y, w, h, a = stats[i]
        if a < HOLE and x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            m[lab == i] = 1
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), SMOOTH) > 0.5


def polys(mask):
    m = mask.astype(np.uint8) * 255
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < MIN_AREA:
            m[lab == i] = 0
    contours, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    h, w = m.shape
    out = []
    for c in contours:
        c = cv2.approxPolyDP(c, 0.5, True)[:, 0, :]
        if len(c) < 3 or abs(cv2.contourArea(c)) < MIN_AREA / 2:
            continue
        out.append([[round((x - w / 2) * MM_PER_PX, 3), round((h / 2 - y) * MM_PER_PX, 3)] for x, y in c])
    return out


if __name__ == "__main__":
    data = {c: polys(m) for c, m in masks(os.path.join(HERE, "clawd.jpg")).items()}
    json.dump(data, open(os.path.join(HERE, "clawd.json"), "w"), separators=(",", ":"))
    print({c: len(p) for c, p in data.items()})
