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

### Layer 26 status & model-calibration finding

A layer-26 scan (583 tiles) was started to upgrade the consensus to 4 layers. During the run we discovered a **cross-model calibration hazard**: tiles analyzed with `claude-sonnet-4-8` returned probabilities of 0.45–0.72 on virtually every tile (mean ≈ 0.63) — including blank-papyrus control tiles that `claude-opus-4-8` scores at 0.02–0.10 in the identical prompt. Sonnet-4.8 does not honor the prompt's probability anchoring, so its outputs are **not comparable** with the calibrated Opus layers and were excluded from the consensus (raw data retained locally for the record).

Consequence: the published consensus remains the calibrated 3-layer (27+28+29) fusion above. Layer-26 will be re-scanned on Opus before upgrading to a 4-layer consensus; [`fuse_4layer.py`](fuse_4layer.py) is ready and takes ~1 min once a calibrated layer-26 raw file exists.

Engineering additions shipped during this work: crash-safe per-tile checkpointing with atomic writes + auto-resume (`ckpt_layer{N}.json`), and a fix for a silently-ignored `--max-tiles` CLI flag that previously caused unmasked 1073-tile runs instead of the intended 583-tile masked sets.

## Data provenance & fragment identity

Fragment used here is the official competition **Frag 1 = `PHercParis2Fr47`**
(54 keV, 3.24 µm — **not** the full-scroll `Scroll1/PHercParis4`; an earlier
local note pointed at the wrong source and was corrected).

Verified 2026-09-02 against `dl.ash2txt.org`:

```
fragments/Frag1/PHercParis2Fr47.volpkg/working/54keV_exposed_surface/
  inklabels.png  md5 6cf3550e128b00884499b063e9d28895  (local == server)
  mask.png       md5 8f283d6a0d60e73301f9e9d21aad3bbd  (local == server)
  surface_volume/28.tif md5 01a8fc299ea2d541a8bce9b90e8a4d24 (local == server)
```

65 surface layers (00–64, 8181×6330, 16-bit), surface volume uuid `20230205211313`,
voxel 3.24 µm. Local path: `~/Desktop/Vesuvius/vesuvius_data/Frag1`
(`~/Desktop/vesuvius_data` is a symlink to it). The `inklabels.png` ground truth
has 5,339,364 ink pixels / 29,142,840 valid = 18.3% coverage, consistent with the
F1=0.668 evaluation.

## Files

| File | Purpose |
|---|---|
| `vesuvius_ink_detector.py` | Main detector — tiling, Claude vision inference, fusion, heatmap rendering, checkpoint/resume |
| `fuse_4layer.py` | 4-layer consensus builder (free, local) — ready for calibrated layer-26 data |
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

**Note:** set `SCROLL_IMAGE_PATH` to a single layer `.tif` per run — repeat for layers 26–29 and fuse with `fuse_4layer.py`. Outputs raw per-tile JSON verdicts, a full-resolution probability heatmap, and a binary detection mask.
