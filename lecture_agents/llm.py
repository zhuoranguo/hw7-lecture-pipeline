"""Gemini text + vision calls with JSON extraction."""

from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai
from PIL import Image

from lecture_agents.config import api_key, gemini_model_name

_CONFIGURED = False


def _response_text(resp: Any) -> str:
    """Collect text parts; strip. Whitespace-only counts as empty (avoids bogus JSON parse at col 0)."""
    chunks: list[str] = []
    try:
        t = getattr(resp, "text", None)
        if t is not None and str(t).strip():
            chunks.append(str(t))
    except Exception:
        pass
    if not chunks:
        cands = getattr(resp, "candidates", None) or []
        for c in cands:
            content = getattr(c, "content", None)
            if not content:
                continue
            for p in getattr(content, "parts", None) or []:
                tx = getattr(p, "text", None)
                if tx:
                    chunks.append(tx)
    out = "".join(chunks).strip()
    if not out:
        fb = getattr(resp, "prompt_feedback", None)
        block = getattr(fb, "block_reason", None) if fb else None
        fr = None
        cands = getattr(resp, "candidates", None) or []
        if cands:
            fr = getattr(cands[0], "finish_reason", None)
        extra = f" block_reason={block!r} finish_reason={fr!r}" if block or fr else ""
        raise RuntimeError(
            "Empty or blocked model response (no text parts after strip)." + extra
        )
    return out


def _ensure_configured() -> None:
    global _CONFIGURED
    if not _CONFIGURED:
        genai.configure(api_key=api_key())
        _CONFIGURED = True


def _json_model() -> genai.GenerativeModel:
    """Model configured so Gemini emits syntactically valid JSON (handles quotes inside strings)."""
    _ensure_configured()
    return genai.GenerativeModel(
        gemini_model_name(),
        generation_config={"response_mime_type": "application/json"},
    )


def _response_to_dict(resp: Any) -> dict[str, Any]:
    raw = _response_text(resp)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        preview = (raw[:800] + "…") if len(raw) > 800 else raw
        raise json.JSONDecodeError(
            f"Invalid JSON from model (expected application/json). Preview: {preview!r}",
            raw,
            e.pos,
        ) from e
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object, got {type(data).__name__}")
    return data


def generate_text(system_and_user: str) -> str:
    _ensure_configured()
    model = genai.GenerativeModel(gemini_model_name())
    resp = model.generate_content(system_and_user)
    return _response_text(resp)


def generate_json_from_prompt(prompt: str) -> dict[str, Any]:
    model = _json_model()
    full = (
        prompt
        + "\n\nRespond with a single JSON object matching the schema described above."
    )
    resp = model.generate_content(full)
    return _response_to_dict(resp)


def generate_json_with_image(prompt: str, image_path: str) -> dict[str, Any]:
    model = _json_model()
    img = Image.open(image_path).convert("RGB")
    full = (
        prompt
        + "\n\nRespond with a single JSON object matching the schema described above."
    )
    resp = model.generate_content([full, img])
    return _response_to_dict(resp)
