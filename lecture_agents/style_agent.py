"""Build style.json from the instructor transcript."""

from __future__ import annotations

import json
from pathlib import Path

from lecture_agents.llm import generate_json_from_prompt

STYLE_PROMPT = """You are analyzing a raw lecture transcript (captions) from an instructor.
Infer their spoken delivery style for a narrator who should sound like them in a video lecture.

Return JSON with these keys (all string or array values as appropriate):
- "tone": overall tone (e.g. conversational, humorous, direct).
- "pacing": how they pace ideas (e.g. frequent asides, quick pivots, deliberate buildup).
- "fillers_and_hedges": typical fillers, hedges, discourse markers (list of short examples).
- "how_they_frame_ideas": how they introduce and connect ideas (2-4 sentences).
- "audience_address": how they talk to the audience (e.g. informal, inclusive).
- "signature_phrases": short phrases or patterns that recur (list, up to 8 items).
- "narration_guidance": 3-5 bullet-style sentences telling a TTS narrator how to read slide narrations to match this instructor (imperative voice).

Transcript (may be truncated if very long):
---
{transcript}
---
"""


def run_style_agent(transcript_text: str, out_path: Path, max_chars: int = 120_000) -> None:
    snippet = transcript_text[:max_chars]
    prompt = STYLE_PROMPT.format(transcript=snippet)
    data = generate_json_from_prompt(prompt)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
