#!/usr/bin/env python3
"""
generate_pixel_csv.py — Expand tile-level consensus detections to pixel-level CSV.

Reads consensus_tiles.json (111 multi-layer consensus tiles) and produces:
  1. vesuvius_pixel_detections.csv — one row per detected PIXEL with
     (x, y, fused_probability, source_tile_x, source_tile_y, layers_agree, gt_ink)
     suitable for overlay in QGIS/napari or direct judging.
  2. Console summary: total pixels, overlap with ground truth.

Tile probability is painted as a soft plateau: full fused_probability inside the
tile core, linearly feathered across the 32px overlap zone so adjacent tiles blend.

Usage:
    python3 generate_pixel_csv.py [consensus_json] [inklabels_png]
Defaults:
    /home/zubair/Desktop/results/consensus_tiles.json
    /home/zubair/Desktop/vesuvius_data/Frag1/inklabels.png
Output:
    /home/zubair/Desktop/results/vesuvius_pixel_detections.csv
"""
import csv
import json
import sys

import numpy as np
from PIL import Image

TILE_SIZE = 256
OVERLAP = 32

def main():
    consensus_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/home/zubair/Desktop/results/consensus_tiles.json"
    gt_path = sys.argv[2] if len(sys.argv) > 2 else \
        "/home/zubair/Desktop/vesuvius_data/Frag1/inklabels.png"

    with open(consensus_path) as f:
        data = json.load(f)
    tiles = data["tiles"]
    print(f"Loaded {len(tiles)} consensus tiles from {consensus_path}")

    # Ground truth for hit-rate stats only (never used for detection values)
    gt = np.array(Image.open(gt_path)) > 0 if gt_path else None

    rows = []
    for t in tiles:
        tx, ty = int(t["tile_x"]), int(t["tile_y"])
        p = float(t["fused_probability"])
        agree = int(t["layers_above_threshold"])
        for dy in range(0, TILE_SIZE):
            y = ty + dy
            for dx in range(0, TILE_SIZE):
                x = tx + dx
                # feather inside overlap band on each edge
                fx = min((dx + 1), (TILE_SIZE - dx)) / (OVERLAP + 1)
                fy = min((dy + 1), (TILE_SIZE - dy)) / (OVERLAP + 1)
                feather = max(0.0, min(1.0, min(fx, fy)))
                rows.append((x, y, round(p * feather, 4),
                             tx, ty, agree,
                             int(gt[y, x]) if gt is not None else ""))

    out_path = consensus_path.rsplit("/", 1)[0] + "/vesuvius_pixel_detections.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "fused_probability",
                    "source_tile_x", "source_tile_y",
                    "layers_agree", "gt_ink"])
        w.writerows(rows)

    arr = np.array([r[2] for r in rows])
    hits = sum(r[6] == 1 for r in rows) if gt is not None else 0
    print(f"\nSaved: {out_path}")
    print(f"Pixels written : {len(rows):,}")
    print(f"Mean prob      : {arr.mean():.4f} | Max: {arr.max():.4f}")
    if gt is not None:
        print(f"On GT ink      : {hits:,} px ({hits/len(rows)*100:.1f}%)")

if __name__ == "__main__":
    main()
