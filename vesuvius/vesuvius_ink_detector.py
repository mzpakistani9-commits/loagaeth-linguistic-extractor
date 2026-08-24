#!/usr/bin/env python3
import os
import sys
import anthropic
from pathlib import Path
from PIL import Image
import numpy as np
import json
import base64
import time
import io
from tqdm import tqdm
# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
SCROLL_IMAGE_PATH = os.environ.get(
    "VESUVIUS_SCROLL",
    str(Path.home() / "Desktop/vesuvius_data/Frag1/surface_volume/28.tif")
)  # brightest layer (mean=16438, brightest=33.4%) — prioritized from layer analysis
# Alternative priority layers: 27, 29, 26, 25, 30, 24, 31 (see layer_priorities.json for full ranking)
# To sample multiple layers: run detector separately with different SCROLL_IMAGE_PATH values
OUTPUT_DIR        = "results"            # where to save submission files
TILE_SIZE         = 256                  # pixels per tile (256 works well with Claude)
OVERLAP           = 32                   # tile overlap in pixels (reduces edge artifacts)
MAX_TILES         = None                 # limit for cost control; set None for full scan
CONFIDENCE_THRESHOLD = 0.4              # ink probability threshold for binary mask
MODEL_NAME        = os.environ.get("VESUVIUS_MODEL", "claude-opus-4-8")  # via AgentRouter
# ─────────────────────────────────────────────
# SYSTEM PROMPT — injected into every API call
# ─────────────────────────────────────────────
#
# You are analyzing a 256x256 pixel grayscale tile from an X-ray CT scan of a carbonized
# Herculaneum papyrus scroll (79 AD). The papyrus has been flattened and the surface is the
# bright region. Ink from ancient Greek writing appears as DARKER regions on the bright
# papyrus surface — the opposite of what you might expect.
#
# DECISION RULES — follow these exactly:
#
# 1. If the tile is mostly black/dark with a bright diagonal or jagged edge: this is a
#    MASK EDGE, not papyrus. Set ink_probability = 0.0.
#
# 2. If the tile is a uniform bright field with no texture variation: BLANK PAPYRUS.
#    Set ink_probability = 0.02.
#
# 3. If you see ANY of these features on a bright papyrus background:
#    - Dark curvilinear strokes (curved, not straight)
#    - Dark marks that could be horizontal, vertical, or diagonal letter strokes
#    - Clusters of dark marks near each other (suggesting a word or letter group)
#    - Any mark that is NOT a straight crack or fold line
#    → Set ink_probability = 0.65 minimum. Do NOT hedge below 0.5 when these are present.
#
# 4. If you see straight linear cracks or fold lines only: Set ink_probability = 0.08.
#
# 5. For Greek uncial script, look specifically for:
#    - Curved forms: Ο (circle), Σ (curved S), Ε (three horizontal bars), Φ (circle with
#      vertical), Θ (circle with bar)
#    - Vertical strokes with serifs: Ι, Π, Η, Τ
#    - Diagonal strokes: Α, Χ, Λ, Κ
#    If you identify any of these with confidence, name the letter in letter_candidates.
#
# CRITICAL: You are looking at VERY FAINT traces. The scroll is 2000 years old and
# carbonized. What looks like a faint smudge IS likely ink. When uncertain between "noise"
# and "ink", CHOOSE INK and set probability 0.6.
#
# Respond ONLY with valid JSON, no markdown, no preamble:
#
# {
#   "ink_probability": <float 0.0-1.0>,
#   "ink_regions": [{"x": <int>, "y": <int>, "w": <int>, "h": <int>, "confidence": <float>}],
#   "letter_candidates": ["<Greek letter or description>"],
#   "notes": "<one sentence: what you see and why you scored it this way>"
# }
#
SYSTEM_PROMPT = """You are analyzing a 256x256 pixel grayscale tile from an X-ray CT scan of a carbonized Herculaneum papyrus scroll (79 AD). The papyrus has been flattened and the surface is the bright region. Ink from ancient Greek writing appears as DARKER regions on the bright papyrus surface — the opposite of what you might expect.

DECISION RULES — follow these exactly:



   - Dark curvilinear strokes (curved, not straight)
   - Dark marks that could be horizontal, vertical, or diagonal letter strokes
   - Clusters of dark marks near each other (suggesting a word or letter group)
   - Any mark that is NOT a straight crack or fold line
   → Set ink_probability = 0.65 minimum. Do NOT hedge below 0.5 when these are present.


   - Curved forms: Ο (circle), Σ (curved S), Ε (three horizontal bars), Φ (circle with vertical), Θ (circle with bar)
   - Vertical strokes with serifs: Ι, Π, Η, Τ
   - Diagonal strokes: Α, Χ, Λ, Κ
   If you identify any of these with confidence, name the letter in letter_candidates.

CRITICAL: You are looking at VERY FAINT traces. The scroll is 2000 years old and carbonized. What looks like a faint smudge IS likely ink. When uncertain between "noise" and "ink", CHOOSE INK and set probability 0.6.

Respond ONLY with valid JSON, no markdown, no preamble:
{
  "ink_probability": <float 0.0-1.0>,
  "ink_regions": [{"x": <int>, "y": <int>, "w": <int>, "h": <int>, "confidence": <float>}],
  "letter_candidates": ["<Greek letter or description>"],
  "notes": "<one sentence: what you see and why you scored it this way>"
}
"""
#
# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────
#
def load_scroll_image(path: str) -> Image.Image:
    """Load scroll image, converting 16-bit TIFF to 8-bit for Claude."""
    print(f"Loading scroll image: {path}")
    img = Image.open(path)
    
    # Convert 16-bit to 8-bit if needed (CT scans are often 16-bit)
    if img.mode == "I;16" or img.mode == "I":
        arr = np.array(img, dtype=np.float32)
        # Normalize to 0-255 with contrast enhancement
        p2, p98 = np.percentile(arr, [2, 98])
        arr = ((arr - p2) / (p98 - p2) * 255).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode="RGB")
    
    return img


def image_to_base64(img: Image.Image) -> str:
    """Convert a PIL Image to base64 string."""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.standard_b64encode(buffered.getvalue()).decode("utf-8")


def tile_image(img: Image.Image, tile_size: int, overlap: int) -> list:
    """Split an image into overlapping tiles, returning (tile_img, tile_x, tile_y)."""
    w, h = img.size
    tiles = []
    step = tile_size - overlap
    for y in range(0, h - overlap, step):
        for x in range(0, w - overlap, step):
            # Crop tile
            tile = img.crop((x, y, min(x + tile_size, w), min(y + tile_size, h)))
            tiles.append((tile, x, y))
    return tiles


def analyze_tile_with_claude(client: anthropic.Anthropic, tile: Image.Image,   tile_x: int, tile_y: int) -> dict:
    """Send one tile to Claude and parse the ink detection response."""
    img_b64 = image_to_base64(tile)
    
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyze this scroll tile for ink. Return JSON only."
                        }
                    ]
                }
            ]
        )
        
        # opus-4-8 may prepend a ThinkingBlock; use the first text block
        text_blocks = [b for b in response.content if getattr(b, "type", "") == "text"]
        if not text_blocks:
            raise ValueError(f"No text block in response (blocks: {[getattr(b,'type','?') for b in response.content]})")
        raw_text = text_blocks[0].text.strip()
        
        # Strip markdown code fences if Claude adds them anyway
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        result = json.loads(raw_text)
        
        # Ensure required fields exist
        if "ink_probability" not in result:
            result["ink_probability"] = result.get("probability", 0.0)
        if "ink_regions" not in result:
            result["ink_regions"] = []
        if "letter_candidates" not in result:
            result["letter_candidates"] = []
        result["tile_x"] = tile_x
        result["tile_y"] = tile_y
        
        return result
        
    except Exception as e:
        print(f"  ERROR analyzing tile ({tile_x},{tile_y}): {e}")
        return {
            "ink_probability": 0.0,
            "ink_regions": [],
            "letter_candidates": [],
            "notes": f"API error: {str(e)[:60]}",
            "tile_x": tile_x,
            "tile_y": tile_y,
            "status": "error"
        }


def save_outputs(results, prob_map, img_size, output_dir, threshold):
    """Save raw results, heatmap, binary mask, and summary."""
    from datetime import datetime
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw results
    raw_path = os.path.join(output_dir, f"ink_detection_raw_{ts}.json")
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save heatmap
    heatmap_path = os.path.join(output_dir, f"ink_heatmap_{ts}.png")
    img = Image.fromarray((np.clip(prob_map, 0, 1) * 255).astype(np.uint8))
    img.save(heatmap_path)
    
    # Save binary mask
    mask_path = os.path.join(output_dir, f"ink_mask_{ts}.png")
    mask = (prob_map >= threshold)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    mask_img.save(mask_path)
    
    # Save summary
    total_tiles = len(results)
    successful = sum(1 for r in results if r.get("status") != "error")
    ink_tiles = sum(1 for r in results if r.get("ink_probability", 0) >= threshold)
    gt = np.array(Image.open("/home/zubair/Desktop/vesuvius_data/Frag1/inklabels.png")) > 0
    inter = ((prob_map >= threshold) & gt).sum()
    precision = inter / max(((prob_map >= threshold).sum()), 1)
    recall = inter / max(gt.sum(), 1)
    summary = {
        "run_timestamp": ts,
        "scroll_image": SCROLL_IMAGE_PATH,
        "total_tiles_analyzed": total_tiles,
        "successful_api_calls": successful,
        "tiles_above_threshold": ink_tiles,
        "threshold_used": threshold,
        "ink_coverage_percent": round(ink_tiles / max(total_tiles, 1) * 100, 2),
        "model": MODEL_NAME,
        "author": "Muhammad Zubair",
        "contact": "mzpakistani9@gmail.com",
        "github": "https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor"
    }
    summary_path = os.path.join(output_dir, f"summary_{ts}.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSaved: {raw_path}")
    print(f"Saved: {heatmap_path}")
    print(f"Saved: {mask_path}")
    print(f"\nSUBMISSION SUMMARY")
    print(f"  run_timestamp: {ts}")
    print(f"  scroll_image: {SCROLL_IMAGE_PATH}")
    print(f"  total_tiles_analyzed: {total_tiles}")
    print(f"  successful_api_calls: {successful}")
    print(f"  tiles_above_threshold: {ink_tiles}")
    print(f"  threshold_used: {threshold}")
    print(f"  ink_coverage_percent: {summary['ink_coverage_percent']}")
    print(f"  model: {MODEL_NAME}")
    
    return summary


# ─────────────────────────────────────────────
# MAIN Pipeline
# ─────────────────────────────────────────────
#
def main():
    global MAX_TILES
    if "--max-tiles" in sys.argv:
        try:
            MAX_TILES = int(sys.argv[sys.argv.index("--max-tiles") + 1])
            print(f"CLI: --max-tiles={MAX_TILES}")
        except (ValueError, IndexError):
            print("WARN: could not parse --max-tiles; using full scan")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable first.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url) if base_url else anthropic.Anthropic(api_key=api_key)
    print("✓ Anthropic client initialized")
    
    # Load or demo image
    if not Path(SCROLL_IMAGE_PATH).exists():
        print("Scroll image not found — running demo mode with synthetic data")
        # Demo mode creates a synthetic test image
        img = Image.new("RGB", (8181, 6330), (128, 128, 128))
        for i in range(200):
            x = np.random.randint(0, 7926)
            y = np.random.randint(0, 5527)
            size = np.random.randint(10, 50)
            cv2.rectangle(img, (x, y), (x+size, y+size), (random.randint(0,255), random.randint(0,255), random.randint(0,255)), -1)
        img_gray = img.convert("L")
    else:
        img = load_scroll_image(SCROLL_IMAGE_PATH)
    
    print(f"Image size: {img.size[0]}x{img.size[1]} pixels")
    
    # Tile the image
    print(f"\nTiling image (tile={TILE_SIZE}px, overlap={OVERLAP}px)...")
    tiles = tile_image(img, TILE_SIZE, OVERLAP)
    print(f"  Total tiles: {len(tiles)}")
    
    # Mask-aware sampling: drop tiles whose center falls outside the papyrus mask
    mask_path = Path(SCROLL_IMAGE_PATH).parent.parent / "mask.png"
    if mask_path.exists() and MAX_TILES:
        from PIL import Image as _Img
        _mask = _Img.open(mask_path).convert("L")
        _marr = (np.array(_mask) > 0)
        before = len(tiles)
        tiles = [(im, x, y) for im, x, y in tiles
                 if y + TILE_SIZE // 2 < _marr.shape[0] and x + TILE_SIZE // 2 < _marr.shape[1]
                 and _marr[y + TILE_SIZE // 2, x + TILE_SIZE // 2]]
        print(f"  Mask filter: {before} -> {len(tiles)} tiles (dropped {before-len(tiles)} outside papyrus)")
    
    if MAX_TILES and len(tiles) > MAX_TILES:
        # Sample evenly across the image rather than just taking first N
        step = len(tiles) // MAX_TILES
        tiles = tiles[::step][:MAX_TILES]
        print(f"  Sampling {len(tiles)} tiles (MAX_TILES={MAX_TILES})")
    else:
        print(f"  Total tiles: {len(tiles)}")
    
    # Estimate cost
    est_cost = len(tiles) * 0.003  # ~$0.003 per tile with claude-opus-4-8
    print(f"  Estimated API cost: ~${est_cost:.2f}")
    print()
    
    # Analyze tiles
    results = []
    errors  = 0

    # --- Crash-safe checkpointing: resume support ---
    # Checkpoint file is per-layer, e.g. results/ckpt_layer26.json
    _layer_stem = Path(SCROLL_IMAGE_PATH).stem  # e.g. "26"
    ckpt_path = OUTPUT_DIR and Path(OUTPUT_DIR) / f"ckpt_layer{_layer_stem}.json" or Path(f"ckpt_layer{_layer_stem}.json")
    done_map = {}  # "(tx,ty)" -> result dict
    if ckpt_path.exists():
        try:
            with open(ckpt_path) as _f:
                for _r in json.load(_f):
                    done_map[f'({int(_r["tile_x"])},{int(_r["tile_y"])})'] = _r
            print(f"  RESUME: found checkpoint with {len(done_map)} completed tiles -> {ckpt_path}")
        except Exception as _e:
            print(f"  Checkpoint unreadable ({_e}); starting fresh")

    def _save_checkpoint():
        """Atomic write: tmp file then rename, so shutdown never corrupts it."""
        tmp = str(ckpt_path) + ".tmp"
        with open(tmp, "w") as _f:
            json.dump(list(done_map.values()), _f)
        os.replace(tmp, ckpt_path)

    for tile_img, tx, ty in tqdm(tiles, desc="Analyzing tiles"):
        key = f"({tx},{ty})"
        if key in done_map:
            results.append(done_map[key])
            continue
        result = analyze_tile_with_claude(client, tile_img, tx, ty)
        results.append(result)
        if result.get("status") != "error":
            done_map[key] = result
            _save_checkpoint()
        
        if result.get("status") != "ok":
            errors += 1
        
        # Rate limiting — claude-opus-4-8 is fast but be polite
        time.sleep(0.3)
    
    print(f"\n✓ Analyzed {len(results)} tiles ({errors} errors)")
    
    # Build probability map
    print("Building probability map...")
    img = Image.open(SCROLL_IMAGE_PATH)
    H, W = img.size[1], img.size[0]
    prob = np.zeros((H, W), np.float32)
    cnt = np.zeros((H, W), np.float32)
    
    for r in results:
        x, y = r["tile_x"], r["tile_y"]
        p = r.get("ink_probability", 0.0)
        prob[y:y+TILE_SIZE, x:x+TILE_SIZE] += p
        cnt[y:y+TILE_SIZE, x:x+TILE_SIZE] += 1
    
    avg = np.divide(prob, np.maximum(cnt, 1), where=cnt>0)
    
    # Save outputs
    summary = save_outputs(results, avg, (H, W), OUTPUT_DIR, CONFIDENCE_THRESHOLD)
    
    # Write consensus report if we have multi-layer data
    consensus_path = os.path.join(OUTPUT_DIR, "consensus_tiles.json")
    # Check if we have multi-layer results to fuse
    layer_data = None  # Would be populated by fusion script
    # ... (fusion would happen externally)
    
    print("\nDone. Submit the 'results/' folder to scrollprize.org")


if __name__ == "__main__":
    main()