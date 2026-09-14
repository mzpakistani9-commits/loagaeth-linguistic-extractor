# Voynich Manuscript — Beinecke MS 408

## Corpus Statistics
- Beinecke MS 408, carbon-dated 1404–1438 CE (95% CI, University of Arizona). 116 surviving folios.
- 37,919 words, 8,114 unique word types.
- Top words: daiin (892), qol (654), ol (589), chor (412), dain (382).
- Entropy h1 ≈ 3.7 bits/char, h2 ≈ 2.6 bits/char.
- Sections: Herbal (66v), Astronomical, Balneological, Cosmological, Pharmaceutical, Recipes.

## The IC Paradox
- Index of Coincidence (IC) = 0.027 — BELOW the random baseline (~0.038): unprecedented for any language or simple cipher.
- Yet the text fits Zipf-Mandelbrot perfectly — natural-language-shaped word frequency distribution.
- Resolution path: characters are less repetitive than chance (deliberate diversity maximization) while deep linguistic regularity persists → consistent with a letterform-manipulation cipher, not substitution.

## Tucker & Tucker (2013) — Middle English "Old Law Hands" Cipher
Core thesis: the text is Middle English written by physically manipulating Latin alphabet letterforms (flipped, rotated, stem-removed, loop-altered), NOT a substitution cipher.

## All 26 Manipulations (EVA)
- a = flipped and reversed (U+FF417)
- b = stem removed (U+FF447)
- c = top removed (U+FF400)
- d = stem moved to top (MISSING glyph)
- e = stem removed (U+FF414)
- f = middle stem removed
- g = upper + flip (U+FF40C)
- h = alter stem (U+FF404)
- i = connect bottom (U+FF41A) — KEY for minim sequences (aiin)
- k = remove right (U+FF408)
- l = remove bottom + double (U+FF48A)
- m = upside down (U+FF505)
- n = upside down (U+FF501)
- p = add loop + stem (U+FF420)
- q = upside down + partial (U+FF4B1)
- r = split in half (U+FF403)
- s = none (U+FF409)
- t = rotate 180° + reverse (U+FF422)
- u = connect top (U+FF4C0)
- v = upside down + reverse (U+FF4C1)
- w = remove curves (U+FF41B)
- x = remove bottom (EVA+91)
- y = remove stem + flip (U+FF5B9)
- z = flip top (U+FF40F)

## Minim Sequences
- aiin = a + i + i + n, NOT always preceded by EVA-d. The connected-bottom 'i' (U+FF41A) is the key marker stroke for aiin minim runs.

## Working Guidance
- When working with "daiin qol chor" style BOT (Basic Old Text) sequences, use EVA transcription and test the Tucker manipulation for each sign.
- Apply the honesty rule: alternative readings are typed [UNDECIPHERED] with confidence POSSIBLE/UNKNOWN.