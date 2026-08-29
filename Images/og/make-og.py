#!/usr/bin/env python3
"""
Open Graph cards for every LucidBit app, in one house style.

    python3 make-og.py             # all six
    python3 make-og.py peekpaste   # just one

# What this makes

PeekFocus's typography on Tesserac's dark ground:

    • serif wordmark, large, left-aligned beside the icon
    • one line beneath it — the app's own subtitle
    • "LucidBit" small, bottom right
    • dark gradient background, washed with the app's accent colour

# Where the words come from

`index.html`, parsed at run time — the app name and the `card-sub` line from
each card, plus the accent from its `--card-accent` custom property. Nothing is
duplicated here, so the cards can't drift from the site: change a subtitle on
the index page, run this, and the social card agrees with it.

# Typefaces

Fonts live in `fonts/` next to this script and are committed with the repo, so
the cards render identically on any machine. They are NOT looked up in system
font directories — that would make the output depend on what each machine
happens to have installed, and deploy.sh reads "the generator changed a file"
as a stale-asset error, so a machine-dependent font would fail every deploy.

The site itself sets headings in Cormorant and everything else in Outfit, both
served from Google's CDN rather than installed locally. The vendored fallbacks
are Lora (serif) and Poppins (geometric sans), the closest equivalents to hand.
Drop `Cormorant-Light.ttf` and `Outfit-Regular.ttf` into `fonts/` and the cards
switch to the real brand faces with no code change — see FACES below.

# Sizes are cap heights, not point sizes

Point size is a container, not a measurement — two faces at 72pt print letters
of visibly different heights. The layout below was measured off the rendered
PeekFocus card, so it's matched in the same terms and holds whichever font is
actually available.
"""

from pathlib import Path
import html
import re

from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE   = Path(__file__).resolve().parent
IMAGES = HERE.parent
SITE   = IMAGES.parent
W, H   = 1200, 630

# ── Layout, measured from og-peekfocus.png ───────────────────────────────────
ICON      = (124, 251 - 90, 310)     # x, y, size — lifted to centre the block
TEXT_X    = 503
NAME_TOP  = 205                      # top of the wordmark's cap band
NAME_CAP  = 74
SUB_TOP   = 325
SUB_CAP   = 20
MARK      = (1140, 566, 18)          # right edge, cap top, cap height

# ── Dark ground, from og-tesserac.png ────────────────────────────────────────
BG_TOP    = (14, 29, 55)
BG_BOTTOM = (4, 12, 22)
NAME_INK  = (238, 240, 246)

# ── LucidBit ─────────────────────────────────────────────────────────────────
# "Bit" is the brand plum. #7851A9 is the value the site uses on its white
# pages; against this dark ground it goes muddy, so the mark takes the light
# stop of the logo's own gradient instead — same hue, enough luminance to read.
MARK_INK   = (208, 212, 224)
BRAND_PLUM = (155, 114, 196)
# The mark's three quiet tiles, matching favicon.svg exactly.
MARK_TILES = [(0xD4, 0xC7, 0xE3), (0xC1, 0xAF, 0xD7), (0xAE, 0x97, 0xCB)]

ICONS = {
    "peekpaste":   "PeekPaste/Icon-macOS-Default-1024x1024@1x.webp",
    "displaydial": "DisplayDial/Icon-macOS-Dark-1024x1024@1x.webp",
    "tesserac":    "Tesserac/Icon-macOS-Default-1024x1024@1x.webp",
    "peekfocus":   "PeekFocus/Icon-macOS-Default-1024x1024@1x.webp",
    "activestat":  "ActiveStat/Icon-iOS-Dark-1024x1024@1x.webp",
    "gentlelimit": "GentleLimit/Icon-macOS-Default-1024x1024@1x.webp",
}


def apps() -> dict:
    """Name, subtitle and accent for each app, read from the index page."""
    t = (SITE / "index.html").read_text()
    # The site's own card, in the same house style as the app cards. It has no
    # product icon, so the logo mark stands in for one, and it skips the
    # bottom-right lockup — the name IS the lockup here.
    found = {}
    for m in re.finditer(r'app-card app-card-(\w+)[^>]*href="([^"]+)"(.*?)</a>', t, re.S):
        colour, href, body = m.groups()
        accent = re.search(rf'\.app-card-{colour}\s*{{ --card-accent: (#\w{{6}})', t)
        found[href.split("/")[0].lower()] = dict(
            name=re.search(r'card-name">(.*?)<', body).group(1),
            sub=html.unescape(re.search(r'card-sub">(.*?)<', body).group(1)),
            accent=tuple(int(accent.group(1)[i:i + 2], 16) for i in (1, 3, 5)),
        )
    return found


FONTS = HERE / "fonts"

# Faces are looked up in order and the first one present wins. The vendored
# files in fonts/ are last-resort fallbacks that ship with the repo; drop the
# site's real Cormorant and Outfit alongside them and the cards upgrade to the
# actual brand faces with no code change.
FACES = {
    "serif":       ["Cormorant-Light.ttf", "Cormorant-Regular.ttf",
                    "Lora-Variable.ttf"],
    "sans":        ["Outfit-Regular.ttf", "Poppins-Regular.ttf"],
    "sans-medium": ["Outfit-Medium.ttf", "Poppins-Medium.ttf"],
}


def font(kind: str, cap_height: int) -> ImageFont.FreeTypeFont:
    """
    A face at a given CAP HEIGHT, resolved from fonts/ next to this script.

    Fonts are vendored rather than looked up in system directories on purpose.
    An earlier version searched /usr/share/fonts, which meant the script only
    ran on Linux — and worse, would have produced different cards on different
    machines depending on what happened to be installed. deploy.sh treats "the
    generator changed a file" as a stale-asset error, so a font that varies by
    machine turns every deploy into a false alarm. Shipping the exact files
    makes the output byte-identical anywhere.
    """
    for name in FACES[kind]:
        p = FONTS / name
        if p.exists():
            path = str(p)
            break
    else:
        raise SystemExit(
            f"No '{kind}' font found. Looked for {', '.join(FACES[kind])} "
            f"in {FONTS}.\nThe repo ships fallbacks there — if they are "
            f"missing, restore them from git."
        )

    size = cap_height * 2
    for _ in range(24):
        f = ImageFont.truetype(path, size)
        box = f.getbbox("H")
        actual = box[3] - box[1]
        if abs(actual - cap_height) <= 1:
            return f
        size = max(8, round(size * cap_height / max(actual, 1)))
    return ImageFont.truetype(path, size)


def legible(rgb, floor=0.62, ceiling=0.80):
    """
    Nudge an accent to a usable brightness for small text on the dark ground.

    Six accents span a wide luminance range — ActiveStat's lime is naturally
    bright, DisplayDial's muted violet is not — so setting the subtitle to the
    raw accent gives one card a shouting line and another a line that fades
    into the background. This mixes toward white when a colour is too dark and
    toward black when it's too bright, leaving hue alone, so the six cards read
    as one family with six tints rather than six different emphases.
    """
    r, g, b = (c / 255 for c in rgb)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if lum < floor:
        t = (floor - lum) / (1 - lum)
        r, g, b = (c + (1 - c) * t for c in (r, g, b))
    elif lum > ceiling:
        t = ceiling / lum
        r, g, b = (c * t for c in (r, g, b))
    return tuple(round(c * 255) for c in (r, g, b))


def ink_left(f: ImageFont.FreeTypeFont, text: str) -> float:
    """
    How far the first visible pixel sits from the drawing origin.

    Measured by rendering, not asked of the font. `getbbox` reports the
    outline's advance-space box, which for these faces comes back as 0 even
    when the rendered stem plainly starts a few pixels in — antialiasing and
    hinting move the first lit pixel. Rendering once and looking is cheap
    (a handful of small bitmaps per card) and it can't disagree with the
    output, because it IS the output.
    """
    pad = 40
    probe = Image.new("L", (round(f.getlength(text)) + pad * 2, pad * 4), 0)
    ImageDraw.Draw(probe).text((pad, pad), text, font=f, fill=255)
    cols = probe.getbbox()
    return (cols[0] - pad) if cols else 0.0


def draw_cap(d, xy, text, f, fill, anchor_right=False, tracking=0, optical=True):
    """
    Draw text with the cap TOP at y and its INK left edge at x.

    Two corrections, both about the gap between what a font measures and what
    an eye sees:

    · Vertical — the drawing origin is the ascender line, which sits above the
      capitals by an amount that differs per face. Subtracting the "H" bbox top
      pins the capitals themselves to y, so a serif wordmark and a sans
      subtitle set to the same y actually line up.

    · Horizontal — every glyph carries a left side bearing, and it differs by
      letter. Drawing "DisplayDial" and "DISPLAY CONTROL" at the same x leaves
      their visible left edges a few pixels apart, and at this size that reads
      as a wobble in the left margin. Subtracting the first glyph's bearing
      aligns the ink instead of the origin.
    """
    x, y = xy
    y -= f.getbbox("H")[1]
    if optical and text:
        x -= ink_left(f, text)

    if tracking:
        if anchor_right:
            x -= sum(f.getlength(c) + tracking for c in text) - tracking
        for ch in text:
            d.text((x, y), ch, font=f, fill=fill)
            x += f.getlength(ch) + tracking
        return

    d.text((x, y), text, font=f, fill=fill,
           anchor="ra" if anchor_right else "la")


def rounded_tile(d, box, radius, fill):
    d.rounded_rectangle(box, radius=radius, fill=fill)


def draw_mark(d, x, y, size, plate=None):
    """
    The 2x2 logo mark: three quiet tiles and one plum, matching favicon.svg.

    `plate` optionally draws a squircle behind it, the way an app icon has a
    rounded container. Without one the four tiles float, and a floating mark
    has no silhouette — it reads as scattered shapes rather than one object.
    """
    if plate:
        d.rounded_rectangle([x, y, x + size, y + size],
                            radius=round(size * 0.225), fill=plate)
        inset = size * 0.20
        x, y, size = x + inset, y + inset, size - inset * 2

    unit = size / 2
    pad = max(0.6, unit * 0.06)
    r = max(1, round(unit * 0.28))
    for col, row, colour in [(0, 0, MARK_TILES[0]), (0, 1, MARK_TILES[1]),
                             (1, 1, MARK_TILES[2]), (1, 0, BRAND_PLUM)]:
        x0, y0 = x + col * unit + pad, y + row * unit + pad
        d.rounded_rectangle([x0, y0, x0 + unit - 2 * pad, y0 + unit - 2 * pad],
                            radius=r, fill=colour)


def draw_lucidbit(img, right_x, cap_top, cap_height):
    """
    The signature: "Lucid" in light ink, "Bit" in brand plum — the same split
    the site's nav and footer use.

    Wordmark only. The mark is deliberately absent: on an app card the product
    icon is already the subject, and repeating a second icon in the corner
    gives the eye two things claiming to be the logo. The words alone are
    unambiguous and stay out of the way.
    """
    d = ImageDraw.Draw(img)
    f = font("sans-medium", cap_height)
    top = cap_top - f.getbbox("H")[1]
    x = right_x - (f.getlength("Lucid") + f.getlength("Bit"))
    d.text((x, top), "Lucid", font=f, fill=MARK_INK)
    d.text((x + f.getlength("Lucid"), top), "Bit", font=f, fill=BRAND_PLUM)


def ground(accent, centre=(270, 340)) -> Image.Image:
    """Dark gradient, washed with a blurred accent glow at `centre`."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))

    # The accent as a wash rather than a shape — an ellipse blurred until it
    # has no edge. It's what makes cards on the same dark ground still look
    # like different apps.
    cx, cy = centre
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - 390, cy - 300, cx + 390, cy + 300],
                                 fill=tuple(round(c * 0.42) for c in accent))
    return Image.blend(img, glow.filter(ImageFilter.GaussianBlur(150)), 0.55)


def build(key: str, spec: dict) -> Path:
    img = ground(spec["accent"])
    d = ImageDraw.Draw(img)

    x, y, size = ICON
    icon_path = IMAGES / ICONS[key] if key in ICONS else None
    if icon_path and icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((size, size), Image.LANCZOS)
        # A shadow under the icon, so it sits ON the card rather than in it.
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow.paste((0, 0, 0, 150), (x + 6, y + 18, x + size + 6, y + size + 18),
                     icon.split()[3])
        shadow = shadow.filter(ImageFilter.GaussianBlur(26))
        img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
        img.paste(icon, (x, y), icon)
        d = ImageDraw.Draw(img)

    name_font = font("serif", NAME_CAP)
    if spec["name"] == "LucidBit":
        # The brand card splits its own wordmark the way the nav and footer do.
        draw_cap(d, (TEXT_X, NAME_TOP), "Lucid", name_font, NAME_INK)
        d.text((TEXT_X - ink_left(name_font, "Lucid") + name_font.getlength("Lucid"),
                NAME_TOP - name_font.getbbox("H")[1]),
               "Bit", font=name_font, fill=BRAND_PLUM)
    else:
        draw_cap(d, (TEXT_X, NAME_TOP), spec["name"], name_font, NAME_INK)

    # Subtitles are already uppercase on four of the six cards; the other two
    # are title case. Uppercasing here makes the set consistent without
    # editing the index page, and tracking is what stops uppercase at this
    # size from reading as a shout.
    draw_cap(d, (TEXT_X, SUB_TOP), spec["sub"].upper(),
             font("sans-medium", SUB_CAP), legible(spec["accent"]), tracking=2.4)

    if spec.get("signature", True):
        draw_lucidbit(img, *MARK)

    out = HERE / f"og-{key}.png"
    img.save(out, "PNG", optimize=True)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# The brand card
#
# It is NOT the app-card template with the logo dropped into the icon slot, and
# the reason is worth stating: an app icon arrives with a squircle around it.
# The container gives it mass, an edge and a shadow, so it reads as one object
# sitting on the card. The bare 2x2 mark has none of that — blown up to 310px
# it's four pale rectangles floating in space, which looks like a placeholder.
#
# The studios that do this well — Linear, Things, Panic, Raycast — all invert
# the hierarchy on their brand card. On a product card the icon is the subject.
# On the brand card the SENTENCE is the subject, and the mark shrinks to the
# size of a signature. That's the move; the three layouts below are three ways
# of making it.
# ─────────────────────────────────────────────────────────────────────────────

TAGLINE = "Every pixel earns its place."
BRAND_VARIANT = "depth"   # which layout og-lucidbit.png uses

# Order matters — this is the shelf, left to right.
SHELF = ["peekpaste", "tesserac", "peekfocus", "displaydial",
         "activestat", "gentlelimit"]


def draw_wordmark(d, x, cap_top, cap_height, centred=False):
    """LucidBit in serif, "Bit" in plum. Returns the width drawn."""
    f = font("serif", cap_height)
    w = f.getlength("Lucid") + f.getlength("Bit")
    if centred:
        x -= w / 2
    else:
        x -= ink_left(f, "Lucid")
    top = cap_top - f.getbbox("H")[1]
    d.text((x, top), "Lucid", font=f, fill=NAME_INK)
    d.text((x + f.getlength("Lucid"), top), "Bit", font=f, fill=BRAND_PLUM)
    return w


def brand_card(variant: str = "shelf") -> Path:
    accent = (120, 81, 169)
    centre = {"statement": (330, 250), "centred": (600, 315),
              "plate": (270, 340), "shelf": (600, 250),
              "depth": (820, 300), "rail": (240, 300)}[variant]
    img = ground(accent, centre)
    d = ImageDraw.Draw(img)

    if variant == "statement":
        # The tagline at full size, set as a two-line serif statement. The mark
        # is a 56px credential above it and the wordmark signs the bottom-right,
        # so nothing competes with the sentence.
        draw_mark(d, 120, 118, 56)
        f = font("serif", 62)
        for i, line in enumerate(["Every pixel", "earns its place."]):
            draw_cap(d, (120, 252 + i * 108), line, f, NAME_INK)
        draw_cap(d, (120, 508), "LUCIDBIT", font("sans-medium", 17),
                 legible(accent), tracking=4.2)

    elif variant == "centred":
        # Symmetric and calm: plated mark, wordmark, rule, tagline. Reads as a
        # colophon — closest to how Things and Flexibits present themselves.
        draw_mark(d, W // 2 - 52, 132, 104, plate=(30, 26, 48))
        nf = font("serif", 66)
        w = nf.getlength("Lucid") + nf.getlength("Bit")
        x = W // 2 - w / 2
        top = 300 - nf.getbbox("H")[1]
        d.text((x, top), "Lucid", font=nf, fill=NAME_INK)
        d.text((x + nf.getlength("Lucid"), top), "Bit", font=nf, fill=BRAND_PLUM)

        d.line([(W // 2 - 34, 404), (W // 2 + 34, 404)], fill=(70, 62, 92), width=1)

        tf = font("sans", 19)
        draw_cap(d, (round(W // 2 - tf.getlength(TAGLINE) / 2), 440),
                 TAGLINE, tf, MARK_INK, optical=False)

    elif variant == "shelf":
        # The studio IS its apps. Six product icons on a shelf, wordmark and
        # tagline beneath. No abstract mark at all — the icons are the proof,
        # and anyone who already owns one recognises the family instantly.
        n, size, gap = len(SHELF), 118, 34
        total = n * size + (n - 1) * gap
        x0, y0 = (W - total) // 2, 150
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        icons = []
        for i, k in enumerate(SHELF):
            p = IMAGES / ICONS[k]
            if not p.exists():
                continue
            ic = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
            ix = x0 + i * (size + gap)
            shadow.paste((0, 0, 0, 130),
                         (ix + 3, y0 + 12, ix + size + 3, y0 + size + 12),
                         ic.split()[3])
            icons.append((ic, ix))
        img = Image.alpha_composite(
            img.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(16))
        ).convert("RGB")
        for ic, ix in icons:
            img.paste(ic, (ix, y0), ic)
        d = ImageDraw.Draw(img)

        draw_wordmark(d, W // 2, 372, 52, centred=True)
        tf = font("sans", 19)
        draw_cap(d, (round(W // 2 - tf.getlength(TAGLINE) / 2), 468),
                 TAGLINE, tf, MARK_INK, optical=False)

    elif variant == "depth":
        # The mark blown up past the frame and sunk into the background, so it
        # reads as texture rather than a logo. Crisp type sits on top. Scale
        # without shouting — the trick Linear and Vercel use.
        #
        # Two details do the work. It bleeds off three edges, because a shape
        # that fits inside the frame is a picture of a logo while one that runs
        # off it is a surface the card was cut from. And the plum tile keeps its
        # colour while the quiet tiles go grey, so the brand hue is present at
        # thumbnail size even when no text is legible.
        ghost = Image.new("RGB", (W, H), (0, 0, 0))
        draw_mark(ImageDraw.Draw(ghost), 560, -190, 900)
        img = Image.blend(img, ghost.filter(ImageFilter.GaussianBlur(3)), 0.16)
        d = ImageDraw.Draw(img)

        draw_cap(d, (110, 214), "INDEPENDENT STUDIO",
                 font("sans-medium", 16), legible(accent), tracking=4.0)
        draw_wordmark(d, 110, 268, 78)
        draw_cap(d, (110, 392), TAGLINE, font("sans", 24), MARK_INK)

    elif variant == "rail":
        # Editorial: a plum rule down the left margin, everything hung off it.
        # Quiet, structural, and the only variant that doesn't rely on the
        # mark or the icons to carry the card.
        d.rectangle([110, 190, 113, 440], fill=BRAND_PLUM)
        draw_cap(d, (158, 196), "INDEPENDENT STUDIO",
                 font("sans-medium", 16), legible(accent), tracking=4.0)
        draw_wordmark(d, 158, 250, 76)
        draw_cap(d, (158, 386), TAGLINE, font("sans", 25), MARK_INK)
        # No mark here on purpose. At the scale this layout leaves for it the
        # tiles collapse into a speck that reads as a smudge, not a logo — and
        # the rule already does the job of anchoring the block.

    else:  # "plate" — the app-card layout, but the mark given a container
        draw_mark(d, ICON[0], ICON[1], 240, plate=(30, 26, 48))
        nf = font("serif", NAME_CAP)
        x = 440
        draw_cap(d, (x, NAME_TOP), "Lucid", nf, NAME_INK)
        d.text((x - ink_left(nf, "Lucid") + nf.getlength("Lucid"),
                NAME_TOP - nf.getbbox("H")[1]), "Bit", font=nf, fill=BRAND_PLUM)
        draw_cap(d, (x, SUB_TOP), TAGLINE.upper().rstrip("."),
                 font("sans-medium", SUB_CAP), legible(accent), tracking=2.4)

    out = HERE / (f"og-lucidbit.png" if variant == BRAND_VARIANT
                  else f"og-lucidbit-{variant}.png")
    img.save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    import sys
    found = apps()
    wanted = [a.lower() for a in sys.argv[1:]] or ["lucidbit"] + list(found)
    for key in wanted:
        if key == "lucidbit":
            p = brand_card(BRAND_VARIANT)
            print(f"{p.name:<22} {p.stat().st_size // 1024:>4} KB   "
                  f"LucidBit — {TAGLINE}")
            continue
        if key not in found:
            print(f"unknown app: {key}")
            continue
        p = build(key, found[key])
        print(f"{p.name:<22} {p.stat().st_size // 1024:>4} KB   "
              f"{found[key]['name']} — {found[key]['sub']}")
