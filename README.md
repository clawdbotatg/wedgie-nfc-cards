# Dollar NFC card (the one we make)

A 3D-printed card that looks like a dollar bill, with an NTAG215 NFC sticker (Ø25 mm) inside.
Three prints per card: base, medallion (the swappable logo), lid. 3D view: wedgie.dev/dollar/seven (`seven.html`).

## Make it

1. Change anything in `seven.py` (sizes at the top), then build:
   `uv run --with manifold3d --with numpy --with fonttools python seven.py`
   It writes the print files (`3mf/seven-*`, `stl/seven-*`) and `seven.html`.
2. New logo for a medallion: drop the image in `art/`, trace it with
   `uv run --with opencv-python-headless --with numpy python art/trace.py` (edit the file name and colors in it),
   add it to `MEDALLIONS` in `seven.py`.
3. Update the website: copy `seven.html` into `wedgie-dev/public/dollar/seven.html` with the three.js URLs
   pointed at `/dollar/three.min.js` and `/dollar/OrbitControls.js` (the site blocks outside scripts), push wedgie-dev.
4. Print: POST each 3MF to the print Mac inbox, `http://GriffithRobots-Mac-mini.local:8800/drop`
   (`-F file=@… -F from=… -F notes=…`). It plans the plates.

## Prints

PLA, 0.2 mm layers, no supports. About 6 per plate, away from the bed's hot center and its edges.

| Print | File | Colors (filament order) | Prints |
|---|---|---|---|
| Base | `3mf/seven-base.3mf` | 1 black | floor down |
| Lid | `3mf/seven-lid.3mf` | 1 white, 2 grey, 3 green, 4 red | face down. Flat face |
| ETH medallion | `3mf/seven-medallion.3mf` | 1 black, 2 grey, 3 green | tabs down, face up. Green steps up 0.8 mm |
| USDC medallion | `3mf/seven-medallion-usdc.3mf` | 1 black, 2 blue | tabs down, face up. Blue steps up 0.6 mm |
| CLAWD medallion | `3mf/seven-medallion-clawd.3mf` | 1 black, 2 red, 3 white | tabs down, face up |

## Build a card

1. NFC sticker into the pocket in the base.
2. Medallion over it, its tabs in the seat.
3. A drop of PETG super glue on each tab, and in the 4 corner pits.
4. Lid on top, inside the black border. Press.

## What we learned (don't undo)

- 2.0 mm total. Thinner tore: one layer under the chip ripped coming off the bed. At least 3 layers (0.6) anywhere a part peels off the bed.
- Keep prints off the bed center (the 3MFs are placed off center). Parts stuck hard there.
- Pry notches (first layer left out) at the base's ends and the medallion's top and bottom, to get a blade under.
- The medallion sits in a seat in the base, so nothing floats. 1.5 mm glue room around each tab.
- Glue pits in the base sit exactly under the lid's green circles, so glue only tints green.
- The lid prints face down, flat. Raised colors (face up) looked worse: uneven. `RAISE` in `seven.py` brings them back.

## Production run (sent 2026-10-24)

10 ETH + 10 USDC cards: 20 bases, 20 lids, 10 ETH medallions, 10 USDC medallions. CLAWD medallion: file ready, count not set.

---

# Older work

# wedgie NFC card

A business-card wedgie with an NTAG215 sticker (Ø25 mm) inside. Three prints, PLA, 0.2 mm layers
(first layer 0.2 too: the colors are 2 layers deep). 1.8 mm thick when glued. No supports.

| Print | Files | Colors | Prints |
|---|---|---|---|
| Back | `stl/back-black.stl` | black | outside face down, chip pocket up |
| Tile (the screen) | `3mf/tile-<5,10,20,eth>.3mf` or `stl/tile-*-black/color.stl` | 1 black, 2 white (eth: blue) | lip down, face up. Iron the top. |
| Front | `3mf/front.3mf` or `stl/front-white/grey/green/red.stl` | 1 white, 2 grey, 3 green, 4 red | face down |

The 3MFs hold each multi-color part as one object, one filament per color, in the order above.
Not yet checked in a slicer: confirm the preview shows the colors before printing.
The STLs are the same parts, one file per color, already in place: load them together as one object.

Build: sticker into the back's pocket, tile on top, front over it (its recess holds the tile's lip).
A few drops of glue between back and front.

Not tested yet: the 0.15 mm fit, and the pocket depth (0.4 mm) against a real sticker.

Change sizes or add a tile: `make.py`, then
`uv run --with manifold3d --with numpy --with fonttools python make.py`.

3D preview: open `preview.html` (shows the older 1.6 mm version).

## Dollar version

`dollar.html` (live at wedgie.dev/dollar): eleven dollar-bill face designs in 3D. Made by `dollar.py`
(same `uv run` line as above).

Picked: #11 Ringed. 1.0 mm. Print files:

| Print | Files | Prints |
|---|---|---|
| Back | `stl/dollar-tray-black.stl` | floor down |
| Face | `3mf/dollar-ringed-face.3mf` (1 white, 2 grey, 3 green, 4 red) | face down |
| Oval (swappable) | `3mf/dollar-ringed-medallion.3mf` (1 black, 2 grey, 3 green) | lip down, face up. Iron the top. |

Build: sticker in the back's pocket, oval piece over it, press the face into the border. No glue.
Swap: push the face out through the hole in the back.

Not tested: the press fit (0.05 mm gap, `PRESS` in `dollar.py`), the single-layer lip and floor under the chip.
