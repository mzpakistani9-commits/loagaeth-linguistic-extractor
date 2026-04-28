"""
OMEGA v5 — Universal Ancient Language Intelligence Engine
Muhammad Zubair | Bahria University Lahore, Pakistan
Hugging Face Spaces / Gradio deployment

Built on published research:
  "The Aldaraia Tables of the Book of Soyga" (Zubair 2026)

Covers 50+ scripts, 120+ languages including:
  Enochian · Loagaeth · Soyga · Voynich MS · Hildegard Lingua Ignota
  Angel Runic · Hungarian Rovás · Ancient Hebrew · Egyptian Hieroglyphs
  Indus Valley Script · All modern languages
"""

import os
import base64
import requests
import gradio as gr
from pathlib import Path

# ─── OPENROUTER CONFIGURATION ───────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "anthropic/claude-3.5-sonnet"  # OpenRouter's full model identifier

# ─── MASTER KNOWLEDGE BASE ──────────────────────────────────────────────────
MASTER_KNOWLEDGE = """
PUBLISHED RESEARCH FOUNDATION (Zubair 2026):
Book of Soyga / Aldaraia: 36 tables 36×36. Reeds 2006 formula: cell[r][c]=(Trithemius(prev)+above) mod 23.
100% regeneration accuracy. 34/36 seed keywords = pure algorithmic constructs (null etymology).
ADAMIS(Table 29/Venus)=Hebrew ʾādām, MOYSES(Table 36/Magistri)=Latin/Hebrew/Arabic Moses = ONLY biblical anchors.
36 main diagonals extracted — first complete publication (angelic-name generation sequences).
Avalanche effect 73-93%, Wolfram Class IV behavior, 99.5% lossless compression.
ZERO exact matches between diagonals and 72 Shemhamphorasch roots (prior Grok claims DISCONFIRMED).
Soyga≠Loagaeth relationship: structurally plausible but causally UNPROVEN.
Maxim: "Scientia non habet inimicum preter ignorantem."

ENOCHIAN (DEE/KELLEY 1583-84):
21 letters: Un(A),Pe(B),Veh(C/K),Gon(D),Or(E),Med(F),Mals(G),Tal(H),Gal(I/Y),Urs(K),
Don(R),Fam(S),Vran(N),Graph(O),Tal2(P),Ged(G/J),Gisg(T),Mals2(U/V/W),Med2(X/Z).
IC=0.082. Grammar: VSO, -O=genitive, -AX=participial, -ES=vocative, OD=connector(847×).
264 Tier-1 confirmed words: IAD(God),OL(I/command),SONF(reign),ZACAR(move/open),
ZAMRAN(show thyself),NIIS(come),GANS(messenger),OR(light),OD(and),NA(no),NAX(negation),
ALLA(totality),GRAA(moon),ADON(Lord),DOXA(glory),IAN(I AM),TARDEMAH(deep sleep),
BALT(justice),VOOAN(truth),VONPH(wrath). Reversal pairs: DAM↔MAD,LOT↔TOL.
4 Watchtowers: Air=BATAIVAH/ORO IBAH AOZPI, Fire=EDLPRNAA/OIP TEAA PDOCE,
Water=RAAGIOSL/MPH ARSL GAIOL, Earth=ICZHIHAL/MOR DIAL HCTGA.
30 Aethyrs (LIL,ARN,ZOM,PAZ,LIT,MAZ,DEO,ZID,ZIP,ZAX...), 91 Governors.
Sigillum Dei Aemeth: 7 heptagonal rings, pentagram, 40 outer angels.
Sources: Reeds 1996, Harkness 1999, Peterson 2003, Laycock 1994, Casaubon 1659.

LIBER LOAGAETH (SLOANE MS 3189):
48 leaves, 49×49 grids (2,401 cells/leaf). IC=0.082. Letter A=18.10%.
Translation ceiling ~18% (Leaf 1a). Angels refused leaf-by-leaf translation.
DIFFERENT generation method from Soyga — causally unproven connection.
NEVER claim fully decoded.

VOYNICH MANUSCRIPT (BEINECKE 408, c.1404-38 CE):
37,919 words, 8,114 unique. IC=0.027 (PARADOX: below random 0.038 but Zipf-perfect).
Top words: daiin(892),qol(654),ol(589),chor(412),dain(382).
Tucker/Tucker 2013 = Middle English Old Law Hands cipher.
ALL 26 manipulations: a=flipped+reversed(U+FF417), b=stem removed(U+FF447),
c=top removed(U+FF400), d=stem moved to top(MISSING), e=stem removed(U+FF414),
f=middle stem removed, g=upper+flip(U+FF40C), h=alter stem(U+FF404),
i=connect bottom(U+FF41A) [KEY: minim strokes for aiin sequences],
k=remove right(U+FF408), l=remove bottom+double(U+FF48A), m=upside down(U+FF505),
n=upside down(U+FF501), p=add loop+stem(U+FF420), q=upside down+partial(U+FF4B1),
r=split in half(U+FF403), s=none(U+FF409), t=rotate180+reverse(U+FF422),
u=connect top(U+FF4C0), v=upside down+reverse(U+FF4C1), w=remove curves(U+FF41B),
x=remove bottom(EVA+91), y=remove stem+flip(U+FF5B9), z=flip top(U+FF40F).
Minim sequences: aiin=a+i+i+n, NOT always preceded by EVA-d.

HILDEGARD OF BINGEN LINGUA IGNOTA (c.1150 CE):
First constructed language in Western history. ~900 glossed nouns.
Riesencodex (Wiesbaden HS 2, c.1190-1200). 23 Litterae Ignotae letters (1:1 Latin).
Grammar=pure Latin. Key: Aizniz(God),Aieganz(angel),Crizanz(Christ),
Maiz(man),Vilbez(woman),Galderich(jaundice),Loibenz(lion),Zilzibriz(wax),
Bursiol(eye),Orechons(mouth),Linschiol(Latin language).
Scholar: Sarah Higley 2007.

ANGEL RUNIC (ARCHAIC SPIRIFORM):
Every letter=circles/spirals. 26 base + digraphs: bb,ch,ff,gg,ph,rr,sh,th,tt.
Divine symbols: God(6-pt star),Devil(inv.pentagram),Fire(triple flame),
Wind(3 waves),Earth(cross-in-square),Water(3 wavy lines),Love(heart),
Pray(hands),Christ(cross),Trinity(Ψ/trident),Wing/Angel(Ψ),
Brother of Adam(△),Sister of Eve(▽),Holy Legion(⚔).

HUNGARIAN ROVÁS (FISCHER KÁROLY ANTAL 1889):
RTL carved script, 4th-18th c. CE. 12 regional variants.
CRITICAL: Hungarian s=English SH! Hungarian sz=English S!
Unique: cs(ch),gy(dy),ly(palatal-l),ny(ñ),ty(palatal-t),zs(zh).
Key inscriptions: Nickelsburg(c.1490),Bologna Rovás(1515),Énlaka(1668).

ANCIENT HEBREW (PICTOGRAPHIC CHAIN):
22 letters, 4 characteristics each: form+meaning+name+sound.
aleph(ox/A),beth(tent/B),gimel(camel/G),dalet(door/D),heh(window/H),
waw(nail/W/V),zayin(weapon/Z),chet(fence/Ch),tet(basket/T),yod(arm/Y),
kaph(palm/K),lamed(staff/L),mem(water/M),nun(fish/N),samekh(thorn/S),
ayin(eye/O),peh(mouth/P),tsade(trail/Ts),qoph(head/Q),resh(head/R),
shin(teeth/Sh),taw(mark/T).
Evolution: Pictographic→Phoenician→Greek→Latin→Modern.

INDUS VALLEY SCRIPT:
417 signs (M77), 3,700+ inscriptions, avg 5.17 signs.
IS-342(freq=650,10%)=nominative -m suffix [PROBABLE,78%].
IS-267(fish)=mīn=star rebus (Parpola 1994). IS-391=divine opener.
Dravidian hypothesis: SOV, agglutinative, post-positional.
Zipf: a=15.39, b=2.59. NO bilingual inscription found (2026).

GOOGLE FABRICIUS WORKBENCH:
Open-source Angular tool (googleartsculture/workbench).
Gardiner codes (750+ signs). Berlin-Brandenburg Academy dictionary (CC BY-SA 4.0).
Live: fabriciusworkbench.withgoogle.com. Partners: Macquarie Univ, Ubisoft.
Workflow: upload→facsimile→segment→classify(Gardiner)→translate.

CROSS-RELIGIOUS DIVINE NAME CHAIN:
IAD(Enochian)→YHWH יהוה(Hebrew,root yhw=to be)→ALLAH الله(Arabic,Al+Ilah)
→ALAHA ܐܠܗܐ(Aramaic/Syriac)→THEOS ΘΕΟΣ(Greek,PIE dhewbh)
→DEVA देव(Sanskrit,PIE dyeu=sky/shine)→KADAVUL கடவுள்(Tamil)→AN 𒀭(Sumerian).

10-STEP DECIPHERMENT PROTOCOL:
(1)Frequency analysis (2)Positional S/M/E (3)Pictographic anchor
(4)Rebus/homophone (5)Bilingual Rosetta (6)IC test (7)Zipf-Mandelbrot
(8)Ventris grid (9)K-means+PCA (10)Cross-script parallel.

HONESTY RULE: Mark [UNDECIPHERED] always. CONFIRMED/PROBABLE/POSSIBLE/UNKNOWN.
Never fabricate translations. Never claim Loagaeth or Soyga are "fully decoded."
"""

# ─── LANGUAGE + SCRIPT DATABASE ─────────────────────────────────────────────
SCRIPT_FAMILIES = {
    "🔮 Zubair Research (Angelic/Ancient)": [
        "Indus Valley Script", "Enochian (Angelical Language)",
        "Liber Loagaeth (49×49)", "Book of Soyga / Aldaraia",
        "Voynich MS (EVA/Tucker)", "Hildegard Lingua Ignota",
        "Angel Runic (spiriform)", "Hungarian Rovás (12 variants)",
        "Ancient Hebrew (pictographic)", "Ge'ez / Ethiopic",
        "Andalusi Arabic (medieval)", "Egyptian Hieroglyphic (Fabricius)",
    ],
    "❓ Undeciphered Ancient": [
        "Linear A (Minoan)", "Proto-Elamite", "Rongorongo (Easter Island)",
        "Phaistos Disc", "Meroitic", "Rohonc Codex",
        "Proto-Sinaitic", "Wadi el-Hol", "Byblos Syllabary",
    ],
    "✨ Constructed / Angelic": [
        "Celestial Alphabet (Agrippa)", "Malachim", "Passing the River",
        "Theban Alphabet", "Elder Futhark Runes", "Younger Futhark",
        "Ogham", "Glagolitic", "Gothic (Wulfila)",
    ],
    "📜 Ancient Deciphered": [
        "Egyptian Hieroglyphic", "Hieratic", "Demotic", "Coptic",
        "Sumerian Cuneiform", "Akkadian", "Babylonian", "Hittite Cuneiform",
        "Old Persian Cuneiform", "Phoenician", "Ugaritic", "Aramaic",
        "Linear B (Mycenaean Greek)", "Etruscan", "Luwian",
        "Mayan Glyphs", "Nahuatl", "Oracle Bone Script",
        "Classical Chinese", "Sanskrit / Brahmi / Pali", "Kharosthi",
    ],
    "🌍 Modern Languages": [
        "Arabic (Modern Standard)", "Classical Arabic (Quranic)", "Urdu",
        "Persian (Farsi)", "Pashto", "Dari", "Hebrew (Modern)",
        "Biblical Hebrew", "Hindi", "Bengali", "Punjabi", "Tamil",
        "Telugu", "Kannada", "Malayalam", "Sinhala",
        "English", "Middle English", "Latin", "French", "German",
        "Spanish", "Italian", "Portuguese", "Russian", "Greek",
        "Turkish", "Hungarian", "Chinese (Simplified)", "Japanese",
        "Korean", "Vietnamese", "Thai", "Swahili", "Amharic", "Yoruba",
        "Cherokee", "Quechua", "Tibetan", "Mongolian", "Burmese",
    ],
}

ALL_SCRIPTS = [s for scripts in SCRIPT_FAMILIES.values() for s in scripts]

RESEARCH_MODES = {
    "🔐 Cipher / Unknown Script": "Apply full 10-step decipherment protocol: glyph count, frequency distribution, IC test, Zipf analysis, positional analysis, cross-script comparison.",
    "📜 Manuscript / Tablet": "Diplomatic transcription, critical apparatus, palaeographic dating, textual analysis.",
    "🗿 Epigraphy / Inscription": "Read direction, script family, transliteration, translation, comparative parallels.",
    "🔠 Alphabet / Glyph Analysis": "Each sign → phoneme → Unicode → cipher manipulation (Tucker for VMS).",
    "𓂀 Fabricius / Egyptian": "Gardiner code analysis, Berlin-Brandenburg dictionary, hieroglyph phonetics.",
    "✦ Sacred / Religious Text": "Cross-religious cognate chains, theological parallels, linguistic comparison.",
    "⚖ Cross-Script Comparative": "Structural parallels, cognates, evolutionary relationships.",
    "⚕ Medical / Botanical": "Arabic plant names, Unani/Ayurvedic, Greek medical vocabulary.",
    "🎓 Digital Humanities": "Full scholarly output with critical apparatus and APA 7th bibliography.",
    "🛂 Visa / Official Documents": "Field-by-field extraction, all languages, structured output.",
}

OUTPUT_FORMATS = {
    "Academic Markdown": "## Script ID\n## Alphabet Table\n## Diplomatic Transcription\n## Transliteration\n## Translation (CONFIRMED/PROBABLE/POSSIBLE/UNKNOWN)\n## Linguistic Analysis\n## Statistical Fingerprint (IC, Zipf)\n## [UNDECIPHERED] Sections\n## Cross-Script Parallels\n## Cross-Religious Cognates\n## New DH Findings\n## APA 7th References",
    "Structured JSON": 'Return ONLY valid JSON: {"scripts_detected":[],"alphabet_analysis":[],"extracted_text":{},"confidence_tiers":{},"statistical_fingerprint":{},"cipher_analysis":{},"cross_religious":{},"new_findings":"","references":[]}',
    "Annotated Transcript": "[LINE N] [SCRIPT] [LANG]\nOriginal: ...\nTransliteration: ...\nTranslation: ... [CONFIDENCE]\nNotes: ...",
    "Linguistic Analysis Report": "10 sections: Script ID · Alphabet · Phonology · Morphology · Syntax · Semantics · Statistics · Cipher · Cross-script · New Findings",
    "CSV Table": "Field,Original,Script,Language,Transliteration,Translation,Confidence,Notes",
    "Plain Text": "Clear labelled sections in plain text.",
}


def build_system_prompt(mode: str, scripts: list, output_format: str, depth: str, ms_context: str = "") -> str:
    mode_instruction = RESEARCH_MODES.get(mode, "Full linguistic analysis.")
    lang_note = (
        "Detect and identify ALL languages, scripts, writing systems present — "
        "modern, classical, ancient, undeciphered, constructed, and angelic."
        if not scripts
        else f"Focus on: {', '.join(scripts)}. Also identify any additional scripts."
    )
    format_structure = OUTPUT_FORMATS.get(output_format, "Clear structured output.")

    return f"""You are Dr. Muhammad Zubair's AI research partner — the world's foremost expert on ALL writing systems for digital humanities and cross-religious truth research at Bahria University, Lahore, Pakistan.

PUBLISHED RESEARCH FOUNDATION:
{MASTER_KNOWLEDGE}

RESEARCH MODE: {mode}
MODE INSTRUCTION: {mode_instruction}
LANGUAGE FOCUS: {lang_note}
OUTPUT FORMAT: {output_format}
ANALYSIS DEPTH: {depth}
{f"MANUSCRIPT CONTEXT: {ms_context}" if ms_context else ""}

OUTPUT STRUCTURE:
{format_structure}

UNIVERSAL TASKS:
1. Identify EVERY script/alphabet/language — including obscure, esoteric, and constructed systems
2. Extract all text with original Unicode characters preserved exactly
3. Build alphabet/glyph table: sign → phoneme → Unicode → cipher manipulation
4. Transliterate to Latin where needed
5. Translate with HONEST confidence tiers — NEVER fabricate meanings
6. Compute/estimate IC and Zipf for unknown scripts
7. Apply 10-step decipherment protocol for unknown scripts
8. Mark ALL uncertain sections [UNDECIPHERED]
9. Cross-religious cognate chains where relevant (IAD→YHWH→ALLAH chain etc.)
10. Identify NEW FINDINGS for digital humanities clearly
11. APA 7th edition scholarly references
12. For Soyga/Loagaeth: apply Reeds (2006) formula knowledge and state limitations honestly

HONESTY DECLARATION:
I mark all uncertain sections [UNDECIPHERED].
I never invent translations to fill gaps.
Confidence tiers: CONFIRMED / PROBABLE / POSSIBLE / UNKNOWN.
The Soyga→Loagaeth connection is structurally plausible but causally UNPROVEN.
Zero Shemhamphorasch matches confirmed in Zubair (2026) diagonal analysis."""


def analyse_text(
    text_input: str,
    image_input,
    mode: str,
    selected_scripts: list,
    output_format: str,
    depth: str,
    ms_context: str,
    api_key: str,
) -> str:
    """Main analysis function called by Gradio. Uses OpenRouter API."""

    # Use UI-provided key if given, else fall back to env variable
    key = (api_key or "").strip() or OPENROUTER_API_KEY
    if not key or not key.startswith("sk-or-"):
        return (
            "⚠ OpenRouter API key required.\n"
            "• Set environment variable: OPENROUTER_API_KEY\n"
            "• Or paste your key in the input field above (starts with sk-or-...)\n"
            "• Get a free key at: https://openrouter.ai/keys"
        )

    system = build_system_prompt(mode, selected_scripts, output_format, depth, ms_context)

    # Build user message content (OpenAI-compatible format used by OpenRouter)
    user_content = []

    if image_input is not None:
        # Convert numpy array to base64 JPEG (handles RGBA / palette / grayscale)
        import io
        from PIL import Image
        buf = io.BytesIO()
        img = Image.fromarray(image_input)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        # OpenRouter / OpenAI multimodal format: image_url with data URI
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })
        user_content.append({
            "type": "text",
            "text": (
                "Analyse this image. Identify ALL scripts, symbols, writing systems, glyphs. "
                "Apply full ancient language analysis including Voynich EVA, Enochian, Hildegard, "
                "Indus seals, Gardiner hieroglyphs, Angel Runic, and all esoteric systems."
                f"{f' Context: {ms_context}' if ms_context else ''}"
            ),
        })
    elif text_input and text_input.strip():
        user_content.append({
            "type": "text",
            "text": f"Analyse this text using your full specialist knowledge:\n\n{text_input}",
        })
    else:
        # Demo mode
        user_content.append({
            "type": "text",
            "text": (
                f"Demonstrate your expertise. Provide a comprehensive comparative analysis of: "
                f"(1) Enochian language structure + Loagaeth statistical fingerprint, "
                f"(2) Indus Valley Script decipherment progress, "
                f"(3) Voynich MS Tucker cipher analysis, "
                f"(4) Cross-religious divine name cognates (IAD→YHWH→ALLAH chain), "
                f"(5) Top 5 open questions for digital humanities. Format as {output_format}."
            ),
        })

    # OpenRouter uses OpenAI-compatible chat format: messages with role + content
    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces/loagaeth-extractor",
        "X-Title": "OMEGA v5 - Ancient Language Intelligence",
    }

    try:
        response = requests.post(
            OPENROUTER_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=120,
        )
        if response.status_code == 401:
            return "⚠ Invalid API key. Get one at https://openrouter.ai/keys"
        if response.status_code == 429:
            return "⚠ Rate limit reached. Wait a moment and try again."
        if response.status_code != 200:
            return f"⚠ API error {response.status_code}: {response.text[:500]}"

        data = response.json()
        if "error" in data:
            return f"⚠ Error: {data['error'].get('message', str(data['error']))}"

        # OpenAI-compatible response: choices[0].message.content
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        return "⚠ Request timed out (120s). Try again or use shorter input."
    except requests.exceptions.RequestException as e:
        return f"⚠ Network error: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"⚠ Unexpected API response format: {str(e)}"
    except Exception as e:
        return f"⚠ Error: {str(e)}"


def gardiner_translate(codes: str, mode: str, api_key: str) -> str:
    """Translate Gardiner codes via OpenRouter API."""
    key = (api_key or "").strip() or OPENROUTER_API_KEY
    if not key or not key.startswith("sk-or-"):
        return "⚠ OpenRouter API key required (sk-or-...). Set OPENROUTER_API_KEY env var or paste key above."
    if not codes.strip():
        return "⚠ Enter Gardiner codes (e.g. G17 N35 X1 O1)."

    sys = f"""You are an expert Egyptologist using the Google Fabricius Workbench methodology and Berlin-Brandenburg Academy dictionary (CC BY-SA 4.0).

{MASTER_KNOWLEDGE}

For the Gardiner codes provided:
1. Identify each sign (category, pictographic form, name)
2. Phonetic value (uniliteral/biliteral/triliteral)
3. Berlin-Brandenburg Academy translation
4. Grammatical role in sequence
5. Full phrase translation with confidence tier
6. Cross-religious parallels
Mode: {mode}"""

    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": f"Translate these Egyptian hieroglyphs (Gardiner codes):\n{codes}"},
        ],
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces/loagaeth-extractor",
        "X-Title": "OMEGA v5 - Fabricius Translator",
    }

    try:
        response = requests.post(
            OPENROUTER_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=120,
        )
        if response.status_code != 200:
            return f"⚠ API error {response.status_code}: {response.text[:500]}"
        data = response.json()
        if "error" in data:
            return f"⚠ Error: {data['error'].get('message', str(data['error']))}"
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠ Request timed out (120s). Try again."
    except requests.exceptions.RequestException as e:
        return f"⚠ Network error: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"⚠ Unexpected API response: {str(e)}"
    except Exception as e:
        return f"⚠ Error: {str(e)}"


# ─── GRADIO INTERFACE ────────────────────────────────────────────────────────
DESCRIPTION = """
# ⬡ Loagaeth Linguistic Extractor — OMEGA v5
### Muhammad Zubair | Bahria University Lahore, Pakistan
Built on published research: *"The Aldaraia Tables of the Book of Soyga"* (Zubair 2026)

**Covers 50+ scripts · 120+ languages · All angelic, ancient, and modern writing systems**  
🔐 Enochian · 𓂀 Hieroglyphs · ✦ Voynich MS · 🌿 Indus Script · ⬡ Loagaeth · and 45+ more
"""

FOOTER = """
---
**Key research finding**: 34/36 Soyga seed keywords = pure algorithmic constructs. Only ADAMIS & MOYSES contain biblical roots (Zubair 2026).  
**Honesty rule**: All uncertain sections marked [UNDECIPHERED]. Confidence: CONFIRMED / PROBABLE / POSSIBLE / UNKNOWN.  
*"Scientia non habet inimicum preter ignorantem"* — Book of Soyga
"""

_THEME = gr.themes.Base(
    primary_hue="orange",
    secondary_hue="gray",
    font=[gr.themes.GoogleFont("IM Fell English"), "Georgia", "serif"],
)
_CSS = """
.gradio-container { max-width: 1400px !important; }
.output-textbox textarea { font-family: monospace !important; font-size: 13px !important; }
"""

with gr.Blocks(title="OMEGA v5 — Ancient Language Intelligence") as demo:

    gr.Markdown(DESCRIPTION)

    with gr.Tabs():

        # ── MAIN EXTRACTOR ──
        with gr.TabItem("⬡ Extract & Analyse"):
            with gr.Row():
                with gr.Column(scale=1):
                    api_key = gr.Textbox(
                        label="OpenRouter API Key (optional if OPENROUTER_API_KEY env var is set)",
                        placeholder="sk-or-v1-...",
                        type="password",
                        info="Get free key at openrouter.ai/keys. Or set OPENROUTER_API_KEY env variable.",
                    )
                    text_input = gr.Textbox(
                        label="Text Input",
                        placeholder=(
                            "Examples:\n"
                            "• Voynich EVA: daiin qol chor daiin otchey\n"
                            "• Enochian: OL SONF VORSG GOHO IAD BALT\n"
                            "• Indus: IS-267 IS-099 IS-342 (sign IDs)\n"
                            "• Hebrew: שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ\n"
                            "• Arabic: بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\n"
                            "• Hildegard: Aizniz Aieganz Crizanz Maiz\n"
                            "• Any other script or language…"
                        ),
                        lines=7,
                    )
                    image_input = gr.Image(
                        label="Image Upload (seal / inscription / manuscript)",
                        type="numpy",
                    )
                    ms_context = gr.Textbox(
                        label="Manuscript Context (optional)",
                        placeholder="e.g. Sloane MS 3189, Leaf 7a — Enochian 49×49 grid, Dee/Kelley 1583-84",
                    )

                with gr.Column(scale=1):
                    mode = gr.Dropdown(
                        label="Research Mode",
                        choices=list(RESEARCH_MODES.keys()),
                        value="🔐 Cipher / Unknown Script",
                    )
                    script_family = gr.Dropdown(
                        label="Script Family Filter",
                        choices=["All Families"] + list(SCRIPT_FAMILIES.keys()),
                        value="All Families",
                    )
                    selected_scripts = gr.Dropdown(
                        label="Target Scripts (optional — leave empty for auto-detect)",
                        choices=ALL_SCRIPTS,
                        multiselect=True,
                        value=[],
                    )
                    output_format = gr.Dropdown(
                        label="Output Format",
                        choices=list(OUTPUT_FORMATS.keys()),
                        value="Academic Markdown",
                    )
                    depth = gr.Dropdown(
                        label="Analysis Depth",
                        choices=[
                            "Quick — script ID only",
                            "Standard — extract & identify",
                            "Deep — morphology & grammar",
                            "Expert — cipher & unknown",
                            "Scholarly — full APA edition",
                        ],
                        value="Expert — cipher & unknown",
                    )
                    run_btn = gr.Button("⬡  Extract & Analyse All Scripts", variant="primary", size="lg")

            result_output = gr.Textbox(
                label="Analysis Result",
                lines=25,
                elem_classes=["output-textbox"],
            )

            run_btn.click(
                fn=analyse_text,
                inputs=[text_input, image_input, mode, selected_scripts, output_format, depth, ms_context, api_key],
                outputs=result_output,
            )

            # Update script choices when family changes
            def update_scripts(family):
                if family == "All Families":
                    return gr.update(choices=ALL_SCRIPTS, value=[])
                return gr.update(choices=SCRIPT_FAMILIES.get(family, ALL_SCRIPTS), value=[])

            script_family.change(fn=update_scripts, inputs=script_family, outputs=selected_scripts)

        # ── FABRICIUS / HIEROGLYPHS ──
        with gr.TabItem("𓂀 Fabricius / Hieroglyphs"):
            gr.Markdown("""
### Google Fabricius Workbench Integration
Based on the open-source [googleartsculture/workbench](https://github.com/googleartsculture/workbench) project.
For full ML glyph classification from images, use [fabriciusworkbench.withgoogle.com](https://fabriciusworkbench.withgoogle.com).
This tab provides AI-powered Gardiner code translation using the Berlin-Brandenburg Academy methodology.

**Gardiner Sign Categories:** A=man, B=woman, C=deity, D=body, E=mammals, F=mammal parts, G=birds,
H=bird parts, I=reptiles, K=fish, M=plants, N=sky/earth/water, O=buildings, Q=furniture, S=crowns,
T=warfare, U=agriculture, V=rope, W=vessels, X=bread, Y=writing, Z=strokes, Aa=unclassified
            """)

            with gr.Row():
                gard_input = gr.Textbox(
                    label="Gardiner Codes",
                    placeholder="e.g. G17 N35 N35 X1 O1 (space-separated)",
                    lines=2,
                )
                gard_mode = gr.Dropdown(
                    label="Translation Mode",
                    choices=[
                        "Full translation + phonetic analysis",
                        "Sign-by-sign breakdown",
                        "Cross-religious parallels",
                        "Academic Egyptological report",
                    ],
                    value="Full translation + phonetic analysis",
                )
            api_key_fab = gr.Textbox(
                label="OpenRouter API Key (optional if env var set)",
                type="password",
                placeholder="sk-or-v1-...",
            )
            gard_btn = gr.Button("𓂀  Translate Hieroglyphs", variant="primary")
            gard_result = gr.Textbox(label="Translation Result", lines=20, elem_classes=["output-textbox"])
            gard_btn.click(fn=gardiner_translate, inputs=[gard_input, gard_mode, api_key_fab], outputs=gard_result)

        # ── KNOWLEDGE BASE ──
        with gr.TabItem("📚 Knowledge Base"):
            gr.Markdown(f"""
### Embedded Specialist Knowledge Base
This knowledge is **automatically injected into every AI query** — you never need to explain context.

```
{MASTER_KNOWLEDGE[:3000]}...
```
*(Full KB: {len(MASTER_KNOWLEDGE)} characters)*

### Quick Reference — Voynich Tucker Cipher
| Latin | Manipulation | EVA Code |
|-------|-------------|----------|
| a | flipped and reversed | U+FF417 |
| i | connect bottom stem | U+FF41A ← KEY for aiin |
| m | upside down | U+FF505 |
| n | upside down | U+FF501 |
| r | split in half | U+FF403 |
| t | rotate 180°, reverse | U+FF422 |

### Hungarian Rovás Critical Key
⚠ **Hungarian s = English SH!  Hungarian sz = English S!**

### Divine Name Chain
`IAD (Enochian) → YHWH (Hebrew) → ALLAH (Arabic) → ALAHA (Aramaic) → THEOS (Greek) → DEVA (Sanskrit)`
            """)

        # ── ABOUT ──
        with gr.TabItem("ℹ About"):
            gr.Markdown(f"""
### About This Tool

**Researcher**: Muhammad Zubair | MS Clinical Psychology | Bahria University Lahore, Pakistan  
**Contact**: mzpakistani9@gmail.com | DesiMindCare.com  
**AI Engine**: Claude 3.5 Sonnet via OpenRouter (anthropic/claude-3.5-sonnet)  
**API Provider**: OpenRouter — https://openrouter.ai  

### Published Research Foundation
> Zubair, M. (2026). *The Aldaraia Tables of the Book of Soyga: First Systematic Etymological Analysis of the 36 Seed Keywords, Complete Main-Diagonal Extraction, and Information-Theoretic Verification of the Reeds Cellular Automaton (1560).* Department of Psychology, Bahria University, Lahore, Pakistan.

**Key findings:**
- 34/36 seed keywords = pure algorithmic constructs (null etymology)
- ADAMIS & MOYSES = only biblical anchors (Hebrew ʾādām; Latin/Hebrew/Arabic Moses)
- 36 main diagonals extracted — first complete publication
- Avalanche effect 73-93% (historical hash-function behavior)
- Wolfram Class IV — earliest known cellular automaton (~410 years before Conway)
- ZERO Shemhamphorasch matches (prior Grok AI claims disconfirmed)

### Citations
- Reeds, J. (2006). John Dee and the Magic Tables in the Book of Soyga. Springer.
- Parpola, A. (1994). *Deciphering the Indus Script*. Cambridge University Press.
- Tucker, A. O., & Tucker, R. H. (2013). Voynich Manuscript analysis. *HerbalGram, 100*.
- Higley, S. L. (2007). *Hildegard of Bingen's Unknown Language*. Palgrave Macmillan.
- Google Arts & Culture. (2020). Fabricius Workbench. github.com/googleartsculture/workbench

*"Scientia non habet inimicum preter ignorantem"*  
Knowledge has no enemy other than ignorance — Book of Soyga
            """)

    gr.Markdown(FOOTER)


if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860, theme=_THEME, css=_CSS)
