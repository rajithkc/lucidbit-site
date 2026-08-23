#!/usr/bin/env python3
"""
Every raster of the LucidBit mark, rendered from one recipe.

    python3 make-logo.py

Writes, at the SITE ROOT — these are the files the pages actually link to:

    favicon.png            96px, referenced by <link rel="icon">
    favicon.ico            16 / 32 / 48, for older browsers and pinned tabs
    apple-touch-icon.png   180px, opaque, for iOS home screens

and in Images/ — referenced by site.webmanifest:

    lucidbit-logo-192.png
    lucidbit-logo-512.png

`favicon.svg` is the source of truth for the mark and stays hand-edited; this
script exists so the rasters can never fall out of step with it.

# A caution about which copies matter

The site has icon files in three places: the root, `Images/`, and a `favicon/`
folder left over from RealFaviconGenerator. Only the ROOT ones are served —
every `<link>` in the HTML points at `/favicon.png`, `/favicon.ico`,
`/apple-touch-icon.png`, and `styles.css` resolves `url('favicon.svg')` against
the root too. The others are copies nothing reads. It is entirely possible to
update the mark, verify it in `Images/`, and ship the old one, because the
duplicates look authoritative and aren't.

# The palette

Three quiet tiles, tints of the brand plum #7851A9 mixed 32 / 46 / 60% toward
white, and one tile in the plum gradient. The quiet tiles are tints rather than
neutral greys so the mark reads as one hue in four steps, with the gradient
tile as the deepest.

They are flat values, not a pale grey faded with opacity. That was the original
construction and it made the mark effectively invisible on the site's own page:
#E5E6F0 at 40% over #FAFAFB composites to about #F7F7FA, a contrast ratio of
1.03:1. Three of the four tiles couldn't be seen, so the logo read as a single
floating purple square.

# Why supersampling

Pillow's rounded_rectangle antialiases poorly at small radii, and these tiles
are drawn at 16px in the favicon. Everything is rendered at 8x and resampled
down with LANCZOS, which is slower and correct, rather than drawn at final size
and left with visibly stepped corners.
"""

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # the served site root
SS = 8                                   # supersample factor

PLUM_HI, PLUM_LO = (0x9B, 0x72, 0xC4), (0x5C, 0x2E, 0x8A)
TILES = [(0xD4, 0xC7, 0xE3), (0xC1, 0xAF, 0xD7), (0xAE, 0x97, 0xCB)]

# Geometry on the 64-unit grid favicon.svg uses: x, y, and which fill.
CELLS = [(2, 2, TILES[0]), (2, 34, TILES[1]), (34, 34, TILES[2])]
PLUM_CELL = (34, 2)
CELL, RADIUS = 28, 5


def mark(px: int) -> Image.Image:
    """The mark, transparent background, `px` square."""
    n = 64 * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x, y):
        return [x * SS, y * SS, (x + CELL) * SS, (y + CELL) * SS]

    for x, y, fill in CELLS:
        d.rounded_rectangle(box(x, y), radius=RADIUS * SS, fill=fill + (255,))

    # The plum cell carries a vertical gradient, so it is painted through a
    # mask of its own rounded rect rather than filled flat.
    grad = Image.new("RGBA", (n, n))
    gd = ImageDraw.Draw(grad)
    y0, y1 = PLUM_CELL[1] * SS, (PLUM_CELL[1] + CELL) * SS
    for y in range(n):
        t = min(1, max(0, (y - y0) / (y1 - y0)))
        gd.line([(0, y), (n, y)],
                fill=tuple(round(a + (b - a) * t)
                           for a, b in zip(PLUM_HI, PLUM_LO)) + (255,))
    cell = Image.new("L", (n, n), 0)
    ImageDraw.Draw(cell).rounded_rectangle(box(*PLUM_CELL),
                                           radius=RADIUS * SS, fill=255)
    img.paste(grad, (0, 0), cell)

    return img.resize((px, px), Image.LANCZOS)


def canvas(px, inset=0, background=None):
    """`inset` pads the mark inward; `background` fills behind it."""
    img = Image.new("RGBA", (px, px),
                    (background + (255,)) if background else (0, 0, 0, 0))
    art = mark(px - inset * 2)
    img.paste(art, (inset, inset), art)
    return img


def write(path: Path, px, inset=0, background=None):
    """
    apple-touch-icon needs both arguments. iOS composites the icon onto its
    own rounded mask and does not honour transparency, so a mark drawn edge to
    edge gets its corners clipped — hence the white plate and the breathing
    room.
    """
    img = canvas(px, inset, background)
    img.convert("RGB" if background else "RGBA").save(path, "PNG", optimize=True)
    print(f"{path.relative_to(ROOT)!s:<30} {px}px")


def write_ico(path: Path):
    """
    Multi-resolution .ico at 16 / 32 / 48.

    Each size is rendered from the vector recipe rather than downsampled from
    one big bitmap. At 16px the tiles are 7 device pixels across with a 1px
    corner radius, and a generic resample turns that into mush — drawing it at
    8x supersample and reducing to exactly 16 keeps the corners readable.
    """
    frames = [canvas(s, inset=max(1, round(s * 0.03))) for s in (48, 32, 16)]
    frames[0].save(path, format="ICO", sizes=[(48, 48), (32, 32), (16, 16)],
                   append_images=frames[1:])
    print(f"{path.relative_to(ROOT)!s:<30} 16/32/48")


if __name__ == "__main__":
    # Served files, at the root. These are the ones that matter.
    write(ROOT / "favicon.png", 96, inset=3)
    write(ROOT / "apple-touch-icon.png", 180, inset=30, background=(255, 255, 255))
    write_ico(ROOT / "favicon.ico")

    # Referenced by site.webmanifest.
    write(HERE / "lucidbit-logo-192.png", 192, inset=6)
    write(HERE / "lucidbit-logo-512.png", 512, inset=16)
