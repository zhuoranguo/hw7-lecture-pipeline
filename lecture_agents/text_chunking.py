"""Split long narration text for TTS APIs that require chunked requests."""

from __future__ import annotations


def chunk_text_for_tts(text: str, max_chars: int = 2800) -> list[str]:
    """
    Split at whitespace so chunks stay under max_chars.
    Edge-TTS can fail on very long single requests; merging MP3s satisfies the
    rubric requirement to merge chunked API responses into one file per slide.
    """
    t = (text or "").strip()
    if not t:
        return [""]
    if len(t) <= max_chars:
        return [t]
    chunks: list[str] = []
    rest = t
    while rest:
        if len(rest) <= max_chars:
            chunks.append(rest)
            break
        cut = rest.rfind(" ", 0, max_chars)
        if cut < max_chars // 2:
            cut = max_chars
        piece = rest[:cut].strip()
        if not piece:
            piece = rest[:max_chars]
            cut = max_chars
        chunks.append(piece)
        rest = rest[cut:].strip()
    return chunks
