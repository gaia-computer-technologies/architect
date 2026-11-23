# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10", "numpy>=1.26"]
# ///
"""Make README gallery tiles from skill outputs, on Gaia paper (#FDFDFA).

Usage: uv run assets/src/paper_tiles.py <image> <out.png> [size=800]
Trims white margins, fits the image into a square with padding, and turns
near-white pixels into paper so the tile sits on the Gaia canvas.
"""
import sys
import numpy as np
from PIL import Image, ImageChops

PAPER = (253, 253, 250)

def tile(src: str, out: str, size: int = 800, pad: int = 28) -> None:
    im = Image.open(src).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if box:
        im = im.crop(box)
    im.thumbnail((size - 2 * pad, size - 2 * pad), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    a[(a > 244).all(axis=2)] = PAPER
    canvas = Image.new("RGB", (size, size), PAPER)
    canvas.paste(Image.fromarray(a.astype(np.uint8)), ((size - im.width) // 2, (size - im.height) // 2))
    canvas.save(out, optimize=True)
    print(f"wrote {out} ({size}x{size}) from {src}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    tile(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 800)
