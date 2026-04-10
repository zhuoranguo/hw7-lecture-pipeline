"""Cap very large JSON/text for model prompts while preferring the full assignment document."""

from __future__ import annotations

# Generous cap so typical decks stay intact; avoids blowing context on pathological inputs.
_MAX_DEFAULT = 900_000


def cap_for_model(text: str, max_chars: int = _MAX_DEFAULT) -> str:
    if len(text) <= max_chars:
        return text
    return (
        text[:max_chars]
        + "\n\n[Input truncated here for API context limits; remainder omitted.]\n"
    )
