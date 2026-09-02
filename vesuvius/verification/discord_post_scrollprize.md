# Tailored Post for Vesuvius Challenge / ScrollPrize Discord

## Where to post
- **Best thread:** "Iterative Labeling on fragments" by Youssef Nader — exactly matches this
  work (improving ink detection on fragments' hidden layers via iterative labeling).
  https://discord.com/channels/1079907749569237093/1279263442913591349/1279263442913591349
- **Good alternative:** any ink-detection community-project thread.
- **Discord invite:** https://discord.com/invite/uTfNwwecCQ

## Context that shapes the post
Paul Henderson's Aug 2026 "From CT Scan to Ancient Text" post is the community's canonical
verification guidance. It says: **"Be strict about false positives... verify that candidate
text forms coherent rows aligned with the papyrus fibers."** So the community validates ink
by row-alignment + expert greek-letter confirmation — I frame my request around that, not a
generic blind read.

---
## Post (tailored, matching the "Iterative Labeling" conversation)

**Title:** 🔁 Frag1 ink candidates — would love a spot-check before I label/retrain

**Body:**

Hi — following the iterative-labeling thread. I'm running a vision-model tile pipeline on
Frag1, got ~73 tiles flagged as ink, cross-checked against official labels (66% agreement;
ink pixels are measurably darker than surrounding papyrus on these). Following the guidance
to *be strict about false positives*, I want a fresh-eyes check before I feed these into a
label/retrain loop.

📦 21 MB, 78 crops — each tile across 3 CT layers (L28 large + L27/29 thumbs) so you can
check persistence. Top-20 montage thumbnail below. Zip: `frag1_ink_verify.zip`

**The ask (top 20, images `00`–`19`):** for any you can read —
- Letter(s) you see
- Do the strokes form a **coherent row aligned with the papyrus fibers**? (the criterion I
  should hold the detector to)
- Confidence H/M/L

**Blind note:** manifest.json has coords — read the PNGs first if you want an unbiased pass,
but your expert take on row-alignment and actual Greek letters is the most valuable input.

Anything you confirm as plausible writing becomes my first iterative-labels. Anything you
read as fiber/noise gets dropped before retraining.

(Tile crops shared here per the scrollprize Discord data agreement — no reconstructed-word
or raw-data reveals outside the server.)

Papyrology/reading experience welcome; a strict unbiased look is just as useful.

Thanks 🙏

---
## Notes
- Aligns with Youssef Nader's Iterative Labeling thread + Paul Henderson's Aug 2026 guidance.
- Frames output as "labels to retrain on" → matches progress-prize iterative workflow.
- Montage thumbnail: /home/zubair/Desktop/results/top20_montage_thumb.png
