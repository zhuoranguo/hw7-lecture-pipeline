"""Per-slide descriptions with prior-description chaining."""

from __future__ import annotations

import json
from pathlib import Path

from lecture_agents.llm import generate_json_with_image

PROMPT = """You are describing a single slide image from a university lecture deck.

You are given the current slide as an image. Separately, the text below lists the full descriptions of every slide that comes BEFORE this one, in order. Use that history to stay consistent and to explain how the current slide continues the story (this is required — do not ignore prior slides when they exist).

Descriptions of ALL PREVIOUS slides (none if this is the first slide):
{previous_descriptions}

Task: Describe ONLY the current slide image. Be specific: visible titles, bullet text you can read, diagrams, and how this slide relates to the narrative suggested by prior slides.

Return JSON exactly in this shape:
{{"slide_index": <int>, "description": "<detailed plain text, 3-8 sentences>"}}

Current slide index: {slide_index}
"""


def run_slide_description_agent(slide_images_dir: Path, out_path: Path) -> None:
    pngs = sorted(slide_images_dir.glob("slide_*.png"))
    if not pngs:
        raise FileNotFoundError(f"No slide_*.png under {slide_images_dir}")

    slides: list[dict] = []

    for png in pngs:
        name = png.stem
        try:
            idx = int(name.split("_", 1)[1])
        except (IndexError, ValueError) as e:
            raise ValueError(f"Bad slide filename: {png.name}") from e

        prev_text = (
            "\n\n".join(
                f"Slide {s['slide_index']}: {s['description']}" for s in slides
            )
            if slides
            else "(none — this is the first slide.)"
        )
        prompt = PROMPT.format(
            previous_descriptions=prev_text,
            slide_index=idx,
        )
        data = generate_json_with_image(prompt, str(png))
        if data.get("slide_index") != idx:
            data["slide_index"] = idx
        slides.append({"slide_index": idx, "description": data["description"]})

    payload = {"slides": slides}
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
