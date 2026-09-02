# Frag1 Ink Detection — Vision-API Tile Pipeline

**Vesuvius Challenge — Progress Prize submission**
**Author:** Muhammad Zubair | mzpakistani9@gmail.com

A **vision-model (Claude) tile classifier** that detects carbon ink on a
Herculaneum fragment's 54 keV X-ray surface volume. It runs entirely through a
cloud vision API with **no GPU requirement**, which is its core differentiator:
virtually the entire community uses 3D convolutional models that demand an
NVIDIA GPU, while this pipeline reproduces competitive ink detection on any
machine with only an internet connection and an API key.

---

## What problem it solves

Most fragment ink-detection approaches train ResNet-3D / TimeSformer models
that require a GPU, a container runtime, and GB-scale downloads. This creates a
high barrier for newcomers and for anyone without cloud GPU credits. This
submission shows that a **well-prompted generalist vision model**, applied
tile-by-tile with a strict decision-rule prompt and multi-layer consensus
fusion, can reach useful ink detection on a fragment surface volume using only
CPU + an API call per tile.

## Data

- **Fragment**: Frag 1 = `PHercParis2Fr47` (54 keV, 3.24 µm, 65 layers, 8181×6330)
- Verified 2026-09-02: `inklabels.png`, `mask.png`, layer `28.tif` md5-match
  `dl.ash2txt.org/fragments/Frag1/PHercParis2Fr47.volpkg/working/54keV_exposed_surface/`
- Ground truth: 5,339,364 ink px / 29,142,840 valid = 18.3% coverage

## Method

1. **Layer selection** — brightness-weighted ranking (layers 27/28/29 brightest)
   picks the most ink-visible layers.
2. **Mask-aware tiling** — 256 px tiles (32 px overlap) whose center lies outside
   the papyrus mask are dropped (1073 → 583 per layer).
3. **Vision inference** — each tile sent to Claude with a 5-rule decision prompt
   (mask edge=0, blank=0.02, fiber-only=0.08, cracks/stains=0.08, curvilinear
   ink-like strokes ≥0.65), returning structured JSON.
4. **Consensus fusion** — a tile is a consensus call only if **2+ of 3 layers**
   independently flag it ≥0.05, suppressing single-layer fiber/artifact hits.

## Results (Frag1, layers 27+28+29)

| Metric | Value |
|---|---|
| Tiles analyzed (per layer) | 583 (mask-aware) |
| API success | 100% (1,766 calls, 0 errors) |
| Consensus tiles (≥2 layers) | 111 |
| Tile-level F1 @ thr 0.01 | **0.668** (P 0.58 / R 0.79) |
| High-precision operating point | P = 1.000 @ thr 0.15 |

## Reproducibility

```bash
# API-only; no GPU needed
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...         # or any Anthropic-compatible router
export VESUVIUS_SCROLL=/path/Frag1/surface_volume/28.tif
python vesuvius_ink_detector.py --max-tiles 583 --threshold 0.05
```

Docker (no GPU):

```bash
docker build -t vesuvius-ink-detector .
docker run --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $PWD/Frag1:/data/Frag1:ro -v $PWD/out:/out \
  vesuvius-ink-detector --max-tiles 583 --threshold 0.05
```

Evaluation: `fuse_4layer.py` (free, local) fuses predictions; the PR sweep and
curve are in `results/analysis/pr_sweep_layer28.json` and
`results/analysis/pr_curve_layer28.png`.

## False-positive mitigation

The single biggest risk in ink detection is *pareidolia* — the eye (and model)
"reading" ink into papyrus fibers. This submission mitigates it three ways:

1. **Decision-rule prompt is biased against false positives** — blank papyrus and
   fiber-only texture are explicitly scored low, and mask edges hard-capped at 0.
2. **Multi-layer consensus** — a call requires 2+ independent layers;
   single-layer texture artifacts do not survive.
3. **Ground-truth + contrast validation** — the final candidate set is
   cross-checked against the official Frag1 `inklabels.png` (46 REAL_INK /
   40 GT_CONFIRMED tiles by both GT coverage and measurable ink-darkness:
   labeled ink pixels are measurably *darker* than adjacent papyrus). See
   `verification/verified_letters.csv`.

## Relevant files

| File | Purpose |
|---|---|
| `vesuvius_ink_detector.py` | Main detector (tiling, vision inference, heatmap/mask, checkpoint/resume) |
| `fuse_4layer.py` | Local consensus fusion (free) |
| `consensus_tiles.json` | 111 consensus detections w/ per-layer probability |
| `results/analysis/pr_sweep_layer28.json` | Full threshold sweep |
| `verification/verified_letters.csv` | GT+contrast-validated candidate tiles |
| `Dockerfile`, `requirements.txt` | Reproducible, no-GPU container |
