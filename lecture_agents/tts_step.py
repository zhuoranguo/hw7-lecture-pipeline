"""Synthesize per-slide narration to MP3 via edge-tts (chunk + merge when needed)."""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path

import edge_tts
from moviepy import AudioFileClip, concatenate_audioclips

from lecture_agents.text_chunking import chunk_text_for_tts


async def _synthesize_one(text: str, out_mp3: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_mp3.as_posix())


async def _synthesize_slide_merged(text: str, out_mp3: Path, voice: str) -> None:
    chunks = chunk_text_for_tts(text)
    if len(chunks) == 1:
        await _synthesize_one(chunks[0], out_mp3, voice)
        return

    tmpdir = Path(tempfile.mkdtemp(prefix="tts_chunks_"))
    clip_paths: list[Path] = []
    audio_clips: list[AudioFileClip] = []
    merged = None
    try:
        for i, ch in enumerate(chunks):
            p = tmpdir / f"part_{i:04d}.mp3"
            await _synthesize_one(ch, p, voice)
            clip_paths.append(p)

        audio_clips = [AudioFileClip(p.as_posix()) for p in clip_paths]
        merged = concatenate_audioclips(audio_clips)
        merged.write_audiofile(out_mp3.as_posix(), codec="libmp3lame", logger=None)
    finally:
        if merged is not None:
            merged.close()
        for c in audio_clips:
            try:
                c.close()
            except Exception:
                pass
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_tts(
    narration_path: Path,
    audio_dir: Path,
    voice: str = "en-US-GuyNeural",
) -> None:
    audio_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(narration_path.read_text(encoding="utf-8"))
    slides = data["slides"]

    async def _run_all() -> None:
        for s in slides:
            idx = s["slide_index"]
            text = s["narration"].strip()
            out_mp3 = audio_dir / f"slide_{idx:03d}.mp3"
            await _synthesize_slide_merged(text, out_mp3, voice)

    asyncio.run(_run_all())
