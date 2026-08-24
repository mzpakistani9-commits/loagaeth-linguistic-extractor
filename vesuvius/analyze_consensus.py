#!/usr/bin/env python3
"""Free offline analysis: PR curve, threshold sweep, letter-candidate mining,
top-tile visual crops. No API calls. Outputs to ~/Desktop/results/analysis/"""
import json, os
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

DESK = Path("/home/zubair/Desktop")
RES = DESK / "results"
OUT = RES / "analysis"
OUT.mkdir(exist_ok=True)
DATA = DESK / "vesuvius_data/Frag1"
TILE = 256
RAW = {"27": RES / "ink_detection_raw_20260822_174012.json",
       "28": RES / "ink_detection_raw_20260822_154604.json",
       "29": RES / "ink_detection_raw_20260822_191209.json"}

def load(path):
    return {(int(e["tile_x"]), int(e["tile_y"])): float(e["ink_probability"])
            for e in json.load(open(path)) if e.get("status") == "ok"}

def main():
    # ---------- 1. Threshold sweep on calibrated layer-28 ----------
    probs = load(RAW["28"])
    gt = np.array(Image.open(DATA / "inklabels.png").convert("L"))
    rows, best = [], None
    for thr in [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]:
        tp = fp = fn = 0
        for (x, y), p in probs.items():
            has_gt = float(np.mean(gt[y:y+TILE, x:x+TILE] > 0)) > 0.02
            pred = p >= thr
            if pred and has_gt: tp += 1
            elif pred and not has_gt: fp += 1
            elif has_gt: fn += 1
        prec = tp / max(1, tp + fp); rec = tp / max(1, tp + fn)
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        rows.append({"threshold": thr, "precision": round(prec, 3),
                     "recall": round(rec, 3), "f1": round(f1, 3)})
        if best is None or f1 > best["f1"]: best = rows[-1]
    json.dump(rows, open(OUT / "pr_sweep_layer28.json", "w"), indent=1)
    print("PR sweep:"); [print(f"  thr={r['threshold']:<6} P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f}") for r in rows]
    print(f"  BEST: {best}")

    # ---------- 2. PR curve rendered with PIL ----------
    W, H, M = 800, 560, 70
    img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
    pts = [(M + r["recall"] * (W - 2 * M), H - M - r["precision"] * (H - 2 * M)) for r in reversed(rows)]
    for gx in range(11):
        x = M + gx * (W - 2 * M) / 10; y = M + gx * (H - 2 * M) / 10
        d.line([(x, M), (x, H - M)], fill=(230, 230, 230)); d.line([(M, y), (W - M, y)], fill=(230, 230, 230))
    d.line(pts, fill=(20, 80, 200), width=3)
    for px, py in pts: d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(200, 30, 30))
    bx, by = pts[len(rows)//2]  # marker near best
    for i, r in enumerate(reversed(rows)):
        if abs(r["f1"] - best["f1"]) < 1e-9:
            px, py = pts[i]; d.ellipse([px - 7, py - 7, px + 7, py + 7], outline=(0, 140, 0), width=3)
    for gx in range(11):
        x = M + gx * (W - 2 * M) / 10
        d.text((x - 8, H - M + 8), f"{gx/10:.1f}", fill="black")
        y = H - M - gx * (H - 2 * M) / 10
        d.text((M - 38, y - 6), f"{gx/10:.1f}", fill="black")
    d.text((W // 2 - 90, H - 26), "Recall", fill="black")
    d.text((14, M - 24), "Precision", fill="black")
    d.text((W // 2 - 170, 18), f"PR curve - layer 28 tile detections (best F1={best['f1']} @ thr {best['threshold']})", fill="black")
    img.save(OUT / "pr_curve_layer28.png")

    # ---------- 3. Letter-candidate mining across layers ----------
    cand = Counter()
    notes_by_tile = {}
    for lay, path in RAW.items():
        for e in json.load(open(path)):
            if e.get("status") != "ok": continue
            key = (int(e["tile_x"]), int(e["tile_y"]))
            lc = e.get("letter_candidates") or []
            if isinstance(lc, list):
                cand[key] += len(lc)
                if lc and key not in notes_by_tile:
                    notes_by_tile[key] = (lay, str(e.get("notes"))[:220])
    multi = {k: v for k, v in cand.items() if v >= 2}
    ranked = sorted(multi.items(), key=lambda kv: -kv[1])[:15]
    out_rows = []
    for (x, y), n in ranked:
        gtf = float(np.mean(gt[y:y+TILE, x:x+TILE] > 0))
        lay, note = notes_by_tile[(x, y)]
        out_rows.append({"tile": [x, y], "candidate_hits_across_layers": n,
                         "gt_ink_fraction": round(gtf, 2), "example_note": note})
    json.dump(out_rows, open(OUT / "letter_candidate_tiles.json", "w"), indent=1)
    print(f"letter-candidate tiles with >=2 layer hits: {len(multi)} | top saved: {len(ranked)}")

    # ---------- 4. Top-10 consensus tile crops with GT outline ----------
    ct = json.load(open(RES / "consensus_tiles.json"))["tiles"]
    tif = Image.open(DATA / "surface_volume/28.tif").convert("L")
    topdir = OUT / "top_tiles"; topdir.mkdir(exist_ok=True)
    for i, t in enumerate(sorted(ct, key=lambda e: -e["ground_truth_ink_fraction"])[:10]):
        x, y = t["tile_x"], t["tile_y"]
        crop = tif.crop((x, y, min(x+TILE, tif.width), min(y+TILE, tif.height))).convert("RGB")
        gcrop = np.array(Image.open(DATA / "inklabels.png").convert("L").crop((x, y, x+TILE, y+TILE)))
        edge = gcrop > 0
        arr = np.array(crop)
        arr[edge] = [arr[edge].max(), int(arr[edge].max())//3, int(arr[edge].max())//3]  # red tint where GT ink
        Image.fromarray(arr).save(topdir / f"{i:02d}_tile_{x}_{y}_gt{t['ground_truth_ink_fraction']:.2f}.png")
    print("top-10 evidence crops saved to analysis/top_tiles/")
    print(json.dumps(out_rows[:5], indent=1)[:600])

if __name__ == "__main__":
    main()
