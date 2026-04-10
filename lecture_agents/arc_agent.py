"""Lecture arc from premise + slide descriptions."""

from __future__ import annotations

import json
from pathlib import Path

from lecture_agents.doc_truncation import cap_for_model
from lecture_agents.llm import generate_json_from_prompt

PROMPT = """You plan the narrative arc of a video lecture.

Use the premise JSON and the full slide description JSON. The arc must be consistent with the premise and reflect how ideas build across slides.

Return JSON with keys:
- "overview": 2-4 sentences on overall flow.
- "acts": array of objects, each with "name", "slide_range" (e.g. "1-5"), "purpose" (string).
- "transitions": array of 3-8 strings describing how each major section hands off to the next.
- "emphasis": what to stress emotionally or pedagogically (paragraph).

Premise JSON:
---
{premise_json}
---

Slide descriptions JSON:
---
{slide_json}
---
"""


def run_arc_agent(premise_path: Path, slide_description_path: Path, out_path: Path) -> None:
    premise_raw = premise_path.read_text(encoding="utf-8")
    slide_raw = slide_description_path.read_text(encoding="utf-8")
    prompt = PROMPT.format(
        premise_json=cap_for_model(premise_raw, max_chars=120_000),
        slide_json=cap_for_model(slide_raw),
    )
    data = generate_json_from_prompt(prompt)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
