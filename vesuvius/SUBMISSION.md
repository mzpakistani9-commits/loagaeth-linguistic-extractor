# Vesuvius Challenge — Ink Detection Submission
# Muhammad Zubair | mzpakistani9@gmail.com
# GitHub: https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor

## Submission Summary

This submission uses a tile-based Claude Opus 4.8 vision pipeline (routed through AgentRouter) to detect ink regions in Herculaneum papyrus scroll fragments from the Vesuvius Challenge dataset.

### Data Used

- **Fragment**: Frag1 (PHercParis2Fr47) — Vesuvius Challenge competition fragment
- **Surface volume layers**: 65 .tif files (8181×6330, 16-bit TIFF, mode I;16B)
- **Ground truth**: `inklabels.png` (5,339,364 ink pixels of 29,142,840 valid pixels, 18.3% coverage)
- **Layer selection**: Priority given to layers 27, 28, 29 (brightest by mean intensity)
- **Total API calls**: 1,766 across 583 tiles × 3 layers, zero errors

### Methodology

1. **Layer selection**: Brightness-weighted prioritization identified layers 27, 28, 29 as most ink-visible.
2. **Tile-based analysis**: 256×256 pixel tiles with 32-pixel overlap, Claude Opus 4.8 with explicit decision rules.
3. **Probability aggregation**: Tile-level probabilities aggregated into full-image heatmap.
4. **Multi-layer fusion**: Tiles where 2+ of 3 layers independently detect ink_probability ≥ 0.05 are fused by average probability.

### Results (583-tile full scan on layer 28, threshold 0.05)
- **Total tiles analyzed**: 583 (mask-aware sampling dropped 490/1073 as outside papyrus)
- **Successful API calls**: 583 (zero errors)
- **Tiles above threshold (0.05)**: 121
- **Ink coverage estimate**: 20.75%

### Fused 3-layer consensus (layers 27+28+29, threshold 0.05)
- **Consensus tiles (2+ layers)**: 111
- **Tile-level F1 @ thr=0.01**: 0.67 (precision 0.58, recall 0.79)

### Key Innovations

- **Brightness-weighted layer selection**: Prioritizing the most ink-visible layers.
- **Multi-layer consensus fusion**: 2+ of 3 layers agreeing provides stronger evidence.
- **Explicit decision-rule prompt**: Claude prompted with 5 strict rules for ink classification.
- **AgentRouter API routing**: All calls routed through AgentRouter.

### Files Submitted

- `consensus_tiles.json` — 111 tiles confirmed across 2+ of 3 layers
- `mask_fuse3.png` — Fused 3-layer binary ink mask
- `heatmap_fuse3.png` — Fused 3-layer probability heatmap
- `submission_description.md` — This file

### Contact

Muhammad Zubair | mzpakistani9@gmail.com
GitHub: https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor
