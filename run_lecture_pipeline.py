#!/usr/bin/env python3
"""
Entrypoint for Homework 7: PDF slide deck → style profile, agents, TTS, one MP4.

Assignment: https://zlisto.github.io/genAI_social_media/hw7.html
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from lecture_agents.arc_agent import run_arc_agent
from lecture_agents.config import (
    DEFAULT_PDF_FILENAME,
    DEFAULT_PDF_URL,
    DEFAULT_TRANSCRIPT_FILENAME,
    DEFAULT_TRANSCRIPT_URL,
    REPO_ROOT,
)
from lecture_agents.narration_agent import run_narration_agent
from lecture_agents.pdf_raster import rasterize_pdf
from lecture_agents.premise_agent import run_premise_agent
from lecture_agents.slide_description_agent import run_slide_description_agent
from lecture_agents.style_agent import run_style_agent
from lecture_agents.tts_step import run_tts
from lecture_agents.video_assembly import assemble_video


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "hw7-lecture-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Agentic lecture video pipeline (Homework 7).")
    p.add_argument(
        "--transcript",
        type=Path,
        default=REPO_ROOT / DEFAULT_TRANSCRIPT_FILENAME,
        help="Path to Lecture 11 Section 2 captions .txt",
    )
    p.add_argument(
        "--pdf",
        type=Path,
        default=REPO_ROOT / DEFAULT_PDF_FILENAME,
        help="Path to Lecture 17 PDF at repo root",
    )
    p.add_argument(
        "--style-out",
        type=Path,
        default=REPO_ROOT / "style.json",
        help="Output path for style.json (default: repo root)",
    )
    p.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Use an existing project folder instead of creating project_YYYYMMDD_HHMMSS",
    )
    p.add_argument(
        "--fetch-missing",
        action="store_true",
        help="Download transcript and/or PDF from course URLs if files are missing",
    )
    p.add_argument(
        "--tts-voice",
        default="en-US-GuyNeural",
        help="edge-tts voice name (see `edge-tts --list-voices`)",
    )
    p.add_argument("--skip-style", action="store_true")
    p.add_argument("--skip-slides", action="store_true")
    p.add_argument("--skip-premise", action="store_true")
    p.add_argument("--skip-arc", action="store_true")
    p.add_argument("--skip-narration", action="store_true")
    p.add_argument("--skip-tts", action="store_true")
    p.add_argument("--skip-video", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    transcript_path: Path = args.transcript
    pdf_path: Path = args.pdf

    if args.fetch_missing:
        if not transcript_path.is_file():
            print(f"Downloading transcript → {transcript_path}")
            download(DEFAULT_TRANSCRIPT_URL, transcript_path)
        if not pdf_path.is_file():
            print(f"Downloading PDF → {pdf_path}")
            download(DEFAULT_PDF_URL, pdf_path)

    if not transcript_path.is_file():
        print(
            f"Transcript not found: {transcript_path}\n"
            "Place the Lecture 11 Section 2 captions file there or run with --fetch-missing.",
            file=sys.stderr,
        )
        return 1
    if not pdf_path.is_file():
        print(
            f"PDF not found: {pdf_path}\n"
            "Place Lecture_17_AI_screenplays.pdf at the repo root or run with --fetch-missing.",
            file=sys.stderr,
        )
        return 1

    if args.project_dir:
        project_dir = args.project_dir.resolve()
        project_dir.mkdir(parents=True, exist_ok=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = (REPO_ROOT / "projects" / f"project_{stamp}").resolve()
        project_dir.mkdir(parents=True, exist_ok=True)

    slide_images = project_dir / "slide_images"
    audio_dir = project_dir / "audio"
    # Empty dirs exist before media is written (assignment allows committing empty slide_images/ + audio/).
    slide_images.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    slide_desc = project_dir / "slide_description.json"
    premise_path = project_dir / "premise.json"
    arc_path = project_dir / "arc.json"
    narration_path = project_dir / "slide_description_narration.json"
    style_out: Path = args.style_out

    print(f"Project directory: {project_dir}")

    if not args.skip_style:
        print("Stage: style.json from transcript…")
        run_style_agent(transcript_path.read_text(encoding="utf-8", errors="replace"), style_out)
    else:
        print("Skipping style stage.")

    if not args.skip_slides:
        print("Stage: rasterize PDF…")
        n = rasterize_pdf(pdf_path, slide_images)
        print(f"  Wrote {n} PNGs under {slide_images}")
        print("Stage: slide descriptions (vision + prior chaining)…")
        run_slide_description_agent(slide_images, slide_desc)
    else:
        print("Skipping slide raster + descriptions.")

    if not args.skip_premise:
        print("Stage: premise.json…")
        run_premise_agent(slide_desc, premise_path)
    else:
        print("Skipping premise.")

    if not args.skip_arc:
        print("Stage: arc.json…")
        run_arc_agent(premise_path, slide_desc, arc_path)
    else:
        print("Skipping arc.")

    if not args.skip_narration:
        print("Stage: narrations…")
        run_narration_agent(
            style_path=style_out,
            premise_path=premise_path,
            arc_path=arc_path,
            slide_description_path=slide_desc,
            slide_images_dir=slide_images,
            out_path=narration_path,
        )
    else:
        print("Skipping narration.")

    if not args.skip_tts:
        print("Stage: TTS (edge-tts)…")
        run_tts(narration_path, audio_dir, voice=args.tts_voice)
    else:
        print("Skipping TTS.")

    if not args.skip_video:
        stem = pdf_path.stem
        out_mp4 = project_dir / f"{stem}.mp4"
        print("Stage: MoviePy video assembly…")
        assemble_video(slide_images, audio_dir, narration_path, out_mp4)
        print(f"Done. Video: {out_mp4}")
    else:
        print("Skipping video assembly.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
