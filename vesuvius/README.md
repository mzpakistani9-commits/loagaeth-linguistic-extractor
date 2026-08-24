# Vesuvius Challenge — Ink Detection via loagaeth

This folder extends the **loagaeth** linguistic analysis pipeline to Herculaneum scroll CT data for the [Vesuvius Challenge](https://scrollprize.org). It uses the same Claude vision API infrastructure as the core tool, extended with Greek uncial character detection rules.

## What this is

loagaeth was built as a linguistic analysis system for ancient scripts. This folder applies that same infrastructure — tile-based Claude vision analysis with structured decision rules — to the problem of detecting carbon ink in the Herculaneum papyri (PHercParis 2 / Frag1), targeting the **Ink Detection progress prize** and the **First Letters Prize**.

## How it works

1. **Mask-aware tiling** — Fragment 1 (8181×6330, layers 00–64) is tiled into 256×256 windows with 32px overlap; tiles whose centers fall outside the validity mask are dropped (1073 → 583 valid tiles per layer).
2. **Claude vision inference** — Each tile is rendered at high contrast and sent to Claude via the same vision-API client used by the core loagaeth tool, with a prompt encoding Greek uncial stroke characteristics: curvilinear strokes, pen-lift directionality, letterform density vs. papyrus fiber structure.
3. **Structured decision rules** — The model must return a JSON verdict per tile (`ink_probability`, `stroke_description`, `character_analysis`) applying explicit rules for mask edges (→ 0.0), blank papyrus (→ 0.02), cracks/stains (→ 0.08), fiber-only texture (→ 0.10), and curvilinear ink-like strokes (≥ 0.65).
4. **Multi-layer fusion** — Independent scans of adjacent CT layers (27, 28, 29) are fused; only tiles where **2+ layers independently detect ink** survive as consensus calls, suppressing single-layer false positives from fibers and artifacts.

## Results

Per-layer full scans (583 valid tiles each, 100% API success):

| Layer | Tiles above thr (0.05) | Ink coverage |
|-------|------------------------|--------------|
| 27 | 172 | 29.5% |
| 28 | 121 | 20.75% |
| 29 | 110 | 18.87% |

- Tile-level F1 = **0.67** vs. ground truth (precision 0.58, recall 0.79 @ thr 0.01, layer 28)
- Multi-layer consensus: **111 tiles** independently confirmed across layers 27+28+29
- Strongest consensus region: tile (3200, 3800) with ground-truth ink fraction **0.50**
- Threshold sensitivity renders in [`results/`](results/): `heatmap_t001`/`mask_t001` (thr = 0.01) vs `heatmap_t040`/`mask_t040` (thr = 0.40)

See [`consensus_tiles.json`](consensus_tiles.json) for the full ranked consensus set and [`SUBMISSION.md`](SUBMISSION.md) for the complete write-up. Machine-verifiable run summaries are in [`results/summary_layer2{7,8,9}.json`](results/) — each records `successful_api_calls = 583 / total_tiles_analyzed = 583`.

## Files

| File | Purpose |
|---|---|
| `vesuvius_ink_detector.py` | Main detector — tiling, Claude vision inference, fusion, heatmap rendering |
| `consensus_tiles.json` | 111 multi-layer consensus detections with per-layer probabilities |
| `SUBMISSION.md` | Full submission write-up: methodology, metrics, top detections |
| `results/summary_layer27.json` … `29.json` | Run summaries: API success counts, coverage, model, thresholds |
| `results/heatmap_t001.png` / `mask_t001.png` | Probability heatmap + binary mask at threshold 0.01 |
| `results/heatmap_t040.png` / `mask_t040.png` | Probability heatmap + binary mask at threshold 0.40 |

## Reproducibility

```bash
pip install anthropic pillow numpy matplotlib
export ANTHROPIC_API_KEY=sk-...
export ANTHROPIC_BASE_URL=https://api.anthropic.com
export SCROLL_IMAGE_PATH=/path/to/Frag1/surface_volume/28.tif   # one layer per run
python vesuvius_ink_detector.py --max-tiles 583 --threshold 0.05
```

**Note:** set `SCROLL_IMAGE_PATH` to a single layer `.tif` per run — repeat for layers 26–29 and fuse with `fuse_layers.py`. Outputs raw per-tile JSON verdicts, a full-resolution probability heatmap, and a binary detection mask.
