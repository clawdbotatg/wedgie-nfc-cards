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

## #7 Mix ETH, with a seat (seven.py → seven.html, wedgie.dev/dollar/seven)

1.2 mm. Every part has its own place.

| Print | Files | Prints |
|---|---|---|
| Base | `stl/seven-base-black.stl` | floor down |
| Medallion | `3mf/seven-medallion.3mf` (1 black, 2 grey) | tabs down, face up. Iron the top. |
| Lid | `3mf/seven-lid.3mf` (1 white, 2 grey, 3 green, 4 red) | face down |

Build: NFC sticker in its pocket, medallion + tabs in the seat, a drop of PETG super glue on each tab, lid on top.
