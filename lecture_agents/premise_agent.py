"""Structured lecture premise from slide descriptions."""

from __future__ import annotations

import json
from pathlib import Path

from lecture_agents.doc_truncation import cap_for_model
from lecture_agents.llm import generate_json_from_prompt

PROMPT = """You are given JSON describing every slide in a lecture deck (field "slides" with slide_index and description).

Produce a structured lecture premise grounded ONLY in that content.

Return JSON with keys:
- "title": short working title for the lecture.
- "thesis": one paragraph core argument or through-line.
- "scope": what the lecture covers and what it excludes (paragraph).
- "learning_objectives": array of 4-7 strings.
- "intended_audience": who this is for (1-2 sentences).
- "key_themes": array of 3-6 short theme labels.

Input slide descriptions JSON:
---
{slide_json}
---
"""


def run_premise_agent(slide_description_path: Path, out_path: Path) -> None:
    slide_raw = slide_description_path.read_text(encoding="utf-8")
    prompt = PROMPT.format(slide_json=cap_for_model(slide_raw))
    data = generate_json_from_prompt(prompt)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
