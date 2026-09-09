#!/usr/bin/env python3
"""Turn the QuanteX Beast lockup into the square mark the desk needs.

The artwork is a wide lockup - the lion on the left, the wordmark on the right,
on black. Every slot that draws it is a small square: the browser tab, the
sidebar header, the app launcher. Dropped in whole it would either shrink to an
unreadable smudge or be cropped by the browser at a place nobody chose.

So this takes the lion only, squares it, and drops the black ground so the mark
sits on light and dark desks alike.

    python scripts/install_brand_mark.py ~/Downloads/quantex-beast.png

Then `bench build --app swift_theme` and hard-reload. Nothing else changes:
api/boot.py already points every logo and the favicon at this filename.
"""

import os
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow is needed: /home/ali/bench-16/env/bin/pip install Pillow")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "swift_theme", "public", "icons", "quantex-beast.png")
# Black, or near enough - the artwork's ground is not a flat #000 at the edges.
NEAR_BLACK = 34


def trim_black(im):
    """The bounding box of everything that is not the black ground."""
    rgb = im.convert("RGB")
    mask = rgb.point(lambda v: 255 if v > NEAR_BLACK else 0).convert("L")
    return im.crop(mask.getbbox() or (0, 0, im.width, im.height))


def drop_black(im):
    """Black ground to transparent, so the mark works on a light desk too.

    Built as a mask off the brightest channel rather than walked pixel by
    pixel: same result, and it does not depend on getdata(), which Pillow is
    retiring.
    """
    im = im.convert("RGBA")
    r, g, b, a = im.split()
    brightest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    keep = brightest.point(lambda v: 255 if v > NEAR_BLACK else 0)
    im.putalpha(ImageChops.darker(a, keep))
    return im


def main(src):
    im = drop_black(trim_black(Image.open(src)))

    # The lion is the left of the lockup. Its own bounding box is found rather
    # than assumed: take the left third, trim it, and square it on its centre.
    lion = trim_black(im.crop((0, 0, int(im.width * 0.42), im.height)))
    side = max(lion.width, lion.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(lion, ((side - lion.width) // 2, (side - lion.height) // 2), lion)

    square.resize((512, 512), Image.LANCZOS).save(OUT)
    print(f"source {im.width}x{im.height} -> lion {lion.width}x{lion.height} -> {OUT} (512x512)")
    print("now: bench build --app swift_theme && bench --site swiftcheck.local clear-cache")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
