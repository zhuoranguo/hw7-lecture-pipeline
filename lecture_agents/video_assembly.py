"""Mux slide PNGs with MP3s and concatenate to one MP4 using MoviePy (no system ffmpeg)."""

from __future__ import annotations

import json
from pathlib import Path

from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

# Still image video: one frame rate for encoding; clip length = audio duration (no silent tail).
_DEFAULT_FPS = 24


def assemble_video(
    slide_images_dir: Path,
    audio_dir: Path,
    narration_path: Path,
    output_mp4: Path,
    fps: int = _DEFAULT_FPS,
) -> None:
    data = json.loads(narration_path.read_text(encoding="utf-8"))
    slides = sorted(data["slides"], key=lambda s: int(s["slide_index"]))

    segments: list[ImageClip] = []
    final = None
    try:
        for s in slides:
            idx = s["slide_index"]
            png = slide_images_dir / f"slide_{idx:03d}.png"
            mp3 = audio_dir / f"slide_{idx:03d}.mp3"
            if not png.is_file():
                raise FileNotFoundError(f"Missing PNG: {png}")
            if not mp3.is_file():
                raise FileNotFoundError(f"Missing MP3: {mp3}")

            audio = AudioFileClip(mp3.as_posix())
            duration = audio.duration
            if duration is None or duration <= 0:
                audio.close()
                raise RuntimeError(f"Invalid audio duration for {mp3}")

            still = (
                ImageClip(png.as_posix(), duration=duration)
                .with_fps(fps)
                .with_audio(audio)
            )
            segments.append(still)

        final = concatenate_videoclips(segments, method="chain")

        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            output_mp4.as_posix(),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            audio_bitrate="192k",
            preset="medium",
            pixel_format="yuv420p",
            logger=None,
        )
    finally:
        if final is not None:
            final.close()
        for seg in segments:
            try:
                seg.close()
            except Exception:
                pass
