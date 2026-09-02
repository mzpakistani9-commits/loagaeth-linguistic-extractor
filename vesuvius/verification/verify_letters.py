#!/usr/bin/env python3
"""Verify letter-candidate tiles using VALID signals only.

Cross-layer structural correlation was tested and REJECTED for this dataset
(blank papyrus corr = 0.867, ink tiles corr = 0.849 — non-discriminative).
The two signals that actually separate ink from pareidolia on carbonized
papyrus are:

  1. Ground-truth agreement  — official Frag1 inklabels.png (md5-match verified
     against dl.ash2txt.org PHercParis2Fr47) mark real ink there.
  2. Physical contrast        — labeled ink pixels are darker (lower CT value)
     than surrounding papyrus, measured per tile.

Output: ranked 'verified letters' CSV. Verdicts use only these signals;
cross_layer_corr is kept for reference but never drives classification.
"""
import numpy as np
from PIL import Image
from pathlib import Path
import json
import csv
from collections import Counter

BASE = Path('/home/zubair/Desktop/Vesuvius/vesuvius_data/Frag1')
RESULTS = Path('/home/zubair/Desktop/results')
LAYERS = [26, 27, 28, 29]
TILE = 256

def load_layer(L):
    p = BASE / 'surface_volume' / f'{L}.tif'
    if not p.exists():
        return None
    return np.array(Image.open(p)).astype(np.float32)

layer_arrays = {L: load_layer(L) for L in LAYERS}
gt = np.array(Image.open(BASE / 'inklabels.png')) > 0
mask = np.array(Image.open(BASE / 'mask.png').convert('L')) > 0

print("Layers loaded:", [L for L, a in layer_arrays.items() if a is not None])

def tile_contrast(x, y, ref_layer=28):
    """Mean layer value inside GT-labeled ink pixels minus mean of non-ink
    papyrus pixels in the same tile. Negative = ink darker = real signal."""
    a = layer_arrays.get(ref_layer)
    if a is None:
        return 0.0
    t = a[y:y+TILE, x:x+TILE]
    g = gt[y:y+TILE, x:x+TILE]
    ink_vals = t[g]
    pap_vals = t[~g & (t > 0)]
    if ink_vals.size == 0 or pap_vals.size == 0:
        return float('nan')
    return round(float(ink_vals.mean() - pap_vals.mean()), 1)

def eval_tile(x, y, det_prob=0.0, layer_hits=0, n_candidates=0):
    if x + TILE > gt.shape[1] or y + TILE > gt.shape[0]:
        return None
    cx, cy = x + TILE//2, y + TILE//2
    if cx >= mask.shape[1] or cy >= mask.shape[0] or not mask[cy, cx]:
        return None  # off-papyrus
    gt_patch = gt[y:y+TILE, x:x+TILE]
    gt_frac = float(gt_patch.mean())
    contrast = tile_contrast(x, y)

    # Classification (valid signals only)
    gt_confirmed = gt_frac >= 0.02
    dark = contrast is not None and not np.isnan(contrast) and contrast < 0

    if gt_confirmed and dark:
        verdict = "REAL_INK"
    elif gt_confirmed:
        verdict = "GT_CONFIRMED"
    elif dark:
        verdict = "CONTRAST_ONLY"
    else:
        verdict = "UNCONFIRMED"

    return {
        'x': x, 'y': y,
        'gt_ink_frac': round(gt_frac, 4),
        'contrast_28': contrast,
        'detector_prob': det_prob,
        'layer_hits': layer_hits,
        'n_candidates': n_candidates,
        'verdict': verdict,
    }

def main():
    results = []

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

    seen = {}
    for r in results:
        key = (r['x'], r['y'])
        if key not in seen or r['gt_ink_frac'] > seen[key]['gt_ink_frac']:
            seen[key] = r
    results = list(seen.values())
    print(f"Total unique tiles evaluated: {len(results)}")

    order = {'REAL_INK': 0, 'GT_CONFIRMED': 1, 'CONTRAST_ONLY': 2, 'UNCONFIRMED': 3}
    results.sort(key=lambda r: (order[r['verdict']], -r['gt_ink_frac']))

    out_csv = RESULTS / 'verified_letters.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['x', 'y', 'verdict', 'gt_ink_frac', 'contrast_28',
                    'detector_prob', 'layer_hits', 'n_candidates', 'source'])
        for r in results:
            w.writerow([r['x'], r['y'], r['verdict'], r['gt_ink_frac'],
                        r['contrast_28'], r['detector_prob'], r['layer_hits'],
                        r['n_candidates'], r['source']])

    cnt = Counter(r['verdict'] for r in results)
    print("\n=== VERDICT SUMMARY ===")
    for v in ['REAL_INK', 'GT_CONFIRMED', 'CONTRAST_ONLY', 'UNCONFIRMED']:
        print(f"  {v:<14} {cnt.get(v,0)}")

    print("\n=== TOP VERIFIED LETTER TILES (REAL_INK, best gt + darkest) ===")
    for r in [r for r in results if r['verdict'] == 'REAL_INK'][:30]:
        print(f"  ({r['x']:4d},{r['y']:4d}) gt={r['gt_ink_frac']:.2f} "
              f"contrast={str(r['contrast_28']):>7} hits={r['layer_hits']} "
              f"{r['source'][:45]}")

    print(f"\nSaved: {out_csv}")

if __name__ == '__main__':
    main()