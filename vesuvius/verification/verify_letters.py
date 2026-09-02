#!/usr/bin/env python3
"""Verify letter-candidate tiles: cross-layer persistence + ground-truth agreement.

Scores every tile by:
  1. Cross-layer structural correlation (real ink persists across CT layers)
  2. Ground-truth ink agreement (does the official label map agree ink is there?)
  3. Detector consensus probability (did the vision model fire on it?)

Output: ranked 'verified letters' CSV separating real ink from fiber pareidolia.
"""
import numpy as np
from PIL import Image
from pathlib import Path
import json
import csv

BASE = Path('/home/zubair/Desktop/vesuvius_data/Frag1')
RESULTS = Path('/home/zubair/Desktop/results')
LAYERS = [26, 27, 28, 29]
TILE = 256

def load_layer(L):
    p = BASE / 'surface_volume' / f'{L}.tif'
    if not p.exists():
        return None
    return np.array(Image.open(p)).astype(np.float32)

# Cache layer arrays
layer_arrays = {L: load_layer(L) for L in LAYERS}
gt = np.array(Image.open(BASE / 'inklabels.png')) > 0
mask = np.array(Image.open(BASE / 'mask.png').convert('L')) > 0

print("Layers loaded:", [L for L, a in layer_arrays.items() if a is not None])

def cross_layer_corr(x, y, ref_layer=28):
    """Mean pairwise correlation of tile dark-structure across layers."""
    tiles = {}
    for L, a in layer_arrays.items():
        if a is None:
            continue
        t = a[y:y+TILE, x:x+TILE]
        tiles[L] = (t - t.mean()) / (t.std() + 1e-9)
    base = tiles[ref_layer]
    corrs = [float(np.corrcoef(base.ravel(), tiles[L].ravel())[0, 1])
             for L in tiles if L != ref_layer]
    return float(np.mean(corrs)) if corrs else 0.0

def eval_tile(x, y, det_prob=0.0, layer_hits=0, n_candidates=0):
    if x + TILE > gt.shape[1] or y + TILE > gt.shape[0]:
        return None
    cx, cy = x + TILE//2, y + TILE//2
    if cx >= mask.shape[1] or cy >= mask.shape[0] or not mask[cy, cx]:
        return None  # off-papyrus
    gt_patch = gt[y:y+TILE, x:x+TILE]
    gt_frac = float(gt_patch.mean()) if gt_patch.dtype == bool else float(gt_patch.sum() / (TILE*TILE*255))
    corr = cross_layer_corr(x, y)

    # Classification
    # Real ink: high cross-layer persistence AND ground-truth agreement
    if corr >= 0.60 and gt_frac >= 0.05:
        verdict = "REAL_INK"
    elif corr >= 0.55 or gt_frac >= 0.05:
        verdict = "PROBABLE"
    elif corr >= 0.35 or gt_frac >= 0.02:
        verdict = "POSSIBLE"
    else:
        verdict = "PARELDOLIA"

    return {
        'x': x, 'y': y,
        'cross_layer_corr': round(corr, 3),
        'gt_ink_frac': round(gt_frac, 4),
        'detector_prob': det_prob,
        'layer_hits': layer_hits,
        'n_candidates': n_candidates,
        'verdict': verdict,
    }

def main():
    results = []

    # 1) From letter candidates
    lc_path = RESULTS / 'analysis' / 'letter_candidate_tiles.json'
    if lc_path.exists():
        with open(lc_path) as f:
            letter_cands = json.load(f)
        for c in letter_cands:
            x, y = c['tile'][0], c['tile'][1]
            r = eval_tile(x, y, det_prob=0.0, layer_hits=c.get('candidate_hits_across_layers', 0),
                          n_candidates=1)
            if r:
                r['source'] = f"letter-candidate:{c.get('example_note','')[:40]}"
                results.append(r)
        print(f"Loaded {len(letter_cands)} letter candidates")

    # 2) From consensus tiles
    ck_path = RESULTS / 'consensus_tiles.json'
    if ck_path.exists():
        with open(ck_path) as f:
            cons = json.load(f)
        for t in cons.get('tiles', []):
            r = eval_tile(t['tile_x'], t['tile_y'], det_prob=t.get('fused_probability', 0),
                          layer_hits=t.get('layers_above_threshold', 0),
                          n_candidates=len(t.get('letter_candidates', [])))
            if r:
                r['source'] = f"consensus:{t.get('notes','')[:40]}"
                results.append(r)
        print(f"Loaded {len(cons['tiles'])} consensus tiles")

    # Dedup by (x,y), keep highest info
    seen = {}
    for r in results:
        key = (r['x'], r['y'])
        if key not in seen or r['cross_layer_corr'] > seen[key]['cross_layer_corr']:
            seen[key] = r
    results = list(seen.values())
    print(f"Total unique tiles evaluated: {len(results)}")

    # Sort by real-ink likelihood
    order = {'REAL_INK': 0, 'PROBABLE': 1, 'POSSIBLE': 2, 'PARELDOLIA': 3}
    results.sort(key=lambda r: (order[r['verdict']], -r['cross_layer_corr']))

    # Output CSV
    out_csv = RESULTS / 'verified_letters.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['x', 'y', 'verdict', 'cross_layer_corr', 'gt_ink_frac',
                    'detector_prob', 'layer_hits', 'n_candidates', 'source'])
        for r in results:
            w.writerow([r['x'], r['y'], r['verdict'], r['cross_layer_corr'],
                        r['gt_ink_frac'], r['detector_prob'], r['layer_hits'],
                        r['n_candidates'], r['source']])

    # Print summary
    from collections import Counter
    cnt = Counter(r['verdict'] for r in results)
    print("\n=== VERDICT SUMMARY ===")
    for v in ['REAL_INK', 'PROBABLE', 'POSSIBLE', 'PARELDOLIA']:
        print(f"  {v:<12} {cnt.get(v,0)}")

    print("\n=== TOP VERIFIED LETTER TILES (REAL_INK) ===")
    for r in [r for r in results if r['verdict'] == 'REAL_INK'][:30]:
        print(f"  ({r['x']:4d},{r['y']:4d}) corr={r['cross_layer_corr']:+.3f} "
              f"gt={r['gt_ink_frac']:.2f} hits={r['layer_hits']} {r['source'][:45]}")

    print(f"\nSaved: {out_csv}")

if __name__ == '__main__':
    main()
