"""Paths and environment for the pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent

# Official Homework 7 transcript (Lecture 11 Section 2 captions).
DEFAULT_TRANSCRIPT_URL = (
    "https://zlisto.github.io/genAI_social_media/slides_pdf/"
    "MGT%20575%2001-02%20(SP26)_%20%20Generative%20AI%20and%20Social%20Media%20"
    "Lecture%2011%20Section%202_Captions_English%20(United%20States).txt"
)

DEFAULT_PDF_URL = (
    "https://zlisto.github.io/genAI_social_media/slides_pdf/Lecture_17_AI_screenplays.pdf"
)

DEFAULT_TRANSCRIPT_FILENAME = "Lecture_11_Section_2_Captions.txt"
DEFAULT_PDF_FILENAME = "Lecture_17_AI_screenplays.pdf"


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in the environment or a .env file."
        )
    return key


def gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
