#!/usr/bin/env python3
"""Convert 16-bit native crops to 8-bit PNG + build a viewable montage.

16-bit I;16 PNGs don't render in Discord/browsers, so convert to 8-bit grayscale
(with proper 16->8 normalization) and save a labelled montage for the post.
Reads ~/Desktop/results/native_crops and writes an 8-bit mirror + montage there.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

SRC = Path("/home/zubair/Desktop/results/native_crops")
OUT8 = SRC / "preview8"
OUT8.mkdir(exist_ok=True)

def to8(p16):
    """uint16 -> uint8 with 2-98 percentile stretch (keeps strokes visible)."""
    lo, hi = np.percentile(p16, 2), np.percentile(p16, 98)
    a = np.clip((p16.astype(np.float32) - lo) / max(hi - lo, 1) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(a)

def main():
    manifest = json.load(open(SRC / "manifest.json"))
    names = [m["file"] for m in manifest]
    thumbs = []
    for n in names:
        p16 = np.array(Image.open(SRC / n))
        im8 = to8(p16)
        im8.save(OUT8 / n.replace(".png", "_8.png"))
        thumbs.append((n, im8))
    # also 8-bit previews of the true 256px native tiles
    for m in manifest:
        tile = m.get("tile_file")
        if not tile:
            continue
        p16 = np.array(Image.open(SRC / tile))
        to8(p16).save(OUT8 / tile.replace(".png", "_8.png"))
    # grid montage with labels
    cell = 200
    grid = 4
    cols = grid
    rows = (len(thumbs) + cols - 1) // cols
    W, H = cols * cell, rows * cell
    mont = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mont)
    for i, (n, im) in enumerate(thumbs):
        r, c = divmod(i, cols)
        x, y = c * cell, r * cell
        mont.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        d.text((x + 4, y + 4), f"{i:02d}", fill=255)
    mont.save(SRC / "clear_letter_montage_8bit.png")
    print(f"wrote {len(names)} 8-bit previews + montage -> {OUT8}")

if __name__ == "__main__":
    main()