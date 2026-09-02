#!/usr/bin/env python3
"""Export SHARP, native-1:1 crops of confirmed Frag1 ink tiles directly from
the layer-28 TIF (8181x6330 px), bypassing the blurry upscaled 256-px tiles.

Outputs, to ~/Desktop/results/native_crops/:
  - <n>_tile_<x>_<y>_gt<frac>.png   per-tile native 512x512 crop (2-tile window)
  - clear_letter_montage.png         composite for Discord
Plus a `manifest.json` with coords / scale info.

The crops are read at full scan resolution so letter strokes are as crisp as the
CT data allows (256 px tile @ 3.24 um = 0.83 mm; 512 px crop = 1.66 mm).
"""
import csv, json, os
from pathlib import Path
import numpy as np
from PIL import Image

RESULTS = Path("/home/zubair/Desktop/results")
TIF = RESULTS / "../vesuvius_data/Frag1/surface_volume/28.tif"
OUT = RESULTS / "native_crops"
OUT.mkdir(exist_ok=True)

TILE = 256
MARGIN = 128          # 128 px each side => 512x512 native crop centered on tile
CROP = 2 * MARGIN + TILE

PIXEL_UM = 3.24       # voxel size in microns

def load_layer():
    im = Image.open(TIF)
    a = np.array(im)  # I;16B grayscale
    print(f"layer-28 loaded: {a.shape} dtype={a.dtype}")
    return a

def write_crop(a, x, y, gt_frac, idx):
    """Center a 512x512 crop on tile top-left (x,y), clamped to image bounds."""
    cx, cy = x + TILE // 2, y + TILE // 2
    x0, y0 = cx - MARGIN, cy - MARGIN
    x1, y1 = x0 + CROP, y0 + CROP
    x0b, y0b = max(x0, 0), max(y0, 0)
    x1b, y1b = min(x1, a.shape[1]), min(y1, a.shape[0])
    crop = a[y0b:y1b, x0b:x1b]
    # pad if clamped at edge
    pad = np.zeros((CROP, CROP), dtype=crop.dtype)
    pad[y0b - y0: y0b - y0 + crop.shape[0], x0b - x0: x0b - x0 + crop.shape[1]] = crop
    img = Image.fromarray(pad)
    name = f"{idx:02d}_tile_{x}_{y}_gt{gt_frac:.0%}.png"
    img.save(OUT / name)
    return name

def make_montage(names):
    thumbs = []
    for n in names:
        im = Image.open(OUT / n).convert("L").resize((256, 256), Image.LANCZOS)
        thumbs.append(im)
    grid = 4
    rows = []
    for i in range(0, len(thumbs), grid):
        row = thumbs[i:i+grid]
        row += [Image.new("L", (256, 256), 0)] * (grid - len(row))
        rows.append(np.hstack([np.array(r) for r in row]))
    mont = Image.fromarray(np.vstack(rows))
    # add a small pixel-scale bar label
    mont.save(OUT / "clear_letter_montage.png")

def main():
    a = load_layer()
    rows = list(csv.DictReader(open(RESULTS / "verified_letters.csv")))
    # pick the top confirmed tiles with the best (real ink + darkest contrast)
    confirmed = [r for r in rows if r["verdict"] in ("REAL_INK", "GT_CONFIRMED")]
    confirmed.sort(key=lambda r: (-float(r["gt_ink_frac"]), float(r["contrast_28"])))
    top = confirmed[:12] if len(confirmed) >= 12 else confirmed
    print(f"exporting {len(top)} native crops")
    names = []
    manifest = []
    for idx, r in enumerate(top):
        x, y = int(r["x"]), int(r["y"])
        name = write_crop(a, x, y, float(r["gt_ink_frac"]), idx)
        names.append(name)
        manifest.append({
            "file": name, "tile_x": x, "tile_y": y,
            "verdict": r["verdict"], "gt_ink_frac": float(r["gt_ink_frac"]),
            "contrast_28": float(r["contrast_28"]),
            "crop_px": CROP, "crop_um": round(CROP * PIXEL_UM, 1),
            "source": "native 1:1 crop from layer-28.tif",
        })
    make_montage(names)
    json.dump(manifest, open(OUT / "manifest.json", "w"), indent=2)
    print(f"done -> {OUT}")

if __name__ == "__main__":
    main()