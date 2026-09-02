# Corrected Discord Post — Active ScrollPrize Server (2026-09-02)

Supersedes `discord_post_scrollprize.md` / `~/Desktop/results/READY_TO_POST.md` (both target
a 2-year-old thread on the old server). Post in a **current, active** ink-detection or
fragments thread on the **ScrollPrize Discord** (`https://discord.gg/V4fJhvtaQn`, channel
`1079907749569237093` is the OLD server — do not reuse).

## Why this corrects the earlier draft

- Old draft cited the 2024 "Iterative Labeling on fragments" thread (Youssef Nader) — that
  server/thread is stale. New post goes to the current server.
- Old numbers (78 tiles / 73 flagged) replaced by the corrected, valid-signals verification:
  **46 REAL_INK / 40 GT_CONFIRMED / 4 CONTRAST_ONLY / 35 UNCONFIRMED = 125 unique tiles**
  (cross-layer tile correlation dropped as an ink signal; only official GT agreement + ink
  darkness vs. papyrus are used).
- Reflects fully verified fragment identity (Frag1 = `PHercParis2Fr47`, md5-matched) and the
  no-GPU vision-API method now documented in `SUBMISSION_README.md` + `Dockerfile`.

---

## Final post message (copy-paste; links included, no upload needed)

🔍 **Frag 1 ink candidates — HP-grade spot check before I label/retrain**

Hi — I run a **no-GPU vision-API pipeline** on Frag 1 (= `PHercParis2Fr47`, 54 keV @ 3.24 µm,
data md5-verified against `dl.ash2txt.org`). Cloud vision model over 256 px tiles, strict
5-rule FP-biased prompt, multi-layer (2/3) consensus across L27/28/29, then GT + contrast
validation against the official labels.

After cleaning the verification to valid signals only (GT coverage + ink-darker-than-papyrus),
125 unique candidate tiles split as: **46 REAL_INK, 40 GT_CONFIRMED, 4 CONTRAST_ONLY, 35
UNCONFIRMED**. Tile-level F1 = 0.668 (P 0.58 / R 0.79), P = 1.000 at thr 0.15.

Following Paul Henderson's guidance to *be strict about false positives*, I want a
fresh-eyes check before these become training labels:

📦 **Package + crops for the confirmed/real tiles** (each across 3 CT layers):
https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor/tree/main/vesuvius/verification
(montage, zip + CSV in the folder)

**The ask (top 20, images 00–19):** for any you can read —
- Letter(s) you see
- Do the strokes form a **coherent row aligned with the papyrus fibers**?
- Confidence H/M/L

**Blind note:** `manifest.json` has coords — read the PNGs first if you want an unbiased
pass. Your expert take on row alignment and actual Greek letters is the most valuable input.

Anything you confirm as plausible writing becomes my first iterative labels; anything read
as fiber/noise gets dropped before retraining.

(Sent per the ScrollPrize data agreement — no raw-volume or reconstructed-word reveals
outside the server.)

Papyrology/reading experience very welcome; a strict unbiased look is just as useful. 🙏

## GitHub links (reference)
- Repo (detector, Docker, docs): https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor/tree/main/vesuvius
- Verification folder: https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor/tree/main/vesuvius/verification
- Montage: https://raw.githubusercontent.com/mzpakistani9-commits/loagaeth-linguistic-extractor/main/vesuvius/verification/top20_montage_thumb.png
- Zip: https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor/blob/main/vesuvius/verification/frag1_ink_verify.zip
- CSV: https://github.com/mzpakistani9-commits/loagaeth-linguistic-extractor/blob/main/vesuvius/verification/verified_letters.csv

## Honest caveats to keep in the post or answer in-thread
- 256 px tile @ 3.24 µm = **0.83 mm window**; organizers discourage >0.5 mm windows for ML
  outputs. State that we validated at letter-stroke scale via GT+contrast and plan a
  64 px (0.21 mm) compliant pass.
- The overview count in the snippet is 125 unique tiles; the "top 20" crops are a subset — be
  precise about which set you're asking people to check.