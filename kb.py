"""
RAG knowledge layer for the Loagaeth Linguistic Extractor (OMEGA v5).

TIER 1 — Deterministic per-script retrieval (zero model/API cost)
    knowledge/*.md files are chunked by "## " section; the selected
    scripts in the UI map directly to files so only relevant references
    are injected into the prompt (instead of the whole ~15KB KB on
    every request).

TIER 2 — Semantic retrieval (top-k embedding search)
    sentence-transformers all-MiniLM-L6-v2 (small, local, free) ranks
    chunks for the free-text query. If the model is unavailable (no
    internet / memory), a dependency-free character n-gram scorer is
    used so retrieval never breaks.

No API keys are stored in this module.
"""

import re
import threading
from collections import Counter
from pathlib import Path

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5                          # semantic chunks (Tier 2)
KB_MAX_CHARS_DEFAULT = 7000        # prompt budget for retrieved context
ALWAYS_INCLUDE = ["protocol"]      # methodology/honesty always injected

# Script name -> dedicated knowledge file (stem). "" = LLM handles directly.
SCRIPT_KB_MAP = {
    # Zubair Research (Angelic/Ancient)
    "Indus Valley Script": "indus",
    "Enochian (Angelical Language)": "enochian",
    "Liber Loagaeth (49×49)": "loagaeth",
    "Book of Soyga / Aldaraia": "research",
    "Voynich MS (EVA/Tucker)": "voynich",
    "Hildegard Lingua Ignota": "hildegard",
    "Angel Runic (spiriform)": "angel-runic",
    "Hungarian Rovás (12 variants)": "rovash",
    "Ancient Hebrew (pictographic)": "hebrew",
    "Ge'ez / Ethiopic": "classical-scripts",
    "Andalusi Arabic (medieval)": "classical-scripts",
    "Egyptian Hieroglyphic (Fabricius)": "hieroglyphs",
    # Undeciphered Ancient
    "Linear A (Minoan)": "undeciphered",
    "Proto-Elamite": "undeciphered",
    "Rongorongo (Easter Island)": "undeciphered",
    "Phaistos Disc": "undeciphered",
    "Meroitic": "undeciphered",
    "Rohonc Codex": "undeciphered",
    "Proto-Sinaitic": "undeciphered",
    "Wadi el-Hol": "undeciphered",
    "Byblos Syllabary": "undeciphered",
    # Constructed / Angelic
    "Celestial Alphabet (Agrippa)": "enochian",
    "Malachim": "enochian",
    "Passing the River": "enochian",
    "Theban Alphabet": "enochian",
    "Elder Futhark Runes": "classical-scripts",
    "Younger Futhark": "classical-scripts",
    "Ogham": "classical-scripts",
    "Glagolitic": "classical-scripts",
    "Gothic (Wulfila)": "classical-scripts",
    # Ancient Deciphered
    "Egyptian Hieroglyphic": "hieroglyphs",
    "Hieratic": "hieroglyphs",
    "Demotic": "hieroglyphs",
    "Coptic": "hieroglyphs",
    "Sumerian Cuneiform": "classical-scripts",
    "Akkadian": "classical-scripts",
    "Babylonian": "classical-scripts",
    "Hittite Cuneiform": "classical-scripts",
    "Old Persian Cuneiform": "classical-scripts",
    "Phoenician": "classical-scripts",
    "Ugaritic": "classical-scripts",
    "Aramaic": "classical-scripts",
    "Linear B (Mycenaean Greek)": "classical-scripts",
    "Etruscan": "classical-scripts",
    "Luwian": "classical-scripts",
    "Mayan Glyphs": "classical-scripts",
    "Nahuatl": "classical-scripts",
    "Oracle Bone Script": "classical-scripts",
    "Classical Chinese": "classical-scripts",
    "Sanskrit / Brahmi / Pali": "classical-scripts",
    "Kharosthi": "classical-scripts",
}

# Aliases used to auto-detect the relevant knowledge files from free text.
_FILE_ALIASES = {
    "research": ["soyga", "aldaraia", "zubair", "seed keyword", "diagonal",
                 "shemhamphorasch", "shem ha-mphorasch", "reeds", "cellular automaton"],
    "enochian": ["enochian", "angelical", "celestial alphabet", "malachim",
                 "passing the river", "theban", "aethyr", "aethyrs", "watchtower",
                 "governor", "sigillum dei", "iad", "dee", "kelley"],
    "loagaeth": ["loagaeth", "liber loagaeth", "sloane 3189", "49x49", "49×49", "leaf"],
    "voynich": ["voynich", "eva", "tucker", "vms", "beinecke 408", "daiin", "qol",
                "aiin", "ollad", "uncial"],
    "hildegard": ["hildegard", "lingua ignota", "riesencodex", "aizniz", "aieganz"],
    "angel-runic": ["angel runic", "runic", "spiriform", "divine symbol", "spirit symbol"],
    "rovash": ["rovas", "rovás", "hungarian", "fischer", "szeged", "nickelsburg",
               "énlaka", "enlaka", "bologna rovas"],
    "hebrew": ["ancient hebrew", "pictographic hebrew", "aleph", "beth", "gimel",
               "zayin", "hebrew letter", "hebrew pictographic"],
    "indus": ["indus", "is-342", "is-267", "is-391", "parpola", "harappa",
              "mohenjo", "dholavira", "kalibangan", "dravidian", "indus valley"],
    "hieroglyphs": ["hieroglyph", "gardiner", "fabricius", "egyptian", "hieratic",
                    "demotic", "coptic", "berlin-brandenburg", "hieroglyphs",
                    "n35", "g17"],
    "divine-names": ["divine name", "cross-religious", "cognate", "yhwh", "allah",
                     "alaha", "theos", "deva", "kadavul", "aum", "divine chain"],
    "undeciphered": ["linear a", "proto-elamite", "rongorongo", "phaistos",
                     "meroitic", "rohonc", "proto-sinaitic", "wadi el-hol",
                     "byblos", "undeciphered"],
    "classical-scripts": ["cuneiform", "sumerian", "akkadian", "babylonian",
                          "hittite", "linear b", "phoenician", "ugaritic",
                          "aramaic", "old persian", "mayan", "etruscan", "luwian",
                          "oracle bone", "brahmi", "sanskrit", "kharosthi",
                          "futhark", "ogham", "glagolitic", "gothic", "hiero"],
}


def _normalize(text: str) -> str:
    return re.sub(r"[\W_]+", " ", text.lower())


def _ngrams(text: str, n: int):
    t = _normalize(text)
    return {t[i:i + n] for i in range(len(t) - n + 1)}


class KnowledgeBase:
    def __init__(self, kb_dir: str = None, load_model: bool = True):
        self.kb_dir = Path(kb_dir) if kb_dir else Path(__file__).parent / "knowledge"
        self.chunks = []          # {"file": stem, "heading": str, "text": str}
        self.model = None
        self.embeddings = None
        self._model_error = None
        self._load_files()
        if load_model:
            self._start_model_loader()

    # ── loading ────────────────────────────────────────────────────────────
    def _load_files(self):
        if not self.kb_dir.exists():
            return
        for md in sorted(self.kb_dir.glob("*.md"), key=lambda p: p.name):
            self._load_file(md)

    def _load_file(self, path: Path):
        stem = path.stem
        raw = path.read_text(encoding="utf-8")
        # First "# Title" line = file heading
        lines = raw.splitlines()
        title = ""
        sections = []
        current_head = []
        current_body = []
        for line in lines:
            if line.startswith("## "):
                if current_head or current_body:
                    sections.append((" ".join(current_head), "\n".join(current_body)))
                current_head = [line[3:].strip()]
                current_body = []
            elif line.startswith("# ") and not title:
                title = line[2:].strip()
            else:
                if current_head:
                    current_body.append(line)
                # pre-title content folded into title chunk
        if current_head or current_body:
            sections.append((" ".join(current_head), "\n".join(current_body)))
        for head, body in sections:
            heading = head.strip() or title or stem
            text = body.strip()
            if text:
                self.chunks.append({"file": stem, "heading": heading, "text": text})
        if not self.chunks and title:
            # fall back to whole file as one chunk
            self.chunks.append({"file": stem, "heading": title, "text": raw.strip()})

    def _start_model_loader(self):
        def loader():
            try:
                from sentence_transformers import SentenceTransformer  # noqa
                m = SentenceTransformer(EMBED_MODEL)
                texts = [c["heading"] + "\n" + c["text"][:1500] for c in self.chunks]
                self.embeddings = m.encode(
                    texts, normalize_embeddings=True, convert_to_numpy=True,
                    batch_size=32, show_progress_bar=False,
                )
                self.model = m
            except Exception as e:  # pragma: no cover — model optional
                self.model = None
                self._model_error = str(e)
        threading.Thread(target=loader, daemon=True).start()

    # ── tier 1: deterministic ──────────────────────────────────────────────
    def by_files(self, file_set) -> list:
        seen = set()
        out = []
        for c in self.chunks:
            if c["file"] in file_set and (c["file"], c["heading"]) not in seen:
                seen.add((c["file"], c["heading"]))
                out.append(c)
        return out

    def detect_files(self, query: str) -> set:
        q = _normalize(query)
        hits = set()
        for alg in _FILE_ALIASES:
            for alias in _FILE_ALIASES[alg]:
                if alias in q:
                    hits.add(alg)
        return hits

    def tier1(self, scripts, query="") -> list:
        files = set(ALWAYS_INCLUDE)
        for s in scripts or []:
            f = SCRIPT_KB_MAP.get(s, "")
            if f:
                files.add(f)
        files |= self.detect_files(query)
        return self.by_files(files)

    # ── tier 2: semantic ───────────────────────────────────────────────────
    @property
    def model_ready(self):
        return self.model is not None and self.embeddings is not None

    def _nscore(self, query: str, text: str) -> float:
        """Dependency-free char-n-gram overlap + rare-token boost (no model)."""
        q = _normalize(query)
        if not q:
            return 0.0
        score = 0.0
        for n in (3, 4, 5):
            qg = _ngrams(query, n)
            tg = _ngrams(text, n)
            if tg:
                score += len(qg & tg) / float(len(tg))
        q_tokens = Counter(q.split())
        corpus_tokens = self._token_df
        for tok, c in q_tokens.items():
            df = corpus_tokens.get(tok, 1)
            if len(tok) >= 4 and df <= 3:   # rare tokens are strong signals
                score += c * 0.5
        return score

    def _ensure_token_df(self):
        if getattr(self, "_token_df", None) is None:
            df = Counter()
            for c in self.chunks:
                df.update(set(_normalize(c["text"]).split()))
            self._token_df = df
        return self._token_df

    def tier2(self, query: str, top_k: int = TOP_K, exclude=()) -> list:
        if not query or not self.chunks:
            return []
        self._ensure_token_df()
        scores = self._score_all(query)
        exclude_keys = set(exclude) if exclude else set()
        out = []
        for i in sorted(scores, key=lambda i: -scores[i]):
            c = self.chunks[i]
            if (c["file"], c["heading"]) in exclude_keys:
                continue
            out.append(c)
            if len(out) >= top_k:
                break
        return out

    def _score_all(self, query: str) -> dict:
        """Hybrid score = embedding similarity (Tier 2) blended with a
        rare-token exact-match boost (keeps IS-267 / G17 / tardemah / daiin
        style queries landing on the right chunk even when the embedding
        model has never seen those tokens)."""
        sims = None
        if self.model_ready:
            try:
                qv = self.model.encode([query], normalize_embeddings=True)
                sims = (self.embeddings @ qv[0]).tolist()  # pyright: ignore
            except Exception:
                sims = None

        scores = {}
        for i, c in enumerate(self.chunks):
            n = self._nscore(query, c["heading"] + " " + c["text"])
            if sims is not None:
                scores[i] = 0.7 * max(sims[i], 0.0) + 0.3 * n
            else:
                scores[i] = n
        # Normalize so weights are comparable across chunks.
        mx = max(scores.values()) or 1.0
        return {i: s / mx for i, s in scores.items()}

    # ── combined ───────────────────────────────────────────────────────────
    def build_knowledge(self, scripts, query="", max_chars: int = KB_MAX_CHARS_DEFAULT,
                        top_k: int = TOP_K) -> str:
        parts = []
        used = set()
        budget = max_chars

        # Tier 1 first (deterministic, high precision), capped to reserve room.
        for c in self.tier1(scripts, query):
            block = f"[[SOURCE: {c['file']} — {c['heading']}]]\n{c['text']}"
            if len(block) > budget:
                block = block[:budget]
            parts.append(block)
            used.add((c["file"], c["heading"]))
            budget -= len(block)
            if budget <= 500:
                break

        # Tier 2 fills remaining room with semantically relevant extras.
        if budget > 1000 and query.strip() and len(query.strip()) > 3:
            for c in self.tier2(query, top_k=top_k, exclude=used):
                block = f"[[SOURCE: {c['file']} — {c['heading']}]]\n{c['text']}"
                if len(block) > budget:
                    block = block[:budget]
                parts.append(block)
                budget -= len(block)
                if budget <= 500:
                    break

        if not parts:
            return ""
        return "\n\n".join(parts)

    def status(self) -> str:
        if not self.chunks:
            return f"RAG disabled (no `knowledge/` files found in {self.kb_dir})"
        mode = "sentence-transformers embeddings" if self.model_ready \
            else "char n-gram fallback" + (f" ({self._model_error})" if self._model_error else " (model loading)")
        return f"{len(self.chunks)} chunks from knowledge/ · engine: {mode}"


KB = None  # set by app.py after import (avoids circular import during tests)