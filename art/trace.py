"""Trace a logo into printable color shapes (mm) for a medallion.

    uv run --with opencv-python-headless --with numpy python art/trace.py

art/clawd.jpg -> art/clawd.json: {color: [polygon, ...]}, polygons in mm, centered, y up. Fill rule: even-odd.
Black in the logo = the medallion itself, so only red and white are traced. Dark lines are thickened so they print.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MM_PER_PX = 0.085           # 400 px logo -> 34 mm, about the medallion's size
LINE_GROW = 2               # px added to each side of every black line (2 px lines -> ~0.5 mm)
MIN_AREA = 40               # px; smaller specks are dropped


def masks(path):
    im = cv2.imread(path)[:, :, ::-1].astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    white = ((r > 175) & (g > 175) & (b > 175)) | ((r > 170) & (g > 140) & (b < 170) & (g > r - 60))
    red = (r > 150) & (r > g + 45) & ~white
    black = ~(red | white)
    grow = cv2.dilate(black.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * LINE_GROW + 1,) * 2))
    return {"red": red & (grow == 0), "white": white & (grow == 0)}


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
