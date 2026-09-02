# Independent Reader Verification — Vesuvius Frag1 (PHercParis2 Fr47)

**Purpose:** Get a second, independent human read on tiles flagged as containing ink,
WITHOUT the reader seeing any labels, priors, or prior hypotheses. This is the clean
test that distinguishes **real letterforms** from **pareidolia** (pattern-matching on
fiber texture/staining).

## Package Contents

- `00_tile_*.png` ... `72_tile_*.png` — 73 enhanced crops, ranked by ground-truth ink
  fraction (highest first). Each image shows:
  - **Top (large):** layer 28 — the brightest, most ink-visible layer
  - **Bottom-left (small):** layer 27 (adjacent CT layer)
  - **Bottom-right (small):** layer 29 (adjacent CT layer)
- `top5_confirmed/` — the 5 highest-confidence letter candidates (A–E), shown in the
  same 3-layer layout. These were the starting point of this verification exercise.
- `manifest.json` — technical metadata (x,y coords, ground-truth fraction). **Do NOT
  read this before doing your blind read** — it biases you.

## The Blind-Reading Protocol (IMPORTANT)

Read the images BEFORE looking at manifest.json or any other context. For each image:

1. **Do NOT try to read words or decode meaning.** Just answer: are there 1-2 clear,
   consistent letterform-like shapes that persist in the SAME position across all
   three layers (big + both small thumbnails)?
2. If yes, name the letter(s) you'd assign (e.g., "A", "Y/Ψ", "C/E").
3. If the shape is present in layer 28 (big) but NOT in the adjacent layers (small),
   that suggests fiber texture, NOT real ink — mark it "layer-only".
4. Rate confidence: **high** (clear, persistent) / **medium** (persistent but faint) /
   **low** (present in one layer only, or ambiguous).

## Fill in this table (each row = one image)

| Image # | Letter(s) seen | Present in all 3 layers? | Confidence (H/M/L) | Notes |
|---------|---------------|--------------------------|--------------------|-------|
| 00      |               |                          |                    |       |
| 01      |               |                          |                    |       |
| 02      |               |                          |                    |       |
| ...     |               |                          |                    |       |

**Focus on the top 20 (00-19)** — those have the strongest ground-truth signal. If
you confirm the same letterforms independently, that's real ink. If you see nothing
or inconsistent shapes, that's pareidolia.

## Ground Truth Context (read AFTER your blind pass)

- These 73 tiles were flagged by an AI vision detector and cross-checked against the
  competition's official ground-truth ink labels.
- The top ~20 have 60-91% of their area covered by official ground-truth ink.
- Detection false-positive rate is ~34% overall — so roughly 1 in 3 of these may be
  fiber/edge artifact, not ink. Your independent read is what separates them.

## How to send results

Return your filled table. The goal is the top-20 list: tiles where two independent
readers (you + the machine model) agree on the same letterform.
