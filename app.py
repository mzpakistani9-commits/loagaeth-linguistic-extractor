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

# ─── LLM PROVIDER CHAIN (secrets come from env vars / HF Space secrets) ────
# Keys are NEVER hardcoded here — set them as environment variables / HF Secrets:
#   OPENROUTER_API_KEY, THEHIVE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY
# Providers are tried top-to-bottom; if a key is missing/expired/quota-limited,
# the app automatically moves to the next provider (then the next model).
PROVIDERS = [
    {
        "name": "OpenRouter",
        "env": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "models": [
            "openrouter/auto",  # Auto-routes to best available free model
            "deepseek/deepseek-r1:free",
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen-2-7b-instruct:free",
        ],
        "headers_extra": {
            "HTTP-Referer": "https://huggingface.co/spaces/mzubair-dh/loagaeth-extractor",
            "X-Title": "OMEGA v5 - Ancient Language Intelligence",
        },
    },
    {
        "name": "TheHive",
        "env": "THEHIVE_API_KEY",
        "url": "https://api.thehive.ai/api/v3/chat/completions",
        "models": [
            "deepseek-ai/deepseek-v4.1-flash",
            "hive/vision-language-model",
        ],
    },
    {
        "name": "DeepSeek",
        "env": "DEEPSEEK_API_KEY",
        "url": "https://api.deepseek.com/chat/completions",
        "models": [
            "deepseek-flash",
            "deepseek-chat",
        ],
    },
    {
        "name": "OpenAI",
        "env": "OPENAI_API_KEY",
        "url": "https://api.openai.com/v1/chat/completions",
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
        ],
    },
]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def call_llm_with_fallback(
    messages: list,
    key_override: str = "",
    max_tokens: int = 4000,
    timeout: int = 120,
) -> dict:
    """
    Call any configured LLM provider with fully automatic fallback.
    Chain: providers top-to-bottom, then models within a provider, then a
    decreasing max_tokens ladder on HTTP 402 (insufficient credits/quota).
    A key pasted in the UI (key_override) is tried as an OpenRouter key first.
    Returns: {"success": True, "content": str, "model": str} or {"success": False, "error": str}
    """
    # Graceful degradation ladder for credit limits (HTTP 402): retry the same
    # model with fewer max_tokens until it fits the remaining balance.
    max_tokens_ladder = [max_tokens, 2000, 1000, 400]

    provider_list = list(PROVIDERS)
    if (key_override or "").strip():
        # UI-pasted key takes priority as an OpenRouter key, then the env chain.
        provider_list = [{
            "name": "OpenRouter (UI key)",
            "env": "__override__",
            "key": key_override.strip(),
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "models": ["openrouter/auto"] + PROVIDERS[0]["models"],
            "headers_extra": PROVIDERS[0]["headers_extra"],
        }] + provider_list

    last_error = None
    for provider in provider_list:
        key = provider.get("key") or os.getenv(provider["env"], "").strip()
        if not key:
            continue

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        headers.update(provider.get("headers_extra") or {})

        provider_failed_auth = False
        for model in provider["models"]:
            if provider_failed_auth:
                break

            for mt in max_tokens_ladder:
                payload = {
                    "model": model,
                    "max_tokens": mt,
                    "messages": messages,
                }

                try:
                    response = requests.post(
                        provider["url"],
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                    )
                    code = response.status_code

                    # Model missing / unsupported — next model
                    if code == 404:
                        last_error = f"{provider['name']}/{model} not available (404)"
                        break

                    # Invalid API key for this provider — skip the whole provider
                    if code == 401:
                        last_error = f"{provider['name']}/{model}: invalid API key (401)"
                        provider_failed_auth = True
                        break

                    # Rate limited — next model
                    if code == 429:
                        last_error = f"{provider['name']}/{model}: rate limit reached (429)"
                        break

                    # Insufficient credits/quota for this max_tokens — retry fewer
                    if code == 402:
                        last_error = f"{provider['name']}/{model}: insufficient credits for {mt} tokens (402)"
                        continue

                    # Provider/model-level rejection (e.g. no vision support) — next model
                    if code != 200:
                        last_error = f"{provider['name']}/{model}: API error {code}: {response.text[:300]}"
                        break

                    data = response.json()
                    if "error" in data:
                        msg = data["error"].get("message", str(data["error"]))
                        code_e = data["error"].get("code")
                        if code_e == 401 or "model" in msg.lower() or code_e == 404:
                            last_error = f"{provider['name']}/{model}: {msg}"
                            if code_e == 401:
                                provider_failed_auth = True
                            break
                        # Other provider-level errors — next model
                        last_error = f"{provider['name']}/{model}: {msg}"
                        break

                    # Success!
                    content = data["choices"][0]["message"].get("content") or ""
                    # Some auto-routed models return only "reasoning" with null content.
                    # Fall back to reasoning, otherwise treat as failure and try next model.
                    if not content.strip():
                        reasoning = data["choices"][0]["message"].get("reasoning") or ""
                        if reasoning.strip():
                            content = f"{reasoning}\n\n_(reasoning-only response from {data.get('model', model)})_"
                        else:
                            last_error = f"{provider['name']}/{model} returned empty content"
                            break
                    return {"success": True, "content": content, "model": f"{model} ({provider['name']})"}

                except requests.exceptions.Timeout:
                    return {"success": False, "error": "Request timed out (120s). Try again or use shorter input."}
                except requests.exceptions.RequestException as e:
                    last_error = f"{provider['name']}/{model}: network error: {str(e)}"
                    break
                except (KeyError, IndexError) as e:
                    last_error = f"{provider['name']}/{model}: unexpected API response: {str(e)}"
                    break

    # All providers/models failed
    tried = ", ".join(
        f"{p['name']}" for p in provider_list
        if p.get("key") or os.getenv(p["env"], "").strip()
    ) or "none (no API keys configured)"
    return {
        "success": False,
        "error": f"All providers failed. Last error: {last_error}. Tried: {tried}"
    }


from kb import KnowledgeBase

# ─── RAG KNOWLEDGE LAYER (Tier 1 + Tier 2) ──────────────────────────────────
# Tier 1: deterministic per-script retrieval from knowledge/*.md files.
# Tier 2: semantic top-k retrieval (sentence-transformers if available,
#         char n-gram fallback otherwise). Embedded locally, zero API cost.
# Only RELEVANT chunks are injected into a prompt, not the whole KB.
KB = KnowledgeBase()

CORE_RULES = """HONESTY & METHODS (apply to ALL output):
- Confidence tiers: CONFIRMED / PROBABLE / POSSIBLE / UNKNOWN.
- Mark ALL uncertain sections [UNDECIPHERED]. NEVER fabricate translations to fill gaps.
- For unknown scripts: compute/estimate IC and Zipf, apply the 10-step decipherment protocol.
- The Soyga->Loagaeth connection is structurally plausible but causally UNPROVEN.
- Zero Shemhamphorasch matches confirmed in Zubair (2026) diagonal analysis.
- Cite sources (Reeds 2006, Parpola 1994, Tucker & Tucker 2013, Higley 2007, Zubair 2026)."""




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


def build_system_prompt(mode: str, scripts: list, output_format: str, depth: str,
                        ms_context: str = "", query: str = "") -> str:
    mode_instruction = RESEARCH_MODES.get(mode, "Full linguistic analysis.")
    lang_note = (
        "Detect and identify ALL languages, scripts, writing systems present — "
        "modern, classical, ancient, undeciphered, constructed, and angelic."
        if not scripts
        else f"Focus on: {', '.join(scripts)}. Also identify any additional scripts."
    )
    format_structure = OUTPUT_FORMATS.get(output_format, "Clear structured output.")

    # RAG: inject only the RELEVANT reference chunks (Tier 1 script-matched
    # + Tier 2 semantic top-k). Falls back gracefully if knowledge/ missing.
    retrieved = KB.build_knowledge(scripts=scripts, query=query)

    return f"""You are Dr. Muhammad Zubair's AI research partner — the world's foremost expert on ALL writing systems for digital humanities and cross-religious truth research at Bahria University, Lahore, Pakistan.

RETRIEVED RESEARCH KNOWLEDGE (ground truth — prefer this over general AI memory):
{retrieved if retrieved else '(no reference knowledge retrieved — rely on scholarly caution)'}

{CORE_RULES}

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
Confidence tiers: CONFIRMED / PROBABLE / POSSIBLE / UNKNOWN."""


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
    """Main analysis function called by Gradio. Uses the LLM provider chain."""

    # Use UI-provided key if given (tried first as OpenRouter), else provider chain
    key = (api_key or "").strip()
    if not key and not any(os.getenv(p["env"], "").strip() for p in PROVIDERS):
        return (
            "⚠ No API key configured.\n"
            "• Add keys as HF Space secrets: OPENROUTER_API_KEY, THEHIVE_API_KEY, "
            "DEEPSEEK_API_KEY, OPENAI_API_KEY (any one is enough — they fall back automatically)\n"
            "• Or paste any API key in the input field above\n"
            "• Get free keys at: https://openrouter.ai/keys · https://platform.deepseek.com/api_keys · https://thehive.ai/models?api_keys=1"
        )

    # Determine retrieval query for the RAG layer
    query = text_input or ms_context or ""
    system = build_system_prompt(mode, selected_scripts, output_format, depth, ms_context, query=query)

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
        demo_text = (
            "Demonstrate your expertise. Provide a comprehensive comparative analysis of: "
            "(1) Enochian language structure + Loagaeth statistical fingerprint, "
            "(2) Indus Valley Script decipherment progress, "
            "(3) Voynich MS Tucker cipher analysis, "
            "(4) Cross-religious divine name cognates (IAD→YHWH→ALLAH chain), "
            f"(5) Top 5 open questions for digital humanities. Format as {output_format}."
        )
        query = query or demo_text
        user_content.append({"type": "text", "text": demo_text})

    # Call OpenRouter with automatic model fallback
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    result = call_llm_with_fallback(messages=messages, key_override=key, max_tokens=4000)

    if not result["success"]:
        return f"⚠ {result['error']}"

    # Add model info to response footer
    model_used = result.get("model", "unknown")
    return f"{result['content']}\n\n---\n_Model: {model_used}_"


def gardiner_translate(codes: str, mode: str, api_key: str) -> str:
    """Translate Gardiner codes via the LLM provider chain."""
    key = (api_key or "").strip()
    if not key and not any(os.getenv(p["env"], "").strip() for p in PROVIDERS):
        return "⚠ No API key configured. Add HF Space secrets (OPENROUTER_API_KEY / THEHIVE_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY) or paste a key above."
    if not codes.strip():
        return "⚠ Enter Gardiner codes (e.g. G17 N35 X1 O1)."

    sys = f"""You are an expert Egyptologist using the Google Fabricius Workbench methodology and Berlin-Brandenburg Academy dictionary (CC BY-SA 4.0).

RETRIEVED HIEROGLYPH KNOWLEDGE:
{KB.build_knowledge(scripts=["Egyptian Hieroglyphic", "Egyptian Hieroglyphic (Fabricius)"], query=codes, max_chars=4000)}

{CORE_RULES}

For the Gardiner codes provided:
1. Identify each sign (category, pictographic form, name)
2. Phonetic value (uniliteral/biliteral/triliteral)
3. Berlin-Brandenburg Academy translation
4. Grammatical role in sequence
5. Full phrase translation with confidence tier
6. Cross-religious parallels
Mode: {mode}"""

    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content": f"Translate these Egyptian hieroglyphs (Gardiner codes):\n{codes}"},
    ]

    result = call_llm_with_fallback(messages=messages, key_override=key, max_tokens=2000)

    if not result["success"]:
        return f"⚠ {result['error']}"

    model_used = result.get("model", "unknown")
    return f"{result['content']}\n\n---\n_Model: {model_used}_"


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
                        label="API Key (optional — used first, then falls back to Space secrets)",
                        placeholder="sk-...",
                        type="password",
                        info="Paste any key (OpenRouter/DeepSeek/OpenAI/TheHive) or leave empty to use HF Space secrets: OPENROUTER_API_KEY, THEHIVE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY.",
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
                label="API Key (optional — falls back to Space secrets)",
                type="password",
                placeholder="sk-...",
            )
            gard_btn = gr.Button("𓂀  Translate Hieroglyphs", variant="primary")
            gard_result = gr.Textbox(label="Translation Result", lines=20, elem_classes=["output-textbox"])
            gard_btn.click(fn=gardiner_translate, inputs=[gard_input, gard_mode, api_key_fab], outputs=gard_result)

        # ── KNOWLEDGE BASE ──
        with gr.TabItem("📚 Knowledge Base"):
            gr.Markdown(f"""
### RAG Knowledge Base — retrieved on demand
This knowledge is stored in `knowledge/*.md` and **injected only when relevant** — Tier 1 (script-matched files from the dropdown) + Tier 2 (semantic top-k chunks for your text). Huge prompts get cheaper and answers more accurate.

```
{KB.status()}
```

Questions often hit a breakthrough: query "daiin aiin" retrieves the Voynich EVA/Tucker tables; "IS-267" retrieves Indus readings; "G17 N35 X1" retrieves Gardiner hieroglyph data — because it's grounded in the files, not the model's memory.

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
**AI Engine**: Multi-provider automatic fallback — OpenRouter → TheHive → DeepSeek → OpenAI  
**Setup**: Add any of these HF Space secrets — `OPENROUTER_API_KEY`, `THEHIVE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`. If one key expires or hits quota, the next is tried automatically.  
**Rate limits**: 20 requests/min, 200 requests/day per model  

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
