"""Per-slide narration with style, premise, arc, and prior narration chaining."""

from __future__ import annotations

import json
from pathlib import Path

from lecture_agents.doc_truncation import cap_for_model
from lecture_agents.llm import generate_json_with_image

SHARED_CONTEXT = """Speaking style profile (JSON):
{style_json}

Lecture premise (JSON):
{premise_json}

Lecture arc (JSON):
{arc_json}

PRIOR SLIDE NARRATIONS (spoken text, in order — do not repeat; continue naturally):
{prior_narrations}

Full slide_description.json (all slides; use the entry for the current slide_index):
---
{slide_doc}
---
"""

TITLE_SLIDE_PROMPT = """You write the spoken narration for slide_index 1 only — the TITLE / opening slide of the lecture video.

Requirements for this slide (mandatory):
- The speaker must introduce themselves as the course instructor (e.g. "I'm your instructor" or a plausible name if one appears in the slide text or descriptions).
- They must give a short, inviting overview of the lecture topic and why it matters (1–3 sentences after the intro).
- Keep total length similar to other slides: about 40–120 words unless the title slide is very dense.
- Natural spoken English for text-to-speech: no stage directions, bullets, or markdown.
- Match tone, pacing, and framing from the style profile.

{shared}

Return JSON exactly:
{{"slide_index": 1, "narration": "<spoken script only>"}}
"""

STANDARD_SLIDE_PROMPT = """You write the spoken narration for one body slide of a narrated lecture video (slide_index is greater than 1).

Current slide_index: {slide_index}

Use:
1) The slide IMAGE (current slide).
2) The style profile, premise, arc, full slide descriptions, and prior narrations below.

Rules:
- Natural spoken English suitable for text-to-speech (no stage directions, no markdown).
- About 40–120 words unless the slide is very dense (max ~180 words).
- Match the instructor style from the style profile.
- Stay faithful to this slide's description and its role in the arc.
- Do not re-read the title introduction; continue the lecture narrative.

{shared}

Return JSON exactly:
{{"slide_index": {slide_index}, "narration": "<spoken script only>"}}
"""


def run_narration_agent(
    style_path: Path,
    premise_path: Path,
    arc_path: Path,
    slide_description_path: Path,
    slide_images_dir: Path,
    out_path: Path,
) -> None:
    style_json = style_path.read_text(encoding="utf-8")
    premise_json = premise_path.read_text(encoding="utf-8")
    arc_json = arc_path.read_text(encoding="utf-8")
    slide_doc = slide_description_path.read_text(encoding="utf-8")
    slide_doc_capped = cap_for_model(slide_doc)

    by_index = {s["slide_index"]: s for s in json.loads(slide_doc)["slides"]}
    indices = sorted(by_index.keys())
    narrations: list[dict] = []

    for idx in indices:
        png = slide_images_dir / f"slide_{idx:03d}.png"
        if not png.is_file():
            raise FileNotFoundError(f"Missing image for slide {idx}: {png}")

        prior_lines = []
        for prev in narrations:
            prior_lines.append(f"Slide {prev['slide_index']}: {prev['narration']}")
        prior_block = (
            "\n\n".join(prior_lines)
            if prior_lines
            else "(none — this is the opening slide; no prior narrations.)"
        )

        shared = SHARED_CONTEXT.format(
            style_json=cap_for_model(style_json, max_chars=80_000),
            premise_json=cap_for_model(premise_json, max_chars=80_000),
            arc_json=cap_for_model(arc_json, max_chars=80_000),
            prior_narrations=prior_block,
            slide_doc=slide_doc_capped,
        )

        if idx == 1:
            prompt = TITLE_SLIDE_PROMPT.format(shared=shared)
        else:
            prompt = STANDARD_SLIDE_PROMPT.format(slide_index=idx, shared=shared)

        data = generate_json_with_image(prompt, str(png))
        if data.get("slide_index") != idx:
            data["slide_index"] = idx
        desc = by_index[idx]["description"]
        narrations.append(
            {
                "slide_index": idx,
                "description": desc,
                "narration": data["narration"].strip(),
            }
        )

    payload = {"slides": narrations}
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
