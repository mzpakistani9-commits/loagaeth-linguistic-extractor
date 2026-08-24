#!/usr/bin/env python3
"""Fuse layers 26+27+28+29 into 4-layer consensus.
Run AFTER layer-26 scan completes. Free (no API calls).
Outputs: consensus_tiles_4layer.json, mask_fuse4.png, heatmap_fuse4.png,
summary_4layer.json  (all in ~/Desktop/results/)
"""
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

DESK = Path("/home/zubair/Desktop")
RESULTS = DESK / "results"
DATA = DESK / "vesuvius_data/Frag1"
TILE = 256

RAW = {
    "layer_27": RESULTS / "ink_detection_raw_20260822_174012.json",
    "layer_28": RESULTS / "ink_detection_raw_20260822_154604.json",
    "layer_29": RESULTS / "ink_detection_raw_20260822_191209.json",
}


def load_raw_list(path):
    data = json.load(open(path))
    out = {}
    for e in data:
        if e.get("status") == "ok":
            out[(int(e["tile_x"]), int(e["tile_y"]))] = float(e["ink_probability"])
    return out


def find_layer26_results():
    ckpt = RESULTS / "ckpt_layer26.json"
    if not ckpt.exists():
        raise SystemExit("No layer-26 results found")
    data = json.load(open(ckpt))
    entries = list(data.values()) if isinstance(data, dict) else data
    out = {}
    for e in entries:
        if e.get("status") != "error":
            out[(int(e["tile_x"]), int(e["tile_y"]))] = float(e["ink_probability"])
    print(f"Layer 26: {len(out)} tiles from checkpoint {ckpt.name}")
    return out


def main():
    layers = {name: load_raw_list(p) for name, p in RAW.items()}
    for name, m in layers.items():
        print(f"{name}: {len(m)} ok-tiles")
    layers["layer_26"] = find_layer26_results()

    common = set.intersection(*[set(m) for m in layers.values()])
    keys = sorted(common)
    print(f"Common tiles across 4 layers: {len(keys)}")

    ink = Image.open(DATA / "inklabels.png").convert("L")
    ink_arr = np.array(ink)
    raw28 = {(int(e["tile_x"]), int(e["tile_y"])): str(e.get("notes", ""))[:300]
             for e in json.load(open(RAW["layer_28"]))}

    tiles_out = []
    n_gt = 0
    fused_vals = []
    for (tx, ty) in keys:
        probs = {name: layers[name][(tx, ty)] for name in ["layer_26", "layer_27", "layer_28", "layer_29"]}
        fused = round(sum(probs.values()) / 4.0, 2)
        above = sum(1 for v in probs.values() if v >= 0.05)
        gt_frac = float(np.mean(ink_arr[ty:ty + TILE, tx:tx + TILE] > 0)) \
            if ty + TILE <= ink_arr.shape[0] and tx + TILE <= ink_arr.shape[1] else 0.0
        has_gt = gt_frac > 0.10
        n_gt += has_gt
        fused_vals.append(fused)
        notes = raw28.get((tx, ty), "")
        tiles_out.append({
            "tile_x": tx, "tile_y": ty,
            "probabilities": {k: round(v, 2) for k, v in probs.items()},
            "fused_probability": fused,
            "layers_above_threshold": above,
            "fused_probability_average": fused,
            "has_ground_truth_ink": has_gt,
            "ground_truth_ink_fraction": round(gt_frac, 3),
            "letter_candidates": [],
            "notes": notes,
        })

    consensus = {
        "description": "Multi-layer consensus ink detections for Frag1 (4-layer: 26+27+28+29)",
        "method": "claude-opus-4-8 vision per 256px tile, mean of 4 depth layers, thr=0.05",
        "author": "Muhammad Zubair",
        "github": "https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor",
        "tiles": tiles_out,
    }
    out_path = RESULTS / "consensus_tiles_4layer.json"
    with open(out_path, "w") as f:
        json.dump(consensus, f, indent=1)
    print(f"Wrote {out_path.name}: {len(tiles_out)} tiles | GT-positive: {n_gt}")

    # Render full-scroll mask + heatmap (canvas = layer-28 tif size)
    img = Image.open(DATA / "surface_volume/28.tif")
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    heat = Image.new("L", (W, H), 0)
    m_px, h_px = mask.load(), heat.load()
    for t in tiles_out:
        tx, ty, p = t["tile_x"], t["tile_y"], t["fused_probability"]
        val = 255 if p >= 0.05 else 0
        hval = min(255, int(p * 255 * 3))
        for yy in range(ty, min(ty + TILE, H)):
            for xx in range(tx, min(tx + TILE, W)):
                if val:
                    m_px[xx, yy] = 255
                if hval:
                    h_px[xx, yy] = max(h_px[xx, yy], hval)
    mask.save(RESULTS / "mask_fuse4.png")
    heat.save(RESULTS / "heatmap_fuse4.png")
    print("Rendered mask_fuse4.png + heatmap_fuse4.png")

    summary = {
        "run_timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "fusion": "mean(layer26+27+28+29)",
        "common_tiles": len(keys),
        "tiles_above_005": sum(1 for v in fused_vals if v >= 0.05),
        "gt_positive_tiles": n_gt,
        "mean_fused_prob": round(float(np.mean(fused_vals)), 3),
        "author": "Muhammad Zubair",
    }
    with open(RESULTS / "summary_4layer.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
